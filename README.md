# Thumbor NewRelic Metrics Plugin

Send Thumbor runtime metrics to your NewRelic account.

## Status


## Installation

```bash
# master branch
pip install -e git://github.com/thumbor-community/newrelic.git@master#egg=tc_newrelic

# latest stable
pip install tc_newrelic
```

## Configuration

```python
# thumbor.conf
METRICS = 'tc_newrelic.metrics.newrelic_metrics'

NEW_RELIC_API_KEY = 'username' # New Relic API key
NEW_RELIC_APP_NAME = 'thumbor' # New Relic application name

# optional with defaults
NEW_RELIC_NAME_PREFIX = 'thumbor' # New Relic metrics prefix
```