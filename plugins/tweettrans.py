# -*- coding: UTF-8 -*-
from nonebot import on_command, CommandSession,NoticeSession,on_notice,permission as perm
from helper import commandHeadtail,keepalive,getlogger,msgSendToBot,CQsessionToStr,TempMemory
from module.twitter import decode_b64,encode_b64,tmemory,data_read,data_save
from module.tweettrans import TweetTrans
import nonebot
import time
import asyncio
import os
import traceback
import config
logger = getlogger(__name__)
__plugin_name__ = '烤推'
__plugin_usage__ = r"""
烤推指令前端
"""
#线程池
from concurrent.futures import ThreadPoolExecutor
pool = ThreadPoolExecutor(max_workers=64)
trans_tmemory = TempMemory('trans_tmemory.json',limit=300,autoload=True,autosave=True)
group_list = []
res = data_read('transwhilelist.json')
if res[0]:
    group_list = res[2]

@on_command('transswitch',aliases=['ts','烤推授权'], permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_OWNER,only_to_me = True)
async def transswitch(session: CommandSession):
    if session.event['message_type'] != 'group':
        return
    if session.event['group_id'] in group_list:
        group_list.remove(session.event['group_id'])
        await session.send('烤推授权关闭')
        data_save('transwhilelist.json',group_list)
    else:
        group_list.append(session.event['group_id'])
        await session.send('烤推授权开启')
        data_save('transwhilelist.json',group_list)

def deal_trans(arg,type_html:str) -> dict:
    trans = {
        'type_html':type_html,
        'text':{}
    }
    tests = arg.split('##')
    if len(tests) == 1:
        kvc = tests[0].partition("#!")
        trans['text']['main'] = []
        trans['text']['main'].append(kvc[0])
        if kvc[2] != '':
            trans['text']['main'].append(kvc[2])
    else:
        del tests[0]
        for test in tests:
            if test == '':
                continue
            kv = test.partition(" ")
            if kv[2] == '':
                return None #格式不正确
            kvc = kv[2].partition("#!")
            trans['text'][kv[0]] = []
            trans['text'][kv[0]].append(kvc[0])
            if kvc[2] != '':
                trans['text'][kv[0]].append(kvc[2])
    return trans
def send_msg(session: CommandSession,msg):
    session.bot.sync.send_msg_rate_limited(self_id=session.self_id,group_id=session.event['group_id'],message=msg)
def send_res(session: CommandSession,tweet_id,tweet_sname,arg1,arg2):
    try:
        tt = TweetTrans()
        for tweet in tmemory.tm:
            if tweet['id'] == tweet_id:
                logger.info('检测到缓存')
                logger.info(tmemory)
                logger.info(tweet)
                tweet_sname = tweet['user']['screen_name']
                break
        type_html = '<p dir="auto" style="color:#1DA1F2;font-size:0.7em;font-weight: 600;">翻译自日文</p>'
        if session.event['group_id'] in config.transtemplate:
            type_html = config.transtemplate[session.event['group_id']]
        tasktype = int(time.time())
        trans = deal_trans(arg2,type_html=type_html)
        res = tt.getTransFromTweetID(str(tweet_id),trans,tweet_sname,str(session.event['group_id'])+'-'+str(tasktype))
        if res[0]:
            time.sleep(1)
            if session.event['message_type'] == 'group':
                nick = None
                if 'nickname' in session.event.sender:
                    nick = session.event.sender['nickname']
                trans_tmemory.join({'id':tweet_id,'mintrans':arg2[0:15],'tweetid':arg1,'tasktype':tasktype,'sourcetweetid':tweet_id,'trans':arg2,'op':session.event['user_id'],'opnick':nick,'group':session.event['group_id']})
            send_msg(session,
                    config.trans_img_path+'/transtweet/transimg/' + str(session.event['group_id'])+'-'+str(tasktype) + '.png' +"\n" + \
                    str('[CQ:image,timeout=' + config.img_time_out + \
                    ',file='+config.trans_img_path+'/transtweet/transimg/' + str(session.event['group_id'])+'-'+str(tasktype) + '.png' + ']'))
        else:
            send_msg(session,"错误，"+res[2])
        logger.info(CQsessionToStr(session))
        del tt
    except:
        s = traceback.format_exc(limit=10)
        logger.error(s)
        send_msg(session,"错误 服务器发生异常!BOT酱摸鱼中~")
