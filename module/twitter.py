# -*- coding: UTF-8 -*-
import queue
import threading
import os
import time
import string
# 图片缓存
import urllib
import traceback
# 引入配置
import config

from datetime import datetime, timedelta, timezone
from module.msgStream import SendMessage
import module.msgStream as msgStream
from helper import dictInit,dictHas,dictGet,dictSet
from helper import data_read,data_save,TempMemory,data_read_auto,file_exists,check_path
from module.PushList import PushList

# 日志输出
from helper import getlogger,check_path,data_read_auto,data_save
logger = getlogger(__name__)
logger_Event = getlogger(__name__+'_event',printCMD=False)
# 引入测试方法
try:
    #event_push
    import v3_test as test
except:
    test = None
'''
推送唯一性检验及推送流
'''
baseconfigpath = 'tweitter'
DEBUG = config.DEBUG
# 10进制与64进制互相转换(由于增速过快，缩写ID不设偏移)
def encode_b64(n:int,offset:int = 0) -> str:
    if n is None:
        return ''
    table = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_'
    result = []
    temp = n - offset
    if temp < 0:
        return ''
    if 0 == temp:
        result.append('0')
    else:
        while 0 < temp:
            result.append(table[int(temp) % 64])
            temp = int(temp)//64
    return ''.join([x for x in reversed(result)])
def decode_b64(str,offset:int = 0) -> int:
    table = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
                "6": 6, "7": 7, "8": 8, "9": 9,
                "a": 10, "b": 11, "c": 12, "d": 13, "e": 14, "f": 15, "g": 16,
                "h": 17, "i": 18, "j": 19, "k": 20, "l": 21, "m": 22, "n": 23,
                "o": 24, "p": 25, "q": 26, "r": 27, "s": 28, "t": 29, "u": 30,
                "v": 31, "w": 32, "x": 33, "y": 34, "z": 35,
                "A": 36, "B": 37, "C": 38, "D": 39, "E": 40, "F": 41, "G": 42,
                "H": 43, "I": 44, "J": 45, "K": 46, "L": 47, "M": 48, "N": 49,
                "O": 50, "P": 51, "Q": 52, "R": 53, "S": 54, "T": 55, "U": 56,
                "V": 57, "W": 58, "X": 59, "Y": 60, "Z": 61,
                "-": 62, "_": 63}
    result : int = 0
    for i in range(len(str)):
        result *= 64
        if str[i] not in table:
            return -1
        result += table[str[i]]
    return result + offset
