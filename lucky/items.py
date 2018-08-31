# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class LuckyItem(scrapy.Item):
    # define the fields for your item here like:
    periodName = scrapy.Field()
    awardNo = scrapy.Field()
    awardTime = scrapy.Field()
    pass
