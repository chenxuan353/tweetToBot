# -*- coding: UTF-8 -*-
from nonebot import on_command, CommandSession, permission as perm
from helper import keepalive,commandHeadtail,getlogger,msgSendToBot,CQsessionToStr
from tweepy import TweepError
from module.twitter import push_list
import module.twitterApi as tweetListener
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

@on_command('runTweetListener',aliases=['启动监听'], permission=perm.SUPERUSER,only_to_me = False)
async def runTweetListener(session: CommandSession):
    await asyncio.sleep(0.2)
    if keepalive['tewwtlistener_alive'] == True or keepalive['reboot_tewwtlistener'] == True:
        await session.send('推特监听仍在运行中，不可以二次启动的哦ヽ(｀Д´)ﾉ')
        return
    keepalive['reboot_tweetListener_cout'] = 0
    await session.send('监听启动中...')
    logger.info(CQsessionToStr(session))
    keepalive['reboot_tewwtlistener'] = True

@on_command('getuserinfo',aliases=['查询推特用户'],permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_ADMIN | perm.GROUP_OWNER,only_to_me = True)
async def getuserinfo(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg == '':
        return
    try:
        if stripped_arg.isdecimal():
            userinfo = tweetListener.api.get_user(user_id = int(stripped_arg))
        else:
            userinfo = tweetListener.api.get_user(screen_name = stripped_arg)
    except TweepError:
        s = traceback.format_exc(limit=5)
        logger.error('tweepy发生错误:'+s)
        await session.send("查询不到这位V哦~复制都能弄歪来┐(ﾟ～ﾟ)┌")
        return

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
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg == '':
        await session.send("在？为什么看别的女人连单推的名字都忘了写？")
        return
    if stripped_arg == re.match('[A-Za-z0-9_]+', stripped_arg, flags=0):
        await session.send("用户名/用户ID 只能包含字母、数字或下划线")
        return
    try:
        if stripped_arg.isdecimal():
            userinfo = tweetListener.api.get_user(user_id = int(stripped_arg))
        else:
            userinfo = tweetListener.api.get_user(screen_name = stripped_arg)
    except TweepError:
        s = traceback.format_exc(limit=5)
        logger.error('tweepy发生错误:'+s)
        await session.send("查询不到信息，不愧是你(๑´ㅂ`๑)")
        return
        
    #tweetListener.tweet_event_deal.seve_image(userinfo.screen_name,userinfo.profile_image_url_https,'userinfo')
    #file_suffix = os.path.splitext(userinfo.profile_image_url_https)[1]
    #'头像:' + '[CQ:image,timeout='+config.img_time_out+',file='+config.img_path+'userinfo/' + userinfo.screen_name + file_suffix + ']'+ "\n" + \
    res = push_list.delPushunitFromPushToAndTweetUserID(
        session.event['message_type'],
        session.event[('group_id' if session.event['message_type'] == 'group' else 'user_id')],
        userinfo.id
        )
    s = '用户UID:'+ str(userinfo.id) + "\n" + \
        '用户ID:' + userinfo.screen_name + "\n" + \
        '用户昵称:' + userinfo.name + "\n" + \
        '头像:' + '[CQ:image,timeout='+config.img_time_out+',file=' + userinfo.profile_image_url_https + ']'+ "\n" + \
        ('已经从监听列表中叉出去了哦' if res[0] == True else '移除失败了Σ（ﾟдﾟlll）:'+res[1])
    push_list.savePushList()
    logger.info(CQsessionToStr(session))
    await session.send(s)

@on_command('addone',aliases=['给俺D一个'],permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_ADMIN | perm.GROUP_OWNER,only_to_me = True)
async def addOne(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg == '':
        await session.send("你D谁呢妹妹")
        return
    if stripped_arg == re.match('[A-Za-z0-9_]+', stripped_arg, flags=0):
        await session.send("用户名/用户ID 只能包含字母、数字或下划线")
        return
    cs = commandHeadtail(stripped_arg)
    try:
        if cs[0].isdecimal():
            userinfo = tweetListener.api.get_user(user_id = int(cs[0]))
        else:
            userinfo = tweetListener.api.get_user(screen_name = cs[0])
    except TweepError:
        s = traceback.format_exc(limit=5)
        logger.error('tweepy发生错误:'+s)
        await session.send("查询不到信息，你D都能D歪来!?(･_･;?")
        return
    #tweetListener.tweet_event_deal.seve_image(userinfo.screen_name,userinfo.profile_image_url_https,'userinfo')
    #file_suffix = os.path.splitext(userinfo.profile_image_url_https)[1]
    #'头像:' + '[CQ:image,timeout='+config.img_time_out+',file='+config.img_path+'userinfo/' + userinfo.screen_name + file_suffix + ']'+ "\n" + \
    nick = ''
    des = ''
    if cs[2] != '':
        cs = commandHeadtail(cs[2])
        nick = cs[0]
        des = cs[2]
    if des == '':
        des = userinfo.name+'('+userinfo.screen_name+')'
    PushUnit = push_list.baleToPushUnit(
        session.event['self_id'],
        session.event['message_type'],
        session.event[('group_id' if session.event['message_type'] == 'group' else 'user_id')],
        userinfo.id,des,nick = nick
        )
    res = push_list.addPushunit(PushUnit)
    s = '用户UID:'+ str(userinfo.id) + "\n" + \
        '用户ID:' + userinfo.screen_name + "\n" + \
        '用户昵称:' + userinfo.name + "\n" + \
        '头像:' + '[CQ:image,timeout='+config.img_time_out+',file=' + userinfo.profile_image_url_https + ']'+ "\n" + \
        ('已经加入了DD名单了哦' if res[0] == True else '没 D 到:'+res[1])
    push_list.savePushList()
    logger.info(CQsessionToStr(session))
    await session.send(s)
