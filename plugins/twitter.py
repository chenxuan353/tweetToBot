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
    res = push_list.delPushunitFromPushTo(message_type,int(sent_id))
    await session.send('已移除此地所有监测' if res[0] == True else res[1])


#获取指定推送对象的推送列表（推送标识，推送对象ID）
def get_pushTo_spylist(message_type:str,pushTo:int):
    if message_type not in push_list.message_type_list:
        raise Exception("无效的消息类型！",message_type)
    table = push_list.getLitsFromPushToAndID(message_type,pushTo)
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

#获取推送对象总属性设置
def getPushToSetting(message_type:str,pushTo:int) -> str:
    attrlist = {    
        'upimg':'图片',#是否连带图片显示(默认不带)-发推有效,转推及评论等事件则无效
        #推特推送模版
        'retweet_template':'转推模版',
        'quoted_template':'转推并评论模版',
        'reply_to_status_template':'回复模版',
        'reply_to_user_template':'提及模版', 
        'none_template':'发推模版',
        
        #推特推送开关
        'retweet':'转推',#转推(默认不开启)
        'quoted':'转推并评论',#带评论转推(默认开启)
        'reply_to_status':'回复',#回复(默认开启)
        'reply_to_user':'提及',#提及某人-多数时候是被提及但是被提及不会接收(默认开启)
        'none':'发推',#发推(默认开启)

        #个人信息变化推送(非实时)
        'change_ID':'ID修改', #ID修改(默认关闭)
        'change_name':'昵称修改', #昵称修改(默认开启)
        'change_description':'描述修改', #描述修改(默认关闭)
        'change_headimgchange':'头像修改', #头像更改(默认开启)
    }
    res = ''
    attrs = push_list.getAttrLitsFromPushTo(message_type,pushTo)
    if attrs == {}:
        return '全局设置未初始化，至少添加一个监测来初始化设置。'
    for key,value in attrs.items():
        res = res + attrlist[key] + ':'  + \
            (value if value not in (0,1,'') else {0:'关闭',1:'开启','':'未定义'}[value]) + '\n'
    return res
@on_command('getGroupSetting',aliases=['全局设置列表'],permission=permission.SUPERUSER,only_to_me = True)
async def setGroupSetting(session: CommandSession):
    res = getPushToSetting(
        session.event['message_type'],
        session.event[('group_id' if session.event['message_type'] == 'group' else 'user_id')]
    )
    await session.send(res)
#获取某个单元的推送设置列表
def userinfoToStr(userinfo):
    if userinfo:
        res = "\n" + '用户名：' + userinfo['name'] + \
            '用户昵称：' + userinfo['screen_name'] + "\n"
        return res
    return ''
