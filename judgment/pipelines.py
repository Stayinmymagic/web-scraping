# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import sqlite3
from datetime import datetime
import mysql.connector
class AgeFilterPipeline:
    def process_item(self, item, spider):
        if item['event_age'] < 20:
            raise DropItem(f"年紀小於 20")
        return item

class DropDuplicatesPipeline:
    def __init__(self):
        self.article = set()
    def process_item(self, item, spider):
        link = item['link'] 
        if link in self.article:
            raise DropItem('duplicates link found %s', item)
        self.article.add(link)
        return item
# class SavePipeline:
#     def process_item(self, item, spider):
#         item.save()
#         print("save item")
#         return item

class SavePipeline:   
    def __init__(self):
        # self.conn = sqlite3.connect('scrapy.db')
        # self.cur = self.conn.cursor()
        self.conn = mysql.connector.connect(
        host='HostName',          # 主機名稱
        database='<DatabaseName>', # 資料庫名稱
        user='UserName',        # 帳號
        password='Password')  # 密碼

        self.cur = self.conn.cursor()
    def process_item(self, item, spider):
        print(item)
        self.cur.execute("""INSERT INTO scrapy_history (pid, name, court, crime_type, event_time,
                            event_age, amount, company, map_family, map_address, link , create_time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (
                                item['pid'],item['name'],item['court'],item['crime_type'],item['event_time'],item['event_age'],
                                item['amount'],item['company'],item['map_family'],item['map_address'],item['link'], datetime.now().strftime("%Y-%m-%d")
                            ))

        self.conn.commit()
        return item
    
    def close_spider(self, spider):
        self.conn.close()

class ScrapyprefectPipeline(object):
    def process_item(self, item, spider):
        return item



