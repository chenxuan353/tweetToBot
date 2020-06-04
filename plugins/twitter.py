# -*- coding: UTF-8 -*-
from nonebot import on_command, CommandSession,NoticeSession,on_notice,permission as perm
from helper import getlogger,msgSendToBot,CQsessionToStr,argDeal
from module.twitter import push_list,decode_b64,encode_b64,mintweetID
import time
import asyncio
import os
import traceback
import module.permissiongroup as permissiongroup
import module.pollingTwitterApi as ptwitter
import config
logger = getlogger(__name__)
__plugin_name__ = '通用推特监听指令'
__plugin_usage__ = r"""
用于配置推特监听
详见：
https://github.com/chenxuan353/tweetToQQbot
"""

#推特事件处理对象，由启动调用的更新检测方法有关
#allow_start_method = ('TweetApi','RSShub','Twint')
if config.UPDATA_METHOD == 'TweetApi':
    import module.twitterApi as tweetListener
elif config.UPDATA_METHOD == 'RSShub':
    import module.RSShub_twitter as tweetListener
elif config.UPDATA_METHOD == 'PollingTweetApi':
    import module.pollingTwitterApi as tweetListener
else:
    raise Exception('暂不支持的更新检测(UPDATA_METHOD)方法：'+config.UPDATA_METHOD)
tweet_event_deal = tweetListener.tweet_event_deal
#转推权限
permgroupname = 'tweetListener'
permissiongroup.perm_addLegalPermGroup(__name__,'转推模块',permgroupname)
permissiongroup.perm_addLegalPermUnit(permgroupname,'listener') #监听权限

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
def perm_del(session: CommandSession,permunit:str,Remotely:dict = None):
    if Remotely != None:
        return permissiongroup.perm_del(
            Remotely['message_type'],
            Remotely['sent_id'],
            Remotely['op_id'],
            permgroupname,
            permunit
            )
    return permissiongroup.perm_del(
        session.event['message_type'],
        (session.event['group_id'] if session.event['message_type'] == 'group' else session.event['user_id']),
        session.event['user_id'],
        permgroupname,
        permunit
        )
def perm_add(session: CommandSession,permunit:str,Remotely:dict = None):
    if Remotely != None:
        return permissiongroup.perm_add(
            Remotely['message_type'],
            Remotely['sent_id'],
            Remotely['op_id'],
            permgroupname,
            permunit
            )
    return permissiongroup.perm_add(
        session.event['message_type'],
        (session.event['group_id'] if session.event['message_type'] == 'group' else session.event['user_id']),
        session.event['user_id'],
        permgroupname,
        permunit
        )

#预处理
def headdeal(session: CommandSession):
    if session.event['message_type'] == "group" and session.event.sub_type != 'normal':
        return False
    return True

@on_command('tweetListenerDeny',aliases=['转推禁用'], permission=perm.SUPERUSER,only_to_me = True)
async def tweetListenerDeny(session: CommandSession):
    if not headdeal(session):
        return
    message_type = session.event['message_type']
    #group_id = (session.event['group_id'] if message_type == 'group' else None)
    user_id = session.event['user_id']
    if message_type != 'private':
        return
    #if perm_check(session,'-listener',user = True):
    #    await session.send('操作被拒绝，权限不足(p)')
    #    return
    logger.info(CQsessionToStr(session))
    arglimit = [
        {
            'name':'msgtype', #参数名
            'des':'消息类型', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':True, #是否转换为小写
            'default':None, #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示允许任意字符串,值不为空时任意字符串将被转变为这个值
                '私聊':'private',
                'private':'private',
                '群聊':'group',
                'group':'group',
                '好友':'private',
                '群':'group',
            }
        },
        {
            'name':'send_id', #参数名
            'des':'对象ID', #参数错误描述
            'type':'int', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':None, #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
            }
        }
    ]
    res = argDeal(session.current_arg_text.strip(),arglimit)
    if not res[0]:
        await session.send(res[1]+'=>'+res[2])
        return
    args = res[1]
    if perm_check(session,'-listener',{
            'message_type':'group',
            'sent_id':args['sendid'],
            'op_id':user_id
        }):
        perm_del(session,'-listener',{
                'message_type':'group',
                'sent_id':args['sendid'],
                'op_id':user_id
            })
        await session.send('转推配置取消锁定')
    else:
        perm_add(session,'-listener',{
                'message_type':'group',
                'sent_id':args['sendid'],
                'op_id':user_id
            })
        await session.send('转推配置已锁定')

