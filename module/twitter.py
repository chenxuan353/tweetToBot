# -*- coding: UTF-8 -*-
import queue
import threading
import os
import time
import string
#图片缓存
import urllib
import traceback
#引入配置
import config

from module.msgStream import SendMessage
import module.msgStream as msgStream
from helper import dictInit,dictHas,dictGet,dictSet
from helper import data_read,data_save,TempMemory,data_read_auto,file_exists,check_path
from module.PushList import PushList

#日志输出
from helper import getlogger
logger = getlogger(__name__)
logger_Event = getlogger(__name__+'_event',printCMD=False)
#引入测试方法
try:
    #event_push
    import v3_test as test
except:
    test = None
'''
推送唯一性检验及推送流
'''
baseconfigpath = 'tweitter'

#10进制与64进制互相转换(由于增速过快，缩写ID不设偏移)
def encode_b64(n:int,offset:int = 0) -> str:
    table = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_'
    result = []
    temp = n - offset
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
    defaulttemplate = "$ifrelate $nick $typestr $relate_name 的推文： $else $nick的推特更新了 $end ：\n$text $imgs $relatestart---------------\n$relate_text $relate_imgs$relateend\n链接：$link\n临时推文ID：#$tempID"
    pushunit_base_config = {
        #是否连带图片显示(默认不带)-发推有效,转推及评论等事件则无效
        'upimg':0,
        #对象自定义选项
        #'unit':{
        #    #'nick':'',
        #    #'des':'',
        #},
        'template':'',#推特推送模版(为空使用默认模版)
        #推送选项(注释则不推送)
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
    #推送单元允许编辑的配置_布尔类型
    Pushunit_allowEdit = (
        #携带图片发送
        'upimg',
        #消息模版
        'retweet_template','quoted_template','reply_to_status_template',
        'reply_to_user_template','none_template',
        #推特转发各类型开关
        'retweet','quoted','reply_to_status',
        'reply_to_user','none',

        #智能推送(仅限推送单元设置，无法全局设置)
        'ai_retweet',
        'ai_reply_to_status',
        'ai_passive_reply_to_status',
        'ai_passive_quoted',
        'ai_passive_reply_to_user',

        #推特个人信息变动推送开关
        'change_ID','change_name','change_description',
        'change_headimg','change_followers'
        )
    def __init__(self,init:bool = False,fileprefix:str = '',pushtype:str = 'tweet',baseconfigpath = baseconfigpath):
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
        self.init()#初始化推送列表(包含自动读取)
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
        if data[0] is False:
            self.PushTemplate = data[2]
            return (True,data[1])
        return data

    #打包成推送单元中()
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

    #添加与删除模版及模版管理
    def pushTemplateAddCover(self,name,config:dict):
        config = config.copy()
        self.PushTemplate[name] = config
        self.pushTemplateSave()
        return (True,'模版已保存')
    def pushTemplateAdd(self,name,config):
        config = config.copy()
        #保存推送设置模版
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

    #模版设置
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
    
    #信息打包
    def baleForConfig(self,nick = '',des = '',upimg = 0,template = '',push:dict = {}):
        return {
            'upimg':upimg,
            'unit':{
                'nick':nick,
                'des':des,
            },
            'template':template,
            'push':push
        }
    #信息获取
    def getMergeConfKey(self,pushtoconfig:dict,config:dict = None,key = None):
        mergeConf = {
            'upimg':0,
            'unit':{
                'nick':'',
                'des':'',
            },
            'template':'',
            'push':{}
        }.update(self.pushunit_default_config)
        if not key:
            mergeConf['upimg'] = pushtoconfig['upimg'] if pushtoconfig['upimg'] else mergeConf['upimg']
            mergeConf['unit'].update(pushtoconfig['unit'] if pushtoconfig['unit'] else {})
            mergeConf['template'] = pushtoconfig['template'] if pushtoconfig['template'] else mergeConf['template']
            mergeConf['push'].update(pushtoconfig['push'] if pushtoconfig['push'] else {})
            if config:
                mergeConf['upimg'] = config['upimg'] if config['upimg'] else mergeConf['upimg']
                mergeConf['unit'].update(config['unit'] if config['unit'] else {})
                mergeConf['template'] = config['template'] if config['template'] else config['template']
                mergeConf['push'].update(config['push'] if config['push'] else {})
            return mergeConf
        elif key == 'upimg':
            mergeConf['upimg'] = pushtoconfig['upimg'] if pushtoconfig['upimg'] else mergeConf['upimg']
            if config:
                mergeConf['upimg'] = config['upimg'] if config['upimg'] else mergeConf['upimg']
            return mergeConf['upimg']
        elif key == 'template':
            mergeConf['template'] = pushtoconfig['template'] if pushtoconfig['template'] else mergeConf['template']
            if config:
                mergeConf['template'] = config['template'] if config['template'] else config['template']
            return mergeConf['template']
        elif key in ('nick','des'):
            mergeConf['unit'].update(pushtoconfig['unit'] if pushtoconfig['unit'] else {})
            if config:
                mergeConf['unit'].update(config['unit'] if config['unit'] else {})
            return mergeConf['unit'][key]
        else:
            mergeConf['push'].update(pushtoconfig['push'] if pushtoconfig['push'] else {})
            if config:
                mergeConf['push'].update(config['push'] if config['push'] else {})
            if key not in mergeConf['push']:
                return None
            return mergeConf['push'][key]
    def getUnitConfKey(self,pushunit,key):
        return self.getMergeConfKey(self.getUnitPushToConfig(pushunit),pushunit['config'],key)

    #触发器
    def pushcheck_trigger(self,unit,**pushunit) -> bool:
        return True
    def setPushToAttr_trigger(self,pushtoconfig:dict,setkey:str,setvalue) -> tuple:
        if setkey != 'upimg':
            if setkey not in self.Pushunit_allowEdit:
                return (False,'属性值不合法')
        
        if setkey == 'upmig':
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
"""
class TweetCache:
    def __init__(self,baseconfigpath = baseconfigpath):
        self.baseconfigpath = baseconfigpath
        #缩写推特ID(缓存条)
        #单元：[缩写ID,推特ID]
        self.newtweetid = 0
        self.mintweetID = data_read_auto('mintweetID.json',default=[],path=baseconfigpath)
        #推特用户缓存(1000条)
        self.userinfolist = TempMemory('userinfolist.json',path = baseconfigpath,limit = 1000,autosave = False,autoload = False)
        self.tweetspath = os.path.join(baseconfigpath,'tweetscache')
        #推文缓存(150条/监测对象)
        #监测ID->缓存内容
        self.tweetscache = {}
    #推文相关
    def getNewID(self):
        newtweetid = self.newtweetid
        newtweetid += 1
        if newtweetid > 9999:
            newtweetid = 1
        return newtweetid
    def getTweetTempID(self,tweetid:int):
        mintweetID = self.mintweetID
        tweetid = int(tweetid)
        for unit in mintweetID:
            if unit[1] == tweetid:
                return unit[0]
        newtweetid = self.getNewID()
        if len(mintweetID) > 9998:
            mintweetID.pop(0)
        mintweetID.append((newtweetid,tweetid))
        data_save('mintweetID.json',mintweetID,path=baseconfigpath)
        return newtweetid
    def findTweetTempID(self,tweetid:int):
        mintweetID = self.mintweetID
        tweetid = int(tweetid)
        for unit in mintweetID:
            if unit[1] == tweetid:
                return unit[0]
        return -1
    def getTweetSourceID(self,minId:int):
        mintweetID = self.mintweetID
        minId = int(minId)
        for unit in mintweetID:
            if unit[0] == minId:
                return unit[1]
        return -1
    def addTweetToCache(self,tweetinfo):
        tweetscache = self.tweetscache
        userid = tweetinfo['user']['id_str']
        #判断缓存中是否已经存在此推文
        if self.findTweetTempID(tweetinfo['id']) != -1:
            return
        if userid not in tweetscache:
            tweetscache[userid] = TempMemory(userid+'_tweets.json',path = self.tweetspath,limit = 150,autosave = False,autoload = False)
        if 'TempID' not in tweetinfo:
            tweetinfo['TempID'] = self.getTweetTempID(tweetinfo['id'])
        tweetscache[userid].join(tweetinfo)
    #从缓存中获取指定用户推文列表
    def getTweetsFromCache(self,userid:str) -> TempMemory:
        tweetscache = self.tweetscache
        userid = str(userid)
        if file_exists(os.path.join(self.tweetspath,userid+'_tweets.json')):
            tweetscache[userid] = TempMemory(userid+'_tweets.json',path = self.tweetspath,limit = 150,autosave = False,autoload = False)
        if userid not in tweetscache:
            return None
        return tweetscache[userid]
    #尝试从缓存中获取推文
    def getTweetFromCache(self,tweetid:str,userid:str = None) -> dict:
        tweetscache = self.tweetscache
        tweetid = str(tweetid)
        if userid:
            tcache = self.getTweetsFromCache(userid)
            if not tcache:
                return None
            res = tweetscache[userid].find((lambda item,val:item['id_str'] == val),tweetid)
            return res
        for userid in tweetscache:
            res = tweetscache[userid].find((lambda item,val:item['id_str'] == val),tweetid)
            if res:
                return res
        return None
    #用户相关
    #尝试从缓存中获取用户信息,返回用户信息表
    def getUserInfo(self, userid:int = None,screen_name:str = None) -> list:
        userid = int(userid)
        if userid:
            tu = self.userinfolist.find((lambda item,val:item['id'] == val),int(userid))
        elif screen_name:
            tu = self.userinfolist.find((lambda item,val:item['screen_name'] == val),screen_name)
        else:
            raise Exception("无效的参数")
        return tu
"""
status处理
"""
class TweetStatusDeal:
    def __init__(self,pushlist:TweePushList,tweetcache:TweetCache):
        self.pushlist = pushlist
        self.tweetcache = tweetcache
    #推文包定义
    def bale_userinfo(self,
            notable,
            id,
            name,
            description,
            screen_name,
            profile_image_url,
            profile_image_url_https,
            **kw
        ):
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
            }
        """
        userinfo = {
                'version':'1.0',
                'id':int(id),
                'id_str':str(id),
                'name':name,
                'description':description,
                'screen_name':screen_name,
                'profile_image_url':profile_image_url,
                'profile_image_url_https':profile_image_url_https,
            }
        userinfo.update(kw)
        return userinfo
    def bale_tweetinfo(self,
        notable,
        tweettype,
        timestamp,
        id,
        text,
        user_id,
        user_name,
        imgs:list = [],
        userinfo:dict = None,
        relate_notable:bool = False,#不存在的推文肯定不值得关注
        relate:dict = None
        ):
        """
            tweetinfo标准字典
            {
                'version':'1.0',
                'type':...,#推文标识
                'notable':...,#推文是否值得关注
                'timestamp':...,
                'id':...,
                'id_str':...,
                'text':...,
                'imgs':{imgsrc1,imgsrc2,...},
                'user_id':...,
                'user_id_str':...,
                'user_name':...,
                'userinfo':{userinfo},
                #依赖对象(可以为空)
                'relate_notable':...,
                'relate':{tweetinfo},
            }
        """
        tweetinfo = {
                'version':'1.0',
                'type':tweettype,
                'timestamp':timestamp,
                'id':int(id),
                'id_str':str(id),
                'text':str(text),
                'imgs':imgs.copy(),
                'user_id':int(user_id),
                'user_id_str':str(user_id),
                'user_name':user_name,
                'userinfo':(userinfo.copy() if userinfo else None),
                #依赖对象(可以为空)
                'relate_notable':relate_notable,
                'relate':(relate.copy() if relate else None),
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
            **kw)
    def bale_tweetinfo_kw(self,*,
        notable,
        tweettype,
        timestamp,
        id,
        text,
        user_id,
        user_name,
        **kw):
        imgs:list = (kw['imgs'] if kw['imgs'] else [])
        userinfo:dict = (kw['userinfo'] if kw['userinfo'] else None)
        relate_notable:dict = (kw['relate_notable'] if kw['relate_notable'] else False) #不存在的推文肯定不值得关注
        relate:dict = (kw['relate'] if kw['relate'] else None)
        return self.bale_tweetinfo(
                    notable,
                    tweettype,
                    timestamp,
                    id,
                    text,
                    user_id,
                    user_name,
                    imgs,
                    userinfo,
                    relate_notable,#不存在的推文肯定不值得关注
                    relate
                    )

    #用户是否是值得关注的(粉丝/关注 大于 5k 且修改了默认图，或粉丝大于10000)
    def isNotableUser(self,user,checkspy:bool = True):
        pushlist = self.pushlist
        if checkspy and pushlist.hasSpy(user['id_str']):
            return True
        if not user['default_profile_image'] and \
            not user['default_profile'] and \
            not user['protected'] and \
            (int(user['followers_count'] / ((user['friends_count']+1))) > 5000 or user['followers_count'] > 10000):
            return True
        return False
    #重新包装推特用户信息(用户数据，是否检查更新)
    def get_userinfo(self,user,checkspy:bool = True):
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
        userinfo = {}
        userinfo['version'] = '1.0'
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
        return userinfo
    #重新包装推特信息
    def get_tweet_info(self,tweet,checkspy:bool = True):
        """
            tweetinfo标准字典
            {
                'version':'1.0',
                'type':...,#推文标识
                'notable':...,#推文是否值得关注
                'timestamp':...,
                'id':...,
                'id_str':...,
                'text':...,
                'imgs':{imgsrc1,imgsrc2,...},
                'user_id':...,
                'user_id_str':...,
                'user_name':...,
                'userinfo':{userinfo},
                #依赖对象(可以为空)
                'relate_notable':...,
                ''
                'relate':{tweetinfo},
            }
        """
        tweetinfo = {}
        tweetinfo['version'] = '1.0'
        tweetinfo['type'] = ''
        tweetinfo['created_at'] = int(tweet.created_at.timestamp())
        tweetinfo['timestamp'] = tweetinfo['created_at']
        tweetinfo['id'] = tweet.id
        tweetinfo['id_str'] = tweet.id_str
        #尝试获取全文
        if hasattr(tweet,'extended_tweet') or hasattr(tweet,'full_text'):
            if hasattr(tweet,'full_text'):
                tweetinfo['text'] = tweet.full_text.replace('&lt;','<').replace('&gt;','>')
            else:
                tweetinfo['text'] = tweet.extended_tweet['full_text'].replace('&lt;','<').replace('&gt;','>')
        else:
            tweetinfo['text'] = tweet.text.replace('&lt;','<').replace('&gt;','>')

        #处理媒体信息
        tweetinfo['extended_entities'] = []
        if hasattr(tweet,'extended_entities'):
            #图片来自本地媒体时将处于这个位置
            if 'media' in tweet.extended_entities:
                for media_unit in tweet.extended_entities['media']:
                    media_obj = {}
                    media_obj['id'] = media_unit['id']
                    media_obj['id_str'] = media_unit['id_str']
                    media_obj['type'] = media_unit['type']
                    media_obj['media_url'] = media_unit['media_url']
                    media_obj['media_url_https'] = media_unit['media_url_https']
                    tweetinfo['extended_entities'].append(media_obj)
        elif hasattr(tweet,'entities'):
            #图片来自推特时将处于这个位置
            if 'media' in tweet.entities:
                for media_unit in tweet.entities['media']:
                    media_obj = {}
                    media_obj['id'] = media_unit['id']
                    media_obj['id_str'] = media_unit['id_str']
                    media_obj['type'] = media_unit['type']
                    media_obj['media_url'] = media_unit['media_url']
                    media_obj['media_url_https'] = media_unit['media_url_https']
                    tweetinfo['extended_entities'].append(media_obj)
        tweetinfo['imgs'] = []
        for unit in tweetinfo['extended_entities']:
            tweetinfo['imgs'].append(unit['media_url_https'])
        tweetinfo['user'] = self.get_userinfo(tweet.user,checkspy)
        tweetinfo['user_id'] = tweetinfo['user']['user_id']
        tweetinfo['user_id_str'] = tweetinfo['user']['user_id_str']
        tweetinfo['user_name'] = tweetinfo['user']['user_name']
        tweetinfo['notable'] = tweetinfo['user']['notable']
        return tweetinfo
   
    def deal_tweet_type(self, status):
        if hasattr(status, 'retweeted_status'):
            return 'retweet' #纯转推
        elif hasattr(status, 'quoted_status'):
            return 'quoted' #推特内含引用推文
        elif status.in_reply_to_status_id != None:
            return 'reply_to_status' #回复
        elif status.in_reply_to_screen_name != None:
            return 'reply_to_user' #提及
        else:
            return 'none' #未分类(主动发推)
    def deal_tweet(self, status) -> dict:
        pushlist = self.pushlist
        tweetcache = self.tweetcache
        """
        推文
        type:推文标识
        """
        #监听流：本人转推、本人发推、本人转推并评论、本人回复、被转推、被回复、被提及
        tweetinfo = self.get_tweet_info(status,True)
        tweetinfo['type'] = self.deal_tweet_type(status)
        tweetinfo['status'] = status #原始数据

        if tweetinfo['type'] == 'retweet':#大多数情况是被转推
            #转推时被转推对象与转推对象同时值得关注时视为值得关注
            tweetinfo['retweeted'] = self.get_tweet_info(status.retweeted_status,True)
            tweetinfo['retweeted']['type'] = 'relate'
            
            tweetinfo['relate'] = tweetinfo['retweeted']
            tweetinfo['relate_notable'] = (tweetinfo['notable'] and tweetinfo['relate']['notable'])
        elif tweetinfo['type'] == 'quoted':
            tweetinfo['quoted'] = self.get_tweet_info(status.quoted_status,True)
            tweetinfo['quoted']['type'] = 'relate'
            
            tweetinfo['relate'] = tweetinfo['quoted']
            tweetinfo['relate_notable'] = (tweetinfo['notable'] and tweetinfo['relate']['notable'])
        elif tweetinfo['type'] != 'none':
            tweetinfo['relate'] = {
                'id':status.in_reply_to_status_id,
                'id_str':status.in_reply_to_status_id_str,
                'text':'',
                'user':{
                    'id':status.in_reply_to_user_id,
                    'id_str':status.in_reply_to_user_id_str,
                    'screen_name':status.in_reply_to_screen_name,
                }
            }
            tweetinfo['relate']['notable'] = pushlist.hasSpy(tweetinfo['relate']['user']['id_str'])
            tweetinfo['relate_notable'] = (tweetinfo['notable'] and tweetinfo['relate']['notable'])

            if pushlist.hasSpy(tweetinfo['Related_user']['id_str']):
                tweetinfo['relate_notable'] = True
            else:
                userinfo = tweetcache.getUserInfo(tweetinfo['Related_user']['id'])
                if userinfo:
                    tweetinfo['relate_notable'] = self.isNotableUser(userinfo,False)
                else:
                    tweetinfo['relate_notable'] = False
        else:
            tweetinfo['relate_notable'] = False
            tweetinfo['relate'] = None
        
        #推文是否值得关注
        if pushlist.hasSpy(tweetinfo['user']['id_str']):
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
    idpattern = '[a-z]+_[a-z_]+'
class TweetEventDeal:
    def __init__(self,tweetstatusdeal:TweetStatusDeal,pushlist:TweePushList = None,tweetcache:TweetCache = None,baseconfigpath = baseconfigpath):
        self.baseconfigpath = baseconfigpath
        if tweetcache:
            self.tweetcache = tweetcache
        else:
            self.tweetcache = tweetstatusdeal.tweetcache
        self.tweetstatusdeal = tweetstatusdeal
        self.pushlist = pushlist
    #用户信息更新检测
    def checkUserInfoUpdata(self,userinfo:dict) -> list:
        #检测个人信息更新,返回更新事件集
        tweetcache = self.tweetcache
        userinfolist = tweetcache.userinfolist
        """
            运行数据比较
            用于监测用户的信息修改
            {
                'id':...,
                'id_str':...,
                'name':...,
                'description':...,
                'screen_name':...,
                'profile_image_url':...,
                'profile_image_url_https':...
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
            def compareChanges(key,data):
                if key not in old_userinfo:
                    return None
                if old_userinfo[key] != userinfo[key]:
                    #禁止粉丝数逆增长
                    if key == 'followers_count' and old_userinfo[key] > userinfo[key]:
                        return None
                    data = {}
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
                    old_userinfo[key] = userinfo[key]
                    if key == 'profile_image_url_https':
                        data['oldimg'] = data['oldkey']
                        data['newimg'] = data['newkey']
                        data['oldkey'] = '[旧头像]'
                        data['newkey'] = '[新头像]'
                    #粉丝数更新仅对千整数推送事件
                    if key == 'followers_count' and old_userinfo[key] % 1000 != 0:
                        return None
                    even = self.bale_event(data['grouptype'],data['unittype'],data['user_id_str'],data)
                    evens.append(even)
                    return even
                return None
            checkkeys = {
                'name':('昵称','ID'),
                'description':('描述','description'),
                'screen_name':('昵称','name'),
                'profile_image_url_https':('头像','headimg'),
                'followers_count':('粉丝数','followers')
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
            evens = self.checkUserInfoUpdata(tweetinfo['user'])
            if tweetinfo['relate'] and tweetinfo['relate']['version']:
                evens.append(self.checkUserInfoUpdata(tweetinfo['relate']['user']))
            res['userevens'] = evens
        return res
    #打包事件(事件组，事件元，引起变化的用户ID，事件数据)
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
    #事件分发
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
        pushlist = self.pushlist
        if event['grouptype'] == 'listen':
            units = pushlist.getLitsFromTweeUserID(event['spyid'])
            if units != []:
                for pushunit in units:
                    value = int(pushlist.getUnitConfKey(pushunit,event['unittype']))
                    if value == 1:
                        self.eventTrigger(event,pushunit)
                    elif event['data']['relate_notable']:
                        aivalue = int(pushlist.getUnitConfKey(pushunit,"al_"+event['unittype']))
                        if aivalue == 1:
                            self.eventTrigger(event,pushunit)
        elif event['grouptype'] == 'reverse':#被动推送
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
                        #关注更新触发器
                        if event['unittype'] == 'followers' and event['data']['newkey'] % (value*1000) != 0:
                            continue
                        self.eventTrigger(event,pushunit)
    #事件到达(触发)
    def eventTrigger(self,event:dict,pushunit:dict):
        if event['grouptype'] in ('listen','reverse'):
            tweetinfo = event['data']
            nick = self.pushlist.getUnitConfKey('nick')
            template = self.pushlist.getUnitConfKey('template')
            msg = self.tweetToMsg(tweetinfo,nick = nick,template = template)
            self.send_msg_pushunit(pushunit,msg)
        elif event['grouptype'] == 'userupdata':
            nick = self.pushlist.getUnitConfKey('nick')
            msg = self.userUpdataToMsg(event['data'],nick)
            self.send_msg_pushunit(pushunit,msg)
        else:
            msgStream.exp_send('推送不可达：{0}'.format(event['grouptype']),source='推送事件到达(触发)',flag="异常")
    #事件转文本
    def eventToStr(self,event):
        msg = '触发事件{0}-{1}来自{2}：\n'.format(event['grouptype'],event['unittype'],event['spyid'])
        if event['grouptype'] in ('listen','reverse'):
            tweetinfo = event['data']
            msg = msg + self.tweetToMsg(tweetinfo)
        elif event['grouptype'] == 'userupdata':
            msg = msg + self.userUpdataToMsg(event['data'])
        else:
            msg = msg + '事件转换失败，{0} 未知事件组'.format(event['grouptype'])
        return msg
    #推特标识转中文
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
    #用户信息转文本
    def userinfoToStr(self,userinfo:dict,simple = True) -> SendMessage:
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
                timestr = time.strftime("%Y年%m月%d %H:%M:%S", time.localtime(userinfo['created_at']))
                msg.append("\n账户创建时间：{0}".format(timestr))
        return msg

    #生成推文数据map
    def tweetinfoGetMap(self,tweetinfo:dict):
        tweetcache = self.tweetcache
        if 'argmap' in tweetinfo:
            tweetinfo['argmap']['senddur'] = str(int(time.time()) - int(tweetinfo['timestmap']))
            return tweetinfo['argmap']
        argmap = {
                'type':tweetinfo['type'],#推文状态
                'typestr':self.tweetTypeToStr(tweetinfo['type']),#推文状态
                'user_uuid':tweetinfo['user_id'],#用户唯一ID
                'user_ID':tweetinfo['user_name'],#用户@ID
                'user_name':(tweetinfo['userinfo']['screen_name'] if tweetinfo['userinfo'] else '@'+tweetinfo['user_name']),#用户名
                'timestmap':tweetinfo['timestmap'],
                'fulltime':time.strftime("%Y年%m月%d %H:%M:%S", time.localtime(int(tweetinfo['timestmap']))),
                'time':time.strftime("%H:%M:%S", time.localtime(int(tweetinfo['timestmap']))),
                'senddur':str(int(time.time()) - int(tweetinfo['timestmap'])),
                'ID':tweetinfo['id_str'],
                'minID':encode_b64(int(tweetinfo['id'])),
                'tempID':tweetcache.findTweetTempID(int(tweetinfo['id'])),
                'text':tweetinfo['text'],
                'imgs':'[!imgs!]',
                'link':"https://twitter.com/{0}/status/{1}".format(tweetinfo['user_name'],tweetinfo['id_str'])
            }
        if argmap['tempID'] == -1:
            argmap['tempID'] = '未生成'
        tweetinfo['argmap'] = argmap
        return argmap
    #将推特数据应用到模版
    def tweetToMsg(self,tweetinfo:dict,nick = None,template:str = None) -> SendMessage:
        if not template:
            template = "推文ID：$ID\n推文标识：$typestr\n发布用户：$nick($user_ID)\n推文内容：$text $imgs\n发布时间：$fulltime"
            template = template + "\n$relatestart---------------\n"
            template = template + "依赖推文ID：$relate_ID\n依赖用户：$relate_user_name($relate_user_ID)\n依赖内容：$relate_text $relate_imgs\n发布时间：$relate_fulltime"
            template = template + "$relateend\n临时推文ID：#$tempID"
        
        #特殊变量(仅识别一次) $relatestart、$relateend:用于分隔依赖推文与主推文
        #特殊变量(仅识别一次) $ifrelate 依赖存在时 $else 不存在时 $end
        msg = SendMessage()
        #生成模版参数地图
        argmap = self.tweetinfoGetMap(tweetinfo)
        if tweetinfo['relate']:
            if not argmap['relate']:
                relate = self.tweetinfoGetMap(tweetinfo['relate'])
                for key in relate:
                    argmap['relate_'+key] = relate[key]
                argmap['relate_imgs'] = '[!relate_imgs!]'
                argmap['relate'] = True
        else:
            argmap['relate'] = False
        argmap['nick'] = nick
        if not argmap['nick'] or argmap['nick'].strip() == '':
            argmap['nick'] = argmap['user_name']
        #模版处理
        if not argmap['relate']:
            res = template.split('$relatestart',maxsplit = 1)
            template = res[0]
            if res[1]:
                res = res[1].split('$relateend',maxsplit = 1)
                if res[1]:
                    template = template + res[1]

        res = template.split('$ifrelate',maxsplit=1)
        template = res[0]
        if res[1]:
            res = res[1].split('$else',maxsplit = 1)
            if argmap['relate']:
                template = template + res[0]
            else:
                if res[1]:
                    template = template + res[1]
        #应用模版
        st = tweetToStrTemplate(template)
        stres = st.safe_substitute(argmap)
        #处理图片(仅处理一次)
        lock = False
        relate_lock = False
        spls = stres.partition('[!imgs!]')
        for spl in spls:
            if spl == '':
                continue
            sspls = spl.split('[!relate_imgs!]')
            for sspl in sspls:
                if sspl == '':
                    continue
                if sspl == '[!imgs!]':
                    if lock:
                        msg.append('[图片]')
                        continue
                    for src in argmap['imgs']:
                        msg.append(msg.baleImgObj(src))
                    lock = True
                elif sspl == '[!relate_imgs!]':
                    if relate_lock:
                        msg.append('[图片]')
                        continue
                    for src in argmap['relate_imgs']:
                        msg.append(msg.baleImgObj(src))
                    relate_lock = True
                else:
                    msg.append(sspl.replace('[!imgs!]','[图片]').replace('[!relate_imgs!]','[图片]'))
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
            template = "{nick}({user_name})的{des}更新了：{oldkey}->{newkey}"
        msg = SendMessage()
        stl = template.format(**userupdata)
        res = stl.split('[旧头像]',maxsplit = 1)
        msg.append(res[0])
        if res[1]:
            msg.append(msg.baleImgObj(userupdata['oldimg']))
            res = res[1].split('[新头像]',maxsplit = 1)
            msg.append(res[0])
            if res[1]:
                msg.append(msg.baleImgObj(userupdata['newimg']))
                msg.append(res[1])
        return msg

    #图片保存(文件名,下载url,基目录-'img',是否覆盖-否),返回值->(是否成功，描述，文件路径，完整文件名)
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
            #下载图片，并保存到文件夹中
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
        if not pushlist.getUnitConfKey(pushunit,'upimg') and isinstance(message,msgStream.SendMessage):
            message.designatedTypeToStr('img')
        return msgStream.send_msg(**pushlist.baleSendTarget(pushunit,message))

pushlist = TweePushList(init = True)
tweetcache = TweetCache()
tweetstatusdeal = TweetStatusDeal(pushlist,tweetcache)
tweetevendeal = TweetEventDeal(tweetstatusdeal)

#新事件缓存
newevenscache = TempMemory('evencache',limit = 100)

"""
运行线程信息，及更新合并请求提交
*线程保证status处理顺序的提交
"""
Submitqueque = queue.Queue(128) #更新提交待处理
tweetEvenQueue = queue.Queue(64) #事件队列
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
        #仅处理值得关注的推文
        if notable:
            even = tweetevendeal.bale_event('listen',tweetinfo['type'],tweetinfo['user_id'],tweetinfo)
            on_even(even,'推文推送')
            #被动推送
            if tweetinfo['relate'] and \
                tweetinfo['relate']['version'] and \
                tweetinfo['relate']['notable'] and \
                tweetinfo['type'] in ('quoted','reply_to_status','reply_to_user'):#被动推送标识检查
                even = tweetevendeal.bale_event('reverse',tweetinfo['type'],tweetinfo['relate']['user_id'],tweetinfo)
                on_even(even,'被动推送')
        for usereven in userevens:
            on_even(usereven,'用户事件推送')
        if test != None:
            try:
                test.on_status(tweetinfo,status)
            except:
                pass
    except:
        s = traceback.format_exc(limit=5)
        logger.error(s)
def on_status(status,merge = False):
    try:
        res = tweetevendeal.dealSourceData(status)
        if merge:
            #检查推文是否被处理过，处理过的推文直接忽略
            if tweetcache.findTweetTempID(res['tweetinfo']['id']) > 0:
                return
        on_resFromDealSourceData(**res)
    except:
        s = traceback.format_exc(limit=5)
        msgStream.exp_send('推文源数据处理时异常',source='推文源',flag = '错误')
        logger.error(status)
        logger.error(s)

#事件处理队列(消耗事件)
def eventDeal():
    while True:
        even = run_info['Eventqueque'].get()
        try:
            run_info['tweetevendeal'].deal_event(even)
            #控制台事件输出
            logger_Event.info(run_info['tweetevendeal'].eventToStr(even))
        except:
            s = traceback.format_exc(limit=5)
            logger.warning(s)
        run_info['queque'].task_done()

#预处理提交(预处理,默认进行合并检查)
def submitStatus(status,merge:bool = True,source = '未知',timeout = 5,block=True):
    try:
        run_info['Submitqueque'].put((status,merge),timeout=timeout,block=True)
    except:
        s = traceback.format_exc(limit=5)
        notice = '推特预处理队列异常或溢出，请检查队列！'
        msgStream.exp_send(notice,source=source+'预处理提交',flag = '异常')
        logger.error(notice + '\n' + s)
#预处理队列
def submitDeal():
    while True:
        onstatusunit = run_info['Submitqueque'].get()
        try:
            on_status(onstatusunit[0],merge = onstatusunit[1])
        except:
            s = traceback.format_exc(limit=5)
            logger.warning(s)
        run_info['Submitqueque'].task_done()

#运行推送线程
def runTwitterApiThread():
    logger.info("TwitterEvenPush 已启动")
    #预处理队列维护线程
    run_info['SubmitStatusThread'] = threading.Thread(
        group=None, 
        target=submitDeal, 
        name='tweetPushDealThread',
        daemon=True
    )
    run_info['SubmitStatusThread'].start()
    #事件队列维护线程
    run_info['EventDealThread'] = threading.Thread(
        group=None, 
        target=eventDeal, 
        name='tweetPushDealThread',
        daemon=True
    )
    run_info['EventDealThread'].start()
    return run_info