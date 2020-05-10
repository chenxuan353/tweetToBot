from nonebot import on_command, CommandSession,NoticeSession,on_notice,permission as perm
import requests
import aiocqhttp
import asyncio
from config import notification_config

__plugin_name__ = "通用通知模板"
__plugin_usage__ = "用于常用会话通知的即时响应"

@on_notice('group_increase')
async def welcome(session: NoticeSession):
    if notification_config['Auto']:
        new = session.event(['user_id'])
        await asyncio.sleep(0.2)
        if '{NEWMEMBER}' in notification_config['Welcome']:
            await session.send(notification_config['Welcome'].format(NEWMEMBER=new))
        else:
            await session.send(notification_config['Welcome'])
    else:
        pass


@on_command('welcome',aliases=('欢迎新龙','欢迎新人','欢迎新组员'),permission=perm.GROUP_ADMIN | perm.GROUP_OWNER | perm.SUPERUSER)
async def manual_welcome(session: CommandSession):
    new = session.event(['user_id'])
    await asyncio.sleep(0.2)
    if '{NEWMEMBER}' in notification_config['Welcome']:
        await session.send(notification_config['Welcome'].format(NEWMEMBER=new))
    else:
        await session.send(notification_config['Welcome'])