"""
推送列表
"""
class TweePushList(PushList):
    defaulttemplate = "$ifrelate $nick $typestr了 $relate_user_name 的推文$else $nick的推特更新了$end：\n$text $imgs $relatestart\n---------------\n$relate_text $relate_imgs$relateend\n跟推延时：$senddur\n链接：$link\n临时推文ID：#$tempID"
    pushunit_base_config = {
        # 是否连带图片显示(默认不带)-发推有效,转推及评论等事件则无效
        'upimg':0,
        # 对象自定义选项
        #'unit':{
        #    #'nick':'',
        #    #'des':'',
        #},
        'template':'',# 推特推送模版(为空使用默认模版)
        # 推送选项(注释则不推送)
        'push':{
            # 推特推送开关
            'retweet':0,# 转推(默认不开启)
            'quoted':1,# 带评论转推(默认开启)
            'reply_to_status':1,# 回复(默认开启)
            'reply_to_user':1,# 提及某人-多数时候是被提及但是被提及不会接收(默认开启)
            'none':1,# 发推(默认开启)

            # 智能推送(仅限推送单元设置，无法全局设置)
            'ai_retweet':0,# 智能推送本人转推(默认不开启)-转发值得关注的人的推特时推送
            'ai_reply_to_status':0,# 智能推送本人回复(默认不开启)-回复值得关注的人时推送
            'ai_passive_reply_to_status':0,# 智能推送 被 回复(默认不开启)-被值得关注的人回复时推送
            'ai_passive_quoted':0,# 智能推送 被 带评论转推(默认不开启)-被值得关注的人带评论转推时推送
            'ai_passive_reply_to_user':0,# 智能推送 被 提及(默认不开启)-被值得关注的人提及时推送

            # 个人信息变化推送(非实时)
            'change_ID':0, # ID修改(默认关闭)
            'change_name':1, # 昵称修改(默认开启)
            'change_description':0, # 描述修改(默认关闭)
            'change_headimg':1, # 头像更改(默认开启)
            'change_followers':1, # 每N千粉推送一次关注数据(默认开启)
        }
    }
    # 推送单元允许编辑的配置_布尔类型
    Pushunit_allowEdit = (
        # 携带图片发送
        'upimg',
        # 消息模版
        'retweet_template','quoted_template','reply_to_status_template',
        'reply_to_user_template','none_template',
        # 推特转发各类型开关
        'retweet','quoted','reply_to_status',
        'reply_to_user','none',

        # 智能推送(仅限推送单元设置，无法全局设置)
        'ai_retweet',
        'ai_reply_to_status',
        'ai_passive_reply_to_status',
        'ai_passive_quoted',
        'ai_passive_reply_to_user',

        # 推特个人信息变动推送开关
        'change_ID','change_name','change_description',
        'change_headimg','change_followers'
        )
    def __init__(self,init:bool = False,fileprefix:str = 'pushs',pushtype:str = 'tweet',baseconfigpath = baseconfigpath):
        super().__init__(pushtype,fileprefix + '_' + pushtype + '.json',basepath = baseconfigpath)
        self.baseconfigpath = baseconfigpath
        self.PushTemplate = {}
        self.pushunit_default_config = self.pushunit_base_config.copy()
        self.pushunit_default_config.update(config.pushunit_default_config)
        if 'diy' in self.pushunit_default_config:
            del self.pushunit_default_config['diy']
        if self.pushunit_default_config['template'].strip() == '':
            self.pushunit_default_config['template'] = self.defaulttemplate
        self.pushTemplateFile = fileprefix + '_' + pushtype + '_PTL.json'
        self.init()# 初始化推送列表(包含自动读取)
    def init(self):
        super().init()
        self.pushTemplateLoad()
    def pushTemplateSave(self,filename:str = None,path:str = 'config') -> tuple:
        if not filename:
            filename = self.pushTemplateFile
        return data_save(filename,self.push_list,path)
    def pushTemplateLoad(self,filename:str = None,path:str = 'config') -> tuple:
        if not filename:
            filename = self.pushTemplateFile
        data = data_read(filename,path)
        if data[0] is True:
            self.PushTemplate = data[2]
            return (True,data[1])
        return data

    # 打包成推送单元中()
    def baleToPushUnit(self,
                        bottype:str,
                        botuuid:str,
                        receivegroup:str,
                        receiveuuid:str,
                        spyuuid:str,
                        pushconfig:dict,
                        create_opuuid:int,
                        create_timestamp:int,
                        lastedit_opuuid:int,
                        lastedit_timestamp:int,
                        receiveobj = None,
                        pushobj = None,
                        spyobj = None,
                        createobj = None,
                        lasteditobj = None
                        ):

        return super().baleToPushUnit(bottype,botuuid,receivegroup,
                        receiveuuid,
                        spyuuid,
                        pushconfig,
                        create_opuuid,
                        create_timestamp,
                        lastedit_opuuid,
                        lastedit_timestamp,
                        receiveobj,
                        pushobj,
                        spyobj,
                        createobj,
                        lasteditobj)

    def addPushunit(self,pushunit:dict):
        return super().addPushunit(pushunit,self.pushunit_default_config)

    # 添加与删除模版及模版管理
    def pushTemplateAddCover(self,name,config:dict):
        config = config.copy()
        self.PushTemplate[name] = config
        self.pushTemplateSave()
        return (True,'模版已保存')
    def pushTemplateAdd(self,name,config):
        config = config.copy()
        # 保存推送设置模版
        if name in self.PushTemplate:
            return (False,'模版重名！')
        self.PushTemplate[name] = config
        self.pushTemplateSave()
        return (True,'模版已保存')
    def pushTemplateDel(self,name):
        if name not in self.PushTemplate:
            return (False,'模版不存在！')
        del self.PushTemplate[name]
        self.pushTemplateSave()
        return (True,'模版成功删除')

    # 模版设置
    def pushTemplateApplyAll(self,name,target:dict):
        if name not in self.PushTemplate:
            return (False,'模版不存在！')
        target.update(self.PushTemplate[name])
        return (True,'设置成功')
    def pushTemplateApplyTemplate(self,name,target:dict):
        if name not in self.PushTemplate:
            return (False,'模版不存在！')
        target.update({'template':self.PushTemplate[name]['template']})
        return (True,'设置成功')
    def pushTemplateApplyPush(self,name,target:dict):
        if name not in self.PushTemplate:
            return (False,'模版不存在！')
        target.update({'push':self.PushTemplate[name]['push'].copy()})
        return (True,'设置成功')
    
    # 信息打包
    def baleForConfig(self,nick = '',des = '',upimg = None,template = None,push:dict = {}):
        res = {
            #'upimg':upimg,
            'unit':{
                'nick':nick,
                'des':des,
            },
            #'template':template,
            'push':push
        }
        if upimg is not None:
            res['upimg'] = upimg
        if template is not None:
            res['template'] = template
        return res
    # 信息获取
    def getMergeConfKey(self,pushtoconfig:dict,config:dict = None,key = None):
        mergeConf = {
            'upimg':0,
            'unit':{
                'nick':'',
                'des':'',
            },
            'template':'',
            'push':{}
        }
        mergeConf.update(self.pushunit_default_config)
        if not key:
            mergeConf['upimg'] = pushtoconfig['upimg'] if 'upimg' in pushtoconfig else mergeConf['upimg']
            mergeConf['unit'].update(pushtoconfig['unit'] if 'unit' in pushtoconfig else {})
            mergeConf['template'] = pushtoconfig['template'] if 'template' in pushtoconfig else mergeConf['template']
            mergeConf['push'].update(pushtoconfig['push'] if 'push' in pushtoconfig else {})
            if config:
                mergeConf['upimg'] = config['upimg'] if 'upimg' in config else mergeConf['upimg']
                mergeConf['unit'].update(config['unit'] if 'unit' in config else {})
                mergeConf['template'] = config['template'] if 'template' in config else mergeConf['template']
                mergeConf['push'].update(config['push'] if 'push' in config else {})
            return mergeConf
        elif key == 'upimg':
            mergeConf['upimg'] = pushtoconfig['upimg'] if 'upimg' in pushtoconfig else mergeConf['upimg']
            if config:
                mergeConf['upimg'] = config['upimg'] if 'upimg' in config else mergeConf['upimg']
            return mergeConf['upimg']
        elif key == 'template':
            mergeConf['template'] = pushtoconfig['template'] if 'template' in pushtoconfig else mergeConf['template']
            if config:
                mergeConf['template'] = config['template'] if 'template'in config else mergeConf['template']
            return mergeConf['template']
        elif key in ('nick','des'):
            mergeConf['unit'].update(pushtoconfig['unit'] if 'unit' in pushtoconfig else {})
            if config:
                mergeConf['unit'].update(config['unit'] if 'unit' in config else {})
            return mergeConf['unit'][key]
        else:
            mergeConf['push'].update(pushtoconfig['push'] if 'push' in pushtoconfig else {})
            if config:
                mergeConf['push'].update(config['push'] if 'push' in config else {})
            if key not in mergeConf['push']:
                return 0
            return mergeConf['push'][key]
    def getUnitConfKey(self,pushunit,key):
        return self.getMergeConfKey(self.getUnitPushToConfig(pushunit)['config'],pushunit['pushconfig'],key)

    # 触发器
    def pushcheck_trigger(self,unit,**pushunit) -> bool:
        return True
    def setPushToAttr_trigger(self,pushtoconfig:dict,setkey:str,setvalue) -> tuple:
        if setkey != 'upimg':
            if setkey not in self.Pushunit_allowEdit:
                return (False,'属性值不合法')
        
        if setkey == 'upimg':
            if setvalue not in (0,1):
                return (False,'设置值不合法')
            sourval = self.getMergeConfKey(pushtoconfig,key = setkey)
            pushtoconfig['upimg'] = setvalue
            return (True,'属性值已更新{0}->{1}'.format(sourval,setvalue))
        elif setkey == 'template':
            if type(setvalue) != str:
                return (False,'设置值不合法')
            sourval = self.getMergeConfKey(pushtoconfig,key = setkey)
            if sourval == '':
                sourval = '(未设置)'
            pushtoconfig['template'] = setvalue
            return (True,'属性值已更新{0}->{1}'.format(sourval,setvalue))
        else:
            if setvalue not in (0,1):
                return (False,'设置值不合法')
            sourval = self.getMergeConfKey(pushtoconfig,key = setkey)
            if 'push' not in pushtoconfig:
                pushtoconfig['push'] = {}
            pushtoconfig['push'][setkey] = setvalue
            return (True,'属性值已更新{0}->{1}'.format(sourval,setvalue))
    def setPushUnitAttr_trigger(self,pushtoconfig:dict,config:dict,setkey:str,setvalue) -> tuple:
        if setkey != 'nick' and setkey != 'des' and setkey != 'upimg':
            if setkey not in self.Pushunit_allowEdit:
                return (False,'属性值不合法')
        
        if setkey == 'upmig':
            if setvalue not in (0,1):
                return (False,'设置值不合法')
            sourval = self.getMergeConfKey(pushtoconfig,config,setkey)
            config['upimg'] = setvalue
            return (True,'属性值已更新{0}->{1}'.format(sourval,setvalue))
        elif setkey == 'template':
            if type(setvalue) != str:
                return (False,'设置值不合法')
            sourval = self.getMergeConfKey(pushtoconfig,config,setkey)
            if sourval == '':
                sourval = '(未设置)'
            config['template'] = setvalue
            return (True,'属性值已更新{0}->{1}'.format(sourval,setvalue))
        elif setkey == 'nick':
            if type(setvalue) != str:
                return (False,'设置值不合法')
            sourval = self.getMergeConfKey(pushtoconfig,config,setkey)
            if sourval == '':
                sourval = '(未设置)'
            if 'unit' not in config:
                config['unit'] = {}
            config['unit']['nick'] = setvalue
            return (True,'属性值已更新{0}->{1}'.format(sourval,setvalue))
        elif setkey == 'des':
            if type(setvalue) != str:
                return (False,'设置值不合法')
            sourval = self.getMergeConfKey(pushtoconfig,config,setkey)
            if sourval == '':
                sourval = '(未设置)'
            if 'unit' not in config:
                config['unit'] = {}
            config['unit']['des'] = setvalue
            return (True,'属性值已更新{0}->{1}'.format(sourval,setvalue))
        else:
            if setkey == 'change_followers':
                if type(setvalue) != int and setvalue >= 0 and setvalue <=100:
                    return (False,'设置值不合法')
            else:
                if setvalue not in (0,1):
                    return (False,'设置值不合法')
            sourval = self.getMergeConfKey(pushtoconfig,config,setkey)
            if 'push' not in config:
                config['push'] = {}
            config['push'][setkey] = setvalue
            return (True,'属性值已更新{0}->{1}'.format(sourval,setvalue))
