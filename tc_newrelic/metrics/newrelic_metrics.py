import os
import time
import requests
from thumbor.metrics import BaseMetrics


class Metrics(BaseMetrics):
    """
    Thumbor Metrics class for New Relic
    """

    @classmethod
    def session(cls, config):
        """
        Cached New Relic session for sending metrics.
        """
        if not hasattr(cls, "_session"):
            cls._session = requests.Session()
            cls._session.headers.update({
                "Api-Key": config.NEW_RELIC_API_KEY,
                "Content-Type": "application/json"
            })
            cls._new_relic_url = config.NEW_RELIC_API_ENDPOINT

        return cls._session

    def incr(self, metricname, value=1):
        """
        Increments a counter metric in New Relic.
        """
        metric_data = [{
            "name": self._prefixed_name(metricname),
            "type": "count",
            "value": value,
            "interval.ms": 500,
            "timestamp": time.time()
        }]
        self._send_metrics(metric_data)

    def timing(self, metricname, value):
        """
        Records a timing metric in New Relic.
        """
        metric_data = [{
            "name": self._prefixed_name(metricname),
            "type": "gauge",
            "value": value,
            "timestamp": time.time()
        }]
        self._send_metrics(metric_data)

    def _send_metrics(self, metrics):
        """
        Sends the given metrics to New Relic.
        """
        session = Metrics.session(self.config)

        payload = [{
            "common": {
                "attributes": {
                    "app.name": self.config.NEW_RELIC_APP_NAME
                }
            },
            "metrics": metrics
        }]

        response = session.post(self._new_relic_url, json=payload)

        if response.status_code != 202:
            print(f"New Relic API Error: {response.status_code} - {response.text}")

    def _prefixed_name(self, metricname):
        """
        Prefixes metric names for better organization.
        """
        return "%s.%s" % (self.config.NEW_RELIC_NAME_PREFIX, metricname)
