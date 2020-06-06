from nonebot import on_command, CommandSession,permission as perm
import asyncio
import config
from helper import getlogger,CQsessionToStr,data_read,data_save,async_msgSendToBot,TokenBucket,TempMemory,argDeal
import helper
import module.permissiongroup as permissiongroup
logger = getlogger(__name__)
__plugin_name__ = '反馈与记录'
__plugin_usage__ = r"""
    记录与处理反馈
"""
#反馈权限
permgroupname = 'feedback'
permissiongroup.perm_addLegalPermGroup(__name__,'反馈模块',permgroupname)
permissiongroup.perm_addLegalPermUnit(permgroupname,'feedback') #反馈权限

feedback_push_switch = config.feedback_push_switch
#反馈存储
feedbacktmemory = TempMemory('feedback.json',100,autoload=True,autosave=True)
rate_limit_bucket = TokenBucket(0.1,5)

def perm_check(session: CommandSession,permunit:str,Remotely:dict = None,user:bool = False):
    if Remotely != None:
        return permissiongroup.perm_check(
            Remotely['message_type'],
            Remotely['sent_id'],
            permgroupname,
            permunit
            )
    elif user:
        return permissiongroup.perm_check(
            'private',
            session.event['user_id'],
            permgroupname,
            permunit
            )
    return permissiongroup.perm_check(
        session.event['message_type'],
        (session.event['group_id'] if session.event['message_type'] == 'group' else session.event['user_id']),
        permgroupname,
        permunit
        )

#预处理
def headdeal(session: CommandSession):
    if session.event['message_type'] == "group" and session.event.sub_type != 'normal':
        return False
    return True


# on_command 装饰器将函数声明为一个命令处理器
@on_command('feedback',aliases=['反馈','Feedback'],only_to_me = True)
async def feedback(session: CommandSession):
    if not headdeal(session):
        return
    if perm_check(session,'-feedback',user = True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    if perm_check(session,'-feedback'):
        await session.send('操作被拒绝，权限不足(g)')
        return
    stripped_arg = session.current_arg.strip()
    if stripped_arg == '':
        await session.send('参数为空！')
        return
    if not rate_limit_bucket.consume(1):
        await session.send("反馈频率过高！")
        return
    logger.info(CQsessionToStr(session))
    message_type = session.event['message_type']
    group_id = str((session.event['group_id'] if message_type == 'group' else 'None'))
    user_id = str(session.event['user_id'])
    nick = user_id
    if 'nickname' in session.event.sender:
        nick = session.event.sender['nickname']
    count = 0
    if feedbacktmemory.tm != []:
        count = feedbacktmemory.tm[-1]['id'] + 1
    feedbackunit = {
        'id':count,
        'deal':False,
        'self_id':session.self_id,
        'message_type':message_type,
        'group_id':group_id,
        'user_id':user_id,
        'nick':nick,
        'text':stripped_arg
    }
    feedbacktmemory.join(feedbackunit)
    msg = "反馈ID:" + str(feedbackunit['id']) + "\n"
    if feedbackunit['message_type'] == 'group':
        msg = msg + '来自群聊 ' + feedbackunit['group_id'] + "\n"
    else:
        msg = msg + '来自私聊' + "\n"
    msg = msg + feedbackunit['nick'] + "(" + feedbackunit['user_id'] + ")" + "\n"
    msg = msg + "反馈了：" + feedbackunit['text']
    #logger.warning('反馈:'+s)
    if feedback_push_switch:
        await async_msgSendToBot(logger,msg)
    await session.send('已收到反馈，反馈ID：' + str(count))

@on_command('dealfeedback',aliases=['处理反馈','反馈处理','dealFeedback'],permission=perm.SUPERUSER,only_to_me = True)
async def dealfeedback(session: CommandSession):
    if not headdeal(session):
        return
    logger.info(CQsessionToStr(session))
    arglimit = [
        {
            'name':'feedid', #参数名
            'des':'反馈ID', #参数错误描述
            'type':'int', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':None, #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
            }
        },
        {
            'name':'text', #参数名
            'des':'反馈内容', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':'', #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
            }
        }
    ]
    args = argDeal(session.current_arg.strip(),arglimit)
    if not args[0]:
        await session.send(args[1] + '=>' + args[2])
        return
    args = args[1]
    feedbackunit = feedbacktmemory.find((lambda item,val: item['id'] == val),args['feedid'])
    if feedbackunit == None:
        await session.send("未搜索到ID:" + str(args['feedid']) + " 的反馈记录")
        return
    if args['text'] == '':
        msg = "---历史反馈---\n" + "已处理：" + ("是" if feedbackunit['deal'] else "否") + "\n"
        msg = msg + "反馈ID:" + str(feedbackunit['id']) + "\n"
        if feedbackunit['message_type'] == 'group':
            msg = msg + '来自群聊 ' + feedbackunit['group_id'] + "\n"
        else:
            msg = msg + '来自私聊' + "\n"
        msg = msg + feedbackunit['nick'] + "(" + feedbackunit['user_id'] + ")" + "\n"
        msg = msg + "反馈了：" + feedbackunit['text']
        await session.send(msg)
        return
    else:
        msg = "ID " + str(feedbackunit['id']) + " 的反馈回复：" + "\n"
        msg = msg + args['text'].replace('&#91;','[').replace('&#93;',']')
        try:
            if feedbackunit['message_type'] == 'group':
                await session.bot.send_msg_rate_limited(
                    self_id=feedbackunit['self_id'],
                    message_type=feedbackunit['message_type'],
                    group_id=int(feedbackunit['group_id']),
                    message=msg
                    )
            else:
                await session.bot.send_msg_rate_limited(
                    self_id=feedbackunit['self_id'],
                    message_type=feedbackunit['message_type'],
                    user_id=int(feedbackunit['user_id']),
                    message=msg
                    )
        except:
            await session.send("回复发送失败")
            return
        if not feedbackunit['deal']:
            feedbackunit['deal'] = True
            feedbacktmemory.save()
        await session.send("回复已发送")

