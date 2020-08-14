# -*- coding: UTF-8 -*-
import threading
import queue
import functools
import asyncio
import time
import module.msgStream as msgStream
from module.msgStream import SendMessage
from helper import getlogger
logger = getlogger(__name__)
"""
    接收插件处理过的消息，并打包成事件转发到对应插件

    消息结构：
    #标识来源(用于回复及后续处理)
    bottype
    botuuid
    botgroup
    uuid
    sourceObj:dict #来源附加数据(用于定位回复对象等)

    msgtype #消息类型 private、group、tempprivate、tempgroup  私聊(一对一)、群聊(一对多)、临时聊天(一对一)、临时群聊(一对多)
    anonymous #消息是否匿名
    atbot #消息是否指向bot
    groupuuid:str #群组UUID(非群聊时为空)
    groupinfo:dict #群组信息
    {
        groupuuid:群组ID,
        name:群组名,
        sendlevel:消息发送方权限等级(6级 0群主 1管理 2预留 3预留 4一般群员 5临时群员-匿名等),
        sendnick:消息发送方群组名片(可能为空)
    }
    senduuid:str,#发送方UUID
    senduuidinfo:dict #发送方信息
    {
        uuid:ID,
        nick:昵称(保证存在),
        name:名字
    }
    plugObj:dict #插件附加数据
    message:SendMessage #消息
"""
class StandEven:
    def __init__(self,
            bottype:str,
            botuuid:str,
            botgroup:str,
            uuid:str,
            msgtype:str,
            anonymous:bool,
            atbot:bool,
            groupuuid:str,
            groupinfo:dict,
            senduuid:str,
            senduuidinfo:dict,
            message:SendMessage,
            sourceObj:dict = None,
            plugObj:dict = None):
        standdata = self.baleToStandEven(bottype,
            botuuid,
            botgroup,
            uuid,
            msgtype,
            anonymous,
            atbot,
            groupuuid,
            groupinfo,
            senduuid,
            senduuidinfo,
            message,
            sourceObj = sourceObj,
            plugObj= plugObj)
        standdata['filtermsg'] = message.filterToStr()
        standdata['simplemsg'] = message.toSimpleStr()
        self.__dict__['lock'] = False
        self.message:SendMessage = None
        self.hasReply = False
        self.__dict__.update(standdata)
    def __setattr__(self,key,value):
        if key in ('lock','hasReply'):
            self.__dict__[key] = value
        elif self.lock:
            raise Exception('当前StandEven已锁定')
        self.__dict__[key] = value
    def __delattr__(self,key):
        if self.lock:
            raise Exception('当前StandEven已锁定')
        if key in ('lock','hasReply'):
            raise Exception('StandEven类不可删除lock与hasReply属性')
        del self.__dict__[key]
    @staticmethod
    def baleToStandGroupInfo(groupuuid,name,sendlevel,sendnick):
        return {
            'groupuuid':groupuuid,
            'name':name,
            'sendlevel':sendlevel,
            'sendnick':sendnick
        }
    @staticmethod
    def baleToStandSenduuidInfo(uuid,nick,name):
        return {
            'uuid':uuid,
            'nick':nick,
            'name':name,
        }
    def setLock(self,value:bool):
        self.lock = value
    def baleToStandEven(self,
            bottype:str,
            botuuid:str,
            botgroup:str,
            uuid:str,
            msgtype:str,
            anonymous:bool,
            atbot:bool,
            groupuuid:str,
            groupinfo:dict,
            senduuid:str,
            senduuidinfo:dict,
            message:SendMessage,
            sourceObj:dict = None,
            plugObj:dict = None,
            ):
        return {
            'bottype':bottype,
            'botuuid':botuuid,
            'botgroup':botgroup,
            'uuid':uuid,
            'sourceObj':sourceObj,
            'msgtype':msgtype,
            'anonymous':anonymous,
            'atbot':atbot,
            'groupuuid':groupuuid,
            'groupinfo':groupinfo,
            'senduuid':senduuid,
            'senduuidinfo':senduuidinfo,
            'message':message,
            'plugObj':plugObj
        }
    def toStr(self):
        msg = "{bottype}-{botuuid}-{botgroup}-{uuid}:".format(**self.__dict__)
        msg += self.message.toSimpleStr()
        return msg
    def Reply(self,message:SendMessage):
        if type(message) == str:
            message = SendMessage(message)
        log = "回复：{bottype}-{botuuid}-{botgroup}-{uuid}:".format(**self.__dict__) + message.toSimpleStr()
        logger.info(log)
        self.hasReply = True
        #pylint: disable=no-member
        return msgStream.send_msg(self.bottype,self.botuuid,self.botgroup,self.uuid,self.sourceObj,message)
    def send(self,message:SendMessage):
        return self.Reply(message)
    async def waitReply(self,message:SendMessage,timeout:int = 15) -> tuple:
        """
            发送消息并等待消息发送结果
            超时时间可以设置为1-60
        """
        if timeout < 1:
            timeout = 1
        res = self.Reply(message)
        if not res[0]:
            return res
        timecount = 0
        while True:
            if timecount > timeout or timeout > 60:
                break
            sendres = msgStream.id_getRes(res[1])
            if sendres[0]:
                return sendres
            await asyncio.sleep(1)
            timecount += 1
        return (False,'获取发送结果超时')
    async def waitsend(self,message:SendMessage,timeout:int = 15) -> tuple:
        return await self.waitReply(message,timeout)
    def setMessage(self,message:SendMessage):
        #用于测试，快速修改信息
        if type(message) == str:
            message = SendMessage(message)
        self.message = message
        self.simplemsg = message.toSimpleStr()