"""
推特信息缓存
加入推文使用addTweetToCache
"""
class TweetCache:
    def __init__(self,baseconfigpath = baseconfigpath):
        self.baseconfigpath = baseconfigpath
        # 缩写推特ID(缓存条)
        # 单元：[缩写ID,推特ID]
        self.newTemptweetid = data_read_auto('newTemptweetid.json',default=0,path = baseconfigpath)
        self.mintweetID = TempMemory('mintweetID',path = baseconfigpath,limit = 9999,autosave = True,autoload = True)
        # 推特用户缓存(1000条)
        self.userinfolist = TempMemory('userinfolist',path = baseconfigpath,limit = 1000,autosave = False,autoload = False)
        self.tweetspath = os.path.join(baseconfigpath,'tweetscache')
        check_path(self.tweetspath)
        # 推文缓存(150条/监测对象)
        # 监测ID->缓存内容
        self.tweetscache = {}
    # 推文相关
    def __getNewID(self):
        self.newTemptweetid += 1
        if self.newTemptweetid > 9999:
            self.newTemptweetid = 1
        data_save('newTemptweetid.json',self.newTemptweetid,path = baseconfigpath)
        return self.newTemptweetid
    def getTweetTempID(self,tweetid:int):
        mintweetID = self.mintweetID
        tweetid = int(tweetid)
        item = mintweetID.find((lambda item,val: item[1] == val),tweetid)
        if item is not None:
            return item[0]
        newTemptweetid = self.__getNewID()
        mintweetID.join((newTemptweetid,tweetid))
        return newTemptweetid
    def findTweetTempID(self,tweetid:int):
        mintweetID = self.mintweetID
        tweetid = int(tweetid)
        item = mintweetID.find((lambda item,val: item[1] == val),tweetid)
        if item is not None:
            return item[0]
        return -1
    def getTweetSourceID(self,minId:int):
        """
            从临时ID获取推特原始ID
            失败返回-1
        """
        mintweetID = self.mintweetID
        minId = int(minId)
        item = mintweetID.find((lambda item,val: item[0] == val),minId)
        if item is not None:
            return item[1]
        return -1
    def addTweetToCache(self,tweetinfo):
        tweetscache = self.tweetscache
        userid = tweetinfo['user_id_str']
        # 判断缓存中是否已经存在此推文
        if self.getTweetFromCache(tweetinfo['id'],tweetinfo['user_id_str']) is not None:
            return
        if userid not in tweetscache:
            tweetscache[userid] = TempMemory(userid+'_tweets',path = self.tweetspath,limit = 150,autosave = True,autoload = True)
        if 'TempID' not in tweetinfo:
            tweetinfo['TempID'] = self.getTweetTempID(tweetinfo['id'])
        tweetscache[userid].join(tweetinfo)
    # 从缓存中获取指定用户推文列表
    def getTweetsFromCache(self,userid:str) -> TempMemory:
        tweetscache = self.tweetscache
        userid = str(userid)
        if userid not in tweetscache:
            if file_exists(os.path.join(self.tweetspath,userid+'_tweets.json')):
                tweetscache[userid] = TempMemory(userid+'_tweets',path = self.tweetspath,limit = 150,autosave = True,autoload = True)
        if userid not in tweetscache:
            return None
        return tweetscache[userid]
    def getTweetFromCache(self,tweetid:int,userid:str = None) -> dict:
        """
            尝试从缓存中获取推文，推文不存在时返回None
        """
        tweetscache = self.tweetscache
        tweetid = int(tweetid)
        if userid:
            tcache = self.getTweetsFromCache(userid)
            if not tcache:
                return None
            res = tweetscache[userid].find((lambda item,val:item['id'] == val),tweetid)
            return res
        for userid in tweetscache:
            res = tweetscache[userid].find((lambda item,val:item['id'] == val),tweetid)
            if res:
                return res
        return None
    # 用户相关
    def getUserInfo(self, userid:int = None,screen_name:str = None) -> dict:
        """
            尝试从缓存中获取用户信息,返回用户信息表
        """
        if userid:
            userid = int(userid)
            tu = self.userinfolist.find((lambda item,val:item['id'] == val),int(userid))
        elif screen_name:
            tu = self.userinfolist.find((lambda item,val:item['screen_name'] == val),screen_name)
        else:
            raise Exception("无效的参数")
        return tu
    def getUserInfoFromllikename(self, name:str) -> dict:
        """
            模糊匹配用户昵称查找用户
        """
        return self.userinfolist.find((lambda item,val:item['name'].find(val) != -1),name)

