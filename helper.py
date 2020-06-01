# -*- coding: UTF-8 -*-
import config
import time
import requests
import traceback
import nonebot
import json
import logging
import sys
import os
import re
from nonebot import CommandSession
"""
帮助函数
"""
file_base_path = "cache"
config_file_base_path = 'config'
log_file_base_path = 'log'
#每天一个日志文件
bindCQID = config.default_bot_QQ
bot_error_printID = config.bot_waring_printID
if bindCQID == '':
    bindCQID = None
else:
    bindCQID = int(bindCQID)
if bot_error_printID == '':
    bot_error_printID = None
else:
    bot_error_printID = int(bot_error_printID)

#判断目录存在性，不存在则生成
def check_path(filepath:str):
    if not os.path.exists(os.path.join(file_base_path,filepath)):
        os.makedirs(os.path.join(file_base_path,filepath))
#设置nonebot的日志对象
def initNonebotLogger():
    logformat = logging.Formatter("[%(asctime)s %(name)s]%(levelname)s: %(message)s")
    trf = logging.handlers.TimedRotatingFileHandler(
                filename=os.path.join(file_base_path,log_file_base_path,"nonebot.log"),
                encoding="utf-8",
                when="H", 
                interval=24, 
                backupCount=10,
        )
    trf.setFormatter(logformat)
    nonebot.logger.addHandler(trf)

check_path("")
check_path(os.path.join('config'))
check_path(os.path.join('log'))
initNonebotLogger()


#获取日志对象(记录名，是否输出到控制台)
def getlogger(name,printCMD:bool = True) -> logging.Logger:
    reslogger = logging.getLogger(name)
    reslogger.setLevel(logging.INFO)
    logformat = logging.Formatter("[%(asctime)s %(name)s]%(levelname)s: %(message)s")
    sh = logging.StreamHandler()
    sh.setFormatter(logformat)
    if printCMD != True:
        sh.setLevel(logging.CRITICAL)
    else:
        sh.setLevel(logging.INFO)
    reslogger.addHandler(sh)
    trf = logging.handlers.TimedRotatingFileHandler(
                filename=os.path.join(file_base_path,log_file_base_path,name+".log"),
                encoding="utf-8",
                when="H", 
                interval=24, 
                backupCount=10,
        )
    trf.setFormatter(logformat)
    reslogger.addHandler(trf)
    return reslogger
logger = getlogger(__name__)

#读写文件日志
fileop_logger = getlogger('filesystem',False)

#正则表达式处理字符串
def reDealStr(pat:str,msg:str):
    res = []
    resm = re.match(pat,msg, re.M | re.S)
    if resm == None:
        return None
    for reg in resm.regs:
        res.append(msg[reg[0]:reg[1]])
    if len(res) == 1:
        return res[0]
    return res
#参数处理
def argDeal(msg:str,arglimit:list):
    #使用空白字符分隔参数(全角空格、半角空格、换行符)
    """    
        arglimit = [
            {
                'name':'参数名', #参数名
                'des':'XX参数', #参数描述
                'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
                'strip':True, #是否strip
                'lower':False, #是否转换为小写
                'default':None, #默认值
                'func':None, #函数，当存在时使用函数进行二次处理
                're':None, #正则表达式匹配(match函数)
                'vlimit':{ 
                    #参数限制表(限制参数内容,空表则不限制),'*':''表示允许任意字符串,值不为空时任意字符串将被转变为这个值
                    #处理限制前不进行类型转换，但会进行int float str的类型检查
                    'a':'b',
                    'a1':'b'
                }
            },{
                    #第二个参数
                    #...
                }
            ]
    """
    typefun = {
        'int':int,
        'float':float,
        'str':str,
        'list':list,
        'dict':dict
    }
    arglist = {}
    pat = re.compile('[　 \n]{1}')
    lmsg = msg
    arglimitL = len(arglimit)
    try:
        for i in range(0,arglimitL):
            ad = arglimit[i]
            if i != arglimitL - 1 and lmsg != None:
                res = pat.split(lmsg,maxsplit=1)
                hmsg = res[0]
                if len(res) == 2:
                    lmsg = res[1]
                else:
                    lmsg = None
            elif lmsg == None:
                hmsg = None
            else:
                hmsg = lmsg
            if hmsg != None and hmsg != '':
                if ad['strip']:
                    hmsg = hmsg.strip()
                if ad['lower']:
                    hmsg = hmsg.lower()
                if ad['vlimit'] != {}:
                    if hmsg in ad['vlimit']:
                        hmsg = ad['vlimit'][hmsg]
                    elif '*' in ad['vlimit']:
                        if ad['vlimit']['*'] != '':
                            hmsg = ad['vlimit']['*']
                    else:
                        return (False,ad['des'],'非法参数(不被允许的值)')
                if ad['re'] != None:
                    hmsg = reDealStr(ad['re'],hmsg)
                    if hmsg == None:
                        return (False,ad['des'],'参数不符合规则(re)')
                if ad['func'] != None:
                    hmsg = ad['func'](hmsg,ad)
                    if hmsg == None:
                        return (False,ad['des'],'参数不符合规则(fun)')
                if ad['type'] == 'int' and not (type(hmsg) is int):
                    if not hmsg.isdecimal():
                        return (False,ad['des'],'数值无效')
                elif ad['type'] == 'float' and not (type(hmsg) is float):
                    try:
                        float(hmsg)
                    except:
                        return (False,ad['des'],'数值无效')
                arglist[ad['name']] = typefun[ad['type']](hmsg)
            else:
                if ad['default'] != None:
                    arglist[ad['name']] = ad['default']
                else:
                    return (False,ad['des'],'缺少参数')
    except:
        s = traceback.format_exc(limit=10)
        logger.error(s)
        return (False,'异常','参数提取时异常！')
    return (True,arglist)

