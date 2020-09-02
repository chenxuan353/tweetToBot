# -*- coding: UTF-8 -*-
import config
import json
import logging
import os
import time
import nonebot
import traceback
import re
"""
帮助函数
"""
cache_base_path = "cache" # 基础目录
config_path = 'config' 
log_path = 'log'

# 判断目录存在性，不存在则生成
def check_path(filepath:str):
    cpath = os.path.join(cache_base_path,filepath)
    if not os.path.exists(cpath):
        os.makedirs(cpath)
    return cpath
def file_exists(filepath:str):
    cpath = os.path.join(cache_base_path,filepath)
    return os.path.isfile(cpath)


# 设置nonebot的日志对象
def initNonebotLogger(printCMD:bool = True):
    logformat = logging.Formatter("[%(asctime)s %(name)s]%(levelname)s: %(message)s")
    trf = logging.handlers.TimedRotatingFileHandler(
                filename=os.path.join(cache_base_path,log_path,"nonebot.log"),
                encoding="utf-8",
                when="H", 
                interval=24, 
                backupCount=10,
        )
    trf.setFormatter(logformat)
    nonebot.logger.addHandler(trf)

# 初始化目录
check_path("")
check_path(os.path.join(config_path))
check_path(os.path.join(log_path))
initNonebotLogger()

# 获取日志对象(记录名，是否输出到控制台)
def getlogger(name,printCMD:bool = True,loglevel = logging.INFO) -> logging.Logger:
    reslogger = logging.getLogger(name)
    reslogger.setLevel(loglevel)
    logformat = logging.Formatter("[%(asctime)s %(name)s]%(levelname)s: %(message)s")
    if printCMD == True:
        sh = logging.StreamHandler()
        sh.setFormatter(logformat)
        reslogger.addHandler(sh)
    trf = logging.handlers.TimedRotatingFileHandler(
                filename=os.path.join(cache_base_path,log_path,name+".log"),
                encoding="utf-8",
                when="H", 
                interval=24, 
                backupCount=10,
        )
    trf.setFormatter(logformat)
    reslogger.addHandler(trf)
    return reslogger
logger = getlogger(__name__,printCMD=False)

def arglimitdeal(ls:dict):
    """
    反向字典映射，最后声明的映射会将之前的声明覆盖
    {
        a:[a1,b1,c1],
        b:[b1]
    }=>{
        a1:a,
        b1:b,
        c1:a
    }
    """
    res = {}
    for k in ls.keys():
        res[k]=k
        if type(ls[k]) is list:
            for v in ls[k]:
                res[v]=k
        else:
            res[res[k]]=k
    return res

# dict扩展操作
def dictInit(d:dict,*args,endobj:dict = None) -> bool:
    # 参数：待初始化字典,键名...
    # 初始化层次字典,初始化结构为层层字典嵌套
    # 不重复初始化(不覆盖已有内容),endobj为字典时会被copy
    nowunit = None
    nowd = None
    for unit in args:   
        if nowd is None:
            nowd = d
        else:
            nowd = nowd[nowunit]
        nowunit = unit
        if unit not in nowd:
            nowd[unit] = {}
    if endobj is not None:
        if nowd[nowunit] == {}:
            nowd[nowunit] = (endobj.copy() if type(endobj) == dict else endobj)
            return True
        else:
            return False
    return True
def dictHas(d:dict,*args) -> bool:
    # 参数：待判断字典,键名...
    # 判断多层键是否存在
    nowunit = None
    nowd = None
    for unit in args:
        if nowd is None:
            nowd = d
        else:
            nowd = nowd[nowunit]
        nowunit = unit
        if unit not in nowd:
            return False
    return True
def dictGet(d:dict,*args,default = None) -> dict:
    # 参数：待判断字典,键名...
    # 判断多层键是否存在
    nowunit = None
    nowd = None
    for unit in args:
        if nowd is None:
            nowd = d
        else:
            nowd = nowd[nowunit]
        nowunit = unit
        if unit not in nowd:
            return default
    return nowd[nowunit]