"""
status处理
"""
class TweetStatusDeal:
    def __init__(self,pushlist:TweePushList,tweetcache:TweetCache):
        self.pushlist = pushlist
        self.tweetcache = tweetcache
    # 推文包定义
    def bale_userinfo(self,
            notable,
            id,
            name,
            description,
            screen_name,
            profile_image_url,
            profile_image_url_https,
            default_profile_image,
            default_profile,
            protected,
            followers_count,
            friends_count,
            verified,
            statuses_count,
            created_at
        ):
        """
            userinfo标准字典
            {
                'version':'1.2',
                'notable':...,#用户是否值得关注
                'id':...,
                'id_str':...,
                'name':...,
                'description':...,
                'screen_name':...,
                'profile_image_url':...,
                'profile_image_url_https':...,
                'default_profile_image':...,
                'default_profile':...,
                'protected':...,
                'followers_count':...,
                'friends_count':...,
                'verified':...,
                'statuses_count':...,
                'created_at':...,
            }
        """
        userinfo = {
                'version':'1.0',
                'notable':notable,
                'id':int(id),
                'id_str':str(id),
                'name':name,
                'description':description,
                'screen_name':screen_name,
                'profile_image_url':profile_image_url,
                'profile_image_url_https':profile_image_url_https,
                'default_profile_image':default_profile_image,
                'default_profile':default_profile,
                'protected':protected,
                'followers_count':followers_count,
                'friends_count':friends_count,
                'verified':verified,
                'statuses_count':statuses_count,
                'created_at':created_at
            }
        return userinfo
    def bale_tweetinfo(self,
        tweettype,
        notable,
        createtimestamp,
        id,
        text,
        user_id,
        user_sname,
        media:list,
        userinfo:dict,
        relate_id = None,
        relate_user_id = None,
        relate_user_sname = None,
        relate_userinfo = None,
        relate_notable:bool = False,# 不存在的推文肯定不值得关注
        relate:dict = None
        ):
        """
            tweetinfo标准字典
            {
                'version':'1.2',
                'type':...,#推文标识
                'notable':...,#推文是否值得关注
                'createtimestamp':...,#创健时间戳
                'createtimestr':...,#创建时间文本
                'createtimestrsimple':...,#简化的时间文本
                'id':...,
                'id_str':...,
                'minID':...,#压缩ID
                'text':...,
                'media':{...,...},#媒体域
                'link':...,#推文链接
                'user_id':...,
                'user_id_str':...,
                'user_sname':...,#用户sname
                'userinfo':{userinfo},#用户对象
                #依赖对象(可以为空)
                'hasrelate':...,#是否存在依赖
                'relate_notable':...,#依赖是否值得重视
                'relate_id':...,#依赖的推文ID
                'relate_id_str':...,#依赖的推文ID文本
                'relate_user_id':...,#依赖的推文用户ID
                'relate_user_id_str':...,#依赖的推文用户ID文本
                'relate_user_sname':...,#依赖的推文用户名
                'relate_userinfo':{userinfo},#依赖的用户信息
                'relate':{tweetinfo},#依赖的推文
            }
            媒体域：
                media_obj['id'] = media_unit['id']
                media_obj['id_str'] = media_unit['id_str']
                media_obj['type'] = media_unit['type']
                media_obj['media_url'] = media_unit['media_url']
                media_obj['media_url_https'] = media_unit['media_url_https']
        """
        if relate is None and relate_id is not None and relate_user_sname is not None:
            res = self.tweetcache.getTweetFromCache(relate_id,relate_user_sname)
            if res is not None:
                relate = res
        if relate_userinfo is None and relate_user_id is not None and relate_user_sname is not None:
            if relate is not None:
                relate_userinfo = relate['userinfo']
            else:
                res = self.tweetcache.getUserInfo()
                if res is not None:
                    relate_userinfo = res

        tweetinfo = {
                'version':'1.2',
                'type':tweettype,
                'notable':notable,
                'createtimestamp':createtimestamp,
                'createtimestr':time.strftime("%Y{0}%m{1}%d{2} %H:%M:%S",time.localtime(createtimestamp)).format('年','月','日'),
                'createtimestrsimple':time.strftime("%H:%M:%S", time.localtime(createtimestamp)),
                'id':int(id),
                'id_str':str(id),
                'minID':encode_b64(int(id)),
                'text':str(text),
                'media':media,
                'user_id':int(user_id),
                'user_id_str':str(user_id),
                'user_sname':user_sname,
                'userinfo':userinfo,
                'link':"https://twitter.com/{0}/status/{1}".format(user_sname,id),
                # 依赖对象(可以为空)
                'hasrelate':(relate is not None),
                'relate_notable':relate_notable,
                'relate_id':(int(relate_id) if relate_id is not None else None),
                'relate_id_str':(str(relate_id) if relate_id is not None else None),
                'relate_user_id':(int(relate_user_id) if relate_user_id is not None else None),
                'relate_user_id_str':(str(relate_user_id) if relate_user_id is not None else None),
                'relate_user_sname':relate_user_sname,
                'relate':relate
            }
        return tweetinfo
    def bale_userinfo_kw(self,*,
            notable,
            id,
            name,
            description,
            screen_name,
            profile_image_url,
            profile_image_url_https,
            default_profile_image,
            default_profile,
            protected,
            followers_count,
            friends_count,
            verified,
            statuses_count,
            created_at,
            **kw
        ):
        return self.bale_userinfo(
                notable,
                id,
                name,
                description,
                screen_name,
                profile_image_url,
                profile_image_url_https,
                default_profile_image,
                default_profile,
                protected,
                followers_count,
                friends_count,
                verified,
                statuses_count,
                created_at
            )
    def bale_tweetinfo_kw(self,*,
        tweettype,
        notable,
        createtimestamp,
        id,
        text,
        user_id,
        user_sname,
        imgs:list,
        userinfo:dict,
        relate_id = None,
        relate_user_id = None,
        relate_user_sname = None,
        relate_notable:bool = False,# 不存在的推文肯定不值得关注
        relate:dict = None,
        **kw):
        relate_id:int = (kw['relate_id'] if 'relate_id' in kw else None)
        relate_user_id:int = (kw['relate_user_id'] if 'relate_user_id' in kw else None)
        relate_user_sname:str = (kw['relate_user_sname'] if 'relate_user_sname' in kw else None)
        relate_notable:dict = (kw['relate_notable'] if 'relate_notable' in kw else False) #不存在的推文肯定不值得关注
        relate:dict = (kw['relate'] if 'relate'in kw else None)
        return self.bale_tweetinfo(
                        tweettype,
                        notable,
                        createtimestamp,
                        id,
                        text,
                        user_id,
                        user_sname,
                        imgs,
                        userinfo,
                        relate_id,
                        relate_user_id,
                        relate_user_sname,
                        relate_notable,# 不存在的推文肯定不值得关注
                        relate
                    )

    # 用户是否是值得关注的(粉丝/关注 大于 5k 且修改了默认图，或粉丝大于10000)
    def isNotableUser(self,user,checkspy:bool = True):
        pushlist = self.pushlist
        if checkspy and pushlist.hasSpy(user['id_str']):
            return True
        if not user['default_profile_image'] and \
            not user['protected'] and \
            (int(user['followers_count'] / ((user['friends_count']+1))) > 5000 or user['followers_count'] > 10000):
            return True
        return False
    # 重新包装推特用户信息(用户数据，是否检查更新)
    def get_userinfo(self,user,checkspy:bool = True):
        """
            userinfo标准字典
            {
                'version':'1.2',
                'notable':...,#用户是否值得关注
                'id':...,
                'id_str':...,
                'name':...,
                'description':...,
                'screen_name':...,
                'profile_image_url':...,
                'profile_image_url_https':...,
                'default_profile_image':...,
                'default_profile':...,
                'protected':...,
                'followers_count':...,
                'friends_count':...,
                'verified':...,
                'statuses_count':...,
                'created_at':...,
            }
        """
        userinfo = {}
        userinfo['version'] = '1.2'
        userinfo['id'] = user.id
        userinfo['id_str'] = user.id_str
        userinfo['name'] = user.name
        userinfo['description'] = user.description
        userinfo['screen_name'] = user.screen_name
        userinfo['profile_image_url'] = user.profile_image_url
        userinfo['profile_image_url_https'] = user.profile_image_url_https
        userinfo['default_profile_image'] = user.default_profile_image
        userinfo['default_profile'] = user.default_profile
        userinfo['protected'] = user.protected
        userinfo['followers_count'] = user.followers_count
        userinfo['friends_count'] = user.friends_count
        userinfo['verified'] = user.verified
        userinfo['statuses_count'] = user.statuses_count
        userinfo['created_at'] = int(user.created_at.timestamp())
        userinfo['notable'] = self.isNotableUser(userinfo,checkspy)
        if userinfo['profile_image_url'].endswith('_normal.jpg'):
            userinfo['profile_image_url'] = userinfo['profile_image_url'].replace('_normal.jpg','.jpg')
        if userinfo['profile_image_url_https'].endswith('_normal.jpg'):
            userinfo['profile_image_url_https'] = userinfo['profile_image_url_https'].replace('_normal.jpg','.jpg')
        return userinfo
    def get_tweet_info(self,tweet,checkspy:bool = True):
        """
            重新包装推特信息
            tweetinfo标准字典
            {
                'version':'1.2',
                'type':...,#推文标识
                'notable':...,#推文是否值得关注
                'createtimestamp':...,#创健时间戳
                'createtimestr':...,#创建时间文本
                'createtimestrsimple':...,#简化的时间文本
                'id':...,
                'id_str':...,
                'minID':...,#压缩ID
                'text':...,
                'media':{...,...},#媒体域
                'link':...,#推文链接
                'user_id':...,
                'user_id_str':...,
                'user_sname':...,#用户sname
                'userinfo':{userinfo},#用户对象
                #依赖对象(可以为空)
                'hasrelate':...,#是否存在依赖
                'relate_notable':...,#依赖是否值得重视
                'relate_id':...,#依赖的推文ID
                'relate_id_str':...,#依赖的推文ID文本
                'relate_user_id':...,#依赖的推文用户ID
                'relate_user_id_str':...,#依赖的推文用户ID文本
                'relate_user_sname':...,#依赖的推文用户名
                'relate_userinfo':{userinfo},#依赖的用户信息
                'relate':{tweetinfo},#依赖的推文
            }
            媒体域：
                media_obj['id'] = media_unit['id']
                media_obj['id_str'] = media_unit['id_str']
                media_obj['type'] = media_unit['type']
                media_obj['media_url'] = media_unit['media_url']
                media_obj['media_url_https'] = media_unit['media_url_https']
        """
        userinfo = self.get_userinfo(tweet.user,checkspy)

        tweettext = ''
        # 尝试获取全文
        if hasattr(tweet,'extended_tweet') or hasattr(tweet,'full_text'):
            if hasattr(tweet,'full_text'):
                tweettext = tweet.full_text
            else:
                tweettext = tweet.extended_tweet['full_text']
        else:
            tweettext = tweet.text
        tweettext = tweettext.replace('&lt;','<').replace('&gt;','>')

        media = []
        if hasattr(tweet,'extended_entities'):
            # 图片来自本地媒体时将处于这个位置
            if 'media' in tweet.extended_entities:
                for media_unit in tweet.extended_entities['media']:
                    media_obj = {}
                    media_obj['id'] = media_unit['id']
                    media_obj['id_str'] = media_unit['id_str']
                    media_obj['type'] = media_unit['type']
                    media_obj['media_url'] = media_unit['media_url']
                    media_obj['media_url_https'] = media_unit['media_url_https']
                    media.append(media_obj)
        elif hasattr(tweet,'entities'):
            # 图片来自推特时将处于这个位置
            if 'media' in tweet.entities:
                for media_unit in tweet.entities['media']:
                    media_obj = {}
                    media_obj['id'] = media_unit['id']
                    media_obj['id_str'] = media_unit['id_str']
                    media_obj['type'] = media_unit['type']
                    media_obj['media_url'] = media_unit['media_url']
                    media_obj['media_url_https'] = media_unit['media_url_https']
                    media.append(media_obj)
        tweetinfo = self.bale_tweetinfo(
            'none',
            userinfo['notable'],
            tweet.created_at.replace(tzinfo=timezone(timedelta(hours=0))).timestamp(),
            tweet.id,
            tweettext,
            userinfo['id'],
            userinfo['screen_name'],
            media,
            userinfo
        )
        return tweetinfo
   
    def deal_tweet_type(self, status):
        if hasattr(status, 'retweeted_status'):
            return 'retweet' # 纯转推
        elif hasattr(status, 'quoted_status'):
            return 'quoted' # 推特内含引用推文
        elif status.in_reply_to_status_id != None:
            return 'reply_to_status' # 回复
        elif status.in_reply_to_screen_name != None:
            return 'reply_to_user' # 提及
        else:
            return 'none' # 未分类(主动发推)
    def deal_tweet(self, status) -> dict:
        """
        推文
        type:推文标识
        """
        # 监听流：本人转推、本人发推、本人转推并评论、本人回复、被转推、被回复、被提及
        tweetinfo = self.get_tweet_info(status,True)
        tweetinfo['type'] = self.deal_tweet_type(status)
        #tweetinfo['status'] = status #原始数据

        if tweetinfo['type'] == 'retweet':#大多数情况是被转推
            # 转推时被转推对象与转推对象同时值得关注时视为值得关注
            tweetinfo['relate'] = self.get_tweet_info(status.retweeted_status,True)
            tweetinfo['relate']['type'] = 'relate'
            tweetinfo['relate_id'] = tweetinfo['relate']['id']
            tweetinfo['relate_id_str'] = tweetinfo['relate']['id_str']
            tweetinfo['relate_user_id'] = tweetinfo['relate']['user_id']
            tweetinfo['relate_user_id_str'] = tweetinfo['relate']['user_id_str']
            tweetinfo['relate_user_sname'] = tweetinfo['relate']['user_sname']
            tweetinfo['relate_userinfo'] = tweetinfo['relate']['userinfo']
            tweetinfo['relate_notable'] = (tweetinfo['notable'] and tweetinfo['relate']['notable'])
        elif tweetinfo['type'] == 'quoted':
            tweetinfo['relate'] = self.get_tweet_info(status.quoted_status,True)
            tweetinfo['relate']['type'] = 'relate'
            tweetinfo['relate_id'] = tweetinfo['relate']['id']
            tweetinfo['relate_id_str'] = tweetinfo['relate']['id_str']
            tweetinfo['relate_user_id'] = tweetinfo['relate']['user_id']
            tweetinfo['relate_user_id_str'] = tweetinfo['relate']['user_id_str']
            tweetinfo['relate_user_sname'] = tweetinfo['relate']['user_sname']
            tweetinfo['relate_userinfo'] = tweetinfo['relate']['userinfo']
            tweetinfo['relate_notable'] = (tweetinfo['notable'] and tweetinfo['relate']['notable'])
        elif tweetinfo['type'] != 'none' and tweetinfo['type'] != 'reply_to_user':
            tweetinfo['hasrelate'] = True
            tweetinfo['relate'] = None
            tweetinfo['relate_id'] = status.in_reply_to_status_id
            tweetinfo['relate_id_str'] = status.in_reply_to_status_id_str
            tweetinfo['relate_user_id'] = status.in_reply_to_user_id
            tweetinfo['relate_user_id_str'] = status.in_reply_to_user_id_str
            tweetinfo['relate_user_sname'] = status.in_reply_to_screen_name
            tweetinfo['relate_userinfo'] = None
            tweetinfo['relate_notable'] = False
            res = self.tweetcache.getTweetFromCache(tweetinfo['relate_id'],tweetinfo['relate_user_sname'])
            if res is not None:
                tweetinfo['relate'] = res
            if tweetinfo['relate'] is not None:
                tweetinfo['relate_userinfo'] = tweetinfo['relate']['userinfo']
            else:
                res = self.tweetcache.getUserInfo(userid=tweetinfo['relate_id'])
                if res is not None:
                    tweetinfo['relate_userinfo'] = res
            if tweetinfo['relate_userinfo'] is not None:
                tweetinfo['relate_notable'] = tweetinfo['relate_userinfo']['notable']
            if tweetinfo['relate'] is not None:
                tweetinfo['relate_notable'] = tweetinfo['relate']['notable'] and tweetinfo['relate_notable']
            tweetinfo['relate_notable'] = tweetinfo['notable'] and tweetinfo['relate_notable']
        else:
            tweetinfo['hasrelate'] = False
            tweetinfo['relate'] = None
            tweetinfo['relate_id'] = -1
            tweetinfo['relate_id_str'] = '-1'
            tweetinfo['relate_user_id'] = -1
            tweetinfo['relate_user_id_str'] = '-1'
            tweetinfo['relate_user_sname'] = ''
            tweetinfo['relate_userinfo'] = None
            tweetinfo['relate_notable'] = False
        
        # 推文是否值得关注
        if self.pushlist.hasSpy(tweetinfo['user_id']):
            tweetinfo['tweetNotable'] = True
        else:
            tweetinfo['tweetNotable'] = (not tweetinfo['relate'] or tweetinfo['relate_notable']) and tweetinfo['notable']
        
        return {
            'notable':tweetinfo['tweetNotable'],
            'tweetinfo':tweetinfo
            }
