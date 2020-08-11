#加载所有插件
import glob
import importlib
import os
import functools
from pluginsinterface.EventHandling import StandEven
from enum import Enum
from helper import getlogger
import config
logger = getlogger(__name__)
#插件列表
pluglist = {}
#消息过滤器列表
messagefilterlist = []

DEBUG = config.DEBUG
#消息类型 private、group、tempprivate、tempgroup  私聊(一对一)、群聊(一对多)、临时聊天(一对一)、临时群聊(一对多)
class MsgTypeEnum:
    private = 1
    group = 2
    tempprivate = 4
    tempgroup = 8

#暂时无效
#(6级 0群主 1管理 2预留 3预留 4一般群员 5临时群员-匿名等),
class GroupLevel(Enum):
    owner = 0
    admin = 1
    __reserved1 = 2
    __reserved2 = 3
    ordinary = 4
    temporary = 5

#注册消息函数(消息过滤器,消息类型限制,群聊限制-暂未实现,是否允许匿名,需要指定BOT)
def on_message(msgfilter = '',limitMsgType:MsgTypeEnum = MsgTypeEnum.private | MsgTypeEnum.group,grouplevellimit:GroupLevel = GroupLevel.ordinary,allow_anonymous = False,at_to_me = True):
    global messagefilterlist,logger
    #logger.info('on_msg初始化')
    def decorate(func):
        @functools.wraps(func)
        def wrapper(even:StandEven):
            #函数返回True时将拦截消息，否则消息放行，不返回数据时，发送过回复则拦截，否则放行
            msg:str = even.simplemsg
            if msgfilter != '' and not msg.startswith(msgfilter):
                return False
            even.arg = msg.replace(msgfilter,'',1)
            res = func(even)
            if res == None:
                if even.hasReply:
                    return True
            return res
        if DEBUG:
            logger.info('函数注册{module}.{name}.{msgfilter}'.format(
                module = wrapper.__module__,
                name = wrapper.__name__,
                msgfilter = msgfilter
                ))
        messagefilterlist.append(wrapper)
        return wrapper
    return decorate

def eventArrives(even:StandEven):
    global messagefilterlist
    if DEBUG:
        logger.info(even.toStr())
    for fun in messagefilterlist:
        res = fun(even)
        if res == True:
            break

def __import_modules(pathname: str) -> dict:
    global pluglist
    """
    导入指定路径或者目录下的模块，并返回模块信息

    :param pathname: 要导入的模块路径(相对路径)，可以导入指定目录下的模块，只要符合glob路径表达式写法即可
    :return: 模块信息字典
    """
    #modules_dict = {}
    module_paths = glob.glob(pathname)
    for path in module_paths:
        module_name = path.replace(os.sep, '.')[:-3]
        module = importlib.import_module(module_name)
        logger.info("加载插件："+module.__name__)
        pluglist[module.__name__] = {
            'name':module.__name__
        }
        #modules_dict[module.__name__] = {}
        #for element in dir(module):
        #    # 获取用户自定义的函数和变量名称
        #    if not element.startswith('__'):
        #        modules_dict[module.__name__][element] = eval('module.{}'.format(element))
    return pluglist
def initPlug(plugpath = 'plugins'):
    #加载插件
    module_info = __import_modules(plugpath + '/**.py')
    return module_info