async def privateswitch(session: CommandSession):
    #转推操作可以在私聊进行，操作将对当前聊天进行操作
    if perm_check(session,'-listener',user = True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    if perm_check(session,'*'):
        await session.send('操作无效，存在“*”权限(g)')
        return
    if perm_check(session,'listener'):
        perm_del(session,'listener')
        await session.send('转推操作已禁用')
    else:
        perm_add(session,'listener',)
        await session.send('转推操作已启用')
async def groupswitch(session: CommandSession):
    if perm_check(session,'-listener',user = True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    if perm_check(session,'-listener'):
        await session.send('操作被拒绝，权限不足(g)')
        return
    if perm_check(session,'listener'):
        perm_del(session,'listener')
        await session.send('转推操作已禁用')
    else:
        perm_add(session,'listener')
        await session.send('转推操作已启用')
@on_command('tweetListenerSwitch',aliases=['tls','转推授权'], permission=perm.SUPERUSER,only_to_me = True)
async def tweetListenerSwitch(session: CommandSession):
    if not headdeal(session):
        return
    message_type = session.event['message_type']
    logger.info(CQsessionToStr(session))
    if message_type == 'group':
        await groupswitch(session)
    elif message_type == 'private':
        await privateswitch(session)

@on_command('delall',aliases=['这里单推bot'], permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_OWNER,only_to_me = True)
async def delalltest(session: CommandSession):
    if not headdeal(session):
        return
    await asyncio.sleep(0.2)
    message_type = session.event['message_type']
    group_id = (session.event['group_id'] if message_type == 'group' else None)
    user_id = session.event['user_id']
    if perm_check(session,'-listener',user=True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    sent_id = 0
    if message_type == 'private':
        sent_id = user_id
    elif message_type == 'group':
        if not perm_check(session,'listener'):
            await session.send('操作被拒绝，权限不足(g)')
            return
        sent_id = group_id
    else:
        await session.send('未收录的消息类型:'+message_type)
        return
    logger.info(CQsessionToStr(session))
    sent_id = str(sent_id)
    res = push_list.delPushunitFromPushTo(message_type,int(sent_id),self_id=int(session.event['self_id']))
    push_list.savePushList()
    await session.send('已移除此地所有监测' if res[0] == True else res[1])

#获取指定推送对象的推送列表（推送标识，推送对象ID）
def get_pushTo_spylist(message_type:str,pushTo:int,page:int):
    if message_type not in push_list.message_type_list:
        raise Exception("无效的消息类型！",message_type)
    table = push_list.getLitsFromPushToAndID(message_type,pushTo)
    s = ''
    unit_cout = 0
    for key in table:
        if unit_cout >= (page-1)*5 and unit_cout < (page)*5:
            s = s + (table[key]['nick'] if table[key]['nick'] != '' else tweet_event_deal.tryGetNick(key,"未定义昵称")) + \
                "," + str(key) + ',' + table[key]['des'] + "\n"
        unit_cout = unit_cout + 1
    totalpage = unit_cout//5 + (0 if (unit_cout%5 == 0) else 1)
    if unit_cout > 5 or page != 1:
        s = s + '页数：' + str(page) + '/' + str(totalpage) + ' '
    s = s + '总监测数：' + str(unit_cout)
    if unit_cout == 0:
        s = s + '\n' + '单 推 b o t'
    return s
@on_command('getpushlist',aliases=['DD列表'],permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_ADMIN | perm.GROUP_OWNER,only_to_me = False)
async def getpushlist(session: CommandSession):
    if not headdeal(session):
        return
    await asyncio.sleep(0.2)
    message_type = session.event['message_type']
    group_id = (session.event['group_id'] if message_type == 'group' else None)
    user_id = session.event['user_id']
    sent_id = 0
    if message_type == 'private':
        sent_id = user_id
    elif message_type == 'group':
        sent_id = group_id
    else:
        await session.send('未收录的消息类型:'+message_type)
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

    s = get_pushTo_spylist(message_type,sent_id,page)
    await session.send(s)

#获取推送对象总属性设置
def getPushToSetting(message_type:str,pushTo:int,kind:str='basic') -> str:
    attrlist = {    
        'basic':{
            'upimg':'图片',#是否连带图片显示(默认不带)-发推有效,转推及评论等事件则无效
            
            #推特推送开关
            'retweet':'转推',#转推(默认不开启)
            'quoted':'转推并评论',#带评论转推(默认开启)
            'reply_to_status':'回复',#回复(默认开启)
            'reply_to_user':'提及',#提及某人-多数时候是被提及但是被提及不会接收(默认开启)
            'none':'发推',#发推(默认开启)
        },
        'template':{
            #推特推送模版
            'retweet_template':'转推模版',
            'quoted_template':'转推并评论模版',
            'reply_to_status_template':'回复模版',
            'reply_to_user_template':'提及模版', 
            'none_template':'发推模版',
        },
        'ai':{
            #智能
            'ai_retweet':'智能转推',
            'ai_reply_to_status':'智能转发回复',
            'ai_passive_reply_to_status':'智能转发被回复',
            'ai_passive_quoted':'智能转发被转推并评论',
            'ai_passive_reply_to_user':'智能转发被提及',
        },
        'userinfo':{
            #个人信息变化推送(非实时)
            'change_ID':'ID修改', #ID修改(默认关闭)
            'change_name':'昵称修改', #昵称修改(默认开启)
            'change_description':'描述修改', #描述修改(默认关闭)
            'change_headimgchange':'头像修改', #头像更改(默认开启)
        }
    }
    res = ''
    attrs = push_list.getAttrLitsFromPushTo(message_type,pushTo)
    if attrs == {}:
        return 'BOT酱还没有初始化哦 请至少添加一个检测对象来开始使用我吧~'
    for key,value in attrs.items():
        if key in attrlist[kind]:
            res = res + attrlist[kind][key] + ':'  + \
                (value if value not in (0,1,'') else {0:'关闭',1:'开启','':'未定义'}[value]) + '\n'
    return res
@on_command('getGroupSetting',aliases=['全局设置列表'],permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_ADMIN | perm.GROUP_OWNER,only_to_me = True)
async def setGroupSetting(session: CommandSession):
    if not headdeal(session):
        return
    await asyncio.sleep(0.2)
    logger.info(CQsessionToStr(session))

    arglimit = [
        {
            'name':'kind', #参数名
            'des':'kind', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':'basic', #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
                'basic':'basic','基础':'basic',
                'template':'template','模版':'template',
                'ai':'ai','智能':'ai','智能推送':'ai',
                'userinfo':'userinfo','用户信息':'userinfo','用户':'userinfo','个人资料':'userinfo'
            }
        }
    ]
    args = argDeal(session.current_arg_text.strip(),arglimit)
    if not args[0]:
        await session.send(args[1] + '=>' + args[2])
        return
    args = args[1]

    res = getPushToSetting(
        session.event['message_type'],
        session.event[('group_id' if session.event['message_type'] == 'group' else 'user_id')],
        args['kind']
    )
    await session.send(res)
#获取某个单元的推送设置列表
def userinfoToStr(userinfo):
    if userinfo:
        res = "\n" + '用户名：' + userinfo['name'] + "\n" +\
            '用户昵称：' + userinfo['screen_name']
        return res
    return ''
def getPushUnitSetting(message_type:str,pushTo:int,tweet_user_id:int,kind:str = 'basic') -> str:
    attrlist = {    
        'basic':{
            'upimg':'图片',#是否连带图片显示(默认不带)-发推有效,转推及评论等事件则无效
            
            #推特推送开关
            'retweet':'转推',#转推(默认不开启)
            'quoted':'转推并评论',#带评论转推(默认开启)
            'reply_to_status':'回复',#回复(默认开启)
            'reply_to_user':'提及',#提及某人-多数时候是被提及但是被提及不会接收(默认开启)
            'none':'发推',#发推(默认开启)
        },
        'template':{
            #推特推送模版
            'retweet_template':'转推模版',
            'quoted_template':'转推并评论模版',
            'reply_to_status_template':'回复模版',
            'reply_to_user_template':'提及模版', 
            'none_template':'发推模版',
        },
        'ai':{
            #智能
            'ai_retweet':'智能转推',
            'ai_reply_to_status':'智能转发回复',
            'ai_passive_reply_to_status':'智能转发被回复',
            'ai_passive_quoted':'智能转发被转推并评论',
            'ai_passive_reply_to_user':'智能转发被提及',
        },
        'userinfo':{
            #个人信息变化推送(非实时)
            'change_ID':'ID修改', #ID修改(默认关闭)
            'change_name':'昵称修改', #昵称修改(默认开启)
            'change_description':'描述修改', #描述修改(默认关闭)
            'change_headimgchange':'头像修改', #头像更改(默认开启)
        }
    }
    res = push_list.getPushunit(message_type,pushTo,tweet_user_id)
    if res[0]:
        Pushunit = res[1]
    else:
        return res
    """
        #固有属性
        Pushunit['bindCQID'] = bindCQID #绑定的酷Q帐号(正式上线时将使用此帐户进行发送，用于适配多酷Q账号)
        Pushunit['type'] = pushtype #group/private
        Pushunit['pushTo'] = pushID #QQ号或者群号
        Pushunit['tweet_user_id'] = tweet_user_id #监测ID
        Pushunit['nick'] = nick #推送昵称(默认推送昵称为推特screen_name)
        Pushunit['des'] = des #单元描述
        userinfo['id'] = user.id
        userinfo['id_str'] = user.id_str
        userinfo['name'] = user.name
        userinfo['description'] = user.description
        userinfo['screen_name'] = user.screen_name
        userinfo['profile_image_url'] = user.profile_image_url
        userinfo['profile_image_url_https'] = user.profile_image_url_https
    """
    if tweetListener:
        userinfo = tweet_event_deal.tryGetUserInfo(tweet_user_id)
    res = '用户ID:' + str(tweet_user_id)
    if kind == 'basic':
        res = res + "\n" + '自定义昵称:' + (Pushunit['nick'] if Pushunit['nick'] != '' else '未定义') + "\n" +\
                '描述:' + Pushunit['des'].replace("\\n","\n") + \
                userinfoToStr(userinfo)
    for attrname,attrdisplayname in attrlist[kind].items():
        value = push_list.getPuslunitAttr(Pushunit,attrname)
        res = res + '\n' + attrdisplayname + ':' + \
            (value[1] if value[1] not in (0,1,'') else {0:'关闭',1:'开启','':'未定义'}[value[1]])
    return (True,res)
@on_command('getSetting',aliases=['对象设置列表'],permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_ADMIN | perm.GROUP_OWNER,only_to_me = True)
async def getSetting(session: CommandSession):
    if not headdeal(session):
        return
    await asyncio.sleep(0.2)
    message_type = session.event['message_type']
    group_id = (session.event['group_id'] if message_type == 'group' else None)
    user_id = session.event['user_id']
    sent_id = 0
    if message_type == 'private':
        sent_id = user_id
    elif message_type == 'group':
        sent_id = group_id
    else:
        await session.send('未收录的消息类型:'+message_type)
        return
    logger.info(CQsessionToStr(session))

    arglimit = [
        {
            'name':'tweet_user_id', #参数名
            'des':'推特用户ID', #参数错误描述
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
            'name':'kind', #参数名
            'des':'kind', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':'basic', #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
                'basic':'basic','基础':'basic',
                'template':'template','模版':'template',
                'ai':'ai','智能':'ai','智能推送':'ai',
                'userinfo':'userinfo','用户信息':'userinfo','用户':'userinfo','个人资料':'userinfo'
            }
        }
    ]
    args = argDeal(session.current_arg_text.strip(),arglimit)
    if not args[0]:
        await session.send(args[1] + '=>' + args[2])
        return
    args = args[1]
    res = getPushUnitSetting(
        message_type,
        sent_id,
        args['tweet_user_id'],
        args['kind']
    )
    logger.info(CQsessionToStr(session))
    await session.send(res[1])

#推送对象总属性设置
@on_command('setGroupAttr',aliases=['全局设置'],permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_ADMIN | perm.GROUP_OWNER,only_to_me = True)
async def setGroupAttr(session: CommandSession):
    if not headdeal(session):
        return
    await asyncio.sleep(0.2)
    message_type = session.event['message_type']
    group_id = (session.event['group_id'] if message_type == 'group' else None)
    user_id = session.event['user_id']
    if perm_check(session,'-listener',user=True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    sent_id = 0
    if message_type == 'private':
        sent_id = user_id
    elif message_type == 'group':
        if not perm_check(session,'listener'):
            await session.send('操作被拒绝，权限不足(g)')
            return
        sent_id = group_id
    else:
        await session.send('未收录的消息类型:'+message_type)
        return
    logger.info(CQsessionToStr(session))
    """
            {
                'name':'tweet_user_id', #参数名
                'des':'推特用户ID', #参数错误描述
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
    """
    arglimit = [
        {
            'name':'key', #参数名
            'des':'设置名称', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':None, #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
                #携带图片发送
                'upimg':'upimg','图片':'upimg','img':'upimg',
                #昵称设置
                #'nick':'nick','昵称':'nick',
                #消息模版
                'retweet_template':'retweet_template','转推模版':'retweet_template',
                'quoted_template':'quoted_template','转推并评论模版':'quoted_template',
                'reply_to_status_template':'reply_to_status_template','回复模版':'reply_to_status_template',
                'reply_to_user_template':'reply_to_user_template','被提及模版':'reply_to_user_template',
                'none_template':'none_template','发推模版':'none_template',
                #推特转发各类型开关
                'retweet':'retweet','转推':'retweet',
                'quoted':'quoted','转推并评论':'quoted',
                'reply_to_status':'reply_to_status','回复':'reply_to_status',
                'reply_to_user':'reply_to_user','提及':'reply_to_user',
                'none':'none','发推':'none',
                #智能推送开关
                'ai_retweet':'ai_retweet','智能转推':'ai_retweet',
                'ai_reply_to_status':'ai_reply_to_status','智能转发回复':'ai_reply_to_status',
                'ai_passive_reply_to_status':'ai_passive_reply_to_status','智能转发被回复':'ai_passive_reply_to_status',
                'ai_passive_quoted':'ai_passive_quoted','智能转发被转推并评论':'ai_passive_quoted',
                'ai_passive_reply_to_user':'ai_passive_reply_to_user','智能转发被提及':'ai_passive_reply_to_user',
                #推特个人信息变动推送开关
                'change_id':'change_ID','ID改变':'change_ID','ID修改':'change_ID',
                'change_name':'change_name','名称改变':'change_name','名称修改':'change_name','名字改变':'change_name','名字修改':'change_name','昵称修改':'change_name','昵称改变':'change_name',
                'change_description':'change_description','描述改变':'change_description','描述修改':'change_description',
                'change_headimgchange':'change_headimgchange','头像改变':'change_headimgchange','头像修改':'change_headimgchange'
            }
        },
        {
            'name':'value', #参数名
            'des':'设置值', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':'', #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
                'true':'1','开':'1','打开':'1','开启':'1',
                'false':'0','关':'0','关闭':'0',
                '*':''
            }
        }
    ]
    args = argDeal(session.current_arg_text.strip(),arglimit)
    if not args[0]:
        await session.send(args[1] + '=>' + args[2])
        return
    args = args[1]
    template_attr = (
        'retweet_template',
        'quoted_template',
        'reply_to_status_template',
        'reply_to_user_template',
        'none_template'
    )
    attr = args['key']
    attrv = args['value']
    if attr in template_attr:
        res = push_list.PushTo_setAttr(
            message_type,sent_id,
            attr,attrv
        )
    elif attrv in ('0','1'):
        res = push_list.PushTo_setAttr(
            message_type,
            sent_id,
            attr,
            int(attrv)
        )
    else:
        res = (False,'属性的值不合法！')
        return
    push_list.savePushList()
    await session.send(res[1])