"""
消息推送·事件处理
"""
class tweetToStrTemplate(string.Template):
    delimiter = '$'
    idpattern = '[a-z_]+'
class TweetEventDeal:
    def __init__(self,tweetstatusdeal:TweetStatusDeal,pushlist:TweePushList = None,tweetcache:TweetCache = None,baseconfigpath = baseconfigpath):
        self.baseconfigpath = baseconfigpath
        if tweetcache:
            self.tweetcache = tweetcache
        else:
            self.tweetcache = tweetstatusdeal.tweetcache
        self.tweetstatusdeal = tweetstatusdeal
        self.pushlist = pushlist
    # 用户信息更新检测
    def checkUserInfoUpdata(self,userinfo:dict) -> list:
        # 检测个人信息更新,返回更新事件集
        tweetcache = self.tweetcache
        userinfolist = tweetcache.userinfolist
        """
            运行数据比较
            用于监测用户的信息修改
            userinfo标准字典
            {
                'version':'1.2',
                'notable':...,#用户是否值得关注
                'id':...,
                'id_str':...,
                'name':...,
                'description':...,
                'screen_name':...,
                'profile_image_url':...,
                'profile_image_url_https':...,
                'default_profile_image':...,
                'default_profile':...,
                'protected':...,
                'followers_count':...,
                'friends_count':...,
                'verified':...,
                'statuses_count':...,
                'created_at':...,
            }
            data['grouptype'] = 'userupdata'
            data['unittype'] = data[1]
            data['user_id'] = userinfo['id']
            data['user_id_str'] = str(userinfo['id_str'])
            data['user_name'] = str(userinfo['name'])
            data['user_screen_name'] = str(userinfo['screen_name'])
            data['des'] = data[0]
            data['userinfo'] = userinfo.copy()
            data['oldkey'] = old_userinfo[key]
            data['newkey'] = userinfo[key]
        """
        evens = []
        old_userinfo = userinfolist.find((lambda item,val:item['id'] == val),userinfo['id'])
        if old_userinfo != None:
            def compareChanges(key,cdata):
                if key not in old_userinfo:
                    return None
                if old_userinfo[key] != userinfo[key]:
                    # 禁止粉丝数逆增长
                    if key == 'followers_count' and old_userinfo[key] >= userinfo[key]:
                        return None
                    if key == 'friends_count' and old_userinfo[key] >= userinfo[key]:
                        return None
                    data = {}
                    data['grouptype'] = 'userupdata'
                    data['unittype'] = cdata[1]
                    data['user_id'] = userinfo['id']
                    data['user_id_str'] = str(userinfo['id_str'])
                    data['user_name'] = str(userinfo['name'])
                    data['user_screen_name'] = str(userinfo['screen_name'])
                    data['des'] = cdata[0]
                    data['userinfo'] = userinfo.copy()
                    data['oldkey'] = old_userinfo[key]
                    data['newkey'] = userinfo[key]
                    old_userinfo[key] = userinfo[key]
                    if key == 'profile_image_url_https':
                        data['oldimg'] = data['oldkey']
                        data['newimg'] = data['newkey']
                        data['oldkey'] = '[旧头像]'
                        data['newkey'] = '[新头像]'
                    # 粉丝数更新仅对千整数推送事件
                    if key == 'followers_count' and old_userinfo[key] % 1000 != 0:
                        return None
                    if key not in ('friends_count','protected','verified','default_profile_image','default_profile','statuses_count'):
                        even = self.bale_event(data['grouptype'],data['unittype'],data['user_id_str'],data)
                        evens.append(even)
                        return even
                return None
            checkkeys = {
                'name':('昵称','ID'),
                'description':('描述','description'),
                'screen_name':('用户名','name'),
                'profile_image_url_https':('头像','headimg'),
                'followers_count':('粉丝数','followers'),
                # 以下仅更新，无事件
                'friends_count':('关注数','friends_count'),
                'protected':('推文受保护','protected'),
                'verified':('通过验证的账户','verified'),
                'default_profile_image':('头图','default_profile_image'),
                'default_profile':('是否是默认头图','default_profile'),
                'statuses_count':('发推数','statuses_count'),
                }
            for key in checkkeys:
                compareChanges(key,checkkeys[key])                    
        else:
            userinfolist.join(userinfo)
        return evens
    def dealSourceData(self,status,checkuser:bool = True):
        res = self.tweetstatusdeal.deal_tweet(status)
        res['userevens'] = []
        if checkuser:
            tweetinfo = res['tweetinfo']
            #notable = res['notable']
            events = self.checkUserInfoUpdata(tweetinfo['userinfo'])
            if tweetinfo['relate'] is not None:
                relateevens = self.checkUserInfoUpdata(tweetinfo['relate']['userinfo'])
                for event in relateevens:
                    events.append(event)
            res['userevens'] = events
        return res
    # 打包事件(事件组，事件元，引起变化的用户ID，事件数据)
    def bale_event(self,grouptype:str,unittype:str,spyid:str,data):
        """
            事件基本格式
            grouptype 事件组标识
            unittype 事件元标识
            spyid 触发事件的用户ID
            {
                'relate':'依赖推文',
                'retweet':'转推',
                'quoted':'转推并评论',
                'reply_to_status':'回复',
                'reply_to_user':'提及',
                'unknown':'未分类',
                'none':'发推',
                }
            {
                'name':('昵称','ID'),
                'description':('描述','description'),
                'screen_name':('昵称','name'),
                'profile_image_url_https':('头像','headimg'),
                'followers_count':('粉丝数','followers')
                }
        """
        allow_type = {
            #推文侦听(推文推送事件)
            'listen':[
                'retweet','quoted','reply_to_status','reply_to_user','none','unknown'
            ],
            #被动推送事件
            'reverse':[
                'quoted','reply_to_status','reply_to_user'
            ],
            #用户数据更新事件
            'userupdata':[
                'ID','description','name','headimg','followers'
            ]
        }
        if grouptype not in allow_type:
            raise Exception('事件组标识异常，{0}->{1}'.format(grouptype,unittype))
        if unittype not in allow_type[grouptype]:
            raise Exception('事件元标识异常，{0}->{1}'.format(grouptype,unittype))
        eventunit = {
            'grouptype':grouptype,
            'unittype':unittype,
            'spyid':int(spyid),
            'data':data
        }
        return eventunit
    # 事件分发
    def deal_event(self,event:dict):
        """
            allow_type = {
                #推文侦听(推文推送事件)
                'listen':[
                    'retweet','quoted','reply_to_status','reply_to_user','none','unknown'
                ],
                #智能推送事件
                'intelligent':[
                    'quoted','reply_to_status','reply_to_user'
                ],
                #用户数据更新事件
                'userupdata':[
                    'ID','description','name','headimg','followers'
                ]
            }
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
        """
        if DEBUG:
            triggermsg = self.eventToStr(event)
            logger.info(triggermsg)
        pushlist = self.pushlist
        if event['grouptype'] == 'listen':
            units = pushlist.getLitsFromTweeUserID(event['spyid'])
            if units != []:
                for pushunit in units:
                    value = int(pushlist.getUnitConfKey(pushunit,event['unittype']))
                    if value == 1:
                        self.eventTrigger(event,pushunit)
                    elif event['data']['relate_notable']:
                        aivalue = int(pushlist.getUnitConfKey(pushunit,"ai_"+event['unittype']))
                        if aivalue == 1:
                            self.eventTrigger(event,pushunit)
        elif event['grouptype'] == 'reverse':# 被动推送
            units = pushlist.getLitsFromTweeUserID(event['spyid'])
            if units != []:
                for pushunit in units:
                    value = int(pushlist.getUnitConfKey(pushunit,'ai_passive_'+event['unittype']))
                    if value == 1:
                        self.eventTrigger(event,pushunit)
        elif event['grouptype'] == 'userupdata':
            units = pushlist.getLitsFromTweeUserID(event['spyid'])
            if units != []:
                for pushunit in units:
                    value = int(pushlist.getUnitConfKey(pushunit,'change_'+event['unittype']))
                    if value > 0:
                        # 关注更新触发器
                        if event['unittype'] == 'followers' and event['data']['newkey'] % (value*1000) != 0:
                            continue
                        self.eventTrigger(event,pushunit)
    # 事件到达(触发)
    def eventTrigger(self,event:dict,pushunit:dict):
        if event['grouptype'] in ('listen','reverse'):
            tweetinfo = event['data']
            nick = self.pushlist.getUnitConfKey(pushunit,'nick')
            template = self.pushlist.getUnitConfKey(pushunit,'template')
            msg = self.tweetToMsg(tweetinfo,nick = nick,template = template,simple=False)
            self.send_msg_pushunit(pushunit,msg)
        elif event['grouptype'] == 'userupdata':
            nick = self.pushlist.getUnitConfKey(pushunit,'nick')
            msg = self.userUpdataToMsg(event['data'],nick)
            self.send_msg_pushunit(pushunit,msg)
        else:
            msgStream.exp_send('推送不可达：{0}'.format(event['grouptype']),source='推送事件到达(触发)',flag="异常")
    # 事件转文本
    def eventToStr(self,event):
        msg = '触发事件{0}-{1}来自{2}：\n'.format(event['grouptype'],event['unittype'],event['spyid'])
        if event['grouptype'] in ('listen','reverse'):
            tweetinfo = event['data']
            msg = msg + self.tweetToMsg(tweetinfo,simple=True,even = True).toSimpleStr()
        elif event['grouptype'] == 'userupdata':
            msg = msg + self.userUpdataToMsg(event['data']).toSimpleStr()
        else:
            msg = msg + '事件转换失败，{0} 未知事件组'.format(event['grouptype'])
        return msg
    # 推特标识转中文
    def tweetTypeToStr(self,tweettype:str = 'unknown'):
        types = {
            'relate':'依赖推文',
            'retweet':'转推',
            'quoted':'转推并评论',
            'reply_to_status':'回复',
            'reply_to_user':'提及',
            'unknown':'未分类',
            'none':'发推',
        }
        if tweettype in types:
            return types[tweettype]
        else:
            return '未知'
    # 用户信息转文本
    def userinfoToStr(self,userinfo:dict,simple = True) -> str:
        """
            userinfo标准字典
            {
                'version':'1.0',
                'notable':...,#用户是否值得关注
                'id':...,
                'id_str':...,
                'name':...,
                'description':...,
                'screen_name':...,
                'profile_image_url':...,
                'profile_image_url_https':...,
                #可选字段
                'default_profile_image':...,
                'default_profile':...,
                'protected':...,
                'followers_count':...,
                'friends_count':...,
                'verified':...,
                'statuses_count':...,
                'created_at':...,
            }
        """
        if type(userinfo) != dict or 'version' not in userinfo:
            return '不合法的用户信息组'
        msg:SendMessage = SendMessage()
        msg.append("识别ID：{id}\n用户名：{name}\n昵称：{screen_name}\n描述：{description}\n头像：".format(**userinfo))
        msg.append(msg.baleImgObj(userinfo['profile_image_url_https']))
        if not simple:
            if 'statuses_count' in userinfo:
                msg.append("\n发推数(包括转推)：{0}".format(userinfo['statuses_count']))
            if 'friends_count' in userinfo:
                msg.append("\n关注数：{0}".format(userinfo['friends_count']))
            if 'followers_count' in userinfo:
                msg.append("\n粉丝数：{0}".format(userinfo['followers_count']))
            if 'protected' in userinfo:
                msg.append("\n推文受保护：{0}".format(('是' if userinfo['protected'] else '否')))
            if 'created_at' in userinfo:
                timestr = time.strftime("%Y{0}%m{1}%d{2} %H:%M:%S",time.localtime(userinfo['created_at'])).format('年','月','日')
                msg.append("\n账户创建时间：{0}".format(timestr))
        return msg

    # 生成推文数据map
    def tweetinfoGetMap(self,tweetinfo:dict,nick = ''):
        """
            tweetinfo标准字典
            {
                'version':'1.2',
                'type':...,#推文标识
                'notable':...,#推文是否值得关注
                'createtimestamp':...,#创健时间戳
                'createtimestr':...,#创建时间文本
                'createtimestrsimple':...,#简化的时间文本
                'id':...,
                'id_str':...,
                'minID':...,#压缩ID
                'text':...,
                'media':{...,...},#媒体域
                'link':...,#推文链接
                'user_id':...,
                'user_id_str':...,
                'user_sname':...,#用户sname
                'userinfo':{userinfo},#用户对象
                #依赖对象(可以为空)
                'hasrelate':...,#是否存在依赖
                'relate_notable':...,#依赖是否值得重视
                'relate_id':...,#依赖的推文ID
                'relate_id_str':...,#依赖的推文ID文本
                'relate_user_id':...,#依赖的推文用户ID
                'relate_user_id_str':...,#依赖的推文用户ID文本
                'relate_user_sname':...,#依赖的推文用户名
                'relate_userinfo':{userinfo},#依赖的用户信息
                'relate':{tweetinfo},#依赖的推文
            }
            媒体域：
                media_obj['id'] = media_unit['id']
                media_obj['id_str'] = media_unit['id_str']
                media_obj['type'] = media_unit['type']
                media_obj['media_url'] = media_unit['media_url']
                media_obj['media_url_https'] = media_unit['media_url_https']
        """
        tweetcache = self.tweetcache
        argmap = {
                'type':tweetinfo['type'],#推文状态
                'typestr':self.tweetTypeToStr(tweetinfo['type']),#推文状态
                'user_id':tweetinfo['user_id_str'],#用户唯一ID
                'user_sname':tweetinfo['user_sname'],#用户@ID
                'user_name':tweetinfo['userinfo']['name'],#用户名
                'nick':(nick if nick else tweetinfo['userinfo']['name']),#用户昵称
                'timestamp':tweetinfo['createtimestamp'],
                'fulltime':tweetinfo['createtimestr'],
                'time':tweetinfo['createtimestrsimple'],
                'senddur':int(time.time()) - int(tweetinfo['createtimestamp']),
                'id':tweetinfo['id_str'],
                'minid':tweetinfo['minID'],
                'tempID':tweetcache.findTweetTempID(int(tweetinfo['id'])) if 'TempID' not in tweetinfo else tweetinfo['TempID'],
                'text':tweetinfo['text'],
                'mintext':tweetinfo['text'][:15].replace('\r',' ').replace('\n',' ').strip(),
                'imgs':'[!imgs!]',
                'link':tweetinfo['link'],
                'hasrelate':False
            }
        argmap['senddur'] = '{0}分钟'.format(round(argmap['senddur']/60,2))
        if tweetinfo['type'] != 'none':
            argmap['relate_type'] = 'relate'
            argmap['relate_typestr'] = '依赖推文'
            argmap['relate_user_id'] = tweetinfo['relate_user_id_str']
            argmap['relate_user_sname'] = tweetinfo['relate_user_sname']
            argmap['relate_id'] = tweetinfo['relate_id_str']
            argmap['relate_minid'] = encode_b64(tweetinfo['relate_id'],offset=0)
            argmap['relate_tempID'] = tweetinfo['relate']['TempID'] if tweetinfo['relate'] and 'TempID' in tweetinfo['relate'] else '未知'
            argmap['relate_imgs'] = '[!relateimgs!]'
            argmap['relate_link'] = "https://twitter.com/{0}/status/{1}".format(argmap['relate_user_sname'],argmap['relate_id'])
            if tweetinfo['relate_userinfo'] is None:
                argmap['relate_user_name'] = '@' + tweetinfo['relate_user_sname']
            else:
                argmap['relate_user_name'] = tweetinfo['relate_userinfo']['name']
            if tweetinfo['relate'] is None:
                argmap['hasrelate'] = False
                argmap['relate_timestamp'] = argmap['timestamp']
                argmap['relate_fulltime'] = argmap['fulltime']
                argmap['relate_time'] = argmap['time']
                argmap['relate_senddur'] = argmap['senddur']
                argmap['relate_text'] = ''
                argmap['relate_mintext'] = ''
            else:
                if tweetinfo['type'] == 'retweet':
                    argmap['hasrelate'] = False
                    argmap['text'] = tweetinfo['relate']['text']
                    argmap['mintext'] = tweetinfo['relate']['text'][:15].replace('\r',' ').replace('\n',' ').strip()
                else:
                    argmap['hasrelate'] = True
                    argmap['relate_timestamp'] = tweetinfo['relate']['createtimestamp']
                    argmap['relate_fulltime'] = tweetinfo['relate']['createtimestr']
                    argmap['relate_time'] = tweetinfo['relate']['createtimestrsimple']
                    argmap['relate_senddur'] = int(time.time()) - int(tweetinfo['relate']['createtimestamp'])
                    argmap['relate_text'] = tweetinfo['relate']['text']
                    argmap['relate_mintext'] = tweetinfo['relate']['text'][:15].replace('\r',' ').replace('\n',' ').strip()
                    argmap['relate_senddur'] = '{0}分钟'.format(round(argmap['relate_senddur']/60,2))

            argmap['relate_nick'] = argmap['relate_user_name']
        if argmap['tempID'] == -1:
            argmap['tempID'] = '未生成'
        return argmap
    # 将推特数据应用到模版
    def tweetToMsg(self,tweetinfo:dict,nick = None,template:str = None,simple = False,even = False) -> SendMessage:
        if not template:
            if not simple:
                template = "推文ID：$id\n推文标识：$typestr\n发布用户：$nick(@$user_sname)\n推文内容：\n$text $imgs\n发布时间：$fulltime"
                template += "$relatestart\n---------------\n"
                template += "依赖推文ID：$relate_id\n依赖用户：$relate_user_name(@$relate_user_sname)\n依赖内容：\n$relate_text $relate_imgs\n发布时间：$relate_fulltime"
                template += "$relateend\n链接：$link\n临时推文ID：#$tempID"
            else:
                if even:
                    template = "$nick,$typestr,$mintext"
                else:
                    template = "$typestr,#$tempID,$minid,$mintext"
        # 特殊变量(仅识别一次) $relatestart、$relateend:用于分隔依赖推文与主推文
        # 特殊变量(仅识别一次) $ifrelate 依赖存在时 $else 不存在时 $end
        # 生成模版参数地图
        argmap = self.tweetinfoGetMap(tweetinfo,nick)
        #模版处理
        res = template.split('$relatestart',maxsplit = 1)
        template = res[0]
        if len(res) > 1:
            res = res[1].split('$relateend',maxsplit = 1)
            if argmap['hasrelate']:
                template += res[0]
            if len(res) > 1:
                template += res[1]

        res = template.split('$ifrelate',maxsplit=1)
        template = res[0]
        if len(res) > 1:
            res = res[1].split('$else',maxsplit = 1)
            if argmap['type'] != 'none':
                template += res[0]
            res = res[1].split('$end',maxsplit = 1)
            if len(res) > 1:
                if argmap['type'] == 'none':
                    template += res[0]
                template += res[1]
        # 应用模版
        st = tweetToStrTemplate(template)
        stres = st.safe_substitute(argmap)
        # 处理图片(仅处理一次)
        """
            media_obj['id'] = media_unit['id']
            media_obj['id_str'] = media_unit['id_str']
            media_obj['type'] = media_unit['type']
            media_obj['media_url'] = media_unit['media_url']
            media_obj['media_url_https'] = media_unit['media_url_https']
        """
        # 生成媒体
        msg:SendMessage = SendMessage()
        mediatype = ''
        for media_obj in tweetinfo['media']:
            if media_obj['type'] == 'photo':
                mediatype += '图片 '
            elif media_obj['type'] == 'video':
                mediatype += '视频 '
            elif media_obj['type'] == 'animated_gif':
                mediatype += 'GIF '
            msg.append(msg.baleImgObj(media_obj['media_url']))
        imgs = msg.toStandStr()
        if mediatype:
            imgs = '\n媒体 {0} ({1}个):\n{2}'.format(
                mediatype,
                len(tweetinfo['media']),
                imgs
            )
        
        # 生成依赖媒体
        relateimgs = ''
        if argmap['hasrelate'] and tweetinfo['relate'] is not None:
            msg:SendMessage = SendMessage()
            mediatype = ''
            for media_obj in tweetinfo['relate']['media']:
                if media_obj['type'] == 'photo':
                    mediatype += '图片 '
                elif media_obj['type'] == 'video':
                    mediatype += '视频 '
                elif media_obj['type'] == 'animated_gif':
                    mediatype += 'GIF '
                msg.append(msg.baleImgObj(media_obj['media_url']))
            relateimgs = msg.toStandStr()
            if mediatype:
                relateimgs = '\n依赖媒体 {0} ({1}个):\n{2}'.format(
                    mediatype,
                    len(tweetinfo['relate']['media']),
                    relateimgs
                )
        stres = stres.replace('[!imgs!]',imgs,1).replace('[!relateimgs!]',relateimgs,1)
        stres = stres.replace('[!imgs!]','[不可重复显示图片A]').replace('[!relateimgs!]','[不可重复显示图片B]')
        msg = SendMessage(stres)
        return msg
    def userUpdataToMsg(self,userupdata:dict,nick:str = None,template:str = None) -> SendMessage:
        """
            data['grouptype'] = 'userupdata'
            data['unittype'] = data[1]
            data['user_id'] = userinfo['id']
            data['user_id_str'] = str(userinfo['id_str'])
            data['user_name'] = str(userinfo['name'])
            data['user_screen_name'] = str(userinfo['screen_name'])
            data['des'] = data[0]
            data['userinfo'] = userinfo.copy()
            data['oldkey'] = old_userinfo[key]
            data['newkey'] = userinfo[key]
        """
        if nick and nick.strip() == '':
            nick = None
        userupdata['nick'] = (nick if nick else userupdata['user_screen_name'])
        if not template:
            if userupdata['unittype'] == 'description':
                template = "{nick}({user_name})的推特信息 {des} 更新为：\n{newkey}"
            elif userupdata['unittype'] == 'followers':
                template = "{nick}({user_name})的推特信息 {des} 更新为：{newkey}"
            else:
                template = "{nick}({user_name})的推特信息 {des} 更新了：\n由 {oldkey} 更新为 {newkey}"
        stl = template.format(**userupdata)
        if userupdata['unittype'] == 'headimg':
            msg = SendMessage()
            msg.append(msg.baleImgObj(userupdata['oldimg']))
            oldimgstr = msg.toStandStr()
            msg.clear()
            msg.append(msg.baleImgObj(userupdata['newimg']))
            newimgstr = msg.toStandStr()
            stl = stl.replace('[旧头像]',oldimgstr)
            stl = stl.replace('[新头像]',newimgstr)
        msg = SendMessage(stl)
        return msg

    # 图片保存(文件名,下载url,基目录-'img',是否覆盖-否),返回值->(是否成功，描述，文件路径，完整文件名)
    def seve_image(self, name, url, file_path='img',canCover=False) -> tuple:
        basepath = os.path.join(self.baseconfigpath,file_path)
        basepath = check_path(basepath)
        try:
            file_suffix = os.path.splitext(url)[1]
            filename = os.path.join(basepath,name + file_suffix)
            if os.path.isfile(filename):
                if not canCover:
                    return (False,'保存失败，文件已存在',filename,name + file_suffix)
                os.remove(filename)
            # 下载图片，并保存到文件夹中
            urllib.request.urlretrieve(url,filename=filename)
        except IOError:
            s = traceback.format_exc(limit=5)
            logger.error('图片保存失败：' + s + "\n文件保存路径:"+filename)
            return (False,'保存失败，文件IO错误',filename,name + file_suffix)
        except Exception:
            s = traceback.format_exc(limit=5)
            logger.error('未知异常：' + s)
            return (False,'保存失败，未知异常',filename,name + file_suffix)
        return (True,'保存成功',filename,name + file_suffix)
    def send_msg_kw(self,target):
        return msgStream.send_msg(**target)
    def send_msg_pushunit(self,pushunit,message:SendMessage):
        if not isinstance(message,msgStream.SendMessage):
            if not isinstance(message,int):
                raise TypeError('不支持的消息类型')
            message = SendMessage(message)
        if not pushlist.getUnitConfKey(pushunit,'upimg') and isinstance(message,msgStream.SendMessage):
            message.designatedTypeToStr('img')
        return msgStream.send_msg_kw(**pushlist.baleSendTarget(pushunit,message))