def getPushUnitSetting(message_type:str,pushTo:int,tweet_user_id:int) -> str:
    attrlist = {    
        'upimg':'图片',#是否连带图片显示(默认不带)-发推有效,转推及评论等事件则无效
        #推特推送模版
        'retweet_template':'转推模版',
        'quoted_template':'转推并评论模版',
        'reply_to_status_template':'回复模版',
        'reply_to_user_template':'提及模版', 
        'none_template':'发推模版',
        
        #推特推送开关
        'retweet':'转推',#转推(默认不开启)
        'quoted':'转推并评论',#带评论转推(默认开启)
        'reply_to_status':'回复',#回复(默认开启)
        'reply_to_user':'提及',#提及某人-多数时候是被提及但是被提及不会接收(默认开启)
        'none':'发推',#发推(默认开启)

        #个人信息变化推送(非实时)
        'change_ID':'ID修改', #ID修改(默认关闭)
        'change_name':'昵称修改', #昵称修改(默认开启)
        'change_description':'描述修改', #描述修改(默认关闭)
        'change_headimgchange':'头像修改', #头像更改(默认开启)
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
    userinfo = tweetListener.myStreamListener.tryGetUserInfo(tweet_user_id)
    res = '用户ID:' + str(tweet_user_id) + "\n" + \
        '自定义的昵称:' + (Pushunit['nick'] if Pushunit['nick'] != '' else '未定义昵称') + \
        userinfoToStr(userinfo)
    for attrname,attrdisplayname in attrlist.items():
        value = push_list.getPuslunitAttr(Pushunit,attrname)
        res = res + '\n' + attrdisplayname + ':' + \
            (value[1] if value[1] not in (0,1,'') else {0:'关闭',1:'开启','':'未定义'}[value[1]])
    return (True,res)
@on_command('getSetting',aliases=['对象设置列表'],permission=permission.SUPERUSER,only_to_me = True)
async def getSetting(session: CommandSession):
    stripped_arg = session.current_arg_text.strip().lower()
    if stripped_arg == '':
        await session.send("缺少参数")
        return
    #处理用户ID
    tweet_user_id : int = -1
    if stripped_arg.isdecimal():
        tweet_user_id = int(stripped_arg)
    else:
        await session.send("用户ID错误")
        return
    res = getPushUnitSetting(
        session.event['message_type'],
        session.event[('group_id' if session.event['message_type'] == 'group' else 'user_id')],
        tweet_user_id
    )
    await session.send(res[1])

        
#推送对象总属性设置
@on_command('setGroupAttr',aliases=['全局设置'],permission=permission.SUPERUSER,only_to_me = True)
async def setGroupAttr(session: CommandSession):
    stripped_arg = session.current_arg_text.strip().lower()
    if stripped_arg == '':
        await session.send("缺少参数")
        return
    Pushunit_allowEdit = {
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
        'reply_to_user':'reply_to_user','被提及':'reply_to_user_template',
        'none':'none','发推':'none',
        #推特个人信息变动推送开关
        'change_id':'change_ID','ID改变':'change_ID',
        'change_name':'change_name','名称改变':'change_name',
        'change_description':'change_description','描述改变':'change_description',
        'change_headimgchange':'change_headimgchange','头像改变':'change_headimgchange'
        }
    template_attr = (
        'retweet_template',
        'quoted_template',
        'reply_to_status_template',
        'reply_to_user_template',
        'none_template'
    )
    cs = commandHeadtail(stripped_arg)
    cs = {
        0:cs[0],
        1:cs[1],
        2:cs[2].strip()
    }
    if cs[0] not in Pushunit_allowEdit:
        await session.send('属性值不存在！')
        return
    if cs[2] != '' and Pushunit_allowEdit[cs[0]] in template_attr:
        res = push_list.PushTo_setAttr(
            session.event['self_id'],
            session.event['message_type'],
            Pushunit_allowEdit[cs[0]],
            cs[2]
        )
    elif cs[2] in ('true','开','打开','开启','1'):
        res = push_list.PushTo_setAttr(
            session.event['self_id'],
            session.event['message_type'],
            Pushunit_allowEdit[cs[0]],
            1
        )
    elif cs[2] in ('false','关','关闭','0'):
        res = push_list.PushTo_setAttr(
            session.event['self_id'],
            session.event['message_type'],
            Pushunit_allowEdit[cs[0]],
            0
        )
    else:
        res = (False,'属性的值不合法！')
    await session.send(res[1])
#推送对象的监测对象属性设置
@on_command('setAttr',aliases=['对象设置'],permission=permission.SUPERUSER,only_to_me = True)
async def setAttr(session: CommandSession):
    stripped_arg = session.current_arg_text.strip().lower()
    if stripped_arg == '':
        await session.send("缺少参数")
        return
    cs = commandHeadtail(stripped_arg)
    cs = {
        0:cs[0],
        1:cs[1],
        2:cs[2].strip()
    }
    #处理用户ID
    tweet_user_id : int = -1
    if cs[0].isdecimal():
        tweet_user_id = int(cs[0])
    else:
        await session.send("用户ID错误")
        return
    if cs[2].strip() == '':
        await session.send("缺少参数")
        return
    tcs = commandHeadtail(cs[2])
    cs[2] = tcs[0]
    cs[3] = tcs[1]
    cs[4] = tcs[2].strip()

    Pushunit_allowEdit = {
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
        'reply_to_user':'reply_to_user','被提及':'reply_to_user_template',
        'none':'none','发推':'none',
        #推特个人信息变动推送开关
        'change_id':'change_ID','ID改变':'change_ID',
        'change_name':'change_name','名称改变':'change_name',
        'change_description':'change_description','描述改变':'change_description',
        'change_headimgchange':'change_headimgchange','头像改变':'change_headimgchange'
        }
    template_attr = (
        'retweet_template',
        'quoted_template',
        'reply_to_status_template',
        'reply_to_user_template',
        'none_template'
    )
    if str(tweet_user_id) not in push_list.spylist:
        await session.send("用户不在监测列表内！")
        return
    if cs[2] not in Pushunit_allowEdit:
        await session.send('属性值不存在！')
        return
    if cs[4] != '' and Pushunit_allowEdit[cs[2]] in template_attr:
        res = push_list.setPushunitAttr(
            session.event['self_id'],
            session.event['message_type'],
            tweet_user_id,
            Pushunit_allowEdit[cs[2]],
            cs[4]
        )
    elif cs[4] in ('true','开','打开','开启','1'):
        res = push_list.setPushunitAttr(
            session.event['self_id'],
            session.event['message_type'],
            tweet_user_id,
            Pushunit_allowEdit[cs[2]],
            1
        )
    elif cs[4] in ('false','关','关闭','0'):
        res = push_list.setPushunitAttr(
            session.event['self_id'],
            session.event['message_type'],
            tweet_user_id,
            Pushunit_allowEdit[cs[2]],
            0
        )
    else:
        res = (False,'属性的值不合法！')
    await session.send(res[1])

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