from pluginsinterface.Plugmanagement import on_message,MsgTypeEnum,StandEven
from helper import getlogger
logger = getlogger(__name__)

@on_message(msgfilter='!233')
def _(even:StandEven):
    even.send('233')

@on_message(msgfilter='!爪巴')
def _(even:StandEven):
    even.send('呜呜呜,这就爬')

@on_message(msgfilter='!复读')
def _(even:StandEven):
    even.send(even.arg.strip())