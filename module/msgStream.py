import nonebot
import traceback
import time
import queue
import threading
import asyncio
import os

#日志输出
from helper import getlogger,TempMemory,data_read,data_save,data_read_auto
logger = getlogger(__name__)
sendlogger = getlogger(__name__+'_nocmd',printCMD=False)
"""
消息流处理及推送模块

用于向指定对象推送消息
推送时检查推送健康度 发现多次无法连接的情况会将信息提交
本模块同时负责保存与推送重要信息
"""

send_count_path = 'msgStream.json'
send_count = {}
send_log = {}
exp_info_path = 'msgStream_expinfo.json'
exp_info:TempMemory = TempMemory(exp_info_path,limit = 100,autosave=True,autoload=True)
send_stream = {}
allow_bottype = ['cqhttp','dingding']

def init():
    res = data_read(send_count_path)
    if res[0]:
        send_count = res[2]
        for bottype in send_count:
            for botuuid in send_count[bottype]:
                dictInit(send_log,bottype,botuuid,endobj = TempMemory(os.path.join('msgStream',bottype+'_'+botuuid+'.json'),limit = 250,autosave = True,autoload = True))


"""
消息类·用于组合与生成消息
"""
def IOC_text(msgtype,data):
    return data['text']
def IOC_CQ_img(msgtype,data):
    return "[CQ:image,timeout={timeout},file={src}]".format(**data)
conversionFunc = {
    'default':IOC_text,
    'CQ':{
        'img':IOC_CQ_img
    }
}
class SendMessage:
    def __init__(self,msg:str = None):
        self.infoObjs:list = [].copy()
        if msg:
            self.append(self.baleTextObj(msg))
    def removeAllTypeObj(self,msgtype):
        self.infoObjs = list(filter((lambda obj:obj['msgtype']!=msgtype),self.infoObjs))
    def baleTextObj(self,msg):
        return {
            'msgtype':'text',
            'text':msg
        }
    def baleImgObj(self,src,timeout = 15,text = '[图片]'):
        return {
            'msgtype':'img',
            'src':src,
            'timeout':str(timeout),
            'text':str(text),
        }
    def __checkMsg(self,msgtype,data):
        if type(data) != dict:
            raise Exception('{msgtype},数据类型异常'.format(msgtype))
        if msgtype == 'text':
            if 'text' not in data:
                raise Exception('{msgtype},text类型缺少文本内容'.format(msgtype))
        if msgtype == 'img':
            if 'src' not in data:
                raise Exception('{msgtype},img类型缺少源标签'.format(msgtype))
            if 'timeout' not in data:
                data['timeout'] = 15
            data['timeout'] = str(data['timeout'])
            data['text'] = '[图片]'
        else:
            raise Exception('{msgtype},不支持的数据类型'.format(msgtype))
    def append(self,infoObj):
        if type(infoObj) == str:
            infoObj = self.baleTextObj(infoObj)
        self.__checkMsg(infoObj['msgtype'],infoObj)
        self.infoObjs.append((infoObj['msgtype'],infoObj))
    def __infoObjToStr(self,msgtype,data,Conversion_flag = 'CQ'):
        global conversionFunc
        if Conversion_flag not in conversionFunc:
            return conversionFunc['default'](msgtype,data)
        if msgtype not in conversionFunc[Conversion_flag]:
            if 'default' not in conversionFunc[Conversion_flag]:
                return conversionFunc['default'](msgtype,data)
            else:
                return conversionFunc[Conversion_flag]['default'](msgtype,data)
        return conversionFunc[Conversion_flag][msgtype](msgtype,data)
    def toStr(self,Conversion_flag:str = 'CQ'):
        text = ""
        for infoObj in self.infoObjs:
            text += self.__infoObjToStr(infoObj[0],infoObj[1],Conversion_flag)
        return text
    def toSimpleStr(self):
        text = ""
        for infoObj in self.infoObjs:
            text += infoObj[1]['text']
        return text
"""
消息流
"""
class QueueStream:
    def __init__(self,name,deal_func,max_size:int = 64,senddur = 0.3):
        self.queue = queue.Queue(max_size)
        self.senddur = senddur
        self.deal_func = deal_func
        self.dealthread = threading.Thread(
            group=None, 
            target=self.__deal, 
            name= name + '_QueueDeal',
            daemon=True
        )
    def __deal(self):
        while(True):
            unit = self.queue.get()
            self.deal_func(**unit)
            time.sleep(self.senddur)
    def run(self):
        self.dealthread.start()
    def put(self,unit:dict):
        if type(unit) != dict:
            raise Exception('无法处理此消息,消息类型不为字典(dict)')
        self.queue.put(unit)