@on_command('trans',aliases=['t','烤推'], permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_OWNER | perm.GROUP,only_to_me = False)
async def trans(session: CommandSession):
    if session.event['message_type'] != 'group':
        return
    if session.event['group_id'] not in group_list:
        await session.send("烤推未授权")
        return
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg == '':
        await session.send("烤啥呢弟弟 告诉我要烤哪条哇")
        return
    cs = commandHeadtail(stripped_arg)
    if cs[2] == '':
        await session.send("不 翻 了？")
        return
    arg1 = cs[0] #推文ID
    arg2 = cs[2] #翻译
    tweet_id : int = -1
    tweet_sname : str = 's'
    if arg1.isdecimal() and int(arg1) > 1253881609540800000:
        tweet_id = int(arg1)
    else:
        res = decode_b64(arg1)
        if res == -1:
            await session.send("推特ID似乎不太对呢 请再次检查")
            return
        tweet_id = res
    pool.submit(send_res,session,tweet_id,tweet_sname,arg1,arg2)
    await session.send("图片合成中...")
def getlist(groupid:int,page:int=1):
    ttm = trans_tmemory.tm.copy()
    length = len(ttm)
    cout = 0
    s = ''
    for i in range(length - 1,-1,-1):
        if ttm[i]['group'] == groupid:
            cout = cout + 1
            if ((cout//5)+1) == page:
                s = s + str(ttm[i]['opnick'] if ttm[i]['opnick'] else ttm[i]['op']) + ',' + ttm[i]['tweetid'] +',' + ttm[i]['mintrans'] + "\n"
    totalpage = (cout-1)//5 + (0 if cout%5 == 0 else 1)
    s = s + '页数:'+str(page)+'/'+str(totalpage)+'总记录数：'+str(cout)
    return s
@on_command('translist',aliases=['tl','烤推列表'], permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_OWNER | perm.GROUP,only_to_me = False)
async def translist(session: CommandSession):
    if session.event['message_type'] != 'group':
        return
    if session.event['group_id'] not in group_list:
        await session.send("烤推还没有获得授权哦~")
        return
    page = 1
    stripped_arg = session.current_arg_text.strip().lower()
    if stripped_arg != '':
        if not stripped_arg.isdecimal():
            await session.send("这个页数...你这是在为难我胖BOT.jpg")
            return
        page = int(stripped_arg)
        if page < 1:
            await session.send("反向翻页日神仙 不要乱玩咱啦~")
            return
    s = getlist(session.event['group_id'],page)
    await session.send(s)
    logger.info(CQsessionToStr(session))

@on_command('gettrans',aliases=['gt','获取翻译'], permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_OWNER | perm.GROUP,only_to_me = False)
async def gettrans(session: CommandSession):
    if session.event['message_type'] != 'group':
        return
    if session.event['group_id'] not in group_list:
        await session.send("烤推还没有授权哦~")
        return
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg == '':
        await session.send("没有参数 BOT也不知道要哪一条哇(泪)")
        return
    arg1 = stripped_arg #推文ID
    tweet_id : int = -1
    if arg1.isdecimal() and int(arg1) > 1253881609540800000:
        tweet_id = int(arg1)
    else:
        res = decode_b64(arg1)
        if res == -1:
            await session.send("推特ID似乎不太对呢 请再次检查")
            return
        tweet_id = res
    ttm = trans_tmemory.tm.copy()
    length = len(ttm)
    for i in range(length - 1,-1,-1):
        if ttm[i]['sourcetweetid'] == tweet_id:
            await session.send(config.trans_img_path+'/transtweet/transimg/' + str(ttm[i]['group'])+'-'+str(ttm[i]['tasktype']) + '.png' +"\n" + \
                    str('[CQ:image,timeout=' + config.img_time_out + \
                    ',file='+config.trans_img_path+'/transtweet/transimg/' + str(ttm[i]['group'])+'-'+str(ttm[i]['tasktype']) + '.png' + ']'))
            return
    await session.send("这条推文似乎还没有被翻译过哦~")

@on_command('transabout',aliases=['ta','烤推帮助'],only_to_me = False)
async def transabout(session: CommandSession):
    msg = '当前版本为烤推机测试版V2.0' + "\n" + \
        '!ts -切换烤推授权' + "\n" + \
        '!t 推文ID 翻译 -合成翻译' + "\n" + \
        '!tl -已翻译推文列表' + "\n" + \
        '!gt 推文ID -获取翻译' + "\n" + \
        '多层回复翻译:' + "\n" + \
        '##1 第一层翻译' + "\n" + \
        '#! 第一层层内推文(转推并评论类型里的内嵌推文)' + "\n" + \
        '##2 第二层翻译' + "\n" + \
        '##main 主翻译'
    await session.send(msg)