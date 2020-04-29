# -*- coding: UTF-8 -*-
from nonebot.default_config import *
#添加超级管理员 Q号-数值 例:SUPERUSERS.add(12345678)
SUPERUSERS.add()
#命令起始标识
COMMAND_START = {'!','！'}
#bot称呼-暂无作用
NICKNAME = {'bot', 'bot哥', '工具人', '最菜群友'}

#图片发送目录默认在酷Q 图片文件夹的tweet文件夹内,图片下载文件夹在脚本运行目录的cache文件夹内的tweet文件夹
#可以使用符号链接链接两个目录
#推特基本检测ID，用于维持推特流正常运行(流中至少包括一个监测对象,不影响事件推送)
#2006101 这是yagoo(tanigox)的UID
base_tweet_id = '2006101' 
#推特API代理(127.0.0.1:8080)
api_proxy = ""

#默认botQQ 重要信息及未分类信息将推送至此QQ，为空可能导致错误
default_bot_QQ = 
#bot错误信息推送到的Q号，为空时不进行推送
bot_error_printID = 
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