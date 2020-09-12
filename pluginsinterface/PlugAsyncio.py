# -*- coding: UTF-8 -*-
from pluginsinterface.EventHandling import StandEven
from pluginsinterface.Plugmanagement import async_send_even
import asyncio
import traceback
import threading
from helper import getlogger
logger = getlogger(__name__)

runinfo = {
    'run': False,
    'threading': None,
    'loop': asyncio.new_event_loop(),
    'queue': None
}


async def __even_put(runinfo, even: StandEven):
    return await runinfo['queue'].put(even)


def even_put(even: StandEven):
    global runinfo
    if runinfo['run']:
        asyncio.run_coroutine_threadsafe(__even_put(runinfo, even),
                                         runinfo['loop'])
    return


async def __evendeal(queue):
    while True:
        even = await queue.get()
        try:
            await async_send_even(even)
        except:
            s = traceback.format_exc(limit=10)
            logger.error(s)
            logger.error('出现这条消息表明模块出现异常')
        queue.task_done()


def __runAsyncioTask(runinfo):
    #设置事件循环
    asyncio.set_event_loop(runinfo['loop'])
    runinfo['queue'] = asyncio.Queue(128)
    runinfo['loop'].run_forever()


def RunLoop():
    """
        启动插件处理循环
    """
    global runinfo
    runinfo['threading'] = threading.Thread(group=None,
                                            target=__runAsyncioTask,
                                            args=(runinfo, ),
                                            name='PlugAsyncio_thread',
                                            daemon=True)
    runinfo['threading'].start()
    logger.info('插件事件处理循环启动...')
    asyncio.run_coroutine_threadsafe(__evendeal(runinfo['queue']),
                                     runinfo['loop'])
    runinfo['run'] = True
