# coding: utf-8
from thumbor.config import Config

Config.define('NEW_RELIC_API_KEY', None, 'New Relic API key', 'Metrics')
Config.define('NEW_RELIC_API_ENDPOINT', 'https://metric-api.newrelic.com/metric/v1', 'New Relic API Endpoint', 'Metrics')
Config.define('NEW_RELIC_APP_NAME', 'thumbor', 'New Relic application name', 'Metrics')
Config.define('NEW_RELIC_NAME_PREFIX', 'thumbor', 'New Relic metrics prefix', 'Metrics')
