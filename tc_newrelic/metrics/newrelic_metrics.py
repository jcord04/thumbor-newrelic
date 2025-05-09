#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license

import json
import time
import logging
import threading
import requests
import sys
from urllib.parse import urlparse
from thumbor.metrics import BaseMetrics

# Configure logging
logger = logging.getLogger('thumbor.metrics.newrelic')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.WARNING)

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
        self.license_key = config.NEWRELIC_LICENSE_KEY
        self.metric_api_url = config.NEWRELIC_METRIC_API_URL
        self.app_name = config.NEWRELIC_APP_NAME
        
        # Convert interval to integer if it's a string
        if isinstance(config.NEWRELIC_SEND_INTERVAL_SECONDS, str):
            self.send_interval_seconds = int(config.NEWRELIC_SEND_INTERVAL_SECONDS)
        else:
            self.send_interval_seconds = config.NEWRELIC_SEND_INTERVAL_SECONDS

        # Ensure we have a license key
        if not self.license_key:
            logger.error("NEWRELIC_LICENSE_KEY is not set in the configuration")
            logger.error("Please add NEWRELIC_LICENSE_KEY = 'your-license-key' to your thumbor.conf")
            return
        
        logger.info(f"Initializing New Relic metrics plugin with app_name={self.app_name}, " 
                   f"send_interval={self.send_interval_seconds}s, "
                   f"api_url={self.metric_api_url}")

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
            interval_ms = self.send_interval_seconds * 1000  # Convert to milliseconds
            
            # Process counters - using interval.ms required for count type
            counter_count = 0
            for name, value in Metrics.counters.items():
                # Simplify the metric name
                metric_name, attributes = self._simplify_metric_name(name)
                
                # Add app name attribute
                attributes["app.name"] = self.app_name
                
                # New Relic count metric requires interval.ms
                metric_data = {
                    "name": f"custom.thumbor.{metric_name}",
                    "type": "count",
                    "value": value,
                    "timestamp": timestamp_ms,
                    "interval.ms": interval_ms,  # Required for count metrics!
                    "attributes": attributes
                }
                metrics_data.append(metric_data)
                counter_count += 1
            
            if counter_count > 0:
                logger.debug(f"Prepared {counter_count} counter metrics for sending")
            
            # Process summaries
            summary_count = 0
            for name, data in Metrics.summaries.items():
                # Simplify the metric name
                metric_name, attributes = self._simplify_metric_name(name)
                
                # Add app name attribute
                attributes["app.name"] = self.app_name
                
                # Ensure summary data has required fields with valid values
                summary_value = {
                    "count": data.get("count", 0),
                    "sum": float(data.get("sum", 0)),  # Ensure it's a float
                    "min": float(data.get("min", 0)) if data.get("min", float('inf')) != float('inf') else 0,
                    "max": float(data.get("max", 0))
                }
                
                # For summaries, send summary metrics
                summary_data = {
                    "name": f"custom.thumbor.{metric_name}",
                    "type": "summary",
                    "value": summary_value,
                    "timestamp": timestamp_ms,
                    "interval.ms": interval_ms,  # Also include for summaries
                    "attributes": attributes
                }
                metrics_data.append(summary_data)
                summary_count += 1
                
            if summary_count > 0:
                logger.debug(f"Prepared {summary_count} summary metrics for sending")
            
            # Process gauges
            gauge_count = 0
            for name, value in Metrics.gauges.items():
                # Simplify the metric name
                metric_name, attributes = self._simplify_metric_name(name)
                
                # Add app name attribute
                attributes["app.name"] = self.app_name
                
                gauge_data = {
                    "name": f"custom.thumbor.{metric_name}",
                    "type": "gauge",
                    "value": float(value),  # Ensure it's a float
                    "timestamp": timestamp_ms,
                    "attributes": attributes
                }
                metrics_data.append(gauge_data)
                gauge_count += 1
                
            if gauge_count > 0:
                logger.debug(f"Prepared {gauge_count} gauge metrics for sending")
            
            # Skip if no metrics to send
            if not metrics_data:
                logger.debug("No metrics to send in this interval")
                return
                
            logger.info(f"Sending {len(metrics_data)} metrics to New Relic")
            
            # Send to New Relic
            payload = [{"metrics": metrics_data}]
            headers = {
                "Content-Type": "application/json",
                "Api-Key": self.license_key
            }
            
            try:
                logger.debug(f"Sending payload to New Relic: {json.dumps(payload)}")
                
                response = requests.post(
                    self.metric_api_url,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=10  # Add a timeout to prevent hanging
                )
                
                logger.debug(f"New Relic API response: status={response.status_code}, body={response.text}")
                
                if response.status_code != 202:  # New Relic API returns 202 for success
                    logger.error(f"Failed to send metrics to New Relic: {response.status_code} {response.text}")
                else:
                    logger.info(f"Successfully sent {len(metrics_data)} metrics to New Relic")
            except Exception as e:
                logger.error(f"Exception sending metrics to New Relic: {str(e)}")
                
            # Clear metrics after sending
            Metrics.counters = {}
            Metrics.summaries = {}
            Metrics.gauges = {}

    def _simplify_metric_name(self, name):
        """
        Simplify complex metric names and extract attributes
        
        For example:
        "response.status.statuscode:200" -> ("response.status", {"statuscode": "200"})
        """
        attributes = {}
        parts = name.split('.')
        
        # Check for labels in the format "key:value"
        main_parts = []
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                attributes[key] = value
            else:
                main_parts.append(part)
        
        # If we have a metric like "original_image.fetch.statuscode:200.networklocation:example.com"
        # we want to extract both statuscode and networklocation as attributes
        if len(main_parts) >= 2:
            base_name = '.'.join(main_parts)
            return base_name, attributes
        
        # Otherwise just return the name with any extracted attributes
        return name, attributes

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
            
            logger.debug(f"Incremented metric {metric_key} by {value}, new value: {Metrics.counters[metric_key]}")

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