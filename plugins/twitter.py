import module.twitter as tweetListener
from nonebot import on_command, CommandSession, permission
from helper import commandHeadtail
from tweepy import TweepError
import time
import asyncio
import os
import traceback
import re
#推送列表的引用
push_list : tweetListener.PushList = tweetListener.push_list


# on_command 装饰器将函数声明为一个命令处理器
@on_command('addtest', permission=permission.SUPERUSER,only_to_me = False)
async def addtest(session: CommandSession):
    message_type = session.event['message_type']
    sent_id = 0
    if message_type == 'private':
        sent_id = session.event['user_id']
    elif message_type == 'group':
        sent_id = session.event['group_id']
    else:
        await session.send('未收录的消息类型:'+message_type)
        return
    sent_id = str(sent_id)
    unit = push_list.baleToPushUnit(
        1837730674,
        message_type,sent_id,805435112259096576,
        '增删测试',nick='底层轴man',none_template="$tweet_nick这个人发推了,爪巴")
    push_list.addPushunit(unit)
    await session.send('done!')
@on_command('deltest', permission=permission.SUPERUSER,only_to_me = False)
async def deltest(session: CommandSession):
    message_type = session.event['message_type']
    sent_id = 0
    if message_type == 'private':
        sent_id = session.event['user_id']
    elif message_type == 'group':
        sent_id = session.event['group_id']
    else:
        await session.send('未收录的消息类型:'+message_type)
        return
    sent_id = str(sent_id)
    s = push_list.delPushunitFromPushToAndTweetUserID(message_type,sent_id,805435112259096576)
    await session.send(s)

@on_command('delall',aliases=['这里单推bot'], permission=permission.SUPERUSER,only_to_me = True)
async def delalltest(session: CommandSession):
    message_type = session.event['message_type']
    sent_id = 0
    if message_type == 'private':
        sent_id = session.event['user_id']
    elif message_type == 'group':
        sent_id = session.event['group_id']
    else:
        await session.send('未收录的消息类型:'+message_type)
        return
    sent_id = str(sent_id)
    push_list.delPushunitFromPushTo(message_type,sent_id)
    await session.send('已移除此地所有监测')


#获取指定推送对象的推送列表（推送标识，推送对象ID）
def get_pushTo_spylist(message_type:str,pushTo:int):
    if message_type not in push_list.message_type_list:
        raise Exception("无效的消息类型！",message_type)
    table = push_list.getLitsFromPushTo(message_type,pushTo)
    s = ''
    unit_cout = 0
    for key in table:
        unit_cout = unit_cout + 1
        s = s + (table[key]['nick'] if table[key]['nick'] != '' else tweetListener.myStreamListener.tryGetNick(key,"未定义昵称")) + \
            "," + str(key) + ',' + table[key]['des'] + "\n"
    s = s + '总监测数：' + str(unit_cout)
    if unit_cout == 0:
        s = s + '\n' + '单 推 b o t'
    return s
@on_command('getpushlist',aliases=['DD列表'],only_to_me = False)
async def getpushlist(session: CommandSession):
    message_type = session.event['message_type']
    sent_id = 0
    if message_type == 'private':
        sent_id = session.event['user_id']
    elif message_type == 'group':
        sent_id = session.event['group_id']
    else:
        await session.send('未收录的消息类型:'+message_type)
        return
    s = get_pushTo_spylist(message_type,sent_id)
    await session.send(s)

@on_command('getuserinfo',aliases=['查询推特用户'],permission=permission.SUPERUSER,only_to_me = True)
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
        tweetListener.log_print(3,'推Py错误'+s)
        await session.send("查询不到信息")
        return
    tweetListener.myStreamListener.seve_image(userinfo.screen_name,userinfo.profile_image_url_https,'userinfo')
    file_suffix = os.path.splitext(userinfo.profile_image_url_https)[1]
    s = '用户UID:'+ str(userinfo.id) + "\n" + \
        '用户ID:' + userinfo.screen_name + "\n" + \
        '用户昵称:' + userinfo.name + "\n" + \
        '头像:' + '[CQ:image,file=userinfo/' + userinfo.screen_name + file_suffix + ']'+ "\n" + \
        '描述:' + userinfo.description + "\n" + \
        '推文受保护:' + str(userinfo.protected) + "\n" + \
        '被关注数:' + str(userinfo.followers_count) + "\n" + \
        '关注数:' + str(userinfo.friends_count) + "\n" + \
        '发推数(包括转发)：' + str(userinfo.statuses_count) + "\n" + \
        '账户创建时间：' + str(userinfo.created_at)
    await asyncio.sleep(2.5)
    await session.send(s)
