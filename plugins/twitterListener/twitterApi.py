# -*- coding: UTF-8 -*-
from nonebot import on_command, CommandSession, permission as perm
from helper import getlogger,msgSendToBot,CQsessionToStr,argDeal
from tweepy import TweepError
import module.permissiongroup as permissiongroup
from module.pollingTwitterApi import ptwitterapps
from plugins.twitter import tweetListener
import traceback
import re
import asyncio
import os
import config
logger = getlogger(__name__)
"""
包含了推特API特有命令
"""
__plugin_name__ = '推特API特有命令'
__plugin_usage__ = r"""
用于配置推特监听及调用推特API
详见：
https://github.com/chenxuan353/tweetToQQbot
"""


permgroupname = 'tweetListener'
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

@on_command('runTweetListener',aliases=['启动监听'], permission=perm.SUPERUSER,only_to_me = False)
async def runTweetListener(session: CommandSession):
    if not headdeal(session):
        return
    await asyncio.sleep(0.2)
    if tweetListener.run_info['isRun']:
        await session.send('推特监听仍在运行中，不可以二次启动的哦ヽ(｀Д´)ﾉ')
        return
    tweetListener.setStreamOpen(True)
    await session.send('监听启动中...')
    logger.info(CQsessionToStr(session))

@on_command('stopTweetListener',aliases=['停止监听'], permission=perm.SUPERUSER,only_to_me = False)
async def stopTweetListener(session: CommandSession):
    if not headdeal(session):
        return
    await asyncio.sleep(0.2)
    if not tweetListener.run_info['isRun']:
        await session.send('推特监听处于停止状态！')
        return
    tweetListener.setStreamOpen(False)
    await session.send('监听已关闭')
    logger.info(CQsessionToStr(session))


#获取监听错误列表
def get_tweeterrorlist(page:int):
    table = tweetListener.run_info['errorlist'].tm
    msg = "错误原因,错误代码" + "\n"
    unit_cout = 0
    for i in range(len(table)-1,-1,-1):
        if unit_cout >= (page-1)*5 and unit_cout < (page)*5:
            msg = msg + table[i][1] + ',' + (str(table[i][2]) if (len(table[i])>2) else '-1') + '\n'
        unit_cout = unit_cout + 1
    totalpage = unit_cout//5 + (0 if (unit_cout%5 == 0) else 1)
    if unit_cout > 5 or page != 1:
        msg = msg + '页数：' + str(page) + '/' + str(totalpage) + ' '
    msg = msg + '错误记录数：' + str(unit_cout)
    return msg
@on_command('gettweeterrorlist',aliases=['监听错误列表'],permission=perm.SUPERUSER,only_to_me = False)
async def tweeallpushlist(session: CommandSession):
    if not headdeal(session):
        return
    if 'errorlist' not in tweetListener.run_info:
        await session.send("错误列表不存在")
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
    s = get_tweeterrorlist(page)
    await session.send(s)
    logger.info(CQsessionToStr(session))