#start = QueueStream('allsendmsg',threadSendDeal)
#start.run()
from helper import dictInit,dictHas,dictGet,dictSet

#sendUnit:消息发送元
def SUCqhttpWs(bottype:str,botuuid:str,botgroup:str,senduuid:str,sendObj:dict,message:SendMessage):
    message_type = botgroup
    send_id = senduuid
    bindCQID = botuuid
    message = message.toStr('CQ')
    #初始化
    bot = nonebot.get_bot()
    if message_type not in ('private','group'):
        raise Exception('错误，不支持的消息标识')
    if message_type == 'private':
        bot.sync.send_msg_rate_limited(self_id=bindCQID,user_id=send_id,message=message)
    elif message_type == 'group':
        bot.sync.send_msg_rate_limited(self_id=bindCQID,group_id=send_id,message=message)
SUConfig = {
    'cqhttp':SUCqhttpWs
    }

def exp_send(msg:SendMessage,source = '未知',flag = '信息',other:dict = None):
    global exp_info
    if type(msg) == str:
        msg = SendMessage(msg)
    if not isinstance(msg,SendMessage):
        raise Exception('不支持的消息类型')
    exp_info.join({
        'source':source,
        'flag':flag,
        'msg':msg,
        other:other,
    })
    
def exp_push(eventype,evendes,send_unit):
    msg = ('{bottype}>{botuuid}>{botgroup}>{senduuid} 消息流:{evendes}'.format(evendes = evendes,**send_unit))
    sendlogger.warning(msg)
    exp_send(msg,source='消息流警告触发器',flag = '警告')

#警告触发器(发送单元,信息发送对象,单元错误计数)
def exp_check(send_unit,send_me,uniterrcount):
    if uniterrcount == -1:
        sendlogger.error('{bottype}>{botuuid}>{botgroup}>{senduuid} 消息发送被拒绝:{message}'.format(**send_unit))
        #每十次被拒绝触发一次事件
        if send_me['total_refuse'] % 10 == 0:
            exp_push('warning','十次回绝警告',send_unit)
    elif send_me['last_deal'] != send_me['last_error']:
        sendlogger.error('{bottype}>{botuuid}>{botgroup}>{senduuid} 消息发送异常(edc):{message}'.format(**send_unit))
        #三小时无错误归零，每15次错误一个警告
        if send_me['error'] % 15 == 0:
            exp_push('warning','连续错误警告，已达到十五次阈值(间断不超过三小时)',send_unit)
        #单元发送错误计数，每15次错误触发一次警告，达到五次时触发第一次警报
        if uniterrcount == 5 or uniterrcount % 15 == 0:
            exp_push('warning','首次连续错误警告，已达到五次阈值(间断不超过三小时)',send_unit)
    else:
        sendlogger.error('{bottype}>{botuuid}>{botgroup}>{senduuid} 消息发送异常:{message}'.format(**send_unit))
    send_me['last_deal'] = time.time()

