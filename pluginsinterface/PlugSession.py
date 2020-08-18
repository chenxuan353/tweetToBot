# -*- coding: UTF-8 -*-
from pluginsinterface.TypeExtension import PlugMsgTypeEnum
from pluginsinterface.EventHandling import StandEven
from pluginsinterface.PermissionGroup import authBaleObjectRecognition
from pluginsinterface.PermissionGroup import authCheck,authAllow,authRemoval,authDeny,authDenyRemoval,authCheckDeny
import time
from inspect import isfunction
import config
from module.msgStream import SendMessage
from helper import getlogger
from helper import dictInit,dictHas,dictGet,dictSet
logger = getlogger(__name__)

Session_timeout = config.Session_timeout
PLUGADMIN = config.PLUGADMIN
class Session:
    """
        临时会话，包含过期时间
        过期后会话数据将完全刷新
        注：会话为全局会话，会话对应事件可能会快速变动，但保证所有插件处理完消息前不变动
        注：每个插件的会话有单独的临时作用域，session过期后被清空
        注：会话仅维持对唯一消息来源的会话
            如群聊xxx发送的消息，私聊xxx发送的消息，对群聊不能特定到发送者个人
            针对个人的消息存储需要插件制作者自行实现
        注：如果想维持长期会话，请保存Session对应的事件
        注：事件(StandEven类)将在插件处理完成后解锁修改限制，如不留存事件将丢失
    """
    def __init__(self,even:StandEven = None,timeout = Session_timeout):
        self.__dict__['__lock'] = False
        self.__dict__['__corelock'] = False
        self.__dict__['__coretype'] = (
                    'even','timeout','create_timestamp','lastuse_timestamp',
                    'bottype','botuuid','botgroup','uuid','senduuid',
                    'msgtype','anonymous','atbot','senduuidinfo','sourceObj',
                    'message','messagestand','globalscope','scope','__coretype',
                    'groupinfo','plugObj','groupuuid'
                )
        self.even = even
        self.globalscope = {}
        self.scope = ''
        self.timeout = timeout
        if self.timeout < 60 and self.timeout != 0:
            self.timeout = 60
        self.create_timestamp = int(time.time())
        self.lastuse_timestamp = int(time.time())
        if self.even:
            self.bottype = even.bottype
            self.botuuid = even.botuuid
            self.botgroup = even.botgroup
            self.uuid = even.uuid
            self.groupuuid = even.groupuuid
            self.groupinfo = even.groupinfo
            self.sourceObj = even.sourceObj
            self.senduuid = even.senduuid
            self.senduuidinfo = even.senduuidinfo
            self.msgtype = even.msgtype
            self.anonymous = even.anonymous
            self.atbot = even.atbot
            self.plugObj = even.plugObj
            self.message:SendMessage = even.message
            self.messagestand = self.message.toStandStr()
        self.__dict__['__corelock'] = True
    def __setattr__(self,name,value):
        if name == '__lock':
            self.__dict__[name] = value
        if self.__dict__['__lock']:
            raise Exception("当前session已锁定")
        if name in self.__dict__['__coretype']:
            if self.__dict__['__corelock']:
                raise Exception("当前session核心已锁定")
            self.__dict__[name] = value
        if name in self.__dict__:
            self.__dict__[name] = value
            return
        if 'scope' in self.__dict__ and self.__dict__['scope']:
            self.__dict__['globalscope'][self.__dict__['scope']][name] = value
            return
        self.__dict__[name] = value
    def __delattr__(self,name):
        if name in ('__lock','__corelock','__coretype'):
            raise Exception("不可删除键值")
        if self.__dict__['__lock']:
            raise Exception("当前session已锁定")
        if name in self.__dict__['__coretype']:
            if self.__dict__['__corelock']:
                raise Exception("当前session核心已锁定")
            del self.__dict__[name]
        if 'scope' in self.__dict__ and self.__dict__['scope']:
            del self.__dict__['globalscope'][self.__dict__['scope']][name]
            return
        del self.__dict__[name]
    def __getattribute1(self, name):
        selfdict = super(Session,self).__getattribute__('__dict__')
        if name is '__dict__':
            return selfdict
        if name in selfdict:
            if name in selfdict['__coretype']:
                return selfdict[name]
            if not selfdict['scope']:
                """
                    只有在无作用域时返回无作用域状态的值
                """
                return selfdict[name]
        if name is '__class__':
            return selfdict
        selfclass = super(Session,self).__getattribute__('__class__')
        if name in selfclass.__dict__:
            return selfclass.__dict__[name]
        super().__getattribute__(name)
    def __getattr__(self, name):
        """
            属性不存在时调用
        """
        if self.__dict__['scope']:
            if name not in self.__dict__['globalscope'][self.__dict__['scope']]:
                raise AttributeError(
                        'Session类的对象不存在属性{name}，当前作用域{scope}'.format(
                            name=name,
                            scope=self.__dict__['scope']
                        ))
            return self.__dict__['globalscope'][self.__dict__['scope']][name]
        raise AttributeError('Session类的对象不存在属性{name}，当前无作用域'.format(name=name))
    def setEven(self,even:StandEven):
        """
            设置Session对应的even，请勿手动操作
        """
        self.__dict__['__corelock'] = False
        self.even = even
        self.bottype = even.bottype
        self.botuuid = even.botuuid
        self.botgroup = even.botgroup
        self.uuid = even.uuid
        self.groupuuid = even.groupuuid
        self.groupinfo = even.groupinfo
        self.sourceObj = even.sourceObj
        self.senduuid = even.senduuid
        self.senduuidinfo = even.senduuidinfo
        self.msgtype = even.msgtype
        self.anonymous = even.anonymous
        self.atbot = even.atbot
        self.plugObj = even.plugObj
        self.message:SendMessage = even.message
        self.messagestand = self.message.toStandStr()
        self.__dict__['__corelock'] = True
        self.refresh()
    def refresh(self):
        """
            刷新session的引用，重置过期时间
        """
        self.__dict__['lastuse_timestamp'] = int(time.time())
    def checkExpired(self,usetime:int) -> bool:
        """
            检查session是否过期，过期返回True
        """
        if self.timeout <= 0:
            return True
        return usetime > self.lastuse_timestamp and (usetime - self.lastuse_timestamp) > self.timeout
    def delScope(self):
        """
            删除session作用域，请勿手动操作
        """
        self.__dict__['scope'] = ''
    def setScope(self,name):
        """
            设置session作用域，请勿手动操作
        """
        if name not in self.globalscope:
            self.globalscope[name] = {}
        self.__dict__['scope'] = name
    def setLock(self,value:bool):
        """
            设置session锁，请勿手动操作
        """
        self.__dict__['__lock'] = value
    def setCoreLock(self,value:bool):
        """
            设置session核心锁，请勿手动操作
        """
        self.__dict__['__corelock'] = value
    def reset(self):
        """
            重置session，移除所有非核心属性，请勿手动操作
        """
        self.__dict__['globalscope'] = {}
        self.__dict__['scope'] = ''
        for key in list(self.__dict__.keys()):
            if key not in self.__dict__['__coretype'] and not key.startswith('__') and not isfunction(self.__dict__[key]):
                del self.__dict__[key]
    def authCheck(self,msgtype:str,groupname:str,perm:str) -> bool:
        """
            检查组Session对应对象的指定权限，不判断全局管理员权限
            msgtype要求为文本类型
        """
        return authCheck(self.bottype,self.botuuid,msgtype,self.uuid,groupname,perm)
    def authCheckSend(self,groupname:str,perm:str) -> bool:
        """
            检查组Session对应发送对象的指定私聊权限，判断全局管理员权限
        """
        PLUGADMIN = config.PLUGADMIN
        Admin = dictGet(PLUGADMIN,self.bottype,default=[])
        if self.senduuid in Admin:
            return True
        return authCheck(self.bottype,self.botuuid,'private',self.senduuid,groupname,perm)
    def authCheckSendDeny(self,groupname:str,perm:str) -> bool:
        """
            检查组Session对应发送对象的指定私聊权限，判断全局管理员权限
        """
        return authCheckDeny(self.bottype,self.botuuid,'private',self.senduuid,groupname,perm)
    def __authBaleIdentifyObj(self) -> dict:
        return authBaleObjectRecognition(
                self.bottype,
                self.botuuid,
                self.msgtype,
                self.uuid,
                self.even.message.toStandStr()
            )
    def authAllowSelf(self,
            groupname:str,perm:str,
            overlapping = True
        ) -> tuple:
        """
            给自己授权(消息来源-群聊、私聊 非发送方)
        """
        objectRecognition = self.__authBaleIdentifyObj()
        return authAllow(
            self.bottype,
            self.botuuid,
            PlugMsgTypeEnum.getMsgtype(self.msgtype),
            self.uuid,
            groupname,
            perm,
            objectRecognition = objectRecognition,
            overlapping = overlapping
        )
    def authRemovalSelf(self,
            groupname:str,perm:str
        ) -> tuple:
        """
            取消自己的授权(消息来源-群聊、私聊 非发送方)
        """
        return authRemoval(
            self.bottype,
            self.botuuid,
            PlugMsgTypeEnum.getMsgtype(self.msgtype),
            self.uuid,
            groupname,
            perm
        )
    def authDenySelf(self,
            groupname:str,perm:str,
            overlapping = True
        ) -> tuple:
        """
            授权禁止
        """
        objectRecognition = self.__authBaleIdentifyObj()
        return authDeny(
            self.bottype,
            self.botuuid,
            PlugMsgTypeEnum.getMsgtype(self.msgtype),
            self.uuid,
            groupname,
            perm,
            objectRecognition = objectRecognition,
            overlapping = overlapping
        )
    def authDenyRemovalSelf(self,
            groupname:str,perm:str
        ) -> tuple:
        """
            取消授权
        """
        return authDenyRemoval(
            self.bottype,
            self.botuuid,
            PlugMsgTypeEnum.getMsgtype(self.msgtype),
            self.uuid,
            groupname,
            perm
        )

    def authAllow(self,
            bottype:str,botuuid:str,msgtype:str,
            uuid:str,groupname:str,perm:str,
            overlapping = True
        ) -> tuple:
        """
            授权,msgtype要求为文本类型
        """
        if type(msgtype) is not str:
            raise Exception("msgtype要求为文本类型")
        objectRecognition = self.__authBaleIdentifyObj()
        return authAllow(
            bottype,
            botuuid,
            msgtype,
            uuid,
            groupname,
            perm,
            objectRecognition = objectRecognition,
            overlapping = overlapping
        )
    def authRemoval(self,
            bottype:str,botuuid:str,msgtype:str,
            uuid:str,groupname:str,perm:str
        ) -> tuple:
        """
            取消授权,msgtype要求为文本类型
        """
        if type(msgtype) is not str:
            raise Exception("msgtype要求为文本类型")
        return authRemoval(
            bottype,
            botuuid,
            msgtype,
            uuid,
            groupname,
            perm
        )
    def authDeny(self,
            bottype:str,botuuid:str,msgtype:str,
            uuid:str,groupname:str,perm:str,
            overlapping = True
        ) -> tuple:
        """
            授权禁止,msgtype要求为文本类型
        """
        if type(msgtype) is not str:
            raise Exception("msgtype要求为文本类型")
        objectRecognition = self.__authBaleIdentifyObj()
        return authDeny(
            bottype,
            botuuid,
            msgtype,
            uuid,
            groupname,
            perm,
            objectRecognition = objectRecognition,
            overlapping = overlapping
        )
    def authDenyRemoval(self,
            bottype:str,botuuid:str,msgtype:str,
            uuid:str,groupname:str,perm:str
        ) -> tuple:
        """
            取消授权,msgtype要求为文本类型
        """
        if type(msgtype) is not str:
            raise Exception("msgtype要求为文本类型")
        return authDenyRemoval(
            bottype,
            botuuid,
            msgtype,
            uuid,
            groupname,
            perm
        )
    def Reply(self,message:SendMessage):
        """
            向原路径回复消息
            返回值 (是否发送成功，消息流消息ID)
        """
        return self.even.send(message)
    def send(self,message:SendMessage):
        """
            向原路径回复消息
            返回值 (是否发送成功，消息流消息ID)
        """
        return self.even.Reply(message)
    async def waitReply(self,message:SendMessage,timeout:int = 15):
        """
            发送消息并等待消息发送结果
            超时时间可以设置为1-60
        """
        return await self.even.waitsend(message,timeout)
    async def waitsend(self,message:SendMessage,timeout:int = 15):
        """
            发送消息并等待消息发送结果
            超时时间可以设置为1-60
        """
        return await self.even.waitsend(message,timeout)
    def hasReply(self) -> bool:
        """
            是否原路径回复过消息
        """
        return self.even.hasReply
    def setReplay(self,value):
        self.even.setReply(value)

class SessionManagement:
    """
        会话管理器
    """
    def __init__(self):
        self.sessions = {}
    def getSession(self,bottype:str,botuuid:str,botgroup:str,uuid:str,even:StandEven,usetime:int = None) -> Session:
        dictInit(self.sessions,bottype,botuuid,botgroup,uuid,
            endobj=Session()
            )
        session:Session = dictGet(self.sessions,bottype,botuuid,botgroup,uuid)
        if usetime is None:
            usetime = time.time()
        if session.checkExpired(int(usetime)):
            session.reset()
        session.setEven(even)
        session.refresh()
        return session
    def delSession(self,bottype:str,botuuid:str,botgroup:str,uuid:str):
        dc = dictHas(self.sessions,bottype,botuuid,botgroup)
        if not dc or uuid not in dc:
            return
        del dc[uuid]
    def checkExpired(self,usetime:int = None):
        if usetime is None:
            usetime = time.time()
        for botuuids in self.sessions.values():
            for botgroups in botuuids.values():
                for uuids in botgroups.values():
                    for uuid in uuids:
                        if uuids[uuid].checkExpired(usetime):
                            del uuids[uuid]

sessionManagement:SessionManagement = SessionManagement()
