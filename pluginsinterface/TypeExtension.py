from enum import Enum
"""
插件相关类
"""
class NoInstance(type):
    #通过__call___方法控制访问
    def __call__(self,*args,**kwargs):
        raise TypeError('禁止实例化')

#消息类型 private、group、tempprivate、tempgroup  私聊(一对一)、群聊(一对多)、临时聊天(一对一)、临时群聊(一对多)
class PlugMsgTypeEnum(metaclass=NoInstance):
    """
        插件消息类型定义类
        不可实例化 多个类型过滤使用 | 分隔(例：PlugMsgTypeEnum.private | PlugMsgTypeEnum.group)
        none #全部忽略(用于授权)
        unknown #未知类型(仅用于事件生成过程)
        private #私聊
        group #群聊
        tempprivate #临时私聊
        tempgroup #临时群聊
        plugadmin #插件管理者(仅用于消息过滤时识别管理者)
    """
    none = 0
    unknown = 0
    private = 1
    group = 2
    tempprivate = 4
    tempgroup = 8
    plugadmin = 16 #插件管理者
    allowall = 1 | 2 | 4 | 8 | 16
    @staticmethod
    def getAllowlist(code) -> list:
        l = []
        for key,value in PlugMsgTypeEnum.__dict__.items():
            if not key.startswith('__') and key not in ('getAllowlist','getMsgtype','allowall'):
                if code & value:
                    l.append(key)
        return l
    @staticmethod
    def getMsgtype(code) -> str:
        for key,value in PlugMsgTypeEnum.__dict__.items():
            if not key.startswith('__') and key not in ('getAllowlist','getMsgtype','allowall','plugadmin'):
                if code & value:
                    return key

class PlugMsgReturn(Enum):
    """
        插件返回值定义类
        不可实例化
        Ignore 消息忽略
        Intercept 消息拦截
    """
    Ignore = 1 
    Intercept = 2 

