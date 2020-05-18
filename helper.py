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
from nonebot import CommandSession
"""
帮助函数
"""

file_base_path = "cache"
config_file_base_path = 'config'
log_file_base_path = 'log'
#每天一个日志文件
bindCQID = config.default_bot_QQ
bot_error_printID = config.bot_error_printID
#给主线程传递信息
keepalive = {
    'reboot_tewwtlistener' : False,
    'tewwtlistener_alive' : True,
    'reboot_tweetListener_cout' : 0,
    'tweetListener_threads' : None,
    'nonebot_threads' : None,
    'last_trans': 0, #上次翻译时间
    'clear_chrome': False,
}
#获取日志对象
def getlogger(name) -> logging.Logger:
    reslogger = logging.getLogger(name)
    reslogger.setLevel(logging.INFO)
    logformat = logging.Formatter("[%(asctime)s %(name)s]%(levelname)s: %(message)s")
    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setFormatter(logformat)
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

#判断目录存在性，不存在则生成
def check_path(filepath:str):
    if not os.path.exists(os.path.join(file_base_path,filepath)):
        os.makedirs(os.path.join(file_base_path,filepath))
#参数截断
def commandHeadtail(s:str):
    return s.partition(" ")
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
    if bot_error_printID != '':
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

#数据文件操作,返回(逻辑值T/F,dict数据/错误信息)
def data_read(filename:str,path:str = config_file_base_path) -> tuple:
    try:
        f = open(os.path.join(file_base_path,path,filename),mode = 'r',encoding='utf-8')
        data = json.load(f)
        logger.info('读取配置文件：'+json.dumps(data))
    except IOError:
        logger.error('IOError: 未找到文件或文件不存在-'+os.path.join(file_base_path,path,filename))
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
            self.tm = defdata
    def join(self,data):
        res = None
        self.tm.append(data)
        if len(self.tm) > self.limit:
            res = self.tm.pop(0)
        if self.autosave:
            data_save(self.name,self.tm,"templist")
        return res
    
