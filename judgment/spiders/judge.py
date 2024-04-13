import scrapy
from scrapy import FormRequest, Request
import sqlite3
import pandas as pd
import lxml
import re
from ..items import JudgmentItem
from .utils import parse_event_time
import datetime
# from django.conf import settings
# from django.utils.timezone import make_aware
# settings.TIME_ZONE  # 'UTC'

def connect_sqlite(id):
    con = sqlite3.connect('./scrapy.db')
    cur = con.cursor()
    cur.execute("select * from lender where id = '%s';"%id)
    return cur.fetchall()

def get_code(lender_info):
    high_court = {'臺中' : 'TCH', '臺南': 'TNH', '高雄': 'KSH', '花蓮':'HLH'}
    check_court = set(['TPD', 'SLD'])
    court_code = pd.read_csv('./data/court_code_v2.csv')
    court_dict = dict(zip(list(court_code['Court Code']),list(court_code['Court Name'])))
    for i in ['residenceAddress','companyAddress','currentAddress']:
        if lender_info[i] != '' and lender_info[i] != None: 
            lender_info[i] = lender_info[i].replace('台', '臺')
            try:
                check_court.add(court_code.loc[court_code['Court Name'] == lender_info[i][:2],'Court Code'].values[0])
            except:
                pass
            if i in high_court.keys():
                check_court.add(high_court[i])
    return check_court, court_dict

