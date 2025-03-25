import pandas as pd
import requests
import json
import time
from tdx_data import tdx_data

class etf_fund_data_ths:
    def __init__(self):
        '''
        etf基金数据
        '''
        self.tdx_data=tdx_data()
        self.tdx_data.connect()
    def get_ETF_fund_hist_data(self,stock='159805',end='20500101',limit='1000000',
                                data_type='D',fqt='1',count=8000):
            '''
            获取ETF基金历史数据
            stock 证券代码
            end结束时间
            limit数据长度
            data_type数据类型：
            1 1分钟
            5 5分钟
            15 15分钟
            30 30分钟
            60 60分钟
            D 日线数据
            W 周线数据
            M 月线数据
            fqt 复权
            fq=0股票除权
            fq=1前复权
            fq=2后复权
            '''
            try:
                secid='{}.{}'.format('0',stock)
                data_dict = {'1': '1', '5': '5', '15': '15', '30': '30', '60': '60', 'D': '101', 'W': '102', 'M': '103'}
                klt=data_dict[data_type]
                params={
                    'secid':secid,
                    'klt':klt,
                    'fqt':fqt,
                    'lmt':limit,
                    'end':end,
                    'iscca': '1',
                    'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8',
                    'fields2':'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64',
                    'ut': 'f057cbcbce2a86e2866ab8877db1d059',
                    'forcect': '1',
                }
                url='https://push2his.eastmoney.com/api/qt/stock/kline/get?'
                res = requests.get(url=url, params=params)
                text = res.text
                json_text = json.loads(text)
                df = pd.DataFrame(json_text['data']['klines'])
                df.columns = ['数据']
                data_list = []
                for i in df['数据']:
                    data_list.append(i.split(','))
                data = pd.DataFrame(data_list)
                columns = ['date', 'open', 'close', 'high', 'low', 'volume', 
                        '成交额', '振幅', '涨跌幅', '涨跌额', '换手率','_','_','_']
                data.columns = columns
                del data['_']
                for m in columns[1:-3]:
                    data[m] = pd.to_numeric(data[m])
                data1=data.sort_index(ascending=True,ignore_index=True)
                return data1
            except:
                try:
                    secid='{}.{}'.format('1',stock)
                    data_dict = {'1': '1', '5': '5', '15': '15', '30': '30', '60': '60', 'D': '101', 'W': '102', 'M': '103'}
                    klt=data_dict[data_type]
                    params={
                        'secid':secid,
                        'klt':klt,
                        'fqt':fqt,
                        'lmt':limit,
                        'end':end,
                        'iscca': '1',
                        'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8',
                        'fields2':'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64',
                        'ut': 'f057cbcbce2a86e2866ab8877db1d059',
                        'forcect': '1',
                    }
                    url='https://push2his.eastmoney.com/api/qt/stock/kline/get?'
                    res = requests.get(url=url, params=params)
                    text = res.text
                    json_text = json.loads(text)
                    df = pd.DataFrame(json_text['data']['klines'])
                    df.columns = ['数据']
                    data_list = []
                    for i in df['数据']:
                        data_list.append(i.split(','))
                    data = pd.DataFrame(data_list)
                    columns = ['date', 'open', 'close', 'high', 'low', 'volume', 
                            '成交额', '振幅', '涨跌幅', '涨跌额', '换手率','_','_','_']
                    data.columns = columns
                    del data['_']
                    for m in columns[1:-3]:
                        data[m] = pd.to_numeric(data[m])
                    data1=data.sort_index(ascending=True,ignore_index=True)
                    return data1
                except:
                    '''
                    0 5分钟K线
                    1 15分钟K线 
                    2 30分钟K线 
                    3 1小时K线 
                    4 日K线
                    7 1分钟
                    8 1分钟K线
                    '''
                    data_dict = {'1': '8', '5': '0', '15': '1', '30': '2', '60': '3', 'D': '4', '7': '7',}
                    n=data_dict[data_type]
                    data=self.tdx_data.get_security_minute_data(stock=stock,n=n,count=count)
                    data['volume']=data['vol']
                    data['涨跌幅']=data['close'].pct_change()*100
                    data['涨跌额']=data['close']-data['open']
                    data['振幅']=(data['high']-data['low'])/data['low']*100
                    return data
    
    def get_etf_fund_spot_data(self,stock='159632'):
        '''
        ETF实时数据
        '''
        stock_1=stock
        try:
            secid='{}{}'.format('0.',stock_1)
            url='https://push2.eastmoney.com/api/qt/stock/get?'
            params={
                #cb: jQuery3510250885634607382_1693625754740
                'secid':secid,
                'forcect': '1',
                'invt': '2',
                'fields': 'f43,f44,f45,f46,f48,f49,f50,f51,f52,f59,f60,f108,f152,f161,f168,f169,f170',
                'ut': 'f057cbcbce2a86e2866ab8877db1d059',
                #_: 1693625754746
            }
            res=requests.get(url=url,params=params)
            text=res.json()['data']
            result={}
            result['最新价']=float(text['f43'])/1000
            result['最高价']=text['f44']/1000
            result['最低价']=text['f45']/1000
            result['今开']=text['f46']/1000
            result['金额']=text['f48']
            result['外盘']=text['f49']
            result['量比']=text['f50']/100
            result['涨停价']=text['f51']/1000
            result['跌停价']=text['f52']/1000
            #result['昨收']=text['f60']/1000
            result['涨跌']=text['f169']/1000
            result['内盘']=text['f161']
            result['换手率']=text['f168']/100
            result['涨跌幅']=text['f170']/100
            return result
        except:
            try:
                secid='{}{}'.format('1.',stock_1)
                url='https://push2.eastmoney.com/api/qt/stock/get?'
                params={
                    #cb: jQuery3510250885634607382_1693625754740
                    'secid':secid,
                    'forcect': '1',
                    'invt': '2',
                    'fields': 'f43,f44,f45,f46,f48,f49,f50,f51,f52,f59,f60,f108,f152,f161,f168,f169,f170',
                    'ut': 'f057cbcbce2a86e2866ab8877db1d059',
                    #_: 1693625754746
                }
                res=requests.get(url=url,params=params)
                text=res.json()['data']
                result={}
                result['最新价']=float(text['f43'])/1000
                result['最高价']=text['f44']/1000
                result['最低价']=text['f45']/1000
                result['今开']=text['f46']/1000
                result['金额']=text['f48']
                result['外盘']=text['f49']
                result['量比']=text['f50']/100
                result['涨停价']=text['f51']/1000
                result['跌停价']=text['f52']/1000
                #result['昨收']=text['f60']/1000
                result['涨跌']=text['f169']/1000
                result['内盘']=text['f161']
                result['换手率']=text['f168']/100
                result['涨跌幅']=text['f170']/100
                return result
            except Exception as e:
                print(e)
                json_text=self.tdx_data.get_security_quotes_none(stock=stock_1)
                data_dict={}
                data_dict['最新价']=json_text['price'].tolist()[-1]/10
                data_dict['最高价']=json_text['high'].tolist()[-1]/10
                data_dict['最低价']=json_text['low'].tolist()[-1]/10
                data_dict['今开']=json_text['open'].tolist()[-1]/10
                data_dict['涨跌幅']=((data_dict['最新价']-data_dict['今开'])/data_dict['今开'])*100
                return data_dict
    def get_etf_spot_trader_data(self,stock='159632',limit=600000):
        '''
        ETF实时交易数据3秒一次
        '''
        try:
            secid='{}{}'.format('0.',stock)
            url='https://push2.eastmoney.com/api/qt/stock/details/get?'
            params={
                #cb: jQuery3510250885634607382_1693625754742
                'secid':secid,
                'forcect': '1',
                'invt': '2',
                'pos':-limit,
                'iscca': '1',
                'fields1': 'f1,f2,f3,f4,f5',
                'fields2': 'f51,f52,f53,f54,f55',
                'ut': 'f057cbcbce2a86e2866ab8877db1d059'
                #_: 1693625754806
            }
            res=requests.get(url=url,params=params)
            text=res.json()['data']['details']
            data=[]
            for i in text:
                data.append(i.split(','))
            df=pd.DataFrame(data)
            df.columns=['时间','价格','成交量','未知','买卖盘']
            df['时间']=df['时间'].apply(lambda x:int(''.join(x.split(':'))))
            def select_data(x):
                if x=='1':
                    return '卖盘'
                elif x=='2':
                    return '买盘'
                else:
                    return x
            df['买卖盘']=df['买卖盘'].apply(select_data)
            df=df[df['时间']>=92400]
            df['价格']=pd.to_numeric(df['价格'])
            df['实时涨跌幅']=(df['价格'].pct_change())*100
            df['涨跌幅']=df['实时涨跌幅'].cumsum()
            return df
        except:
            try:
                secid='{}{}'.format('1.',stock)
                url='https://push2.eastmoney.com/api/qt/stock/details/get?'
                params={
                    #cb: jQuery3510250885634607382_1693625754742
                    'secid':secid,
                    'forcect': '1',
                    'invt': '2',
                    'pos':-limit,
                    'iscca': '1',
                    'fields1': 'f1,f2,f3,f4,f5',
                    'fields2': 'f51,f52,f53,f54,f55',
                    'ut': 'f057cbcbce2a86e2866ab8877db1d059'
                    #_: 1693625754806
                }
                res=requests.get(url=url,params=params)
                text=res.json()['data']['details']
                data=[]
                for i in text:
                    data.append(i.split(','))
                df=pd.DataFrame(data)
                df.columns=['时间','价格','成交量','未知','买卖盘']
                df['时间']=df['时间'].apply(lambda x:int(''.join(x.split(':'))))
                def select_data(x):
                    if x=='1':
                        return '卖盘'
                    elif x=='2':
                        return '买盘'
                    else:
                        return x
                df['买卖盘']=df['买卖盘'].apply(select_data)
                df=df[df['时间']>=92400]
                df['价格']=pd.to_numeric(df['价格'])
                df['实时涨跌幅']=(df['价格'].pct_change())*100
                df['涨跌幅']=df['实时涨跌幅'].cumsum()
                return df
            except:
                data=self.tdx_data.get_trader_data(stock=stock,start=0,count=9000)
                data['价格']=data['price']/10
                data['涨跌幅']=(data['价格'].pct_change()*100).cumsum()
                data['实时涨跌幅']=data['涨跌幅']-data['涨跌幅'].shift(1)
                return data
    def get_disk_port_data_fund(self,stock='600031'):
        '''
        获取股票盘口数据
        '''
        df=self.tdx_data.get_security_quotes_none(stock=stock)
        data={}
        data['卖一']=df['ask1'].tolist()[-1]/10
        data['卖二']=df['ask2'].tolist()[-1]/10
        data['卖三']=df['ask3'].tolist()[-1]/10
        data['卖四']=df['ask4'].tolist()[-1]/10
        data['卖五']=df['ask5'].tolist()[-1]/10
        data['买一']=df['bid1'].tolist()[-1]/10
        data['买二']=df['bid2'].tolist()[-1]/10
        data['买三']=df['bid3'].tolist()[-1]/10
        data['买四']=df['bid4'].tolist()[-1]/10
        data['买五']=df['bid5'].tolist()[-1]/10
        data['卖一量']=df['ask_vol1'].tolist()[-1]
        data['卖二量']=df['ask_vol2'].tolist()[-1]
        data['卖三量']=df['ask_vol3'].tolist()[-1]
        data['卖四量']=df['ask_vol4'].tolist()[-1]
        data['卖五量']=df['ask_vol5'].tolist()[-1]
        data['买一量']=df['bid_vol1'].tolist()[-1]
        data['买二量']=df['bid_vol2'].tolist()[-1]
        data['买三量']=df['bid_vol3'].tolist()[-1]
        data['买四量']=df['bid_vol4'].tolist()[-1]
        data['买五量']=df['bid_vol5'].tolist()[-1]
        data['最新价']=df['price'].tolist()[-1]/10
        return data
if __name__=='__main__':
    td = etf_fund_data_ths()
    df = td.get_etf_fund_spot_data("159632")
    print(df)