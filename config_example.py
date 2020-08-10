# -*- coding: UTF-8 -*-
from nonebot.default_config import *
#也可以在此处对nonebot进行设置
#不需要修改的设置
SESSION_RUNNING_EXPRESSION = ''

#nonebot的监听地址与启动端口
NONEBOT_HOST = '0.0.0.0'
NONEBOT_PORT = 8190
#nonebot的debug开关
DEBUG = True

#超级管理员，拥有最高权限(多个用逗号分割)
SUPERUSERS=[123456,1234567]

#命令起始标识
COMMAND_START = {'!','！'}

#维护信息
mastername = "" #维护者，例：XX(QQ123456)
project_des = "" #项目描述
project_addr = "" #项目地址，例：https://www.baidu.com

"""
烤推配置
"""
#烤推图片远程地址，为空时地址不显示(例：https://a.com/trans)
#本地存储路径为cache/transtweet/transimg
trans_img_path = ""

"""
推特API配置
"""
#API代理
api_proxy = "" #127.0.0.1:10809
#填写twitter提供的开发Key和secret
consumer_key = '7yZj***************d'
consumer_secret = 'fIgX******************************SJ'
access_token = '848*************************************A'
access_token_secret = 'ShW****************************************oy'

#pollingTwitterApi可填写的多个应用密钥对 -> ['key','secret']
#推特API应用轮询系统，可增加请求量
polling_silent_start = False #静默启动，启动时不检测更新
polling_interval = 60 #轮询监测间隔 单位秒，每对API速率限制约为1.5次每秒(建议60秒及以上)
polling_consumers = [
    #示例 ['7*********************d','fIgX*****************************SJ'],
    [consumer_key,consumer_secret],#基础密钥对，删除影响运行
    #['******************','********************************************'],
]

#默认推送模版
pushunit_default_config = {
    #是否连带图片显示(默认不带)-发推有效,转推及评论等事件则无效
    'upimg':0,
    'template':'',#推特推送模版(为空使用默认模版)
    #推送选项
    'push':{
        #推特推送开关
        'retweet':0,#转推(默认不开启)
        'quoted':1,#带评论转推(默认开启)
        'reply_to_status':1,#回复(默认开启)
        'reply_to_user':1,#提及某人-多数时候是被提及但是被提及不会接收(默认开启)
        'none':1,#发推(默认开启)

        #智能推送(仅限推送单元设置，无法全局设置)
        'ai_retweet':0,#智能推送本人转推(默认不开启)-转发值得关注的人的推特时推送
        'ai_reply_to_status':0,#智能推送本人回复(默认不开启)-回复值得关注的人时推送
        'ai_passive_reply_to_status':0,#智能推送 被 回复(默认不开启)-被值得关注的人回复时推送
        'ai_passive_quoted':0,#智能推送 被 带评论转推(默认不开启)-被值得关注的人带评论转推时推送
        'ai_passive_reply_to_user':0,#智能推送 被 提及(默认不开启)-被值得关注的人提及时推送

        #个人信息变化推送(非实时)
        'change_ID':0, #ID修改(默认关闭)
        'change_name':1, #昵称修改(默认开启)
        'change_description':0, #描述修改(默认关闭)
        'change_headimg':1, #头像更改(默认开启)
        'change_followers':1, #每N千粉推送一次关注数据(默认开启)
    }
}