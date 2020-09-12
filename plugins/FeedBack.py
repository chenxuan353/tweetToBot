from pluginsinterface.PluginLoader import on_message, Session, on_preprocessor, on_plugloaded
from pluginsinterface.PluginLoader import PlugMsgReturn, plugRegistered, PlugMsgTypeEnum, PluginsManage
from pluginsinterface.PluginLoader import PlugArgFilter

from pluginsinterface.PluginLoader import SendMessage
import time
from module.msgStream import exp_send, send_msg
from helper import getlogger, TempMemory, TokenBucket
logger = getlogger(__name__)
"""
    反馈
"""
# 反馈存储
feedbacktmemory = TempMemory('feedback', 200, autoload=True, autosave=True)
rate_limit_bucket = TokenBucket(0.1, 5)


@plugRegistered('反馈', 'feedback')
def _():
    return {
        'plugmanagement': '1.0',  # 插件注册管理(原样)  
        'version': '1.0',  # 插件版本  
        'auther': 'chenxuan',  # 插件作者  
        'des': '用于反馈的插件'  # 插件描述  
    }


@on_plugloaded()
def _(plug: PluginsManage):
    if plug:
        # 注册权限
        plug.registerPerm('manage',
                          des='管理权限',
                          defaultperm=PlugMsgTypeEnum.none)
        plug.registerPerm('feedback',
                          des='反馈权限',
                          defaultperm=PlugMsgTypeEnum.allowall)
        # plug.registerPerm('infocheck',des = '信息查看权限',defaultperm=PlugMsgTypeEnum.none)
        pass


@on_preprocessor()
async def _(session: Session) -> PlugMsgReturn:
    msg: str = session.sourcefiltermsg
    if msg.startswith(('!', '！')):
        session.sourcefiltermsg = msg[1:]
        return PlugMsgReturn.Allow
    return PlugMsgReturn.Refuse


@on_message(msgfilter='(反馈)|(feedback)',
            bindperm='feedback',
            bindsendperm='feedback',
            des='反馈 反馈内容 - 反馈信息,别名feedback')
async def _(session: Session):
    if not rate_limit_bucket.consume(1):
        session.send("反馈频率过高！")
        return
    feedbackmsg = session.filterargs['tail']
    if not feedbackmsg.strip():
        session.send("并没有反馈任何信息")
        return
    nick = session.senduuidinfo['nick']
    count = 0
    feedbackunit = None
    if feedbacktmemory.tm != []:
        count = feedbacktmemory.tm[-1]['id'] + 1
        for fb in feedbacktmemory.tm:
            if not fb['dealcomplate'] and \
                fb['bottype'] == session.bottype and \
                fb['botuuid'] == session.botuuid and \
                fb['botgroup'] == session.botgroup and \
                fb['uuid'] == session.uuid:
                feedbackunit = fb
                break
    if feedbackunit is None:
        feedbackunit = {
            'bottype': session.bottype,
            'botuuid': session.botuuid,
            'botgroup': session.botgroup,
            'uuid': session.uuid,
            'sourceObj': session.sourceObj,
            'senduuid': session.senduuid,
            'timestamp': time.time(),
            'id': count,
            'deal': False,  # 是否处理过
            'dealcomplate': False,  # 是否处理完成
            'nick': nick,
            'text': feedbackmsg,
            'simpletext': feedbackmsg[:15].replace('\r',
                                                   ' ').replace('\n', ' '),
            'replay': []  # 保存回复链
        }
        feedbacktmemory.join(feedbackunit)
    else:
        feedbackunit['simpletext'] = feedbackmsg[:15].replace('\r',
                                                              ' ').replace(
                                                                  '\n', ' ')
        feedbackunit['replay'].append({
            'flag': '增加',
            'senduuid': session.senduuid,
            'nick': nick,
            'text': feedbackmsg
        })
        feedbacktmemory.save()
    if session.msgtype & PlugMsgTypeEnum.group:
        msgtype = '群聊'
    elif session.msgtype & PlugMsgTypeEnum.private:
        msgtype = '私聊'
    else:
        msgtype = '未知'
    msg = "反馈ID:{0}\n消息来源：{1}-{2}-{3}({4})\n内容：\n{5}\n反馈时间：{6}".format(
        feedbackunit['id'], msgtype, session.uuid, session.senduuid, nick,
        feedbackmsg,
        time.strftime("%Y{0}%m{1}%d{2} %H:%M:%S",
                      time.localtime(feedbackunit['timestamp'])).format(
                          '年', '月', '日'))
    exp_send(SendMessage(msg))
    session.send('已收到反馈，反馈ID：' + str(feedbackunit['id']))


