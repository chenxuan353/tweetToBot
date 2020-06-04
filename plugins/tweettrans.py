# -*- coding: UTF-8 -*-
from nonebot import on_command, CommandSession,NoticeSession,on_notice,permission as perm
from helper import getlogger,msgSendToBot,CQsessionToStr,TempMemory,argDeal,data_read,data_save
from module.twitter import decode_b64,encode_b64,mintweetID
from plugins.twitter import tweet_event_deal
from module.tweettrans import TweetTrans,rate_limit_bucket
import nonebot
import time
import asyncio
import os
import traceback
import re
import module.permissiongroup as permissiongroup
import config
logger = getlogger(__name__)
__plugin_name__ = '烤推'
__plugin_usage__ = r"""
烤推指令前端
"""
#线程池
from concurrent.futures import ThreadPoolExecutor
pool = ThreadPoolExecutor(max_workers=64,thread_name_prefix="trans_Threads")
#烤推列表缓存
trans_tmemory = TempMemory('trans_tmemory.json',limit=300,autoload=True,autosave=True)
#烤推权限
permgroupname = 'transtweet'
permissiongroup.perm_addLegalPermGroup(__name__,'烤推模块',permgroupname)
permissiongroup.perm_addLegalPermUnit(permgroupname,'switch') #烤推切换权限
permissiongroup.perm_addLegalPermUnit(permgroupname,'trans') #烤推权限

trans_img_path = os.path.join(config.trans_img_path,'transtweet','transimg','')

transtemplate_filename = 'transtemplate.json'
transtemplate = {
    #默认模版
    '0':'<p dir="auto" style="color:#1DA1F2;font-size:0.7em;font-weight: 600;">翻译自日文</p>'
}
def loadTranstemplate():
    global transtemplate
    res = data_read(transtemplate_filename)
    if res[0]:
        transtemplate = res[2]
    return res
def transtemplateInit():
    global transtemplate
    res = loadTranstemplate()
    if not res[0]:
        data_save(transtemplate_filename,transtemplate)
transtemplateInit()
def setTranstemplate(key,value):
    transtemplate[key] = value
    data_save(transtemplate_filename,transtemplate)

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


@on_command('transReloadTemplate',aliases=['重载烤推模版'], permission=perm.SUPERUSER,only_to_me = True)
async def transReloadTemplate(session: CommandSession):
    if not headdeal(session):
        return
    res = loadTranstemplate()
    if res[0]:
        await session.send('重载成功')
    else:
        await session.send(res[1])

