# coding: utf-8
from thumbor.config import Config

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license

__version__ = '1.0.0'

Config.define('NEWRELIC_LICENSE_KEY', None, 'New Relic API key', 'Metrics')
Config.define('NEWRELIC_METRIC_API_URL', 'https://metric-api.newrelic.com/metric/v1', 'New Relic API Endpoint', 'Metrics')
Config.define('NEWRELIC_APP_NAME', 'thumbor', 'New Relic application name', 'Metrics')
Config.define('NEWRELIC_SEND_INTERVAL_SECONDS', '15', 'New Relic metrics prefix', 'Metrics')
