import module.twitter as tweetListener
from nonebot import on_command, CommandSession, permission
from helper import commandHeadtail
#推送列表的引用-尚不明确有无效果
push_list : tweetListener.PushList = tweetListener.get_pushList()



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
    unit = push_list.baleToPushunit(message_type,sent_id,'805435112259096576','增删测试',none_template="$tweet_nick这个人发推了,爪巴")
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
    s = push_list.delPushunit('805435112259096576',message_type,sent_id)
    await session.send(s)

@on_command('delalltest', permission=permission.SUPERUSER,only_to_me = False)
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
    push_list.push_list_del(message_type,sent_id)
    await session.send('done!')

@on_command('getpushlist',only_to_me = False)
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
    sent_id = str(sent_id)
    s = push_list.get_pushlist(message_type,sent_id)
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
    res = decode_b64(stripped_arg)
    if res == -1:
        await session.send("缩写推特ID不正确")
        return
    await session.send("推特ID为："+str(res))
    #parameter = commandHeadtail(stripped_arg)
@on_command('entweetid',only_to_me = False)
async def encodetweetid(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
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