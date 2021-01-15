# -*- coding: UTF-8 -*-
#插件标准依赖
from pluginsinterface.PluginLoader import on_message, Session, on_preprocessor, on_plugloaded
from pluginsinterface.PluginLoader import PlugMsgReturn, plugRegistered, PlugMsgTypeEnum, PluginsManage
from pluginsinterface.PluginLoader import PlugArgFilter
#扩展函数
from pluginsinterface.PluginLoader import plugGetListStr, plugGetNameList, plugGetNamePlugDes, SendMessage
import asyncio
from load_config import config
import random
from nonebot import NoneBot
from helper import getlogger
logger = getlogger(__name__)
"""
兼容层使用CX码，可兼容大部分bot
*兼容标识：unknown
*兼容段将交给对应bot的消息解析器处理，通用段保证可以对所有bot兼容
通用段：text,img
固定数据键值对：text-当无法解析时将使用此值
[CX:消息段标识,数据键值对]
"""


@plugRegistered('插件例程', groupname='plugexample')
def _():
    return {
        'plugmanagement': '1.0',  #插件注册管理(原样)  
        'version': '1.0',  #插件版本  
        'auther': 'chenxuan',  #插件作者  
        'des': '用于示例与测试的插件'  #插件描述  
    }


@on_plugloaded()
def _(plug: PluginsManage):
    #插件管理器使用例(插件管理器回调将在插件全部加载完成后立刻调用)
    #如果当前模块未注册插件则plug为None
    if plug:
        #plug.switchPlug(False) #关闭插件
        logger.info(plug.getPlugDes(simple=False))
        logger.info(plug.getPlugFuncsDes())
        plug.registerPerm('say233',
                          des='使用233的权限',
                          defaultperm=PlugMsgTypeEnum.group)


@on_preprocessor()
async def _(session: Session) -> PlugMsgReturn:
    #返回PlugMsgReturn.Allow时消息继续传递，返回PlugMsgReturn.Refuse时消息被拦截
    #此行为仅是插件内行为，而on_message注册的函数拦截会将整个消息拦截不让后续插件处理
    #后续插件将使用 even.sourcefiltermsg 参数进行消息后续过滤(str)
    """
    logger.info('bot类型标识：{0}'.format(session.bottype))
    logger.info('bot唯一标识：{0}'.format(session.botuuid))
    logger.info('发送组标识：{0}'.format(session.botgroup))
    logger.info('发送方标识：{0}'.format(session.uuid))
    logger.info('消息类型标识：{0}'.format(PlugMsgTypeEnum.getAllowlist(session.msgtype)))
    logger.info('标准消息：{0}'.format(session.messagestand))
    """
    msg: str = session.sourcefiltermsg
    if msg.startswith(('!', '！')):
        session.sourcefiltermsg = msg[1:]  #修正源消息方便后续函数使用
        return PlugMsgReturn.Allow
    return PlugMsgReturn.Refuse


#命令注册例
@on_message(msgfilter='233',
            bindperm='say233',
            des='233 - 回复一句233',
            at_to_me=False)
async def _(session: Session) -> PlugMsgReturn:
    session.send('233')


#命令注册例
@on_message(msgfilter='来图', des='来图 - 回复一张图')
async def _(session: Session) -> PlugMsgReturn:
    session.send('[CX:img,src={src},text={text}]'.format(
        src=
        'https://i2.hdslb.com/bfs/face/727d19364b867c2baaf5a2902de6bf28387379e7.jpg',
        text=SendMessage.textCoding('[无法显示的图片]')))


@on_message(msgfilter='爬', des='爬 - 马上就爬', at_to_me=False)
async def _(session: Session):
    session.send('呜呜呜,这就爬')


@on_message(msgfilter='爪巴', des='爪巴 - 随机爪巴', at_to_me=False)
async def _(session: Session):
    ss = ('我爬 我现在就爬Orz', '我爪巴', '你给爷爬OuO', '呜呜呜别骂了 再骂BOT就傻了TAT', '就不爬>_<',
          '欺负可爱BOT 建议超级加倍TuT')
    index = random.randint(0, len(ss) - 1)
    session.send(ss[index])


@on_message(msgfilter='复读', des='复读 参数 - 复读参数', at_to_me=False)
async def _(session: Session):
    res = await session.waitsend(session.argstr.strip())
    #res['message_id'] 会尽可能返回消息在发送消息的BOT对象返回值中获取消息ID
    #session.send('可能的话会在五秒后撤回消息...')
    await asyncio.sleep(5)
    if res[0]:
        res = res[1]
        if session.bottype == 'cqhttp':
            #bot差异化处理
            bot: NoneBot = session.even.plugObj['bot']
            logger.info('消息ID：{0}'.format(res['message_id']))
            await bot.delete_msg(message_id=res['message_id'],
                                 self_id=int(session.botuuid))


@on_message(msgfilter='(绝活)|(异常)|(无内鬼报个错)', des='绝活 参数 - 报个指定消息的异常')
async def _(session: Session):
    exception = ('')
    index = random.randint(0, len(exception) - 1)
    session.send(exception[index])
    #raise Exception(session.argstr.strip())