argfilter = PlugArgFilter()
argfilter.addArg('unit',
                 '反馈ID',
                 '需要输入有效反馈ID',
                 prefunc=(lambda arg: feedbacktmemory.find(
                     (lambda item, val: str(item['id']) == val), arg.strip())),
                 verif='other',
                 canSkip=False)


@on_message(msgfilter='(处理反馈)|(dealfeedback)',
            argfilter=argfilter,
            bindsendperm='manage',
            des='处理反馈 反馈ID 处理信息 - 处理反馈信息,别名dealfeedback')
async def _(session: Session):
    feedbackunit = session.filterargs['unit']
    replaymsg = session.filterargs['tail']
    nick = session.senduuidinfo['nick']
    feedbackunit['deal'] = True
    feedbackunit['replay'].append({
        'flag': '处理',
        'senduuid': session.senduuid,
        'nick': nick,
        'text': replaymsg
    })
    feedbacktmemory.save()

    msg = "来自 ID:{0} 的反馈回复\n上一条消息：\n{1}\n回复内容：\n{2}".format(
        feedbackunit['id'], feedbackunit['replay'][-1]['text'][:30].strip(),
        replaymsg)
    send_msg(feedbackunit['bottype'], feedbackunit['botuuid'],
             feedbackunit['botgroup'], feedbackunit['uuid'],
             feedbackunit['sourceObj'], SendMessage(msg))
    session.send('回复已发送')


@on_message(msgfilter='(反馈完成)|(反馈处理完成)',
            argfilter=argfilter,
            bindsendperm='manage',
            des='反馈完成 反馈ID - 处理反馈信息,别名反馈处理完成')
async def _(session: Session):
    feedbackunit = session.filterargs['unit']
    feedbackunit['dealcomplate'] = True
    feedbacktmemory.save()
    session.send('已将反馈标记为处理完毕的状态')


def getlist(page: int = 1):
    ttm = feedbacktmemory.tm.copy()
    length = len(ttm)
    cout = 0
    s = "反馈ID,处理情况,反馈内容简写\n"
    for i in range(length - 1, -1, -1):
        if cout >= (page - 1) * 5 and cout < (page) * 5:
            feedbackunit = ttm[i]
            dealmsg = "处理中" if feedbackunit['deal'] else "未处理"
            if feedbackunit['dealcomplate']:
                dealmsg = "已完成"
            s = s + "{0},{1},{2}".format(feedbackunit['id'], dealmsg,
                                         feedbackunit['simpletext'])
        cout = cout + 1
    totalpage = int(cout / 5) + 1
    s += '\n页数:{0}/{1}(总共{2}个记录)'.format(page, totalpage, cout)
    s += '页数:' + str(page) + '/' + str(totalpage) + '总记录数：' + str(cout) + '\n'
    s += '使用!处理反馈 反馈ID 获取指定反馈内容' + "\n"
    s += '使用!处理反馈 反馈ID 处理结果 对指定反馈进行处理' + "\n"
    return s


argfilter = PlugArgFilter()
argfilter.addArg(
    'page',
    '页码',
    '页码',
    verif='uintnozero',
    canSkip=True,
    vlimit={'': 1}  # 设置默认值
)


@on_message(msgfilter='(反馈列表)|(feedbacklist)',
            argfilter=argfilter,
            bindsendperm='manage',
            des='反馈列表 页码 - 反馈列表,别名feedbacklist')
async def _(session: Session):
    page = session.filterargs['page']
    msg = getlist(page)
    session.send(msg)
