# -*- coding: UTF-8 -*-
from nonebot.default_config import *
#也可以在此处对nonebot进行设置

#添加超级管理员 Q号-数值 例:SUPERUSERS.add(12345678)
SUPERUSERS.add(12345)
#命令起始标识
COMMAND_START = {'!','！'}
#bot称呼-暂无作用
NICKNAME = {'bot', 'bot哥', '工具人', '最菜群友'}
#nonebot的debug开关
DEBUG = True
#nonebot的监听地址与启动端口
NONEBOT_HOST:str = '0.0.0.0'
NONEBOT_PORT:int = 7000
#推特更新检测方法(twitter_api-推特API,twint-暂未开发)
UPDATA_METHOD = "twitter_api"

#图片发送站点（烤推机图片发送需要，可以是本地相对与酷Q图片发送目录的路径，酷Q远程链接时必须为站点地址）
trans_img_path = '' # https://xxx.xxx.com/
#图片发送超时时间
img_time_out : str= '15' #图片下载超时时间(秒)

#使用推特API必填，用于维持推特流正常运行(至少包括一个监测对象,不影响事件推送)
#不使用推特API时请设置为None或为空 例:base_tweet_id = None 或者 base_tweet_id = ''
base_tweet_id = '2006101'  #2006101 这是yagoo(tanigox)的UID
api_proxy = "" #推特API代理(127.0.0.1:8080)

#默认botQQ 默认推送用的bot，错误信息会使用此bot推送。请务必保持此账号能连接到nonebot
default_bot_QQ : int = 123456
#bot错误信息推送到的Q号，为空时不进行推送
bot_error_printID : int = 123456
#填写twitter提供的开发Key和secret
consumer_key = '********************'
consumer_secret = '********************'
access_token = '********************-********************'
access_token_secret = '********************'

#推送开关默认设置(每个选项默认值不能缺失，否则将影响运行)
pushunit_default_config = {
    'upimg':0,#是否连带图片显示(默认不带)-发推有效,转推及评论等事件则无效

    #推特推送模版
    'retweet_template':'',
    'quoted_template':'',
    'reply_to_status_template':'',
    'reply_to_user_template':'', 
    'none_template':'',
    
    #推特推送开关
    'retweet':0,#转推(默认不开启)
    'quoted':1,#带评论转推(默认开启)
    'reply_to_status':1,#回复(默认开启)
    'reply_to_user':1,#提及某人-多数时候是被提及但是被提及不会接收(默认开启)
    'none':1,#发推(默认开启)

    #个人信息变化推送(非实时)
    'change_ID':0, #ID修改(默认关闭)
    'change_name':1, #昵称修改(默认开启)
    'change_description':0, #描述修改(默认关闭)
    'change_headimgchange':1, #头像更改(默认开启)
}
#自定义烤推标识
transtemplate = {
    12345:'<p dir="auto" style="color:#1DA1F2;font-size:0.7em;font-weight: 600;">翻译自日文</p>',
}