#推送对象的监测对象属性设置
@on_command('setAttr',aliases=['对象设置'],permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_ADMIN | perm.GROUP_OWNER,only_to_me = True)
async def setAttr(session: CommandSession):
    if not headdeal(session):
        return
    await asyncio.sleep(0.2)
    message_type = session.event['message_type']
    group_id = (session.event['group_id'] if message_type == 'group' else None)
    user_id = session.event['user_id']
    if perm_check(session,'-listener',user=True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    sent_id = 0
    if message_type == 'private':
        sent_id = user_id
    elif message_type == 'group':
        if not perm_check(session,'listener'):
            await session.send('操作被拒绝，权限不足(g)')
            return
        sent_id = group_id
    else:
        await session.send('未收录的消息类型:'+message_type)
        return
    logger.info(CQsessionToStr(session))

    arglimit = [
        {
            'name':'tweet_user_id', #参数名
            'des':'推特用户ID', #参数错误描述
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
            'name':'key', #参数名
            'des':'设置名称', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':None, #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
                #携带图片发送
                'upimg':'upimg','图片':'upimg','img':'upimg',
                #描述设置
                'des':'des','描述':'des',
                #昵称设置
                'nick':'nick','昵称':'nick',
                #消息模版
                'retweet_template':'retweet_template','转推模版':'retweet_template',
                'quoted_template':'quoted_template','转推并评论模版':'quoted_template',
                'reply_to_status_template':'reply_to_status_template','回复模版':'reply_to_status_template',
                'reply_to_user_template':'reply_to_user_template','被提及模版':'reply_to_user_template',
                'none_template':'none_template','发推模版':'none_template',
                #推特转发各类型开关
                'retweet':'retweet','转推':'retweet',
                'quoted':'quoted','转推并评论':'quoted',
                'reply_to_status':'reply_to_status','回复':'reply_to_status',
                'reply_to_user':'reply_to_user','提及':'reply_to_user',
                'none':'none','发推':'none',
                #智能推送开关
                'ai_retweet':'ai_retweet','智能转推':'ai_retweet',
                'ai_reply_to_status':'ai_reply_to_status','智能转发回复':'ai_reply_to_status',
                'ai_passive_reply_to_status':'ai_passive_reply_to_status','智能转发被回复':'ai_passive_reply_to_status',
                'ai_passive_quoted':'ai_passive_quoted','智能转发被转推并评论':'ai_passive_quoted',
                'ai_passive_reply_to_user':'ai_passive_reply_to_user','智能转发被提及':'ai_passive_reply_to_user',
                #推特个人信息变动推送开关
                'change_id':'change_ID','ID改变':'change_ID','ID修改':'change_ID',
                'change_name':'change_name','名称改变':'change_name','名称修改':'change_name','名字改变':'change_name','名字修改':'change_name','昵称修改':'change_name','昵称改变':'change_name','昵称修改':'change_name',
                'change_description':'change_description','描述改变':'change_description','描述修改':'change_description',
                'change_headimgchange':'change_headimgchange','头像改变':'change_headimgchange','头像修改':'change_headimgchange'
            }
        },
        {
            'name':'value', #参数名
            'des':'设置值', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':'', #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
                'true':'1','开':'1','打开':'1','开启':'1',
                'false':'0','关':'0','关闭':'0',
                '*':''
            }
        }
    ]
    args = argDeal(session.current_arg_text.strip(),arglimit)
    if not args[0]:
        await session.send(args[1] + '=>' + args[2])
        return
    args = args[1]
    template_attr = (
        'retweet_template',
        'quoted_template',
        'reply_to_status_template',
        'reply_to_user_template',
        'none_template'
    )
    tweet_user_id = args['tweet_user_id']
    attr = args['key']
    attrv = args['value']
    if str(tweet_user_id) not in push_list.spylist:
        await session.send("用户不在监测列表内！")
        return
    if attr == 'des' or attr == 'nick' or attr in template_attr:
        res = push_list.setPushunitAttr(
            message_type,sent_id,
            tweet_user_id,
            attr,attrv
        )
    elif attrv in ('0','1'):
        res = push_list.setPushunitAttr(
            message_type,sent_id,
            tweet_user_id,
            attr,int(attrv)
        )
    else:
        res = (False,'属性的值不合法！')
        return
    push_list.savePushList()
    await session.send(res[1])
    

