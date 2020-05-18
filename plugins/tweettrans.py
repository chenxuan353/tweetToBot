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
trans_tmemory = TempMemory('trans.json',limit=300,autoload=True,autosave=True)
group_list = []
res = data_read('transwhilelist.json')
if res[0]:
    group_list = res[2]

@on_command('transswitch',aliases=['ts','烤推授权'], permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_OWNER,only_to_me = True)
def transswitch(session: CommandSession):
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

def deal_trans(arg,type_html:str='<p dir="auto" style="color:#1DA1F2;font-size:0.7em;font-weight: 600;">翻译自日文</p>') -> dict:
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
                logger.info(tweet)
                tweet_sname = tweet['user']['screen_name']
                break
        trans = deal_trans(arg2)
        res = tt.getTransFromTweetID(str(tweet_id),trans,tweet_sname,str(session.event['group_id'])+'-'+str(tweet_id))
        if res[0]:
            if session.event['message_type'] == 'group':
                nick = None
                if 'nickname' in session.event.sender:
                    nick = session.event.sender['nickname']
                trans_tmemory.join({'id':tweet_id,'mintrans':arg2[0:15],'tweetid':arg1,'sourcetweetid':tweet_id,'trans':arg2,'op':session.event['user_id'],'opnick':nick,'group':session.event['group_id']})
            send_msg(session,
                    config.trans_img_path+'/transtweet/transimg/' + str(session.event['group_id'])+'-'+str(tweet_id) + '.png' +"\n" + \
                    str('[CQ:image,timeout=' + config.img_time_out + \
                    ',file='+config.trans_img_path+'/transtweet/transimg/' + str(session.event['group_id'])+'-'+str(tweet_id) + '.png' + ']'))
        else:
            send_msg(session,"错误，"+res[2])
        logger.info(CQsessionToStr(session))
        del tt
    except:
        s = traceback.format_exc(limit=10)
        logger.error(s)
        send_msg(session,"错误，服务器异常")
@on_command('trans',aliases=['t','烤推'], permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_OWNER | perm.GROUP,only_to_me = True)
async def trans(session: CommandSession):
    if session.event['message_type'] == 'group' and session.event['group_id'] not in group_list:
        await session.send("烤推未授权")
        return
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg == '':
        await session.send("缺少参数")
        return
    cs = commandHeadtail(stripped_arg)
    if cs[2] == '':
        await session.send("缺少参数")
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
            await session.send("推特ID不正确")
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
@on_command('translist',aliases=['tl','烤推列表'], permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_OWNER | perm.GROUP,only_to_me = True)
async def translist(session: CommandSession):
    if session.event['message_type'] != 'group':
        return
    if session.event['group_id'] not in group_list:
        await session.send("烤推未授权")
    return
    page = 1
    stripped_arg = session.current_arg_text.strip().lower()
    if stripped_arg != '':
        if not stripped_arg.isdecimal():
            await session.send("参数不正确")
            return
        page = int(stripped_arg)
        if page < 1:
            await session.send("参数不正确")
            return
    s = getlist(session.event['group_id'],page)
    await session.send(s)
    logger.info(CQsessionToStr(session))

@on_command('gettrans',aliases=['gt','获取翻译'], permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_OWNER | perm.GROUP,only_to_me = True)
async def gettrans(session: CommandSession):
    if session.event['message_type'] != 'group':
        return
    if session.event['group_id'] not in group_list:
        await session.send("烤推未授权")
    return
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg == '':
        await session.send("缺少参数")
        return
    arg1 = stripped_arg #推文ID
    tweet_id : int = -1
    if arg1.isdecimal() and int(arg1) > 1253881609540800000:
        tweet_id = int(arg1)
    else:
        res = decode_b64(arg1)
        if res == -1:
            await session.send("推特ID不正确")
            return
        tweet_id = res
    ttm = trans_tmemory.tm.copy()
    length = len(ttm)
    for i in range(length - 1,-1,-1):
        if ttm[i]['sourcetweetid'] == tweet_id:
            await session.send(config.trans_img_path+'/transtweet/transimg/' + str(ttm[i]['group'])+'-'+str(tweet_id) + '.png' +"\n" + \
                    str('[CQ:image,timeout=' + config.img_time_out + \
                    ',file='+config.trans_img_path+'/transtweet/transimg/' + str(ttm[i]['group'])+'-'+str(tweet_id) + '.png' + ']'))
            return
    await session.send("此推文不存在翻译")