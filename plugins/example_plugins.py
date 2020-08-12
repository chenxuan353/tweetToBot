from pluginsinterface.PluginLoader import on_message,StandEven,on_preprocessor,on_plugloaded
from pluginsinterface.PluginLoader import PlugMsgReturn,plugRegistered,plugGet,PluginsManage
from helper import getlogger
logger = getlogger(__name__)

@on_plugloaded()
def _(plug:PluginsManage):
    #插件管理器使用例
    logger.info(plug.getPlugDes(simple=False))
    logger.info(plug.getPlugFuncsDes())

@plugRegistered('插件例')
def _():
    return {
        'plugmanagement':'1.0',#插件注册管理(原样)  
        'version':'1.0',#插件版本  
        'auther':'~',#插件作者  
        'des':'用于示例与测试的插件'#插件描述  
        }
@on_preprocessor()
def _(even:StandEven) -> PlugMsgReturn:
    #返回忽略时消息继续传递，返回拦截时消息被拦截
    #此行为仅是插件内行为，而on_message注册的函数拦截会将整个消息拦截不让后续插件处理
    #后续插件将使用 even.sourcefiltermsg 参数进行消息后续过滤(str)
    msg:str = even.sourcefiltermsg
    if msg.startswith(('!','！')):
        even.sourcefiltermsg = msg[1:]
        return PlugMsgReturn.Ignore
    return PlugMsgReturn.Intercept

#命令注册例
@on_message(msgfilter='233',des='233 - 回复一句233')
def _(even:StandEven) -> PlugMsgReturn:
    even.send('233')

@on_message(msgfilter='爪巴',des='爪巴 - 随机爪巴')
def _(even:StandEven):
    even.send('呜呜呜,这就爬')

@on_message(msgfilter='复读',des='复读 参数 - 复读参数')
def _(even:StandEven):
    even.send(even.argstr.strip())


