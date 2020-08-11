import asyncio
from nonebot import NLPSession, on_natural_language
from helper import getlogger
logger = getlogger(__name__)
"""
通用插件接口
"""

@on_natural_language(keywords={''})
async def _(session: NLPSession):
    stripped_msg = session.msg_text.strip()