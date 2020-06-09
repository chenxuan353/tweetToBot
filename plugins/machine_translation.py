from nonebot import on_command, CommandSession,permission as perm
from helper import getlogger,CQsessionToStr,TokenBucket,TempMemory,argDeal,data_read,data_save
import module.permissiongroup as permissiongroup
from module.machine_translation import allow_st,engine_nick,engine_list,default_engine
import asyncio
import config
logger = getlogger(__name__)
__plugin_name__ = '机器翻译'
__plugin_usage__ = r"""
    实现机翻以及其它特殊功能(可能使用到自然语言处理器)
"""
config_filename = 'mtransopt_list.json'
mtransopt_list = {}
res = data_read(config_filename)
if res[0]:
    logger.info("配置文件读取成功")
    mtransopt_list = res[2]
#预处理
def headdeal(session: CommandSession):
    if session.event['message_type'] == "group" and session.event.sub_type != 'normal':
        return False
    return True

@on_command('mtransopt',aliases=['翻译设置','设置翻译'],only_to_me = False)
async def mtransopt(session: CommandSession):
    if not headdeal(session):
        return
    global mtransopt_list
    #message_type = session.event['message_type']
    #group_id = (session.event['group_id'] if message_type == 'group' else None)
    user_id = session.event['user_id']

    #if perm_check(session,'-listener',user = True):
    #    await session.send('操作被拒绝，权限不足(p)')
    #    return
    logger.info(CQsessionToStr(session))

    arglimit = [
        {
            'name':'engine', #参数名
            'des':'翻译引擎', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':None, #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':engine_nick
        },
        {
            'name':'Source', #参数名
            'des':'源语言', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':True, #是否转换为小写
            'default':'auto', #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':allow_st['Source']
        },
        {
            'name':'Target', #参数名
            'des':'目标语言', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':True, #是否转换为小写
            'default':'zh', #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':allow_st['Target']
        },
    ]
    args = argDeal(session.current_arg_text.strip(),arglimit)
    if not args[0]:
        await session.send(args[1] + '=>' + args[2])
        return
    args = args[1]
    user_id = str(user_id)
    mtransopt_list[user_id] = args
    data_save(config_filename,mtransopt_list)
    await session.send("设置已保存")

@on_command('mtrans',aliases=['mt','翻译','机翻'],only_to_me = False)
async def mtrans(session: CommandSession):
    if not headdeal(session):
        return
    #message_type = session.event['message_type']
    #group_id = (session.event['group_id'] if message_type == 'group' else None)
    user_id = session.event['user_id']
    logger.info(CQsessionToStr(session))
    user_id = str(user_id)
    if user_id in mtransopt_list:
        engine_func = engine_list[engine_nick[mtransopt_list[user_id]['engine']]]['func']
        res = engine_func(session.current_arg_text.strip(),mtransopt_list[user_id]['Source'],mtransopt_list[user_id]['Target'])
    else:
        res = default_engine(session.current_arg_text.strip())
    await session.send("---翻译结果---\n" + res[1])
def engineListToStr():
    global engine_list
    #("开" if MachineTransApi['google']['switch'] else "关")
    """
        name = {
            'nick':'引擎昵称',#用于展示(帮助列表)
            "switch":MachineTransApi['tencent']['switch'],#是否启用
            'bucket':TokenBucket(5,10),#速率限制的桶（一秒获取5次机会，最高存储10次使用机会）
            ...
        }
    """
    msg = ''
    for eg in engine_list.values():
        msg = msg + "{nick}({switch}) ".format(
            nick = eg['option']['nick'],
            switch = ("开" if eg['option']['switch'] else "关")
            )
    return msg
@on_command('mtranshelp',aliases=['翻译帮助','机翻帮助'],only_to_me = False)
async def mtranshelp(session: CommandSession):
    if not headdeal(session):
        return
    logger.info(CQsessionToStr(session))
    msg = '--机器翻译帮助--' + "\n"
    msg = msg + '!翻译设置 引擎 源语言 目标语言 -设置翻译 可以在私聊设置' + "\n"
    msg = msg + '!翻译 翻译内容 - 翻译指定内容' + "\n"
    msg = msg + '引擎支持：' + engineListToStr() + "\n"
    msg = msg + '语言支持：中日英韩，源语言额外支持自动' + "\n"
    msg = msg + '翻译设置每人独立，源和目标语言设置时可忽略，默认为自动翻译到中文' + "\n"
    msg = msg + '如有疑问或bug报告可以!反馈 反馈内容 进行反馈'
    await session.send(msg)