@on_command('getuserinfo',aliases=['查询推特用户'],permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_ADMIN | perm.GROUP_OWNER,only_to_me = True)
async def getuserinfo(session: CommandSession):
    if not headdeal(session):
        return
    message_type = session.event['message_type']
    #group_id = (session.event['group_id'] if message_type == 'group' else None)
    #user_id = session.event['user_id']
    if perm_check(session,'-listener',user=True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    if message_type == 'group':
        if not perm_check(session,'listener'):
            await session.send('操作被拒绝，权限不足(g)')
            return
    elif message_type != 'private':
        await session.send('未收录的消息类型:'+message_type)
        return
    logger.info(CQsessionToStr(session))

    arglimit = [
        {
            'name':'tweet_user_id', #参数名
            'des':'推特用户ID', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':None, #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':'[A-Za-z0-9_]+$', #正则表达式匹配(match函数)
            're_error':'用户名/用户ID 只能包含字母、数字或下划线',
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
    tweet_user_id = args['tweet_user_id']

    app = ptwitterapps.getAllow('users_show')
    if app == None:
        await session.send("速率限制，请稍后再试")
        return
    if tweet_user_id.isdecimal():
        res = app.users_show(user_id = int(tweet_user_id))
    else:
        res = app.users_show(screen_name = tweet_user_id)
    if not res[0]:
        await session.send("查询不到这位V哦~复制都能弄歪来┐(ﾟ～ﾟ)┌")
    userinfo = res[1]
    #检测信息更新
    tweetListener.tweet_event_deal.get_userinfo(userinfo,True)
    #tweetListener.tweet_event_deal.seve_image(userinfo.screen_name,userinfo.profile_image_url_https,'userinfo',canCover=True)
    #file_suffix = os.path.splitext(userinfo.profile_image_url_https)[1]
    #'头像:' + '[CQ:image,timeout='+config.img_time_out+',file='+config.img_path+'userinfo/' + userinfo.screen_name + file_suffix + ']'+ "\n" + \
    s = '用户UID:'+ str(userinfo.id) + "\n" + \
        '用户ID:' + userinfo.screen_name + "\n" + \
        '用户昵称:' + userinfo.name + "\n" + \
        '头像:' + '[CQ:image,timeout='+config.img_time_out+',file=' + userinfo.profile_image_url_https + ']'+ "\n" + \
        '描述:' + userinfo.description + "\n" + \
        '推文受保护:' + str(userinfo.protected) + "\n" + \
        '被关注数:' + str(userinfo.followers_count) + "\n" + \
        '关注数:' + str(userinfo.friends_count) + "\n" + \
        '发推数(包括转发)：' + str(userinfo.statuses_count) + "\n" + \
        '账户创建时间：' + str(userinfo.created_at)
    logger.info(CQsessionToStr(session))
    await session.send(s)

@on_command('delone',aliases=['我不想D了','俺不想D了'],permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_ADMIN | perm.GROUP_OWNER,only_to_me = True)
async def delOne(session: CommandSession):
    if not headdeal(session):
        return
    message_type = session.event['message_type']
    #group_id = (session.event['group_id'] if message_type == 'group' else None)
    #user_id = session.event['user_id']
    if perm_check(session,'-listener',user=True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    if message_type == 'group':
        if not perm_check(session,'listener'):
            await session.send('操作被拒绝，权限不足(g)')
            return
    elif message_type != 'private':
        await session.send('未收录的消息类型:'+message_type)
        return
    logger.info(CQsessionToStr(session))
    arglimit = [
        {
            'name':'tweet_user_id', #参数名
            'des':'推特用户ID', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':None, #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':'[A-Za-z0-9_]+$', #正则表达式匹配(match函数)
            're_error':'用户名/用户ID 只能包含字母、数字或下划线',
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
    tweet_user_id = args['tweet_user_id']

    app = ptwitterapps.getAllow('users_show')
    if app == None:
        await session.send("速率限制，请稍后再试")
        return
    if tweet_user_id.isdecimal():
        res = tweetListener.tweet_event_deal.tryGetUserInfo(user_id=int(tweet_user_id))
        if res == {}:
            res = app.users_show(user_id = int(tweet_user_id))
            if res[0]:
                res = list(res)
                res[1] = tweetListener.tweet_event_deal.get_userinfo(res[1])
        else:
            res = (True,res)
    else:
        res = tweetListener.tweet_event_deal.tryGetUserInfo(screen_name = tweet_user_id)
        if res == {}:
            res = app.users_show(screen_name = tweet_user_id)
            if res[0]:
                res = list(res)
                res[1] = tweetListener.tweet_event_deal.get_userinfo(res[1])
        else:
            res = (True,res)
    if not res[0]:
        await session.send("查询不到这位V哦~复制都能弄歪来┐(ﾟ～ﾟ)┌")
    userinfo = res[1]
        
    #tweetListener.tweet_event_deal.seve_image(userinfo.screen_name,userinfo.profile_image_url_https,'userinfo')
    #file_suffix = os.path.splitext(userinfo.profile_image_url_https)[1]
    #'头像:' + '[CQ:image,timeout='+config.img_time_out+',file='+config.img_path+'userinfo/' + userinfo.screen_name + file_suffix + ']'+ "\n" + \
    res = push_list.delPushunitFromPushToAndTweetUserID(
        session.event['message_type'],
        session.event[('group_id' if session.event['message_type'] == 'group' else 'user_id')],
        userinfo['id']
        )
    s = '用户UID:'+ str(userinfo['id']) + "\n" + \
        '用户ID:' + userinfo['screen_name'] + "\n" + \
        '用户昵称:' + userinfo['name'] + "\n" + \
        '头像:' + '[CQ:image,timeout='+config.img_time_out+',file=' + userinfo['profile_image_url_https'] + ']'+ "\n" + \
        ('已经从监听列表中叉出去了哦' if res[0] == True else '移除失败了Σ（ﾟдﾟlll）:'+res[1])
    push_list.savePushList()
    await session.send(s)

@on_command('addone',aliases=['给俺D一个'],permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_ADMIN | perm.GROUP_OWNER,only_to_me = True)
async def addOne(session: CommandSession):
    if not headdeal(session):
        return
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
    elif message_type != 'private':
        await session.send('未收录的消息类型:'+message_type)
        return
    arglimit = [
        {
            'name':'tweet_user_id', #参数名
            'des':'推特用户ID', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':None, #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':'[A-Za-z0-9_]+$', #正则表达式匹配(match函数)
            're_error':'用户名/用户ID 只能包含字母、数字或下划线',
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
            }
        },
        {
            'name':'nick', #参数名
            'des':'昵称', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':'', #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':r'[\s\S]{0,50}', #正则表达式匹配(match函数)
            'vlimit':{
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
            }
        },
        {
            'name':'des', #参数名
            'des':'描述', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':'', #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':r'[\s\S]{0,100}', #正则表达式匹配(match函数)
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
    tweet_user_id = args['tweet_user_id']
    app = ptwitterapps.getAllow('users_show')
    if app == None:
        await session.send("速率限制，请稍后再试")
        return
    if tweet_user_id.isdecimal():
        res = tweetListener.tweet_event_deal.tryGetUserInfo(user_id=int(tweet_user_id))
        if res == {}:
            res = app.users_show(user_id = int(tweet_user_id))
            if res[0]:
                res = list(res)
                res[1] = tweetListener.tweet_event_deal.get_userinfo(res[1])
        else:
            res = (True,res)
    else:
        res = tweetListener.tweet_event_deal.tryGetUserInfo(screen_name = tweet_user_id)
        if res == {}:
            res = app.users_show(screen_name = tweet_user_id)
            if res[0]:
                res = list(res)
                res[1] = tweetListener.tweet_event_deal.get_userinfo(res[1])
        else:
            res = (True,res)
    if not res[0]:
        await session.send("查询不到这位V哦~复制都能弄歪来┐(ﾟ～ﾟ)┌")
    userinfo = res[1]

    nick = args['nick']
    des = args['des']
    if des == '':
        des = userinfo['name']+'('+userinfo['screen_name']+')'
    PushUnit = push_list.baleToPushUnit(
        session.event['self_id'],
        message_type,sent_id,
        userinfo['id'],
        user_id,user_id,
        des,
        nick = nick
        )
    res = push_list.addPushunit(PushUnit)
    s = '用户UID:'+ str(userinfo['id']) + "\n" + \
        '用户ID:' + userinfo['screen_name'] + "\n" + \
        '用户昵称:' + userinfo['name'] + "\n" + \
        '头像:' + '[CQ:image,timeout='+config.img_time_out+',file=' + userinfo['profile_image_url_https'] + ']'+ "\n" + \
        ('已经加入了DD名单了哦' if res[0] == True else '添加失败:'+res[1])
    push_list.savePushList()
    await session.send(s)

