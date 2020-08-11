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
cache_base_path = "cache" #基础目录
config_path = 'config' 
log_path = 'log'

#判断目录存在性，不存在则生成
def check_path(filepath:str):
    cpath = os.path.join(cache_base_path,filepath)
    if not os.path.exists(cpath):
        os.makedirs(cpath)
    return cpath
def file_exists(filepath:str):
    cpath = os.path.join(cache_base_path,filepath)
    return os.path.isfile(cpath)


#设置nonebot的日志对象
def initNonebotLogger():
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

#初始化目录
check_path("")
check_path(os.path.join(config_path))
check_path(os.path.join(log_path))
initNonebotLogger()

#获取日志对象(记录名，是否输出到控制台)
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

def reDealStr(pat:str,msg:str) -> list:
    #使用正则表达式处理字符串
    res = []
    resm = re.match(pat,msg, re.M | re.S)
    if resm == None:
        return None
    for reg in resm.regs:
        res.append(msg[reg[0]:reg[1]])
    if len(res) == 1:
        return res[0]
    return res
"""
统一参数处理函数，通过简单配置自动切分参数
返回值 (True,参数表) (False,参数昵称,错误描述,参数描述)
"""
def argDeal(msg:str,arglimits:list) ->tuple:
    #使用空白字符分隔参数(全角空格、半角空格、换行符)
    """    
        arglimits = [
            {
                'name':'参数名', #参数名
                'nick':'XX参数', #用于错误返回的昵称
                'des':'XXXX作用', #参数介绍，错误时返回
                'canSkip':False, #定义为可跳过时参数不符合验证规则将使用默认值
                #执行顺序 prefunc->verif|验证->vlimit->re->func->verif|类型转换
                #预处理函数，参数被分离后处理前的阶段，例:(lambda arg:arg.strip())
                'prefunc':None, #返回值为None或(False,"")时认定为参数无效,其他返回值将作为arg的更新值，特殊情况：(True,更新值)
                'verif':'str', #预先定义的验证规则(str、int、float、uint、dict、list、bool、other-不验证)
                'vlimit':{ 
                    #参数限制表(限制参数内容,空表则不限制),
                    # '*':''表示允许任意字符串,值不为空时任意字符串将被转变为次元素对应值
                    #处理限制前不进行类型转换，但会进行int float str的类型检查
                    'a':'b',
                    'a1':'b',
                    '':'233' #定义默认值
                },
                're':None, #正则表达式匹配(match函数)
                're_error':'', #正则错误信息
                'func':None, #函数，做返回前的处理，在参数限制及正则表达后调用，fun(arg,arglimit)
            },{
                    #第二个参数
                    #...
                }
            ]
    """
    def vfloat(arg):
        try:
            float(hmsg)
        except:
            return False
        return True
    veriffun = {
        'int':{
            'verif':(lambda arg:arg.isdecimal()),
            'res':int
        },
        'uint':{
            'verif':(lambda arg:arg.isdecimal() and int(arg) > 0),
            'res':int
        },
        'float':{'verif':vfloat,'res':float},
        'str':{'verif':None,'res':str},
        'list':{'verif':None,'res':list},
        'dict':{'verif':None,'res':dict},
        'other':{}
    }

    if 'tail' in arglimits:
        raise Exception("参数解析器异常：tail不能作为参数名")
    tailmsg = msg.strip()
    arglists = {'tail':''} #参数列表,尾参数固定命名为tail
    pat = re.compile('[　 \n]{1}') #分割正则
    try:
        larglimits = len(arglimits)
        i = 0
        while i <= larglimits:
            #预处理
            if tailmsg != '':
                res = pat.split(tailmsg,maxsplit=1)
                arg = res[0]
                tailmsg = (res[1] if len(res) == 2 else '')
            else:
                arg = ''
            #执行顺序 prefunc->verif|验证->vlimit->re->func->verif|类型转换
            backuparg = None
            while True and i <= larglimits:
                if backuparg:
                    arg = backuparg
                else:
                    backuparg = arg
                ad = arglimits[i]
                i += 1
                if ad['prefunc']:
                    newarg = ad['prefunc'](arg)
                    if (newarg == None) or (type(newarg) == tuple and not newarg[0]):
                        if ad['canSkip']:
                            arglists[ad['name']] = ad['vlimit']['']
                            continue
                        else:
                            return (False,ad['nick'],'数值无效(PF)',ad['des'])
                    arg = (newarg if type(newarg) != tuple else newarg[1])
                
                vf = veriffun[ad['verif']]
                if vf['verif'] and not vf['verif'](arg):
                    if ad['canSkip']:
                        arglists[ad['name']] = ad['vlimit']['']
                        continue
                    else:
                        return (False,ad['nick'],'数值无效(PF)',ad['des'])
                
                if ad['vlimit'] and ad['vlimit'] != {}:
                    if arg in ad['vlimit']:
                        arg = ad['vlimit'][arg]
                    elif '*' in ad['vlimit']:
                        if ad['vlimit']['*'] != '':
                            arg = ad['vlimit']['*']
                    else:
                        if ad['canSkip']:
                            arglists[ad['name']] = ad['vlimit']['']
                            continue
                        else:
                            return (False,ad['nick'],'非法参数(不被允许的值)',ad['des'])
                
                if ad['re']:
                    arg = reDealStr(ad['re'],arg)
                    if arg == None:
                        if ad['canSkip']:
                            arglists[ad['name']] = ad['vlimit']['']
                            continue
                        else:
                            return (False,ad['des'],(ad['re_error'] if ad['re_error'] else '参数不符合规则(re)'),ad['des'])

                if ad['func']:
                    arg = ad['func'](arg,ad)
                    #处理函数返回格式
                    #其一 None/合法值 其二 tuple对象 -> (参数是否合法,处理后的参数/错误文本)
                    if type(res) is tuple:
                        if res[0]:
                            arg = arg[1]
                        else:
                            return (False,ad['des'],arg[1],ad['des'])
                    elif arg == None:
                        return (False,ad['des'],'参数不符合规则(fun)',ad['des'])
                    
                if vf['res']:
                    arg = vf['res'](arg)
                arglists[ad['name']] = arg
                break
        arglists['tail'] = tailmsg
    except:
        s = traceback.format_exc(limit=10)
        logger.error(s)
        return (False,'异常','参数提取时异常！','Exception')
    return (True,arglists)


