# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
# from webscraper.models import Judge
# from scrapy_djangoitem import DjangoItem

class JudgmentItem(scrapy.Item):
    pid =  scrapy.Field()
    name = scrapy.Field()
    court = scrapy.Field()
    crime_type = scrapy.Field()
    event_time = scrapy.Field()
    event_age =  scrapy.Field()
    amount = scrapy.Field()
    company = scrapy.Field()
    map_family = scrapy.Field() # 是否配對到父母名
    map_address = scrapy.Field() # 是否配對到地址
    # ccis_company = scrapy.Field() # 是否配對到拒往備查公司名
    link = scrapy.Field()

