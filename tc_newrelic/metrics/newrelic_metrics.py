#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license

import json
import time
import logging
import threading
import requests
from urllib.parse import urlparse
from thumbor.metrics import BaseMetrics

logger = logging.getLogger('thumbor.metrics.newrelic')

class Metrics(BaseMetrics):
    """
    Thumbor metrics implementation that forwards metrics to New Relic
    """

    def __init__(self, config):
        """
        Initialize the New Relic metrics forwarder
        """
        super().__init__(config)

        # Get configuration options
        self.license_key = getattr(config, 'NEWRELIC_LICENSE_KEY', None)
        self.metric_api_url = getattr(config, 'NEWRELIC_METRIC_API_URL', 'https://metric-api.newrelic.com/metric/v1')
        self.app_name = getattr(config, 'NEWRELIC_APP_NAME', 'Thumbor')
        self.send_interval_seconds = getattr(config, 'NEWRELIC_SEND_INTERVAL_SECONDS', 15)

        # Ensure we have a license key
        if not self.license_key:
            logger.error("NEWRELIC_LICENSE_KEY is required for the New Relic metrics plugin")
            return

        # Data structures for metrics
        if not hasattr(Metrics, 'counters'):
            Metrics.counters = {}
            Metrics.summaries = {}
            Metrics.gauges = {}
            Metrics.last_sent = time.time()
            Metrics.lock = threading.RLock()
            Metrics.timer_started = False

        # Start the timer to periodically send metrics
        if not Metrics.timer_started:
            threading.Thread(target=self._send_metrics_periodically, daemon=True).start()
            Metrics.timer_started = True

        # Similar to the Prometheus plugin, define metric mapping
        self.mapping = {
            'response.status': ['statuscode'],
            'response.format': ['extension'],
            'response.bytes': ['extension'],
            'response.time': ['statuscode_extension'],
            'original_image.status': ['statuscode', 'networklocation'],
            'original_image.fetch': ['statuscode', 'networklocation'],
        }

    def _send_metrics_periodically(self):
        """
        Periodically send metrics to New Relic
        """
        while True:
            time.sleep(1)  # Check every second
            current_time = time.time()
            
            if current_time - Metrics.last_sent >= self.send_interval_seconds:
                try:
                    self._send_metrics_to_newrelic()
                    Metrics.last_sent = current_time
                except Exception as e:
                    logger.error(f"Error sending metrics to New Relic: {str(e)}")

    def _send_metrics_to_newrelic(self):
        """
        Send collected metrics to New Relic
        """
        with Metrics.lock:
            # Prepare metrics for New Relic format
            metrics_data = []
            timestamp_ms = int(time.time() * 1000)
            
            # Process counters
            for name, value in Metrics.counters.items():
                # New Relic expects "count" type metric
                metric_data = {
                    "name": f"custom.thumbor.{name}",
                    "type": "count",
                    "value": value,
                    "timestamp": timestamp_ms,
                    "attributes": {
                        "app.name": self.app_name
                    }
                }
                metrics_data.append(metric_data)
            
            # Process summaries
            for name, data in Metrics.summaries.items():
                # For summaries, send both count and summary metrics
                summary_data = {
                    "name": f"custom.thumbor.{name}",
                    "type": "summary",
                    "value": {
                        "count": data.get("count", 0),
                        "sum": data.get("sum", 0),
                        "min": data.get("min", 0),
                        "max": data.get("max", 0)
                    },
                    "timestamp": timestamp_ms,
                    "attributes": {
                        "app.name": self.app_name
                    }
                }
                metrics_data.append(summary_data)
            
            # Process gauges
            for name, value in Metrics.gauges.items():
                gauge_data = {
                    "name": f"custom.thumbor.{name}",
                    "type": "gauge",
                    "value": value,
                    "timestamp": timestamp_ms,
                    "attributes": {
                        "app.name": self.app_name
                    }
                }
                metrics_data.append(gauge_data)
            
            # Clear metrics after sending
            Metrics.counters = {}
            Metrics.summaries = {}
            Metrics.gauges = {}
            
            # Skip if no metrics to send
            if not metrics_data:
                return
            
            # Send to New Relic
            payload = [{"metrics": metrics_data}]
            headers = {
                "Content-Type": "application/json",
                "Api-Key": self.license_key
            }
            
            response = requests.post(
                self.metric_api_url,
                headers=headers,
                data=json.dumps(payload)
            )
            
            if response.status_code != 202:  # New Relic API returns 202 for success
                logger.error(f"Failed to send metrics to New Relic: {response.status_code} {response.text}")
            else:
                logger.debug(f"Successfully sent {len(metrics_data)} metrics to New Relic")

    def incr(self, metricname, value=1):
        """
        Increment a counter metric
        """
        name, labels = self._parse_metric(metricname)
        
        with Metrics.lock:
            # Store the counter with its labels
            metric_key = self._get_metric_key(name, labels)
            
            if metric_key not in Metrics.counters:
                Metrics.counters[metric_key] = 0
                
            Metrics.counters[metric_key] += value

    def timing(self, metricname, value):
        """
        Record a timing metric (as summary in New Relic)
        """
        name, labels = self._parse_metric(metricname)
        
        with Metrics.lock:
            # Store the timing data as a summary
            metric_key = self._get_metric_key(name, labels)
            
            if metric_key not in Metrics.summaries:
                Metrics.summaries[metric_key] = {
                    "count": 0,
                    "sum": 0,
                    "min": float('inf'),
                    "max": 0
                }
                
            summary = Metrics.summaries[metric_key]
            summary["count"] += 1
            summary["sum"] += value
            summary["min"] = min(summary["min"], value)
            summary["max"] = max(summary["max"], value)

    def _parse_metric(self, metricname):
        """
        Parse a metric name into name and labels
        """
        # Find the base name for the metric
        basename = metricname
        for mapped in self.mapping.keys():
            if metricname.startswith(mapped + "."):
                basename = mapped
                break
        
        # Get labels from the metric name
        labels = {}
        if basename in self.mapping:
            # Extract label values from the metric name
            values = metricname.replace(basename + '.', '').split('.', len(self.mapping[basename])-1)
            for index, label in enumerate(self.mapping[basename]):
                if index < len(values):
                    labels[label] = values[index]
        
        return basename, labels

    def _get_metric_key(self, name, labels):
        """
        Generate a unique key for a metric based on its name and labels
        """
        if not labels:
            return name
            
        # Sort labels by key to ensure consistent ordering
        sorted_labels = sorted(labels.items())
        label_str = ".".join(f"{key}:{value}" for key, value in sorted_labels if value is not None)
        
        return f"{name}.{label_str}" if label_str else name
    