#移除某个人或某个群的所有监测，用于修复配置错误(退出群/删除好友时不在线)
@on_command('globalRemove',aliases=['全局移除'],permission=perm.SUPERUSER,only_to_me = True)
async def globalRemove(session: CommandSession):
    if not headdeal(session):
        return
    await asyncio.sleep(0.2)
    message_type = session.event['message_type']
    #group_id = (session.event['group_id'] if message_type == 'group' else None)
    #user_id = session.event['user_id']
    if perm_check(session,'-listener',user=True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    if message_type == 'group' and not perm_check(session,'listener'):
        await session.send('操作被拒绝，权限不足(g)')
        return
    logger.info(CQsessionToStr(session))

    arglimit = [
        {
            'name':'msgtype', #参数名
            'des':'消息类型', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':True, #是否转换为小写
            'default':None, #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示允许任意字符串,值不为空时任意字符串将被转变为这个值
                '私聊':'private',
                'private':'private',
                '群聊':'group',
                'group':'group',
                '好友':'private',
                '群':'group',
            }
        },
        {
            'name':'send_id', #参数名
            'des':'对象ID', #参数错误描述
            'type':'int', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':None, #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
            }
        }
    ]
    res = argDeal(session.current_arg_text.strip(),arglimit)
    if not res[0]:
        await session.send(res[1]+'=>'+res[2])
        return
    args = res[1]
    res = push_list.delPushunitFromPushTo(
        args['message_type'],
        args['send_id'],
        self_id=int(session.event['self_id'])
    )
    push_list.savePushList()
    await session.send(res[1])


