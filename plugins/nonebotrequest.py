from nonebot import on_command, CommandSession,RequestSession,on_request,permission as perm,message_preprocessor
import aiocqhttp
from nonebot import NoneBot

import asyncio
from helper import getlogger,msgSendToBot,CQsessionToStr,data_read,data_save,argDeal
logger = getlogger(__name__)
__plugin_name__ = '通知处理与功能附加'
__plugin_usage__ = r"""
    处理加群验证好友验证 退群信息等
    同时添加部分bot操作功能
"""

# 将函数注册为群请求处理器
@on_request('group')
async def _(session: RequestSession):
    # 判断验证信息是否符合要求
    #if session.event.comment == '暗号':
    #    # 验证信息正确，同意入群
    #    await session.approve()
    #    return
    ## 验证信息错误，拒绝入群
    #await session.reject('请说暗号')
    self_id = session.self_id
    user_id = session.event.user_id
    nick = str(user_id)
    if "nickname" in session.event.sender:
        nick = session.event.sender['nickname']
    comment = session.event.comment
    msg = '来自 ' + str(self_id) + ' 的入群请求：' + "\n"
    msg = msg + "用户：" + nick + '(' + str(user_id) + ')' + "\n"
    msg = msg + "验证信息：" + comment
    msgSendToBot(logger,msg)
    