from nonebot import on_command, CommandSession,permission as perm
import asyncio
from helper import getlogger,msgSendToBot,data_read,data_save,argDeal
from module.permissiongroup import perm_getPermList,perm_getPermGroupList,hasPermGroup,perm_getGroup,perm_check,perm_add,perm_del,legalPermissionList
logger = getlogger(__name__)
__plugin_name__ = '权限组'
__plugin_usage__ = r"""
    权限管理插件
"""
@on_command('legalGroupList',aliases=['合法权限组列表'],permission=perm.SUPERUSER,only_to_me = True)
async def legalGroupList(session: CommandSession):
    message_type = session.event['message_type']
    if message_type != 'private':
        return
    global legalPermissionList
    if legalPermissionList == []:
        await session.send("权限组列表为空！")
        return
    s = "权限组列表："
    for key,permlist in legalPermissionList.items():
        s = s + "\n" + key + "(" + permlist['name'] + ")"
    await session.send(s)
@on_command('legalPermList',aliases=['合法权限列表'],permission=perm.SUPERUSER,only_to_me = True)
async def legalPermList(session: CommandSession):
    message_type = session.event['message_type']
    if message_type != 'private':
        return
    logger.info(CQsessionToStr(session))
    arglimit = [
        {
            'name':'groupname', #参数名
            'des':'权限组名', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
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
    permlist = perm_getGroup(args['groupname'])
    if permlist == None:
        await session.send("权限组不存在！")
        return
    s = "权限ID：" + permlist['name'] + "\n" + \
        "描述：" + permlist['des'] + "\n" + \
        "---权限列表---"
    for g in permlist['perms']:
        s = s + "\n" + g
    await session.send(s)


def perm_GroupListToStr(grouplist):
    msg = ""
    for group in grouplist:
        msg = msg + group['groupname'] + ','
        if group['info'] != None:
            msg = msg + group['info']['des']
        else:
            msg = msg + "无描述"
        msg = msg + '\n'
    msg = msg + '总计：' + str(len(grouplist))
    return msg
@on_command('permGroupList',aliases=['权限组列表'],permission=perm.SUPERUSER,only_to_me = True)
async def permgroupList(session: CommandSession):
    message_type = session.event['message_type']
    #group_id = (session.event['group_id'] if message_type == 'group' else None)
    user_id = session.event['user_id']
    if message_type != 'private':
        return
    logger.info(CQsessionToStr(session))
    arglimit = [
        {
            'name':'msgtype', #参数名
            'des':'消息类型', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':True, #是否转换为小写
            'default':message_type, #默认值
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
            'default':user_id, #默认值
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
    res = perm_getPermGroupList(args['msgtype'],args['send_id'])
    if not res[0]:
        await session.send(res[1])
        return
    s = perm_GroupListToStr(res[2])
    await session.send(s)

def perm_GroupToStr(groupname,PermList,info = None):
    msg = groupname
    if info == None:
        info = perm_getGroup(groupname)
    if info != None:
        msg = msg + '(' + info['des'] + ')'
    else:
        msg = msg + '(无描述)'
    msg = msg + "\n"
    for unit in PermList:
        msg = msg + ('+' if unit[:1] != '-' else '') + unit + "\n"
    msg = msg + '总计：' + str(len(PermList))
    return msg
@on_command('permList',aliases=['权限列表'],permission=perm.SUPERUSER,only_to_me = True)
async def permList(session: CommandSession):
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
            'name':'groupname', #参数名
            'des':'权限组名', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
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
            'name':'msgtype', #参数名
            'des':'消息类型', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':True, #是否转换为小写
            'default':message_type, #默认值
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
            'default':user_id, #默认值
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
    res = perm_getPermList(args['msgtype'],args['send_id'],args['groupname'])
    if not res[0]:
        await session.send(res[1])
        return
    s = perm_GroupToStr(args['groupname'],res[2]['permlist'],res[2]['info'])
    await session.send(s)

@on_command('permAdd',aliases=['添加权限'],permission=perm.SUPERUSER,only_to_me = True)
async def permAdd(session: CommandSession):
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
            'name':'groupname', #参数名
            'des':'权限组名', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
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
            'name':'perm_unit', #参数名
            'des':'权限组名', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':'', #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
            }
        },
        {
            'name':'msgtype', #参数名
            'des':'消息类型', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':True, #是否转换为小写
            'default':message_type, #默认值
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
            'default':user_id, #默认值
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
    if args['perm_unit'] == '':
        args['perm_unit'] = None

    if perm_check(args['msgtype'],args['send_id'],args['groupname'],args['perm_unit']):
        await session.send("该权限已存在！")
        return
    res = perm_add(args['msgtype'],args['send_id'],user_id,args['groupname'],args['perm_unit'])
    await session.send(res[1])

@on_command('permDel',aliases=['移除权限'],permission=perm.SUPERUSER,only_to_me = True)
async def permDel(session: CommandSession):
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
            'name':'groupname', #参数名
            'des':'权限组名', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
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
            'name':'perm_unit', #参数名
            'des':'权限组名', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':False, #是否转换为小写
            'default':'', #默认值
            'func':None, #函数，当存在时使用函数进行二次处理
            're':None, #正则表达式匹配(match函数)
            'vlimit':{ 
                #参数限制表(限制参数内容,空表则不限制),'*':''表示匹配任意字符串,值不为空时任意字符串将被转变为这个值
            }
        },
        {
            'name':'msgtype', #参数名
            'des':'消息类型', #参数错误描述
            'type':'str', #参数类型int float str list dict (list与dict需要使用函数或正则表达式进行二次处理)
            'strip':True, #是否strip
            'lower':True, #是否转换为小写
            'default':message_type, #默认值
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
            'default':user_id, #默认值
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
    if args['perm_unit'] == '':
        args['perm_unit'] = None

    if perm_check(args['msgtype'],args['send_id'],args['groupname'],args['perm_unit']):
        await session.send("该权限已存在！")
        return
    res = perm_del(args['msgtype'],args['send_id'],user_id,args['groupname'],args['perm_unit'])
    await session.send(res[1])




