#酷Q插件日志预处理
def CQsessionToStr(session:CommandSession):
    msg = 'cmd:'+session.event['raw_message']+ \
        ' ;self_id:'+str(session.event['self_id']) + \
        ' ;message_type:'+session.event['message_type']+ \
        ' ;send_id:'+str(session.event['user_id']) if session.event['message_type']=='private' else str(session.event['group_id'])+ \
        ' ;text:'+session.current_arg_text
    return msg
#处理日志输出
def msgSendToBot(reclogger:logging.Logger,message:str,*arg):
    for value in arg:
        message = message + str(value)
    reclogger.info(message)
    if bot_error_printID != None and config.error_push_switch:
        try:
            bot = nonebot.get_bot()
            bot.sync.send_msg_rate_limited(
                self_id=bindCQID,
                user_id=bot_error_printID,
                message=message)
            logger.info('向'+str(bot_error_printID)+'发送了：'+message)
        except ValueError:
            logger.warning('BOT未初始化,错误消息未发送')
        except:
            logger.error('BOT状态异常')
            s = traceback.format_exc(limit=10)
            logger.error(s)

async def async_msgSendToBot(reclogger:logging.Logger,message:str,*arg):
    for value in arg:
        message = message + str(value)
    reclogger.info(message)
    if bot_error_printID != None:
        try:
            bot = nonebot.get_bot()
            await bot.send_msg_rate_limited(
                self_id=bindCQID,
                user_id=bot_error_printID,
                message=message)
            logger.info('向'+str(bot_error_printID)+'发送了：'+message)
        except ValueError:
            logger.warning('BOT未初始化,错误消息未发送')
        except:
            logger.error('BOT状态异常')
            s = traceback.format_exc(limit=10)
            logger.error(s)

#数据文件操作,返回(逻辑值T/F,dict数据/错误信息)
def data_read(filename:str,path:str = config_file_base_path) -> tuple:
    try:
        f = open(os.path.join(file_base_path,path,filename),mode = 'r',encoding='utf-8')
        data = json.load(f)
        fileop_logger.info('读取配置文件：'+json.dumps(data))
    except IOError:
        logger.warning('IOError: 未找到文件或文件不存在-'+os.path.join(file_base_path,path,filename))
        return (False,'配置文件读取失败')
    except:
        logger.critical('数据文件读取解析异常')
        s = traceback.format_exc(limit=10)
        logger.critical(s)
        return (False,'配置文件解析异常')
    else:
        f.close()
    return (True,'读取成功',data)
def data_save(filename:str,data,path:str = config_file_base_path) -> tuple:
    try:
        fw = open(os.path.join(file_base_path,path,filename),mode = 'w',encoding='utf-8')
        json.dump(data,fw,ensure_ascii=False,indent=4)
    except IOError:
        logger.error('IOError: 未找到文件或文件不存在-'+os.path.join(file_base_path,path,filename))
        pass
        return (False,'配置文件写入失败')
    except:
        logger.critical('数据文件写入异常')
        s = traceback.format_exc(limit=10)
        logger.error(s)
        return (False,'配置文件写入异常')
    else:
        fw.close()
    return (True,'保存成功')


#临时列表
class TempMemory:
    tm : list= None
    autosave : bool = None
    name : str = ""
    limit : int = 0
    #记录名称、记录长度(默认记录30条),默认数据,是否自动保存(默认否),是否自动读取(默认否)
    def __init__(self,name:str,limit:int = 30,defdata:list = [],autosave:bool = False,autoload:bool = False):
        check_path('templist')
        self.name = name
        self.limit = limit
        self.autosave = autosave
        if autoload:
            res = data_read(self.name,"templist")
            if res[0] == True:
                self.tm = res[2]
        if self.tm == None:
            self.tm = defdata.copy()
    def save(self):
        return data_save(self.name,self.tm,"templist")
    def join(self,data):
        res = None
        self.tm.append(data)
        if len(self.tm) > self.limit:
            res = self.tm.pop(0)
        if self.autosave:
            self.save()
        return res
    def find(self,func,val):
        ttm = self.tm.copy()
        for item in ttm:
            if func(item,val):
                return item
        return None
#速率限制
class TokenBucket(object):
    #作者：simpleapples
    #链接：https://juejin.im/post/5ab10045518825557005db65
    #来源：掘金
    #著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。
    # rate是令牌发放速度(每秒发放数量)，capacity是桶的大小
    def __init__(self, rate, capacity):
        self._rate = rate
        self._capacity = capacity
        self._current_amount = 0
        self._last_consume_time = 0
    # token_amount是发送数据需要的令牌数
    def consume(self, token_amount):
        increment = (int(time.time()) - self._last_consume_time) * self._rate  # 计算从上次发送到这次发送，新发放的令牌数量
        self._current_amount = min(
            increment + self._current_amount, self._capacity)  # 令牌数量不能超过桶的容量
        if token_amount > self._current_amount:  # 如果没有足够的令牌，则不能发送数据
            return False
        self._last_consume_time = int(time.time())
        self._current_amount -= token_amount
        return True