#dict扩展操作
def dictInit(d:dict,*args,endobj:dict = None) -> bool:
    #参数：待初始化字典,键名...
    #初始化层次字典,初始化结构为层层字典嵌套
    #不重复初始化(不覆盖已有内容),endobj会被copy
    nowunit = None
    nowd = None
    for unit in args:
        nowunit = unit
        if nowd == None:
            nowd = d
        else:
            nowd = nowd[unit]
        if unit not in nowd:
            nowd[unit] = {}
    if endobj:
        if nowd[nowunit] == {}:
            nowd[nowunit] = endobj.copy()
            return True
        else:
            return False
    return True
def dictHas(d:dict,*args) -> bool:
    #参数：待判断字典,键名...
    #判断多层键是否存在
    nowd = d
    for unit in args:
        if unit not in nowd:
            return False
        nowd = nowd[unit]
    return True
def dictGet(d:dict,*args,default = None) -> dict:
    #参数：待判断字典,键名...
    #判断多层键是否存在
    nowd = d
    for unit in args:
        if unit not in nowd:
            return default
        nowd = nowd[unit]
    return nowd
def dictSet(d:dict,*args,obj:dict = None) -> None:
    #参数：待初始化字典,键名...
    #初始化层次字典,初始化结构为层层字典嵌套
    #obj不为None时将覆盖末端节点
    nowunit = None
    nowd = None
    for unit in args:
        nowunit = unit
        if nowd == None:
            nowd = d
        else:
            nowd = nowd[unit]
        if unit not in nowd:
            nowd[unit] = {}
    if obj:
        nowd[nowunit] = obj

"""
文件操作相关函数
"""
#文件操作日志
fileop_logger = getlogger('filesystem',False)
#数据文件操作,返回(逻辑值T/F,dict数据/错误信息)
def data_read(filename:str,path:str = config_path) -> tuple:
    try:
        f = open(os.path.join(cache_base_path,path,filename),mode = 'r',encoding='utf-8')
        data = json.load(f)
        fileop_logger.info('读取配置文件：'+json.dumps(data))
    except IOError:
        logger.warning('load IOError: 未找到文件或文件不存在-'+os.path.join(cache_base_path,path,filename))
        return (False,'配置文件读取失败')
    except:
        logger.critical('数据文件读取解析异常')
        s = traceback.format_exc(limit=10)
        logger.critical(s)
        return (False,'配置文件解析异常')
    else:
        f.close()
    return (True,'读取成功',data)
def data_save(filename:str,data,path:str = config_path,object_hook=None) -> tuple:
    try:
        fw = open(os.path.join(cache_base_path,path,filename),mode = 'w',encoding='utf-8')
        json.dump(data,fw,ensure_ascii=False,indent=4,object_hook=object_hook)
    except IOError:
        logger.error('save IOError: 未找到文件或文件不存在-'+os.path.join(cache_base_path,path,filename))
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

def data_read_auto(filename:str,default = None,path:str = config_path):
    res = data_read(filename,path)
    if res[0]:
        return res[2]
    return default

#临时列表
class TempMemory:
    tm : list= None
    autosave : bool = None
    pop_trigger = None #pop函数触发器 FUN(data)
    name : str = ""
    limit : int = 0
    #记录名称、记录长度(默认记录30条),默认数据,是否自动保存(默认否),是否自动读取(默认否)
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
    #作者：simpleapples
    #链接：https://juejin.im/post/5ab10045518825557005db65
    #来源：掘金
    #著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。
    def __init__(self, rate, capacity, initval:int = 1):
        #rate是令牌发放速度(每秒发放数量)，capacity是桶的大小，initval是初始大小(桶的百分比)
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