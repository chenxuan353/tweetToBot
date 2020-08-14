# -*- coding: UTF-8 -*-
import asyncio
from nonebot import NLPSession, on_natural_language
from module.msgStream import SendMessage
from pluginsinterface.EventHandling import StandEven
from pluginsinterface.Plugmanagement import PlugMsgTypeEnum
from pluginsinterface.PlugAsyncio import even_put,runinfo
import config
from helper import getlogger,data_save
logger = getlogger(__name__)
"""
通用插件接口
"""

@on_natural_language(keywords={''},only_short_message=False,only_to_me=False)
async def _(session: NLPSession):
    """
        session.msg
        session.msg_images
        session.msg_text
        session.self_id
        session.event.raw_message
        session.event.message_id
        session.event.sender['nickname]
        session.event.user_id
        session.event.message_type
        #sub_type	friend、group、discuss、other	
        #消息子类型，如果是好友则是 friend，如果从群或讨论组来的临时会话则分别是 group、discuss
    """
    if session.event['sub_type'] == 'notice':
        return
    if 'user_id' not in session.event:
        return 
    sourceID = str(session.event['user_id'])
    senduuid = sourceID
    groupuuid = ''
    groupinfo = None
    anonymous = False
    msgtype = PlugMsgTypeEnum.unknown
    message_type = session.event['message_type']
    sourceObj = {
        'message_type':session.event['message_type']
    }
    nick = sourceID
    nickname = ''
    card = ''
    if message_type == 'private':
        message_type += '_' +session.event['sub_type']
        msgtype = PlugMsgTypeEnum.private
        if session.event['sub_type'] != 'friend':
            msgtype = PlugMsgTypeEnum.tempprivate
        if session.event['sub_type'] == 'other':
            anonymous = True
    elif message_type == 'group':
        #sub_type	normal、anonymous、notice	
        #消息子类型，正常消息是 normal，匿名消息是 anonymous，
        #系统提示（如「管理员已禁止群内匿名聊天」）是 notice
        msgtype = PlugMsgTypeEnum.group
        sourceID = str(session.event['group_id'])
        groupuuid = sourceID
        if session.event['sub_type'] == 'anonymous':
            anonymous = True
            if 'anonymous' in session.event:
                if 'name' in session.event['anonymous']:
                    nickname = session.event['anonymous']['name']
        else:
            if 'card' in session.event['sender']:
                card = session.event['sender']['card']
        groupinfo = StandEven.baleToStandGroupInfo(groupuuid,'',5,card)
    else:
        return
    
    if 'nickname' in session.event['sender']:
        nickname = session.event['sender']['nickname']
    if nickname != '':
        nick = nickname
    if card != '':
        nick = card
    senduuidinfo = StandEven.baleToStandSenduuidInfo(senduuid,nick,nickname)
    atbot = session.event['to_me']

    cqhttpmsg = session.event['message']
    message = SendMessage()
    #'💊\r\n[CQ:image,file=file,url=url]\r\n绝了！'
    #CQ码处理
    for i in range(len(cqhttpmsg)):
        data = cqhttpmsg[i]
        if data.type == 'text':
            message.append(data.data['text'])
        elif data.type == 'image':
            message.append(message.baleImgObj(data.data['url']))
        else:
            #直接组装CQ码
            CQm = '[CQ:' + data.type
            for key,value in data.data.items():
                CQm += ',' + key + '=' + value
            CQm += ']'
            message.append(message.baleUnknownObj('CQ',CQm,{'flag':data.type,'data':data.data}))
    if senduuid in config.PLUGADMIN['cqhttp']:
        msgtype = msgtype | PlugMsgTypeEnum.plugadmin
    plugObj = {'type':'cqhttp','even':session.event,'bot':session.bot}
    #生成事件
    even = StandEven(
        'cqhttp',str(session.self_id),message_type,sourceID,
        msgtype,anonymous,atbot,
        groupuuid,groupinfo,senduuid,senduuidinfo,
        message,plugObj=plugObj,sourceObj=sourceObj
    )
    #发送事件
    if runinfo['run']:
        even_put(even)
    else:
        logger.info('事件处理未启动，插件事件不可达！')