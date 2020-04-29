# -*- coding: UTF-8 -*-
import string
#引入配置
import config
#日志输出
from helper import data_read,data_save
'''
推送列表维护
'''
PushList_config_name = 'PushListData.json'
base_tweet_id = config.base_tweet_id
#推送列表
class PushList:
    #映射推送关联(推送对象(type:str,ID:int)->推送单元)
    __push_list = {
        'private':{},
        'group':{}
    } 
    __spy_relate = {} #映射对象关联(监测ID(ID:int)->推送单元)
    spylist = [str(base_tweet_id)] #流监测列表
    
    #支持的消息类型
    message_type_list = ('private','group') 
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
        #推特个人信息变动推送开关
        'change_ID','change_name','change_description',
        'change_headimgchange'
        )
    """
        推送列表-》推送列表、监测人信息关联表及监测人单的列表-》推送单元
        注：每个推送单元绑定一个推特用户ID以及一个推送对象(群或QQ)
        注：推送单元的配置由其推送对象全局配置以及自身DIY设置共同完成
    """
    #清空推送设置
    def clear(self):
        self.__push_list = {
            'private':{},
            'group':{}
        } 
        self.__spy_relate = {} #映射对象关联(监测ID(ID:int)->推送单元)
        self.spylist = [str(base_tweet_id)] #流监测列表
    #推送单元解包
    def getAllPushUnit(self) -> list:
        sourcedata = self.__spy_relate.copy()
        PushUnits = []
        for PushUnitList in sourcedata.values():
            for PushUnit in PushUnitList:
                PushUnits.append(PushUnit)
        return PushUnits
    def savePushList(self) -> tuple:
        PushUnits = self.getAllPushUnit()
        return data_save(PushList_config_name,PushUnits)
    def readPushList(self) -> tuple:
        data = data_read(PushList_config_name)
        if data[0] != False:
            self.clear()
            for PushUnit in data[2]:
                self.addPushunit(PushUnit)
            return (True,data[1])
        return data
    #打包成推送单元中(推送类型-群/私聊，推送对象-群号/Q号,绑定的推特用户ID,单元描述,绑定的酷Q账号,推送模版,各推送开关)
    def baleToPushUnit(self,bindCQID:int,
                        pushtype:str,
                        pushID:int,
                        tweet_user_id:int,
                        des:str,
                        nick:str='',**config):
        Pushunit = {}
        if not config:
            config = {}
        #固有属性
        Pushunit['bindCQID'] = bindCQID #绑定的酷Q帐号(正式上线时将使用此帐户进行发送，用于适配多酷Q账号)
        Pushunit['type'] = pushtype #group/private
        Pushunit['pushTo'] = pushID #QQ号或者群号
        Pushunit['tweet_user_id'] = tweet_user_id #监测ID
        Pushunit['nick'] = nick #推送昵称(默认推送昵称为推特screen_name)
        Pushunit['des'] = des #单元描述
        Pushunit['config'] = config
        return Pushunit
    #增加一个推送单元，返回状态元组(布尔型-是否成功,字符串-消息)
    def addPushunit(self,Pushunit) -> tuple:
        if Pushunit['pushTo'] in self.__push_list[Pushunit['type']]:
            if Pushunit['tweet_user_id'] in self.__push_list[Pushunit['type']][Pushunit['pushTo']]['pushunits']:
                return ( False, '推送单元已存在' )
        else:
            #初始化推送对象(推送全局属性)
            self.__push_list[Pushunit['type']][Pushunit['pushTo']] = {
                #为推送对象设置全局默认属性
                'Pushunitattr':config.pushunit_default_config.copy(),
                #推送单元组
                'pushunits':{}
            }
        #添加单元至推送列表
        self.__push_list[Pushunit['type']][Pushunit['pushTo']]['pushunits'][Pushunit['tweet_user_id']] = Pushunit
        #同步监测关联（内部同步了监测列表）
        if Pushunit['tweet_user_id'] not in self.__spy_relate:
            self.__spy_relate[Pushunit['tweet_user_id']] = []
            if str(Pushunit['tweet_user_id']) != base_tweet_id:
                self.spylist.append(str(Pushunit['tweet_user_id']))
        self.__spy_relate[Pushunit['tweet_user_id']].append(Pushunit)
        return ( True, '添加成功！' )
    #删除一个推送单元，没有返回值
    def delPushunit(self,Pushunit):
        #从推送列表中移除推送单元
        del self.__push_list[Pushunit['type']][Pushunit['pushTo']]['pushunits'][Pushunit['tweet_user_id']]
        #从监测列表中移除推送单元
        self.__spy_relate[Pushunit['tweet_user_id']].remove(Pushunit)
        #检查监测对象的推送单元是否为空，为空则移出监测列表
        if self.__spy_relate[Pushunit['tweet_user_id']] == []:
            del self.__spy_relate[Pushunit['tweet_user_id']]
            if str(Pushunit['tweet_user_id']) != base_tweet_id:
                self.spylist.remove(str(Pushunit['tweet_user_id']))
        #鲨掉自己
        del Pushunit
    #获取一个推送单元，返回状态列表(布尔型-是否成功,字符串-消息/Pushunit)
    def getPushunit(self,message_type:str,pushTo:int,tweet_user_id:int) -> list:
        if message_type not in self.message_type_list:
            raise Exception("无效的消息类型！",message_type)
        if pushTo not in self.__push_list[message_type]:
            return (False,'推送对象不存在！')
        if tweet_user_id not in self.__push_list[message_type][pushTo]['pushunits']:
            return (False,'推送单元不存在！')
        return (True,self.__push_list[message_type][pushTo]['pushunits'][tweet_user_id])

    #获取推送单元某个属性的值 返回值-(布尔型-是否成功,字符串-消息/属性内容)
    def getPuslunitAttr(self,Pushunit,key) -> tuple:
        if key in Pushunit['config']:
            return (True,Pushunit['config'][key])
        if key not in self.__push_list[Pushunit['type']][Pushunit['pushTo']]['Pushunitattr']:
            return (False,'不存在此属性')
        res = self.__push_list[Pushunit['type']][Pushunit['pushTo']]['Pushunitattr'][key]
        return (True,res)
    
    #返回监测对象关联的推送单元组,监测对象不存在时返回空列表[]
    def getLitsFromTweeUserID(self,tweet_user_id:int) -> list:
        if tweet_user_id not in self.__spy_relate:
            return []
        return self.__spy_relate[tweet_user_id].copy()
    #返回推送对象关联的推送单元组,推送对象不存在时返回空列表[]
    def getLitsFromPushTo(self,message_type:str,pushTo:int) -> list:
        if message_type not in self.message_type_list:
            raise Exception("无效的消息类型！",message_type)
        if pushTo not in self.__push_list[message_type]:
            return []
        dict_ = self.__push_list[message_type][pushTo]['pushunits']
        res = []
        for v in dict_.values():
            res.append(v)
        return res
    #返回推送对象关联的推送单元组-带ID,推送对象不存在时返回空列表[]
    def getLitsFromPushToAndID(self,message_type:str,pushTo:int) -> dict:
        if message_type not in self.message_type_list:
            raise Exception("无效的消息类型！",message_type)
        if pushTo not in self.__push_list[message_type]:
            return []
        return self.__push_list[message_type][pushTo]['pushunits']
    #返回推送对象关联的推送属性组,推送对象不存在时返回空字典{}
    def getAttrLitsFromPushTo(self,message_type:str,pushTo:int) -> dict:
        if message_type not in self.message_type_list:
            raise Exception("无效的消息类型！",message_type)
        if pushTo not in self.__push_list[message_type]:
            return {}
        return self.__push_list[message_type][pushTo]['Pushunitattr']

    #移除某个监测对象关联的所有推送单元,参数-推特用户ID 返回值-(布尔型-是否成功,字符串-消息)
    def delPushunitFromTweeUserID(self,tweet_user_id:int) -> tuple:
        if tweet_user_id not in self.__spy_relate:
            return (False,'此用户不在监测列表中！')
        table = self.getLitsFromTweeUserID(tweet_user_id)
        if table == []:
            return (True,'移除成功！')
        for Pushunit in table:
            self.delPushunit(Pushunit)
        return (True,'移除成功！')
    #移除某个推送对象关联的所有推送单元,参数-消息类型，对象ID，CQID 返回值-(布尔型-是否成功,字符串-消息)
    def delPushunitFromPushTo(self,message_type:str,pushTo:int,self_id:int = 0) -> tuple:
        if message_type not in self.message_type_list:
            raise Exception("无效的消息类型！",message_type)
        table = self.getLitsFromPushTo(message_type,pushTo)
        if table == []:
            return (True,'移除成功！')
        for Pushunit in table:
            if self_id == 0 or self_id == Pushunit['bindCQID']:
                self.delPushunit(Pushunit)
        return (True,'移除成功！')
    #移除某个推送单元,参数-消息类型，对象ID 返回值-(布尔型-是否成功,字符串-消息)
    def delPushunitFromPushToAndTweetUserID(self,message_type:str,pushTo:int,tweet_user_id:int) -> tuple:
        if message_type not in self.message_type_list:
            raise Exception("无效的消息类型！",message_type)
        if pushTo not in self.__push_list[message_type]:
            return (False,'推送对象不存在！')
        if tweet_user_id not in self.__push_list[message_type][pushTo]['pushunits']:
            return (False,'推送单元不存在！')
        self.delPushunit(self.__push_list[message_type][pushTo]['pushunits'][tweet_user_id])
        return (True,'移除成功！')

    #设置指定推送对象的全局属性
    def PushTo_setAttr(self,message_type:str,pushTo:int,key:str,value) -> tuple:
        if message_type not in self.message_type_list:
            raise Exception("无效的消息类型！",message_type)
        if key not in self.Pushunit_allowEdit:
            return (False,'指定属性不存在！')
        if pushTo not in self.__push_list[message_type]:
            return (False,'推送对象不存在！')
        self.__push_list[message_type][pushTo]['Pushunitattr'][key][value]
        return (True,'属性已更新')
    #设置指定推送单元的特定属性
    def setPushunitAttr(self,message_type:str,pushTo:int,tweet_user_id:int,key:str,value):
        if message_type not in self.message_type_list:
            raise Exception("无效的消息类型！",message_type)
        if key not in self.Pushunit_allowEdit:
            return (False,'指定属性不存在！')
        if pushTo not in self.__push_list[message_type]:
            return (False,'推送对象不存在！')
        if tweet_user_id not in self.__push_list[message_type][pushTo]['pushunits']:
            return (False,'推送单元不存在！')
        self.__push_list[message_type][pushTo]['pushunits'][tweet_user_id][key][value]
        return (True,'属性已更新')
#字符串模版
class tweetToStrTemplate(string.Template):
    delimiter = '$'
    idpattern = '[a-z]+_[a-z_]+'
#建立列表
push_list = PushList()