#推特ID编码解码
@on_command('detweetid',aliases=['推特ID解压'],only_to_me = False)
async def decodetweetid(session: CommandSession):
    if not headdeal(session):
        return
    await asyncio.sleep(0.2)
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg == '':
        return
    res = decode_b64(stripped_arg)
    if res == -1:
        await session.send("唔orz似乎没有这个推特ID的缩写呢")
        return
    logger.info(CQsessionToStr(session))
    await session.send("推特ID的真身已判明(ﾟ▽ﾟ)/其名为："+str(res))

@on_command('entweetid',aliases=['推特ID压缩'],only_to_me = False)
async def encodetweetid(session: CommandSession):
    if not headdeal(session):
        return
    await asyncio.sleep(0.2)
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg == '':
        return
    if not stripped_arg.isdecimal():
        await session.send("推特ID似乎搞错了呢(￣▽￣)\"请仔细检查")
        return
    n = int(stripped_arg)
    if n < 1253881609540800000:
        await session.send("推特ID的值过小！")
        return
    res = encode_b64(n)
    logger.info(CQsessionToStr(session))
    await session.send("推特ID压缩好了(oﾟ▽ﾟ)o请使用："+res)

#获取推文
@on_command('gettweettext',aliases=['获取推文','推文','gtt'],only_to_me = False)
async def gettweettext(session: CommandSession):
    if not headdeal(session):
        return
    message_type = session.event['message_type']
    #group_id = (session.event['group_id'] if message_type == 'group' else None)
    #user_id = session.event['user_id']
    if perm_check(session,'-listener',user=True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    if message_type == 'group' and not perm_check(session,'listener'):
        await session.send('操作被拒绝，权限不足(g)')
        return
    logger.info(CQsessionToStr(session))
    def checkTweetId(a,ad):
        if a[:1] == '#':
            ta = a[1:]
            if not ta.isdecimal():
                return None
            res = mintweetID.find(lambda item,val:item[1]==val,int(ta))
            if res == None:
                return None
            return res[0]
        elif a.isdecimal() and int(a) > 1253881609540800000:
            return a
        else:
            res = decode_b64(a)
            if res == -1:
                return None
            return res
    arglimit = [
        {
            'name':'tweet_id', #参数名
            'des':'推特ID', #参数错误描述
            'type':'int', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':None, #默认值
            'func':checkTweetId, #函数，当存在时使用函数进行二次处理
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
    tweet_id = args['tweet_id']
    tweet = tweet_event_deal.tryGetTweet(tweet_id)
    if tweet == None:
        if ptwitter.ptwitterapps.hasApp():
            app = ptwitter.ptwitterapps.getAllow('statuses_lookup')
            if app == None:
                await session.send("速率限制，请稍后再试！")
                return
            res = app.statuses_lookup(id = tweet_id)
            if not res[0] or res[1] == []:
                await session.send("未查找到该推文！")
                return
            tweet = ptwitter.tweet_event_deal.deal_tweet(res[1][0])
        else:
            await session.send("未从缓存中查找到该推文！")
            return
    msg = "推文 " + encode_b64(tweet_id) + " 的内容如下：\n"
    msg = msg + tweet_event_deal.tweetToStr(tweet,'',1,'')
    await session.send(msg)

#推文列表
@on_command('gettweetlist',aliases=['获取推文列表','推文列表','gttl'],only_to_me = False)
async def gettweetlist(session: CommandSession):
    if not headdeal(session):
        return
    await asyncio.sleep(0.2)
    message_type = session.event['message_type']
    group_id = (session.event['group_id'] if message_type == 'group' else None)
    user_id = session.event['user_id']
    if perm_check(session,'-listener',user=True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    sent_id = 0
    if message_type == 'private':
        sent_id = user_id
    elif message_type == 'group':
        if not perm_check(session,'listener'):
            await session.send('操作被拒绝，权限不足(g)')
            return
        sent_id = group_id
    else:
        await session.send('未收录的消息类型:'+message_type)
        return
    logger.info(CQsessionToStr(session))
    #ID为空或者#号时尝试使用默认ID
    def tryget(a,ad):
        tweet_user_id = a
        if tweet_user_id == '' or tweet_user_id == '#':
            l = push_list.getLitsFromPushTo(message_type,sent_id)
            if l == []:
                return (False,'监听列表无成员，无法置入默认值')
            tweet_user_id = str(l[0]['tweet_user_id'])
        if tweet_user_id.isdecimal():
            res = tweetListener.tweet_event_deal.tryGetUserInfo(user_id=int(tweet_user_id))
            if res == {}:
                res = (False,'缓存中不存在此用户！')
            else:
                res = (True,res)
        else:
            res = tweetListener.tweet_event_deal.tryGetUserInfo(screen_name = tweet_user_id)
            if res == {}:
                res = (False,'缓存中不存在此用户！')
            else:
                res = (True,res)
        return res
    arglimit = [
        {
            'name':'userinfo', #参数名
            'des':'推特用户ID', #参数错误描述
            'type':'dict', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':None, #默认值
            'func':tryget, #函数，当存在时使用函数进行二次处理
            'funcdealnull':True, #函数是否处理空值(控制默认值)
            're':None, #正则表达式匹配(match函数)
            're_error':'',
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
            }
        },
        {
            'name':'page', #参数名
            'des':'页码', #参数错误描述
            'type':'int', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':1, #默认值(不会进行二次类型转换)
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
            }
        },
    ]
    args = argDeal(session.current_arg_text.strip(),arglimit)
    if not args[0]:
        await session.send(args[1] + '=>' + args[2])
        return
    args = args[1]
    userinfo = args['userinfo']
    page = args['page']
    res = tweetListener.tweet_event_deal.getUserTSInCache(userinfo['id'])
    if res == None:
        await session.send("推文缓存中不存在此用户数据！")
        return
    tweets = res.tm
    ttr = {'none':'发推','retweet':'转推','quoted':'转评','reply_to_status':'回复','reply_to_user':'提及'}
    msg = userinfo['name'] + "(" + userinfo['screen_name'] + ")的推文列表" + "\n"
    msg = msg + "推文缩写ID,标识,推文简写内容" + "\n"
    unit_cout = 0
    for i in range(len(tweets)-1,-1,-1):
        if unit_cout >= (page-1)*5 and unit_cout < (page)*5:
            msg = msg + ttr[tweets[i]['type']] + ',' + encode_b64(tweets[i]['id']) +',' + tweets[i]['text'][:20].replace("\n"," ") + "\n"
        unit_cout = unit_cout + 1
    totalpage = unit_cout//5 + (0 if (unit_cout%5 == 0) else 1)
    if unit_cout > 5 or page != 1:
        msg = msg + '页数：' + str(page) + '/' + str(totalpage) + ' '
    msg = msg + '总推文缓存数：' + str(unit_cout)
    await session.send(msg)


#获取全局监听推送列表(非正式查错命令)
def get_tweeallpushlist(page:int):
    table = push_list.spylist
    s = ''
    unit_cout = 0
    for item in table:
        if unit_cout >= (page-1)*5 and unit_cout < (page)*5:
            s = s + item + '\n'
        unit_cout = unit_cout + 1
    totalpage = unit_cout//5 + (0 if (unit_cout%5 == 0) else 1)
    if unit_cout > 5 or page != 1:
        s = s + '页数：' + str(page) + '/' + str(totalpage) + ' '
    s = s + '总监测数：' + str(unit_cout)
    return s
@on_command('tweeallpushlist',permission=perm.SUPERUSER,only_to_me = False)
async def tweeallpushlist(session: CommandSession):
    if not headdeal(session):
        return
    await asyncio.sleep(0.1)
    page = 1
    stripped_arg = session.current_arg_text.strip().lower()
    if stripped_arg != '':
        if not stripped_arg.isdecimal():
            await session.send("参数似乎有点不对劲？请再次检查o(￣▽￣)o")
            return
        page = int(stripped_arg)
        if page < 1:
            await session.send("参数似乎有点不对劲？请再次检查o(￣▽￣)o")
            return
    s = get_tweeallpushlist(page)
    await session.send(s)
    logger.info(CQsessionToStr(session))


@on_command('tweeallpushabout',aliases=['转推帮助'],only_to_me = False)
async def tweeallpushabout(session: CommandSession):
    if not headdeal(session):
        return
    logger.info(CQsessionToStr(session))
    msg = '--转推帮助--' + "\n" + \
        '!转推授权 -切换转推授权' + "\n" + \
        '!addone 用户ID/UID -添加监测' + "\n" + \
        '!delone 用户ID/UID -移除监测' + "\n" + \
        '!DD列表 -监听列表' + "\n" + \
        '!全局设置列表 无参数/基础/模版/智能/用户信息 -查看设置' + "\n" + \
        '!对象设置列表 对象ID 无参数/基础/模版/智能/用户信息 -查看设置' + "\n" + \
        '!全局设置 设置属性 值 -设置' + "\n" + \
        '!对象设置 对象ID 设置属性 值 -设置' + "\n" + \
        '!获取推文 推文ID -获取推文(仅检索缓存-待更新)' + "\n" + \
        '如果出现问题可以 !反馈 反馈内容 反馈信息'
    await session.send(msg)


"""
	'font': , 
    'message': [{'type': 'text', 'data': {'text': '!getpushlist'}}], 
    'message_id': , 
    'message_type': 'private', 
    'post_type': 'message', 
    'raw_message': '!getpushlist', 
    'self_id': , 
    'sender': {'age': , 'nickname': '', 'sex': '', 'user_id': }, 
    'sub_type': 'friend', 
    'time': , 
    'user_id': , 
    'to_me': True}
"""