def getlist(page:int=1):
    ttm = feedbacktmemory.tm.copy()
    length = len(ttm)
    cout = 0
    s = "反馈ID,反馈处理,反馈内容简写\n"
    for i in range(length - 1,-1,-1):
        if cout >= (page-1)*5 and cout < (page)*5:
            feedbackunit = ttm[i]
            s = s + str(feedbackunit['id']) + ',' + ("是" if feedbackunit['deal'] else "否") + ',' + feedbackunit['text'][:25] + "\n"
        cout = cout + 1
    totalpage = (cout)//5 + (0 if cout%5 == 0 else 1)
    s = s + '页数:'+str(page)+'/'+str(totalpage)+'总记录数：'+str(cout) + '\n'
    s = s + '使用!处理反馈 反馈ID 获取指定反馈内容' + "\n"
    s = s + '使用!处理反馈 反馈ID 处理结果 对指定反馈进行处理' + "\n"
    return s
@on_command('feedbacklist',aliases=['反馈列表'],permission=perm.SUPERUSER,only_to_me = True)
async def feedbacklist(session: CommandSession):
    if not headdeal(session):
        return
    logger.info(CQsessionToStr(session))
    arglimit = [
        {
            'name':'page', #参数名
            'des':'页码', #参数错误描述
            'type':'int', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':1, #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
            }
        }
    ]
    args = argDeal(session.current_arg_text.strip(),arglimit)
    if not args[0]:
        await session.send(args[1] + '=>' + args[2])
        return
    args = args[1]
    page = args['page']
    if page < 1:
        await session.send("页码不能为负")
        return
    s = getlist(page)
    await session.send(s)


@on_command('about',aliases=['帮助','help','关于'],only_to_me = False)
async def about(session: CommandSession):
    if not headdeal(session):
        return
    logger.info(CQsessionToStr(session))
    msg = '维护：'+config.mastername+' 相关协作者见开源地址' + "\n"
    msg = msg + '!转推帮助 -查看转推帮助' + "\n"
    msg = msg + '!烤推帮助 -查看烤推帮助(不支持私聊)' + "\n"
    msg = msg + '!机翻帮助 -查看机翻帮助' + "\n"
    msg = msg + '如有疑问或bug报告可以!反馈 反馈内容 进行反馈' + "\n"
    msg = msg + '项目开源地址：http://uee.me/dfRwA'
    await session.send(msg)
