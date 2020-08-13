from pluginsinterface.PluginLoader import on_message,Session,on_preprocessor,on_plugloaded
from pluginsinterface.PluginLoader import PlugMsgReturn,plugRegistered,plugGet,PluginsManage
from pluginsinterface.PluginLoader import SendMessage,plugGetListStr
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

@on_plugloaded()
def _(plug:PluginsManage):
    #插件管理器使用例
    logger.info(plug.getPlugDes(simple=False))
    logger.info(plug.getPlugFuncsDes())

@plugRegistered('插件例程',groupname='plugexample')
def _():
    return {
        'plugmanagement':'1.0',#插件注册管理(原样)  
        'version':'1.0',#插件版本  
        'auther':'chenxuan',#插件作者  
        'des':'用于示例与测试的插件'#插件描述  
        }
@on_preprocessor()
def _(session:Session) -> PlugMsgReturn:
    #返回忽略时消息继续传递，返回拦截时消息被拦截
    #此行为仅是插件内行为，而on_message注册的函数拦截会将整个消息拦截不让后续插件处理
    #后续插件将使用 even.sourcefiltermsg 参数进行消息后续过滤(str)
    msg:str = session.sourcefiltermsg
    if msg.startswith(('!','！')):
        session.sourcefiltermsg = msg[1:]
        return PlugMsgReturn.Ignore
    return PlugMsgReturn.Intercept

#命令注册例
@on_message(msgfilter='233',bindperm='say233',des='233 - 回复一句233')
def _(session:Session) -> PlugMsgReturn:
    session.send('233')

#命令注册例
@on_message(msgfilter='来图',des='来图 - 回复一张图')
def _(session:Session) -> PlugMsgReturn:
    session.send('[CX:img,src={src},text={text}]'.format(
        src = 'https://i2.hdslb.com/bfs/face/727d19364b867c2baaf5a2902de6bf28387379e7.jpg',
        text = SendMessage.textCoding('[无法显示的图片]')
    ))

@on_message(msgfilter='爪巴',des='爪巴 - 随机爪巴')
def _(session:Session):
    session.send('呜呜呜,这就爬')

@on_message(msgfilter='复读',des='复读 参数 - 复读参数')
def _(session:Session):
    session.send(session.argstr.strip())

@on_message(msgfilter='(help)|(帮助)',argfilter="page:uint:0",des='help或帮助 参数 - 获取帮助信息')
def _(session:Session):
    page = int(session.filterargs['page'])
    session.send(plugGetListStr(page))
