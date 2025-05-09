# Thumbor NewRelic Metrics Plugin

Send Thumbor runtime metrics to your NewRelic account.

## Status


## Installation

```bash
# master branch
pip install -e git+https://github.com/jcord04/thumbor-newrelic.git@master#egg=tc_newrelic

# latest stable
pip install tc_newrelic
```

## Configuration

```python
# Use New Relic metrics instead of the default
METRICS = 'tc_newrelic.metrics.newrelic_metrics'

# Required: Your New Relic License Key
NEWRELIC_LICENSE_KEY = 'your_license_key_here'

# Optional configurations with defaults
NEWRELIC_METRIC_API_URL = 'https://metric-api.newrelic.com/metric/v1'  # Change for EU or other regions
NEWRELIC_APP_NAME = 'Thumbor'  # The application name in New Relic
NEWRELIC_SEND_INTERVAL_SECONDS = 15  # How often to send metrics (in seconds)

```
## Metrics

This plugin collects the same metrics as the Prometheus plugin for Thumbor and forwards them to New Relic. The metrics are sent with the prefix `custom.thumbor.` to distinguish them in New Relic.

The following metrics are collected:

- `response.status` - HTTP status codes of responses
- `response.format` - Format of responses
- `response.bytes` - Size of responses in bytes
- `response.time` - Response time
- `original_image.status` - Status of original image fetches
- `original_image.fetch` - Time to fetch original images

## Viewing Metrics in New Relic

You can view the metrics in New Relic using NRQL queries. For example:

```sql
SELECT count(*) FROM Metric WHERE metricName LIKE 'custom.thumbor.%' FACET metricName SINCE 1 hour ago TIMESERIES
```

Or create a dashboard with specific metrics:

```sql
SELECT sum(value) FROM Metric WHERE metricName = 'custom.thumbor.response.status' AND statuscode = '200' SINCE 1 day ago TIMESERIES
```

## Multiple Processes Support

If running Thumbor with multiple processes, you should be able to use this plugin without any additional configuration. The metrics are aggregated in-memory and sent to New Relic periodically.

## License

This project is licensed under the MIT License - see the LICENSE file for details.