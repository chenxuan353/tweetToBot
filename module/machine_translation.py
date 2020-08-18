# -*- coding: UTF-8 -*-
from helper import getlogger,TokenBucket,arglimitdeal
import config
import requests
import random
import json
import traceback
logger = getlogger(__name__)
"""
机翻类，用于支持多引擎机翻
"""

MachineTransApi = config.MachineTransApi

def randUserAgent():
    UAs = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2919.83 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2866.71 Safari/537.36',
        'Mozilla/5.0 (X11; Ubuntu; Linux i686 on x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2820.59 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
    ]
    return UAs[random.randint(0,len(UAs)-1)]

#通用翻译语言(参数解析表)
allow_st = {
    'Source':arglimitdeal({
        'auto':['自动识别','自动'],
        'zh':['简体中文','中文','简中','中'],
        #'zh-TW':['繁体中文','繁中'],
        'en':['英语','英'],
        'ja':['日语','日'],
        'ko':['韩语','韩'],
    }),
    'Target':arglimitdeal({
        'zh':['简体中文','中文','简中','中'],
        #'zh-TW':['繁体中文','繁中'],
        'en':['英语','英'],
        'ja':['日语','日'],
        'ko':['韩语','韩'],
    })
}
allow_st['Source'][''] = 'auto'
allow_st['Target'][''] = 'zh'
#引擎参数解析对照表
engine_nick = {
    '':'tencent',
    'tencent':'tencent','腾讯':'tencent',
    'google':'google','谷歌翻译':'google','谷歌':'google',
}
#引擎设置
"""
    name = {
        'nick':'引擎昵称',#用于展示(帮助列表)
        "switch":MachineTransApi['tencent']['switch'],#是否启用
        'bucket':TokenBucket(5,10),#速率限制的桶（一秒获取5次机会，最高存储10次使用机会）
        ...
    }
"""

#使用腾讯云SDK，SDK未安装时无法使用
#pip install tencentcloud-sdk-python
tencent = {
    'nick':"腾讯",
    "switch":MachineTransApi['tencent']['switch'],
    'bucket':TokenBucket(5,5),
    #地区 ap-guangzhou->广州 ap-hongkong->香港
    #更多详见 https://cloud.tencent.com/document/api/551/15615#.E5.9C.B0.E5.9F.9F.E5.88.97.E8.A1.A8
    'Region':MachineTransApi['tencent']['Region'],
    'key':MachineTransApi['tencent']['key'],
    'secret':MachineTransApi['tencent']['secret'],
}
#源文本，源文本语言，翻译到 返回值(是否成功，结果文本/错误说明，返回的源数据)
def tencent_MachineTrans(SourceText:str,Source = 'auto',Target = 'zh'):
    if not tencent['switch']:
        return (False,'错误，当前引擎未启用！')
    if not tencent['bucket'].consume(1):
        return (False,'错误，速率限制！')
    try:
        from tencentcloud.common import credential
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
        from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException 
        from tencentcloud.tmt.v20180321 import tmt_client, models
    except:
        logger.warning('腾讯SDK未安装，无法使用腾讯翻译！')
        return (False,'错误，未找到腾讯SDK！')
    try: 
        cred = credential.Credential(tencent['key'], tencent['secret']) 
        httpProfile = HttpProfile()
        httpProfile.endpoint = "tmt.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile

        client = tmt_client.TmtClient(cred, tencent['Region'], clientProfile) 

        req = models.TextTranslateRequest()
        
        req.SourceText = SourceText.replace("\n","\\n")
        req.Source = Source
        req.Target = Target
        req.ProjectId = 0
        req.UntranslatedText = "\\n"
        resp = client.TextTranslate(req)
        return (True,resp.TargetText.replace("\\n","\n"),resp)
    except TencentCloudSDKException as err: 
        logger.error(err)
        return (False,'获取结果时错误',err) 

google = {
    'nick':"谷歌",
    "switch":MachineTransApi['google']['switch'],
    'bucket':TokenBucket(5,5),
    'url':"http://translate.google.cn/translate_a/single?client=at&dt=t&dj=1&ie=UTF-8&sl={Source}&tl={Target}&q={SourceText}"
}
def google_MachineTrans(SourceText,Source = 'auto',Target = 'zh'):
    if not google['switch']:
        return (False,'错误，当前引擎未启用！')
    if not google['bucket'].consume(1):
        return (False,'错误，速率限制！')
    headers = {
        'User-Agent':randUserAgent()
    }
    try:
        requrl = google['url'].format(SourceText=SourceText,Source=Source,Target=Target)
        r = requests.get(requrl,headers=headers)
        res = json.loads(r.text)
    except:
        s = traceback.format_exc(limit=10)
        logger.error(s)
        try:
            logger.error(r.text)
        except:
            pass
        return (False,'连接服务时异常')
    try:
        msg = ''
        for t in res['sentences']:
            msg = msg + t['trans']
    except:
        logger.error(res)
        return (False,'获取结果时异常')
    return (True,msg)



engine_list = {
    'tencent':{
        'func':tencent_MachineTrans,
        'option':tencent
    },
    'google':{
        'func':google_MachineTrans,
        'option':google
    },
}

default_engine = engine_list[engine_nick[config.MachineTrans_default]]['func']
default_engine_option = engine_list[engine_nick[config.MachineTrans_default]]['option']




