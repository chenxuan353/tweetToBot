from nonebot.default_config import *
#也可以在此处对nonebot进行设置

#全局管理员
SUPERUSERS = {
    #12345,
    #...,
}
#命令起始标识
COMMAND_START = {'!','！'}
#nonebot的debug开关
DEBUG = False
#nonebot的监听地址与启动端口
NONEBOT_HOST = '0.0.0.0'
NONEBOT_PORT = 8190

#有命令在运行时的显示
SESSION_RUNNING_EXPRESSION = '您有命令正在运行！'