pushlist:TweePushList = TweePushList(init = True)
tweetcache:TweetCache = TweetCache()
tweetstatusdeal:TweetStatusDeal = TweetStatusDeal(pushlist,tweetcache)
tweetevendeal:TweetEventDeal = TweetEventDeal(tweetstatusdeal,pushlist,tweetcache)

# 新事件缓存
newevenscache = TempMemory('evencache',limit = 100)

"""
运行线程信息，及更新合并请求提交
*线程保证status处理顺序的提交
"""
Submitqueque = queue.Queue(128) # 更新提交待处理
tweetEvenQueue = queue.Queue(64) # 事件队列
run_info = {
    'EventDealThread':None,
    'Eventqueque':tweetEvenQueue,
    'tweetevendeal':tweetevendeal,
    'SubmitStatusThread':None,
    'Submitqueque':Submitqueque,
    'isDeal':True
}
def getSubmitQueueStatus():
    global Submitqueque
    idle = round(Submitqueque.qsize()*100/128,2)
    return idle
def getEventQueueStatus():
    global tweetEvenQueue
    idle = round(tweetEvenQueue.qsize()*100/64,2)
    return idle

def getQueueStatus():
    idle1 = getSubmitQueueStatus()
    idle2 = getEventQueueStatus()
    avg = (idle1+idle2)/2
    if avg < 5:
        status = '空闲'
    elif avg < 30:
        status = '略有占用'
    elif avg < 50:
        status = '占用略高'
    elif avg < 70:
        status = '繁忙'
    elif avg < 90:
        status = '拥挤'
    else:
        status = '阻塞'
    msg = '队列状态：{0}'.format(status)
    msg = msg + "\n提交队列占用率：{0}%".format(idle1)
    msg = msg + "\n事件队列占用率：{0}%".format(idle2)

    return getSubmitQueueStatus() + "\n" + getEventQueueStatus()