def dictSet(d:dict,*args,obj:dict = None) -> None:
    # 参数：待初始化字典,键名...
    # 初始化层次字典,初始化结构为层层字典嵌套
    # obj不为None时将覆盖末端节点
    nowunit = None
    nowd = None
    for unit in args:
        if nowd is None:
            nowd = d
        else:
            nowd = nowd[nowunit]
        nowunit = unit
        if unit not in nowd:
            nowd[unit] = {}
    if obj is not None:
        nowd[nowunit] = obj

"""
文件操作相关函数
"""
# 文件操作日志
fileop_logger = getlogger('filesystem',False)
# 数据文件操作,返回(逻辑值T/F,dict数据/错误信息)
def data_read(filename:str,path:str = config_path) -> tuple:
    try:
        f = open(os.path.join(cache_base_path,path,filename),mode = 'r',encoding='utf-8')
        data = json.load(f)
        fileop_logger.info('读取配置文件：'+json.dumps(data))
    except IOError:
        logger.warning('load IOError: 未找到文件或文件不存在-'+os.path.join(cache_base_path,path,filename))
        return (False,'配置文件读取失败')
    except:
        logger.critical('数据文件读取解析异常,'+os.path.join(cache_base_path,path,filename))
        s = traceback.format_exc(limit=10)
        logger.critical(s)
        return (False,'配置文件解析异常')
    else:
        f.close()
    return (True,'读取成功',data)

def data_save(filename:str,data,path:str = config_path,object_hook=None) -> tuple:
    try:
        fw = open(os.path.join(cache_base_path,path,filename),mode = 'w',encoding='utf-8')
        if object_hook:
            json.dump(data,fw,ensure_ascii=False,indent=4,object_hook=object_hook)
        else:
            json.dump(data,fw,ensure_ascii=False,indent=4)
    except IOError:
        logger.error('save IOError: 未找到文件或文件不存在-'+os.path.join(cache_base_path,path,filename))
        return (False,'配置文件写入失败')
    except:
        logger.critical('数据文件写入异常,'+os.path.join(cache_base_path,path,filename))
        s = traceback.format_exc(limit=10)
        logger.error(s)
        return (False,'配置文件写入异常')
    else:
        fw.close()
    return (True,'保存成功')

def data_read_auto(filename:str,default = None,path:str = config_path):
    res = data_read(filename,path)
    if res[0]:
        return res[2]
    return default

# 临时列表
class TempMemory:
    # 记录名称、记录长度(默认记录30条),默认数据,是否自动保存(默认否),是否自动读取(默认否)
    def __init__(self,
            name:str,
            limit:int = 30,
            path:str = "templist",
            defdata:list = [],
            autosave:bool = False,
            autoload:bool = False,
            pop_trigger = None
        ):
        check_path('templist')
        if name[-5].lower() != '.json':
            name += '.json'
        self.tm = None
        self.name = name
        self.limit = limit
        self.autosave = autosave
        self.pop_trigger = pop_trigger
        self.path = path
        if autoload:
            res = data_read(self.name,path=self.path)
            if res[0] == True:
                self.tm = res[2]
        if self.tm == None:
            self.tm = defdata.copy()
    def save(self):
        return data_save(self.name,self.tm,path=self.path)
    def pop(self,index:int,save:bool=True):
        res = self.tm.pop(index)
        if self.pop_trigger:
            self.pop_trigger(res)
        if save:
            self.save()
        return res
    def join(self,data):
        res = None
        self.tm.append(data)
        if len(self.tm) > self.limit:
            res = self.pop(0,save=False)
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
    # :author: simpleapples
    # :link: https://juejin.im/post/5ab10045518825557005db65
    # :source: 掘金
    # :note: 著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。
    def __init__(self, rate, capacity, initval:int = 1):
        # rate是令牌发放速度(每秒发放数量)，capacity是桶的大小，initval是初始大小(桶的百分比)
        self._rate = rate
        self._capacity = capacity
        self._current_amount = 0
        self._last_consume_time = 0
        if initval > 1 or initval < 0:
            raise Exception("无效的参数！")
        self.consume(capacity*(1-initval))
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
    def canConsume(self, token_amount):
        increment = (int(time.time()) - self._last_consume_time) * self._rate  # 计算从上次发送到这次发送，新发放的令牌数量
        self._current_amount = min(
            increment + self._current_amount, self._capacity)  # 令牌数量不能超过桶的容量
        if token_amount > self._current_amount:  # 如果没有足够的令牌，则不能发送数据
            return False
        return True