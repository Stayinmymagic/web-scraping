# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json

class GetProxyPipeline:
    def process_item(self, item, spider):
        return item

class JsonWriterPipeline(object):

    def open_spider(self, spider):
        self.file = open('proxy_list.json', 'w+')
        self.file.write('[')
    def close_spider(self, spider):
        
        self.file.write('{}]')
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + ",\n"
        self.file.write(line)
        return item