"""
推送预处理与合并过滤
"""
def on_even(even,source = '未知',timeout = 5,block=True):
    try:
        run_info['Eventqueque'].put(even,timeout=timeout,block=block)
    except:
        s = traceback.format_exc(limit=5)
        notice = '推特监听处理队列异常或溢出，请检查队列！'
        msgStream.exp_send(notice,source=source,flag = '异常')
        logger.error(notice + '\n' + s)
    newevenscache.join(even)
def on_resFromDealSourceData(notable,tweetinfo,userevens):
    #notable = res['notable'] #推文是否值得关注
    #tweetinfo = res['tweetinfo'] #推文数据
    #userevens = res['userevens'] #用户数据更新事件
    #run_info['queque'].put()
    try:
        # 仅处理值得关注的推文
        if notable:
            even = tweetevendeal.bale_event('listen',tweetinfo['type'],tweetinfo['user_id'],tweetinfo)
            on_even(even,'推文推送')
            # 被动推送
            if tweetinfo['relate'] and \
                'version' in tweetinfo['relate'] and \
                tweetinfo['relate']['notable'] and \
                tweetinfo['type'] in ('quoted','reply_to_status','reply_to_user'):#被动推送标识检查
                even = tweetevendeal.bale_event('reverse',tweetinfo['type'],tweetinfo['relate']['user_id'],tweetinfo)
                on_even(even,'被动推送')
        for usereven in userevens:
            on_even(usereven,'用户事件推送')
        if test != None:
            try:
                test.on_status(tweetinfo)
            except:
                pass
    except:
        s = traceback.format_exc(limit=5)
        logger.error(s)
