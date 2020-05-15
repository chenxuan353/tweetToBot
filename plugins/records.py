from nonebot import on_command, CommandSession,permission as perm
import asyncio
from helper import commandHeadtail,getlogger,msgSendToBot,CQsessionToStr,data_read,data_save
logger = getlogger(__name__)
recording_filename = 'recording.json'
recording_val = {
    'cout_id':0, #自增的记录ID
    'data':{} #数据
}
__plugin_name__ = '反馈与记录'
__plugin_usage__ = r"""

"""
def read_recording():
    global recording_val
    res = data_read(recording_filename)
    if res[0]:
        logger.info('记录读取成功')
        recording_val = res[1]

read_recording()
# on_command 装饰器将函数声明为一个命令处理器
@on_command('feedback',aliases=['反馈','Feedback'],permission=perm.SUPERUSER | perm.PRIVATE_FRIEND | perm.GROUP_ADMIN | perm.GROUP_OWNER,only_to_me = False)
async def feedback(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg == '':
        await session.send('参数为空！')
        return
    s = 'cmd:'+session.event['raw_message']+ \
        ' ;self_id:'+str(session.event['self_id']) + \
        ' ;message_type:'+session.event['message_type']+ \
        ' ;send_id:'+str(session.event['user_id']) if session.event['message_type']=='private' else str(session.event['group_id'])+ \
        ' ;text:'+stripped_arg
    logger.warning(s)
    await session.send('已收到反馈')

async def save_recording():
    data_save(recording_filename,recording_val)
@on_command('recording',aliases=['记录','Recording','rec'],permission=perm.SUPERUSER,only_to_me = False)
async def recording(session: CommandSession):
    await asyncio.sleep(0.2)
    await session.send('我爪巴')