from pluginsinterface.PluginLoader import on_message,Session,on_preprocessor,on_plugloaded
from pluginsinterface.PluginLoader import PlugMsgReturn,plugRegistered,plugGet,PluginsManage
from pluginsinterface.PluginLoader import SendMessage,plugGetListStr,PlugMsgTypeEnum
from pluginsinterface.PluginLoader import PlugArgFilter,plugGetNameList,plugGetNamePlugDes
import config
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
mastername = config.mastername
project_des = config.project_des
project_addr = config.project_addr
if not mastername:
    mastername = '未知'
if not project_des:
    project_des = '没有描述'
if not project_addr:
    project_addr = '暂无'

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

#自动参数过滤器的使用
argfilter = PlugArgFilter()
argfilter.addArg(
    'plugnick',
    '插件昵称',
    '需要输入插件的昵称',
    prefunc=(lambda arg:(arg if arg in plugGetNameList() else None)),
    canSkip=True,
    vlimit={'':''}
    )
argfilter.addArg(
    'page',
    '页码',
    '帮助的页码',
    verif='uintnozero',
    canSkip=True,
    vlimit={'':1}#设置默认值
    )
@on_message(msgfilter='(help)|(帮助)',argfilter=argfilter,des='help或帮助 参数 - 获取帮助信息')
def _(session:Session):
    global mastername,project_des,project_addr
    page = session.filterargs['page']
    plugnick = session.filterargs['plugnick']
    if plugnick != '':
        session.send(plugGetNamePlugDes(plugnick))
        return
    msg = '----帮助----\n维护者：{mastername}\n项目描述：{project_des}\n项目地址：{project_addr}\n'.format(
            mastername=mastername,
            project_des=project_des,
            project_addr=project_addr
        )
    msg += plugGetListStr(page)
    session.send(msg)

#命令注册例
@on_message(msgfilter='233',bindperm='say233',defaultperm=PlugMsgTypeEnum.group,des='233 - 回复一句233')
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


