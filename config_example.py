# -*- coding: UTF-8 -*-
"""
全局配置
"""
#启用debug信息
DEBUG = False
#当前支持bot，cqhttp、dingding(待支持)
#是否启用(nonebot使用ws连接，可多对一)
nonebot = True
NONEBOT_HOST = '0.0.0.0'
NONEBOT_PORT = 8091

#插件Session过期时间(单位s)
Session_timeout = 300
#插件管理者
PLUGADMIN = {
    #腾讯QQ
    'cqhttp':[
        12345,
    ],
    #钉钉
    'dingding':[

    ]
}

#维护信息，用于生成help帮助
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
翻译引擎配置
腾讯(tencent)->需要API及SDK
谷歌(google)->可能无法使用(人机验证)
"""
MachineTrans_default = 'google' #默认翻译引擎
MachineTransApi = {
    'tencent':{
        #使用腾讯云SDK，SDK未安装时无法使用
        #pip install tencentcloud-sdk-python
        "switch":False,#开关，配置完成后请设置为True,关闭为False
        #地区 ap-guangzhou->广州 ap-hongkong->香港 na-ashburn->美国(靠近纽约)
        #更多详见 https://cloud.tencent.com/document/api/551/15615#.E5.9C.B0.E5.9F.9F.E5.88.97.E8.A1.A8
        "Region":"ap-guangzhou",
        "key":"AK****************************8KI",
        "secret":"sW************************w8"
    },
    'google':{
        "switch":True,#开关
    }
}


"""
推特API配置
"""
#是否启用推送功能(关闭后无法使用所有推送相关功能)
twitterpush = True
#是否启用流式侦听辅助(ApiStream)
#注：可以大幅增强指定监听对象的推送速度，被动推送能完整运行
twitterStream = False

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
polling_level = 5 #默认轮询优先级(5则为五轮监测一次)，不建议修改，范围0-15
polling_interval = 1 #轮间监测间隔 单位秒，建议值1-15，实际默认间隔约为 polling_level*polling_interval
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

"""
RSShub推送配置
"""
#是否启用RSS订阅
RSS_open = True
#RSS代理配置
RSS_proxy = '' #127.0.0.1:10809
RSS_level = 5 #默认轮询优先级(5则为五轮监测一次)，不建议修改，范围0-15
RSS_interval = 5 #轮间监测间隔 单位秒，建议值1-15，实际默认间隔约为 轮询优先级*轮间监测间隔
#RSShub地址(支持多个)
RSShub_urls = [
    'https://rsshub.app',
]