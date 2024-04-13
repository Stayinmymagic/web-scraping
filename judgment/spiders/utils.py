import datetime
import re
def parse_event_time(text):
    ## find all dates in text and get the earlist one as event time
    timelist = re.finditer(r'(民國|)\d{2,3}(年|\.)\d{1,2}(月|\.)\d{1,2}(日|)', text)
    datelist = []
    for t in timelist:
        try:    
            date = re.findall(r'\d+', t.group())
            date[0] = str(int(date[0]) + 1911)
            date = '-'.join(date)
            datetime_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
            datelist.append(datetime_obj)
        except:                      
            t = t.group()
            num_dict = {'一百': '1', '九十': '9','八十':'8','七十':'7','十':'1',
                        '零':'0', '一': '1', '二':'2', '三': '3', '四':'4',
                        '五': '5', '六':'6', '七': '7', '八':'8', '九':'9'}
            for key in num_dict:
                t = t.replace(key, num_dict[key])
            date = re.findall(r'\d+', t)

            if date[0] == '1':
                date[0] = str(100+1911)
            elif int(date[0]) < 15:
                date[0] = str(int(date[0])*10+1911)
            else:
                date[0] = str(int(date[0])+1911)
            date = '-'.join(date)
            try:
                datetime_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
                datelist.append(datetime_obj)
            except:
                continue
    event_time = min(datelist)
    return event_time