class JudgeSpider(scrapy.Spider):
    name = 'judge'
    allowed_domains = ['judgment.judicial.gov.tw']
    start_urls = ['https://judgment.judicial.gov.tw/FJUD/default.aspx']



    def __init__(self,id = '', url = ''):
        self.id = id 
        self.proxy = url
        # id, name, currentAddress, old, fatherName, motherName, companyAddress, residenceAddress
        super(JudgeSpider, self).__init__()  # python3
            # get lender name, age, parent's name, addresses
        lender = connect_sqlite(id)
        
        dict_key = ['index','id','name','currentAddress','fatherName', 'motherName','companyAddress','residenceAddress','age']
        self.lender_info = dict(zip(dict_key, lender[0]))
        
        # 把居住地 -> 法院代碼
        self.check_court, self.court_dict = get_code(self.lender_info)

    def parse(self, response, **kwargs):
        __VIEWSTATE = response.xpath('//*[@name="__VIEWSTATE"]/@value').get()
        __VIEWSTATEENCRYPTED = response.xpath('//*[@name="__VIEWSTATEENCRYPTED"]/@value').get()
        __VIEWSTATEGENERATOR = response.xpath('//*[@name="__VIEWSTATEGENERATOR"]/@value').get()
        __EVENTVALIDATION = response.xpath('//*[@name="__EVENTVALIDATION"]/@value').get()
        txtKW = self.lender_info['name']
        judtype = 'JUDBOOK'
        whosub = '0'
        
        form = {
            '__VIEWSTATE': __VIEWSTATE,
            '__VIEWSTATEGENERATOR': __VIEWSTATEGENERATOR,
            '__VIEWSTATEENCRYPTED': __VIEWSTATEENCRYPTED,
            '__EVENTVALIDATION':__EVENTVALIDATION,
            'txtKW' : txtKW,
            'judtype': judtype,
            'whosub' : whosub,
            'ctl00$cp_content$btnSimpleQry' : "送出查詢"
        }

        yield FormRequest('https://judgment.judicial.gov.tw/FJUD/default.aspx',
                        formdata=form,
                        callback=self.parse_court,
                        meta = {'proxy': self.proxy})

    # 進入貸款人居住地、工作地、戶籍地的縣市+台北、士林地院搜尋結果分頁
    def parse_court(self, response):
        url = response.css('iframe::attr(src)').extract()[0]

        for i in list(self.check_court):
            yield Request('https://judgment.judicial.gov.tw/FJUD/' + url + "&gy=jcourt&gc=" + i,
                                method = 'GET',
                                callback=self.parse_pages,
                                meta={'court': self.court_dict[i],
                                      'proxy':self.proxy})

    def parse_pages(self, response):
        # 從每一個分頁中抓出裁判書連結
        for j in response.xpath('//a'):
            href_to_save= j.xpath('./@href').get()
            if 'data' in href_to_save:
                case_href = "https://judgment.judicial.gov.tw/FJUD/" + href_to_save
                # case_href = "https://judgment.judicial.gov.tw/errorpage.aspx?aspxerrorpath=/FJUD/error.aspx"
                yield Request(case_href,
                            method = 'GET',
                            callback=self.parse_case,
                            meta={'link': case_href,
                                    'court':response.meta.get('court'),
                                    'proxy':self.proxy},
                            dont_filter=True)
                
        # scrape next page
        next_page_url = response.xpath('//*[@id="hlNext"]/@href').get()
        if next_page_url is not None:  
            nextpage_href = "https://judgment.judicial.gov.tw" + next_page_url
            yield Request(nextpage_href,
                            method = 'GET',
                            callback=self.parse_pages,
                            meta={'court':response.meta.get('court'),
                                  'proxy':self.proxy})

    def parse_case(self, response):
        # count = 0
        # while response == None or '系統忙碌中' in response.text or count < 2:
        #     response = yield Request(response.meta.get('link'),
        #                     method = 'GET',
        #                     meta={'link': response.meta.get('link'),
        #                             'court':response.meta.get('court')},
        #                     dont_filter=True)
        #     count +=1

        # fetch all text in response
        response_list = response.xpath("//*[@id=\"jud\"]").extract()
        if len(response_list) == 0:
            items['pid'] = self.lender_info['id']
            items['name'] = self.lender_info['name']
            items['court'] = ''
            items['event_age'] = 21
            items['crime_type'] = ''
            items['event_time'] = None
            items['amount'] = None
            items['company'] = ''
            items['map_family'] = '' 
            items['map_address'] = '' 
            yield items
        else:
            root = lxml.html.fromstring(response_list[0])
            text = lxml.html.tostring(root, method="text", encoding='unicode')
            text = ''.join(text.split())
        
            # 關鍵字
            keywords = ['本票裁定','支付命令' ,'協商認可','詐欺','洗錢防制法','給付簽帳卡', '槍砲彈藥',\
                '定其應執行刑','毒品', '藥事法', '賭博案','消費者債務清理','拋棄繼承','更生事件','消債之前置協商認可事件','清償借款']
            keyman = ['債務人','相對人','被告','受刑人']


            for i in keywords:
                if "裁判案由："+i in text:
                    # 確認keyman是本人
                    for k in keyman:
                        temp = re.findall("%s\S{0,9}\%s"%(k,self.lender_info['name']), text)
                        if len(temp) > 0:
                        # if k+self.lender_info['name'] in text:
                        # initialize item
                            items = JudgmentItem()
                            # 儲存名字
                            items['pid'] = self.lender_info['id']
                            items['name'] = self.lender_info['name']
                            # 儲存法院
                            items['court'] = response.meta.get('court')
                            # 儲存網址
                            link = response.meta.get('link')
                            items['link'] = link
                        
                            #儲存罪名
                            if i == '消債之前置協商認可事件':
                                i = '消債協商認可事件'
                            items['crime_type'] = i
                            # 確認案發時間年紀
                            # event_time = make_aware(parse_event_time(text))
                            event_time = parse_event_time(text)
                            print(type(parse_event_time(text)))
                            event_age = self.lender_info['age'] - (datetime.datetime.now().year - event_time.year)
                            # event_time = str(event_time.date)
                            
                            items['event_time'] = event_time
                            items['event_age'] = event_age
                            if event_age >= 20 :
                                # continue parsing

                                ## find the loan amount =>不太確定抓到的是不是總金額或是剩餘金額
                                try:
                                    amount = re.finditer(r'[0-9,]{2,10}\元', text)
                                    amountlist = []
                                    for m in amount:
                                        amountlist.append(re.sub(",|元", "",m.group()))
                                    amountlist = [int(x) for x in amountlist]
                                    loan_amount = max(amountlist)
                                    items['amount'] = str(loan_amount)+"元"
                                except:
                                    try:
                                        try:
                                            amount = re.findall("新臺幣（下同）\S{1,12}\元", text)
                                            amount = re.sub("新臺幣（下同）", "",amount[0])
                                        except:
                                            amount = re.findall("新臺幣\S{1,12}\元", text)
                                            amount = re.sub("新臺幣", "",amount[0])
                                        items['amount'] = amount
                                    except:   
                                        items['amount'] = ""
                                try:
                                    ## 尋找債權人
                                    company = re.findall("(聲請人即債權人|聲請人|債權人)(\S+\有限公司)", text)
                                    company_name = re.findall("(聲請人即債權人|聲請人|債權人)(\S+\法定代理人)", text)[0][1].split("法定代理人")[0]
                                    # print('company_name',re.findall("(聲請人即債權人|聲請人|債權人)(\S+\法定代理人)", text))
                                
                                    # print(re.findall("(聲請人即債權人|聲請人|債權人)(\S+\法定代理人)", text)[0][1].split(r"法定代理人|相對人|債務人|聲請人|被告"))
                                    if len(company_name) > 20:
                                        items['company'] = ''
                                    else:
                                        items['company'] = company_name
                
                                except:
                                
                                    items['company'] = ''
                                # map parents name in text
                                items['map_family'] = ' '
                                try:
                                    if (self.lender_info['fatherName'] in text) or (self.lender_info['motherName'] in text):
                                        items['map_family'] = '是'
                                except:
                                    items['map_family'] = '否'
                            
                                ## map address in text
                                items['map_address'] = ' '  
                                if (self.lender_info['residenceAddress'] != '') and (self.lender_info['residenceAddress'] != None):
                                    if self.lender_info['residenceAddress'][:6] in text:
                                        items['map_address'] = '是'
                                elif (self.lender_info['currentAddress'] != '') and (self.lender_info['currentAddress'] != None):
                                    if self.lender_info['currentAddress'][:6] in text:
                                        items['map_address'] = '是'
                                elif (self.lender_info['companyAddress'] != '') and (self.lender_info['companyAddress'] != None):
                                    if self.lender_info['companyAddress'][:6] in text:
                                        items['map_address'] = '是'
                                else:
                                    items['map_address'] = ' '                            
                            ## map broker company with ccis table

                            # for index, row in self.df_ccis_look.iterrows():
                            #     if (companyName in row['who']) and (event_time < datetime.datetime.strptime(row['date'], "%Y/%m/%d")):
                            #         items['ccis_company'] = companyName
                            
                            # for index, row in self.df_ccis_move.iterrows():
                            #     if (companyName in row['who']) and (event_time < datetime.datetime.strptime(row['date'], "%Y/%m/%d")):
                            #         items['ccis_company'] = companyName
                                print(items)
                                yield items
                        
                        
    
    
