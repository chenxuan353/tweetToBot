# -*- coding: UTF-8 -*-
from nonebot.default_config import *
#也可以在此处对nonebot进行设置

#超级管理员，拥有最高权限
SUPERUSERS.add(123456) #多个就复制多行

#命令起始标识
COMMAND_START = {'!','！'}

#nonebot的debug开关
DEBUG = True
#nonebot的监听地址与启动端口
NONEBOT_HOST = '0.0.0.0'
NONEBOT_PORT = 8190

#默认botQQ 默认推送用的bot，错误信息会使用此bot推送。
default_bot_QQ = ''
bot_waring_printID = '' #bot警告信息推送到的Q号，为None时不进行推送

#自动消息推送开关
feedback_push_switch : bool = True #推送反馈信息
error_push_switch : bool = True #推送错误信息

#推特更新检测方法(TweetApi,RSShub,Twint) - 暂不支持twint
UPDATA_METHOD = "RSShub"

#烤推图片路径(用于支持酷Q远程连接) 路径：{trans_img_path}/transtweet/transimg/file
trans_img_path = 'pycache_test' #可以是本地路径 也可以是远程路径 本地路径时无法远程连接bot(需要软链接)
#图片发送超时时间
img_time_out : str= '15' #图片下载超时时间(秒)

#RSShub推送配置
#基础地址 https://rsshub.app http://192.168.71.150:1300
RSShub_base = 'https://rsshub.app' #默认是公用的https://rsshub.app
RSShub_proxy = '' #代理地址
RSShub_updata_interval = 300 #更新间隔-秒(每个监测对象会多消耗1秒以上的时间)
RSShub_silent_start = False #静默启动，启动时不检测更新

#twitter_api需填写
#推特API代理
api_proxy = "127.0.0.1:10809"
#填写twitter提供的开发Key和secret
consumer_key = '7yZj***************cN31d'
consumer_secret = 'fIgX******************************SJ'
access_token = '848*************************************qapA'
access_token_secret = 'ShW****************************************oy'

#推送开关默认设置(每个选项默认值不能缺失，否则将影响运行)
pushunit_default_config = {
    'upimg':0,#是否连带图片显示(默认不带)-发推有效,转推及评论等事件则无效

    #推特推送模版(为空使用默认模版)
    'retweet_template':'',
    'quoted_template':'',
    'reply_to_status_template':'',
    'reply_to_user_template':'', 
    'none_template':'',
    
    #推特推送开关
    'retweet':0,#转推(默认不开启)
    'quoted':1,#带评论转推(默认开启)
    'reply_to_status':1,#回复(默认开启)
    #'reply_to_status_limit':0,#智能回复推送(默认关闭)-开启后仅推送监测人与有足够被关注数的人的回复
    'reply_to_user':1,#提及某人-多数时候是被提及但是被提及不会接收(默认开启)
    'none':1,#发推(默认开启)

    #个人信息变化推送(非实时)
    'change_ID':0, #ID修改(默认关闭)
    'change_name':1, #昵称修改(默认开启)
    'change_description':0, #描述修改(默认关闭)
    'change_headimgchange':1, #头像更改(默认开启)
}