def on_status(status,merge = False):
    global tweetcache
    res = tweetevendeal.dealSourceData(status)
    try:
        if merge:
            # 检查推文是否被处理过，处理过的推文直接忽略
            if tweetcache.findTweetTempID(res['tweetinfo']['id']) > 0:
                return
        tweetcache.addTweetToCache(res['tweetinfo'])
        on_resFromDealSourceData(**res)
    except:
        s = traceback.format_exc(limit=5)
        msgStream.exp_send('推文源数据处理时异常',source='推文源',flag = '错误')
        logger.error(res)
        logger.error(s)

# 事件处理队列(消耗事件)
def eventDeal():
    while True:
        even = run_info['Eventqueque'].get()
        try:
            run_info['tweetevendeal'].deal_event(even)
            # 控制台事件输出
            logger_Event.info(run_info['tweetevendeal'].eventToStr(even))
        except:
            s = traceback.format_exc(limit=5)
            logger.warning(s)
        run_info['Eventqueque'].task_done()

# 预处理提交(预处理,默认进行合并检查)
def submitStatus(status,merge:bool = True,source = '未知',timeout = 5,block=True):
    try:
        run_info['Submitqueque'].put((status,merge),timeout=timeout,block=True)
    except:
        s = traceback.format_exc(limit=5)
        notice = '推特预处理队列异常或溢出，请检查队列！'
        msgStream.exp_send(notice,source=source+'预处理提交',flag = '异常')
        logger.error(notice + '\n' + s)
# 预处理队列
def submitDeal():
    while True:
        onstatusunit = run_info['Submitqueque'].get()
        try:
            on_status(onstatusunit[0],merge = onstatusunit[1])
        except:
            s = traceback.format_exc(limit=5)
            logger.warning(s)
        run_info['Submitqueque'].task_done()

# 运行推送线程
def runTwitterPushThread():
    logger.info("TwitterEvenPush 已启动")
    # 预处理队列维护线程
    run_info['SubmitStatusThread'] = threading.Thread(
        group=None, 
        target=submitDeal, 
        name='tweetSubmitStatusDealThread',
        daemon=True
    )
    run_info['SubmitStatusThread'].start()
    # 事件队列维护线程
    run_info['EventDealThread'] = threading.Thread(
        group=None, 
        target=eventDeal, 
        name='tweetPushDealThread',
        daemon=True
    )
    run_info['EventDealThread'].start()
    return run_info