async def transswitch_group(session: CommandSession):
    if perm_check(session,'-switch',user = True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    if perm_check(session,'-switch'):
        await session.send('操作被拒绝，权限不足(g)')
        return
    if perm_check(session,'*'):
        await session.send('操作无效，存在“*”权限')
        return
    if perm_check(session,'trans'):
        perm_del(session,'trans')
        await session.send('烤推授权关闭')
    else:
        perm_add(session,'trans')
        await session.send('烤推授权开启')
async def transswitch_private(session: CommandSession):
    user_id = session.event['user_id']
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
                #'私聊':'private',
                #'private':'private',
                '群聊':'group',
                'group':'group',
                #'好友':'private',
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
    remote = {
                'message_type':'group',
                'sent_id':args['sendid'],
                'op_id':user_id
            }
    if perm_check(session,'-switch'):
        await session.send('操作被拒绝，权限不足(p)')
        return
    if perm_check(session,'-switch',remote):
        await session.send('操作被拒绝，权限不足(g)')
        return
    if perm_check(session,'*',remote):
        await session.send('操作无效，存在“*”权限(g)')
        return
    if perm_check(session,'trans',remote):
        perm_del(session,'trans',remote)
        await session.send('烤推授权关闭')
    else:
        perm_add(session,'trans',)
        await session.send('烤推授权开启')
@on_command('transswitch',aliases=['ts','烤推授权'], permission=perm.SUPERUSER,only_to_me = True)
async def transswitch(session: CommandSession):
    if not headdeal(session):
        return
    message_type = session.event['message_type']
    if message_type == 'group':
        await transswitch_group(session)
    else:
        await transswitch_private(session)


def deal_trans(arg,ad) -> dict:
    trans = {
        'type_html':'',
        'source':arg,
        'text':{}
    }
    tests = arg.split('##')
    if len(tests) == 1:
        kvc = tests[0].partition("#!")
        trans['text']['main'] = []
        trans['text']['main'].append(kvc[0].strip())
        if kvc[2] != '':
            trans['text']['main'].append(kvc[2].strip())
    else:
        for test in tests:
            test = test.strip()
            if test == '':
                continue
            kv = re.findall(r'^([0-9]{1,2}|main|m)\s{1}(.+)',test,re.S)
            if kv == []:
                return None #格式不正确
            kv = list(kv[0])
            if kv[0].isnumeric():
                kv[0] = str(int(kv[0]))
            elif kv[0] == 'm':
                kv[0] = 'main'
            kvc = kv[1].partition("#!")
            trans['text'][kv[0]] = []
            trans['text'][kv[0]].append(kvc[0].strip())
            if kvc[2] != '':
                trans['text'][kv[0]].append(kvc[2].strip())
    return trans
def send_msg(session: CommandSession,msg):
    session.bot.sync.send_msg_rate_limited(self_id=session.self_id,group_id=session.event['group_id'],message=msg)
def send_res(session: CommandSession,args):
    global transtemplate
    group_id =session.event['group_id']
    user_id = session.event['user_id']
    tweet_id = args['tweet_id']
    trans = args['trans']
    try:
        #使用64进制减少长度
        tasktype = encode_b64(int(time.time()),offset = 0)
        type_html = transtemplate['0']
        if str(group_id) in transtemplate:
            type_html = transtemplate[str(group_id)]
        trans['type_html'] = type_html
        
        #检查推文缓存
        tweet_sname = 's'
        tweet = tweet_event_deal.tryGetTweet(tweet_id)
        if tweet != None:
            logger.info('检测到缓存:' + tweet['id_str'] + '(' + tweet['user']['screen_name'] + ')')
            #logger.info(tweet)
            tweet_cache = tweet
            tweet_sname = tweet_cache['user']['screen_name']

        tt = TweetTrans()
        res = tt.getTransFromTweetID(
            str(tweet_id),
            args['trans'],
            tweet_sname,
            encode_b64(group_id,offset=0)+'-'+str(tasktype)
            )
        if res[0]:
            time.sleep(1)
            if 'nickname' in session.event.sender:
                nick = session.event.sender['nickname']
            else:
                nick = str(user_id)
            
            trans_tmemory.join({
                'id':tweet_id,
                'group':group_id,
                'mintrans':trans['source'][0:15].replace("\n"," "),
                'tweetid':encode_b64(tweet_id),
                'tasktype':tasktype,
                'trans':trans,
                'op':user_id,
                'opnick':nick
                })
            send_msg(session,
                    trans_img_path + encode_b64(group_id,offset=0)+'-'+str(tasktype) + '.png' +"\n" + \
                    str('[CQ:image,timeout=' + config.img_time_out + \
                    ',file='+trans_img_path + encode_b64(group_id,offset=0)+'-'+str(tasktype) + '.png' + ']') + "\n"\
                    "使用 !tl 查看烤推历史"
                    )
        else:
            send_msg(session,"错误，"+res[2])
        del tt
    except:
        s = traceback.format_exc(limit=10)
        logger.error(s)
        send_msg(session,"错误，烤推服务异常!")
@on_command('trans',aliases=['t','烤推'], permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_OWNER | perm.GROUP,only_to_me = False)
async def trans(session: CommandSession):
    if not headdeal(session):
        return
    message_type = session.event['message_type']
    #group_id = (session.event['group_id'] if message_type == 'group' else None)
    #user_id = session.event['user_id']
    if message_type != 'group':
        return
    if perm_check(session,'-switch',user = True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    if not perm_check(session,'trans'):
        await session.send('操作未授权')
        return
    logger.info(CQsessionToStr(session))
    if not rate_limit_bucket.consume(1):
        await session.send("烤推繁忙，请稍后再试")
        return
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
        },{
            'name':'trans', #参数名
            'des':'翻译内容', #参数错误描述
            'type':'dict', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':{
                    'type_html':'',
                    'source':'',
                    'text':{}
                }, #默认值
            'func':deal_trans, #函数，当存在时使用函数进行二次处理
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
    pool.submit(send_res,session,args[1])
    await session.send("图片合成中...")

def getlist(groupid:int,page:int=1):
    ttm = trans_tmemory.tm.copy()
    length = len(ttm)
    cout = 0
    s = "昵称,任务标识,推文标识,翻译简写\n"
    for i in range(length - 1,-1,-1):
        if ttm[i]['group'] == groupid:
            if cout >= (page-1)*5 and cout < (page)*5:
                s = s + str(ttm[i]['opnick'] if ttm[i]['opnick'] else ttm[i]['op']) + ',' + ttm[i]['tasktype'] + ',' + ttm[i]['tweetid'] + ','  + ttm[i]['mintrans'] + "\n"
            cout = cout + 1
    totalpage = (cout)//5 + (0 if cout%5 == 0 else 1)
    s = s + '页数:'+str(page)+'/'+str(totalpage)+'总记录数：'+str(cout) + '\n'
    s = s + '使用!tgt 任务标识 获取指定任务图片' + "\n"
    s = s + '使用!gt 推文标识 获取指定推文最后的译文图片'
    return s
@on_command('translist',aliases=['tl','烤推列表'], permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_OWNER | perm.GROUP,only_to_me = False)
async def translist(session: CommandSession):
    if not headdeal(session):
        return
    message_type = session.event['message_type']
    group_id = (session.event['group_id'] if message_type == 'group' else None)
    #user_id = session.event['user_id']
    if message_type != 'group':
        return
    if perm_check(session,'-switch',user = True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    if not perm_check(session,'trans'):
        await session.send('操作未授权')
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
    s = getlist(group_id,page)
    await session.send(s)

@on_command('gettrans',aliases=['gt','获取翻译'], permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_OWNER | perm.GROUP,only_to_me = False)
async def gettrans(session: CommandSession):
    if not headdeal(session):
        return
    message_type = session.event['message_type']
    #group_id = (session.event['group_id'] if message_type == 'group' else None)
    #user_id = session.event['user_id']
    if message_type != 'group':
        return
    if perm_check(session,'-switch',user = True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    if not perm_check(session,'trans'):
        await session.send('操作未授权')
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
    ttm = trans_tmemory.tm.copy()
    length = len(ttm)
    for i in range(length - 1,-1,-1):
        if ttm[i]['id'] == tweet_id:
            await session.send(trans_img_path + encode_b64(ttm[i]['group'],offset=0)+'-'+str(ttm[i]['tasktype']) + '.png' +"\n" + \
                    str('[CQ:image,timeout=' + config.img_time_out + \
                    ',file='+trans_img_path + encode_b64(ttm[i]['group'],offset=0)+'-'+str(ttm[i]['tasktype']) + '.png' + ']'))
            return
    await session.send("未查找到推文翻译")

@on_command('typeGettrans',aliases=['tgt'], permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_OWNER | perm.GROUP,only_to_me = False)
async def typeGettrans(session: CommandSession):
    if not headdeal(session):
        return
    message_type = session.event['message_type']
    #group_id = (session.event['group_id'] if message_type == 'group' else None)
    #user_id = session.event['user_id']
    if message_type != 'group':
        return
    if perm_check(session,'-switch',user = True):
        await session.send('操作被拒绝，权限不足(p)')
        return
    if not perm_check(session,'trans'):
        await session.send('操作未授权')
        return
    logger.info(CQsessionToStr(session))
    arg = session.current_arg_text.strip()
    if arg == '':
        await session.send('缺少参数')
        return
    ttm = trans_tmemory.tm.copy()
    length = len(ttm)
    for i in range(length - 1,-1,-1):
        if ttm[i]['tasktype'] == arg:
            await session.send(trans_img_path + encode_b64(ttm[i]['group'],offset=0)+'-'+str(ttm[i]['tasktype']) + '.png' +"\n" + \
                    str('[CQ:image,timeout=' + config.img_time_out + \
                    ',file='+trans_img_path + encode_b64(ttm[i]['group'],offset=0)+'-'+str(ttm[i]['tasktype']) + '.png' + ']'))
            return
    await session.send("未查找到推文翻译")

@on_command('transabout',aliases=['ta','烤推帮助'],only_to_me = False)
async def transabout(session: CommandSession):
    if not headdeal(session):
        return
    message_type = session.event['message_type']
    if message_type != 'group':
        return
    res = perm_check(session,'trans')
    logger.info(CQsessionToStr(session))
    msg = '当前版本为烤推机测试版V2.33' + "\n" + \
        '授权状态:' + ("已授权" if res else "未授权") + "\n" + \
        '!ts -切换烤推授权' + "\n" + \
        '!t 推文ID 翻译 -合成翻译' + "\n" + \
        '!tl -已翻译推文列表' + "\n" + \
        '!gt 推文ID/推文标识 -获取最后翻译' + "\n" + \
        '!tgt 任务标识 -获取指定翻译' + "\n" + \
        '!gtt 推文ID/推文标识 -获取指定推文内容' + "\n" + \
        '多层回复翻译:' + "\n" + \
        '##1 第一层翻译' + "\n" + \
        '#! 第一层层内推文(转推并评论类型里的内嵌推文)' + "\n" + \
        '##2 第二层翻译' + "\n" + \
        '##main 主翻译' + "\n" + \
        '烤推支持换行参数，如有需要可以更换翻译自日文到任意图片或文字' + "\n" + \
        '如果出现问题可以 !反馈 反馈内容 反馈信息'
    await session.send(msg)