@on_command('delone',aliases=['我不想D了'],permission=permission.SUPERUSER,only_to_me = True)
async def delOne(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg == '':
        await session.send("缺少参数")
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
        tweetListener.log_print(3,'推Py错误:'+s)
        await session.send("查询不到信息,bksn")
        return
    tweetListener.myStreamListener.seve_image(userinfo.screen_name,userinfo.profile_image_url_https,'userinfo')
    file_suffix = os.path.splitext(userinfo.profile_image_url_https)[1]
    res = push_list.delPushunitFromPushToAndTweetUserID(
        session.event['message_type'],
        session.event[('group_id' if session.event['message_type'] == 'group' else 'user_id')],
        userinfo.id
        )
    s = '用户UID:'+ str(userinfo.id) + "\n" + \
        '用户ID:' + userinfo.screen_name + "\n" + \
        '用户昵称:' + userinfo.name + "\n" + \
        '头像:' + '[CQ:image,file=userinfo/' + userinfo.screen_name + file_suffix + ']'+ "\n" + \
        ('此用户已移出监听列表' if res[0] == True else '移除失败:'+res[1])
    await session.send(s)

@on_command('addone',aliases=['给俺D一个'],permission=permission.SUPERUSER,only_to_me = True)
async def addOne(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg == '':
        await session.send("缺少参数")
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
        tweetListener.log_print(3,'推Py错误:'+s)
        await session.send("查询不到信息,你D都能D歪来")
        return
    tweetListener.myStreamListener.seve_image(userinfo.screen_name,userinfo.profile_image_url_https,'userinfo')
    file_suffix = os.path.splitext(userinfo.profile_image_url_https)[1]
    nick = ''
    des = ''
    if cs[2] != '':
        cs = commandHeadtail(cs[2])
        nick = cs[0]
        des = cs[2]
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
        '头像:' + '[CQ:image,file=userinfo/' + userinfo.screen_name + file_suffix + ']'+ "\n" + \
        ('此用户已添加至监听列表' if res[0] == True else '添加失败:'+res[1])
    await session.send(s)


#推特ID编码解码
#解码成功返回推特ID，失败返回-1
def decode_b64(str) -> int:
    table = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
                "6": 6, "7": 7, "8": 8, "9": 9,
                "a": 10, "b": 11, "c": 12, "d": 13, "e": 14, "f": 15, "g": 16,
                "h": 17, "i": 18, "j": 19, "k": 20, "l": 21, "m": 22, "n": 23,
                "o": 24, "p": 25, "q": 26, "r": 27, "s": 28, "t": 29, "u": 30,
                "v": 31, "w": 32, "x": 33, "y": 34, "z": 35,
                "A": 36, "B": 37, "C": 38, "D": 39, "E": 40, "F": 41, "G": 42,
                "H": 43, "I": 44, "J": 45, "K": 46, "L": 47, "M": 48, "N": 49,
                "O": 50, "P": 51, "Q": 52, "R": 53, "S": 54, "T": 55, "U": 56,
                "V": 57, "W": 58, "X": 59, "Y": 60, "Z": 61,
                "$": 62, "_": 63}
    result : int = 0
    for i in range(len(str)):
        result *= 64
        if str[i] not in table:
            return -1
        result += table[str[i]]
    return result + 1253881609540800000
@on_command('detweetid',only_to_me = False)
async def decodetweetid(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg == '':
        return
    res = decode_b64(stripped_arg)
    if res == -1:
        await session.send("缩写推特ID不正确")
        return
    await session.send("推特ID为："+str(res))
    #parameter = commandHeadtail(stripped_arg)
@on_command('entweetid',only_to_me = False)
async def encodetweetid(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg == '':
        return
    if not stripped_arg.isdecimal():
        await session.send("推特ID不正确")
        return
    res = tweetListener.encode_b64(int(stripped_arg))
    await session.send("推特ID缩写为："+res)
    #parameter = commandHeadtail(stripped_arg)

"""
	'font': 8250736, 
    'message': [{'type': 'text', 'data': {'text': '!getpushlist'}}], 
    'message_id': 436, 
    'message_type': 'private', 
    'post_type': 'message', 
    'raw_message': '!getpushlist', 
    'self_id': 1837730674, 
    'sender': {'age': 20, 'nickname': '晨轩°', 'sex': 'male', 'user_id': 3309003591}, 
    'sub_type': 'friend', 
    'time': 1587967443, 
    'user_id': 3309003591, 
    'to_me': True}
"""