def threadSendDeal(sendstarttime:int,bottype:str,botuuid:str,botgroup:str,senduuid:str,sendObj:dict,message:str):
    global send_count,send_log,allow_bottype,SUConfig
    if bottype not in allow_bottype:
        logger.info(allow_bottype)
        raise Exception('不被允许的bottype')
    dealstarttime = time.time()
    if not dictHas(send_count,bottype,botuuid):
        dictInit(send_count,bottype,botuuid,endobj = {
            'total_send':0,#发送总计数
            'total_error':0,#错误总计数
            'total_refuse':0,#拒绝发送计数
            'error':0,#短期错误计数(距离最后错误时间超过3小时将被清空)
            'reset':0,#重置计数
            'last_error':0,#上次错误时间戳
            'rebirth':0,#轮回计数
            'dealtimeavg':0,#处理时间平均值
            'dealerrtimeavg':0,#异常处理时间平均值
            'sendtimeavg':0,#从发送到发送完毕时间的平均值(不计算异常消耗时)
            'last_change':0,
            'last_deal':0,
        })
        dictInit(send_log,bottype,botuuid,endobj = TempMemory(os.path.join('msgStream',bottype+'_'+botuuid+'.json'),limit = 250,autosave = True,autoload = True))
    dictInit(send_count,bottype,botuuid,botgroup)

    #二阶段初始化
    send_me = dictGet(send_count,bottype,botuuid)
    send_me['total_send'] += 1
    send_me['last_change'] = time.time()
    if send_me['total_send'] > 255659:
        send_me = {
            'total_send':0,#发送总计数
            'total_error':0,#错误总计数
            'total_refuse':0,#拒绝发送计数
            'error':0,#短期错误计数(距离最后错误时间超过3小时将被清空)
            'reset':0,#重置计数
            'last_error':0,#上次错误时间戳
            'rebirth':send_me['rebirth'] + 1,#轮回计数
            'last_change':0,
            'last_deal':0,
            'group':send_me['group'],
            'private':send_me['private']
        }
    
    if not send_me[botgroup][senduuid]:
        send_me[botgroup][senduuid] = 0
        
    send_unit = {
            'status':None,
            'unittype':'msg',#用于标识错误从属类型(msg、warning)
            'bottype':bottype,
            'botuuid':botuuid,
            'botgroup':botgroup,
            'senduuid':senduuid,
            'sendObj':sendObj,
            'message':message,
            'sendtime':time.time(),
            'senddur':time.time()-sendstarttime,
            'dealsenddur':time.time()-dealstarttime
        }
    #发送限制
    if send_me[botgroup][senduuid] == -1:
        send_me['total_refuse'] += 1
        exp_check(send_unit,send_me,-1)
        return
    #数据发送
    try:
        SUConfig[bottype](bottype,botuuid,botgroup,senduuid,sendObj,message)
        sendlogger.info('{bottype}>{botuuid}>{botgroup}>{senduuid} 发送了一条消息:{message}'.format(**send_unit))
    except:
        send_unit['status'] = False
        send_me['total_error'] += 1
        if time.time() - send_me['last_error'] > 10800:
            send_me['error'] = 0
            send_me['reset'] += 1
        send_me['error'] += 1
        send_me['last_error'] = time.time()
        send_me[botgroup][senduuid] += 1

        s = traceback.format_exc(limit=5)
        logger.error(s)
        exp_check(send_unit,send_me,send_me[botgroup][senduuid])
    else:
        send_unit['status'] = True
        send_me[botgroup][senduuid] = 0

    #数据存档
    send_log[bottype][botuuid].join(send_unit)
    #保存包含统计信息的数组
    data_save(send_count_path,send_count)

def send_msg(bottype:str,botuuid:str,botgroup:str,senduuid:str,sendObj:dict,message:SendMessage):
    if not dictHas(send_stream,bottype,botuuid):
        dictInit(send_stream,bottype,botuuid,endobj=QueueStream(bottype+'_'+botuuid,threadSendDeal))
        send_stream[bottype][botuuid].run()
    if type(message) == str:
        message = SendMessage()
        message.append(message)
    unit = {
        'bottype':bottype,
        'botuuid':str(botuuid),
        'botgroup':botgroup,
        'senduuid':str(senduuid),
        'sendObj':sendObj,
        'message':message,
        'sendstarttime':time.time()
    }
    try:
        send_stream[bottype][botuuid].put(unit)
    except:
        s = traceback.format_exc(limit=5)
        exp_send('消息推送队列异常或溢出！请检查队列',source = '消息推送队列',flag='异常')
        logger.error(s)
        return False
    return True
def send_msg_kw(*,bottype:str,botuuid:str,botgroup:str,senduuid:str,sendObj:dict,message:SendMessage,**kw):
    return send_msg(bottype,botuuid,botgroup,senduuid,sendObj,message)
"""
信息接口
"""
def getCountUnit(bottype:str,botuuid:str):
    global send_count
    unit = dictGet(send_count,bottype,botuuid)
    if not unit:
        return None
    return unit
def getPushHealth(bottype:str,botuuid:str):
    unit = getCountUnit(bottype,botuuid)
    if not unit:
        return -1
    return round(1-unit['total_error']/unit['total_send'],3)

def getMsgStreamUnitErr(bottype:str,botuuid:str,botgroup:str,senduuid:str):
    unit = getCountUnit(bottype,botuuid)
    if not unit:
        return -1
    unit = dictGet(unit,botgroup,senduuid)
    if not unit:
        return -1
    return unit

def getMsgStreamInfo(bottype:str,botuuid:str):
    unit = getCountUnit(bottype,botuuid)
    if not unit:
        return "未查询到相关信息！"
    pushhealth = getPushHealth(bottype,botuuid)
    """
        'total_send':0,#发送总计数
        'total_error':0,#错误总计数
        'total_refuse':0,#拒绝发送计数
        'error':0,#短期错误计数(距离最后错误时间超过3小时将被清空)
        'reset':0,#重置计数
        'last_error':0,#上次错误时间戳
        'rebirth':0,#轮回计数
        'last_change':0,
        'last_deal':0,
        'group':{},
        'private':{}
    """
    return """
    健康度：{1}\n
    发送计数：{total_send}\n
    错误计数：{total_error}\n
    回绝计数：{total_refuse}\n
    短时错误计数：{error}
    """.format(pushhealth,**unit)


