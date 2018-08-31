# -*- coding: utf-8 -*-
# Author: leven

from scrapy.cmdline import execute
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
execute(['scrapy','crawl','shishicai1'])
# execute(['scrapy','crawl','boleDetailTopic'])
# execute(['scrapy','crawl','boleUser'])