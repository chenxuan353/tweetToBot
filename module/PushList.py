from helper import dictInit,dictHas,dictGet,dictSet
from helper import data_read,data_save
"""
推送列表
监测对象UUID与推送单元关联表
多层推送单元关联列表

·推送单元
指定推送对象(bottype、botuuid)
推送信息(receivegroup|接收组、receiveuuid|接收者、receiveobj|接收者附加信息、pushconfig|推送配置、pushobj|推送附加信息)
receiveobj:额外的接收者信息
pushobj:提供额外的推送信息(增强兼容)
监听信息(spyuuid|监测对象uuid,spyobj|监听附加信息)
spyobj:提供额外的监听信息(增强兼容)
对象操作信息(create_opuuid、create_timestamp、createobj、lastedit_opuuid、lastedit_timestamp、lasteditobj)
createobj:额外的创建对象信息
lasteditobj:额外的最后编辑对象信息
"""
class PushList:
    puth_type = '' 
    push_list = {} #推送对象与推送单元的关联
    spy_relate = {} #监测对象与推送单元的关联(用于创建推送触发器)
    spylist = [] #直接监听列表(通过触发器更新)
    def __init__(self,puth_type:str,configfilename:str,basepath:str = 'pushlist'):
        self.puth_type = puth_type #推送标识(RSS、tweet等)
        self.configfilename = configfilename
        self.basepath = basepath

    def pushcheck_trigger(self,unit,**pushunit) -> bool:
        return True
    def setPushToAttr_trigger(self,pushtoconfig:dict,setkey:str,setvalue) -> tuple:
        return (False,'未设置全局属性设置触发器')
    def setPushUnitAttr_trigger(self,pushtoconfig:dict,config:dict,setkey:str,setvalue) -> tuple:
        return (False,'未设置单元属性设置触发器')
    #重置推送
    def clear(self):
        self.push_list.clear()
        self.spy_relate.clear()
        self.spylist.clear()
    #获取监测长度
    def getSpyNum(self):
        return len(self.spylist)
    def getSpylist(self):
        return self.spylist
    #获取所有推送单元
    def getAllPushUnit(self) -> list:
        sourcedata = self.push_list.copy()
        PushUnits = []
        for bottypes in sourcedata.values():
            for botuuids in bottypes.values():
                for botgroups in botuuids.values():
                    for pushTo in botgroups.values():
                        #pushTo['config']
                        for pushunit in pushTo['pushlist']:
                            PushUnits.append(pushunit)
        return PushUnits
    def resetSpyRelate(self):
        PushUnits = self.getAllPushUnit()
        self.spy_relate.clear()
        for pushunit in PushUnits:
            self.__addToSpyRelate(pushunit)

    def init(self):
        self.load()
    def hasSpy(self,spyuuid:str):
        spyuuid = str(spyuuid)
        return spyuuid in self.spylist
    #保存与读取
    def load(self,filename:str = None,path:str = None) -> tuple:
        if not filename:
            filename = self.configfilename
        if not path:
            path = self.basepath
        data = data_read(filename,path)
        if data[0] != False:
            self.clear()
            self.push_list = data[2].copy()
            self.resetSpyRelate()
            return (True,data[1])
        return data
    def save(self,filename:str = None,path:str = None) -> tuple:
        if not filename:
            filename = self.configfilename
        if not path:
            path = self.basepath
        return data_save(filename,self.push_list,path)

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
        spyuuid = str(spyuuid)
        botuuid = str(botuuid)
        receiveuuid = str(receiveuuid)
        pushunit = {}
        pushunit['bottype'] = bottype
        pushunit['botuuid'] = botuuid
        pushunit['receivegroup'] = receivegroup
        pushunit['receiveuuid'] = receiveuuid
        pushunit['receiveobj'] = receiveobj
        pushunit['pushconfig'] = pushconfig
        pushunit['pushobj'] = pushobj

        pushunit['spyuuid'] = spyuuid
        pushunit['spyobj'] = spyobj
        
        pushunit['create_opuuid'] = create_opuuid
        pushunit['createobj'] = createobj
        pushunit['create_timestamp'] = create_timestamp

        pushunit['lastedit_opuuid'] = lastedit_opuuid
        pushunit['lasteditobj'] = lasteditobj
        pushunit['lastedit_timestamp'] = lastedit_timestamp
        return pushunit

    #单元增删
    def hasPushunit(self,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str,spyuuid:str) -> bool:
        return dictHas(self.push_list,bottype,botuuid,receivegroup,receiveuuid,spyuuid)
    def hasPushunit_kw(self,*,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str,spyuuid:str,**kw) -> bool:
        return self.hasPushunit(bottype,botuuid,receivegroup,receiveuuid,spyuuid)
    def findPushunit(self,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str,spyuuid:str) -> dict:
        return dictGet(self.push_list,bottype,botuuid,receivegroup,receiveuuid,spyuuid)
    def findPushunit_kw(self,*,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str,spyuuid:str,**kw) -> dict:
        return self.findPushunit(bottype,botuuid,receivegroup,receiveuuid,spyuuid)

    def initPushTo_args(self,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str,defaultConfig:dict):
        defaultobj = {
            'config':defaultConfig,
            'pushlist':{}
        }
        dictInit(self.push_list,bottype,botuuid,receivegroup,receiveuuid,endobj=defaultobj)
        return (True,'成功')
    def initPushTo_kw(self,defaultConfig:dict,*,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str,**kw):
        return self.initPushTo_args(bottype,botuuid,receivegroup,receiveuuid,defaultConfig)
    def initPushTo(self,defaultConfig:dict,pushunit):
        return self.initPushTo_kw(defaultConfig,**pushunit)

    def __addToSpyList(self,spyuuid):
        if spyuuid not in self.spylist:
            self.spylist.append(spyuuid)
    def __addToSpyRelate(self,pushunit):
        spyuuid = pushunit['spyuuid']
        dictInit(self.spy_relate,spyuuid,endobj=set())
        spyunit:set = self.spy_relate[spyuuid]
        spyunit.add(pushunit)
    def __addPushunit(self,pushunit,*,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str,spyuuid:str,**kw):
        if self.pushcheck_trigger:
            if not self.pushcheck_trigger(pushunit,**pushunit):
                return (False,"单元检查不通过！")
        
        dictSet(self.push_list,bottype,botuuid,receivegroup,receiveuuid,spyuuid,obj=pushunit)
        self.__addToSpyRelate(pushunit)
        self.__addToSpyList(spyuuid)
        return (True,"成功！")
    def addPushunit(self,pushunit:dict,defaultConfig:dict):
        #非覆盖式单元添加(添加的单元，默认推送对象配置)
        """
            pushunit['bottype'] = bottype
            pushunit['botuuid'] = botuuid
            pushunit['receivegroup'] = receivegroup
            pushunit['receiveuuid'] = receiveuuid
            pushunit['receiveobj'] = receiveobj
            pushunit['pushconfig'] = pushconfig
            pushunit['pushobj'] = pushobj

            pushunit['spyuuid'] = spyuuid
            pushunit['spyobj'] = spyobj
            
            pushunit['create_opuuid'] = create_opuuid
            pushunit['createobj'] = createobj
            pushunit['create_timestamp'] = create_timestamp

            pushunit['lastedit_opuuid'] = lastedit_opuuid
            pushunit['lasteditobj'] = lasteditobj
            pushunit['lastedit_timestamp'] = lastedit_timestamp
        """
        self.initPushTo(defaultConfig,pushunit)
        
        if self.hasPushunit_kw(**pushunit):
            return (False,'指定推送对象已存在！')
        res = self.__addPushunit(pushunit,**pushunit)
        if not res[0]:
            return res
        return res
    def __delToSpyList(self,spyuuid):
        if spyuuid not in self.spylist:
            return
        relates = dictGet(self.spy_relate,spyuuid)
        if not relates or len(relates) == 0:
            self.spylist.remove(spyuuid)
    def __delToSpyRelate(self,pushunit):
        spyuuid = pushunit['spyuuid']
        if spyuuid not in self.spy_relate:
            return
        spylist:set = self.spy_relate[spyuuid]
        spylist.discard(pushunit)
    def __delPushunit(self,pushunit,*,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str,spyuuid:str,**kw):
        recpoint = dictGet(self.push_list,bottype,botuuid,receivegroup,receiveuuid)
        searchpushunit = recpoint[spyuuid]
        if pushunit != searchpushunit:
            return (False,"待删除推送对象与已存在的推送对象不符")
        self.__delToSpyRelate(searchpushunit)
        self.__delToSpyList(spyuuid)
        del recpoint[spyuuid]
        return (True,"成功！")
    def delPushunit(self,pushunit:dict):
        if not self.hasPushunit_kw(**pushunit):
            return (False,'指定推送对象不存在！')
        res = self.__delPushunit(pushunit,**pushunit)
        if not res[0]:
            return res
        return res
    
    #资讯获取接口
    def getPushTo(self,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str):
        return dictGet(self.spylist,bottype,botuuid,receivegroup,receiveuuid)
    def getPushTo_kw(self,*,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str,**kw):
        return dictGet(self.spylist,bottype,botuuid,receivegroup,receiveuuid)
    def getUnitPushToConfig(self,pushunit):
        return self.getPushTo_kw(**pushunit)
    def baleSendTarget(self,pushunit,message):
        #bottype:str,botuuid:str,botgroup:str,senduuid:str,sendObj:dict,message:SendMessage
        sendtarget = {}
        sendtarget['bottype'] = pushunit['bottype']
        sendtarget['botuuid'] = pushunit['botuuid']
        sendtarget['botgroup'] = pushunit['receivegroup']
        sendtarget['senduuid'] = pushunit['receiveuuid']
        sendtarget['sendObj'] = pushunit['receiveobj']
        sendtarget['message'] = message
        return sendtarget

    #返回监测对象关联的推送单元组,监测对象不存在时返回空列表[]
    def getLitsFromTweeUserID(self,spyuuid:str) -> list:
        return list(dictGet(self.spy_relate,spyuuid,default=[]))
    #返回推送对象关联的推送单元组,推送对象不存在时返回空列表[]
    def getLitsFromPushTo(self,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str) -> list:
        res = dictGet(self.spylist,bottype,botuuid,receivegroup,receiveuuid,default=None)
        if not res:
            return []
        return list(res['pushlist'].values())
    #返回推送对象关联的推送单元组-带ID,推送对象不存在时返回空列表{}
    def getLitsFromPushToAndID(self,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str) -> dict:
        res = dictGet(self.spylist,bottype,botuuid,receivegroup,receiveuuid,default=None)
        if not res:
            return {}
        return res['pushlist']
    #返回推送对象关联的推送属性组,推送对象不存在时返回空字典{}
    def getConfigFromPushTo(self,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str) -> dict:
        pushto = self.getPushTo(bottype,botuuid,receivegroup,receiveuuid)
        if not pushto:
            return {}
        return pushto['config']
    #移除某个监测对象关联的所有推送单元,参数-监测对象UUID 返回值-(布尔型-是否成功,字符串-消息)
    def delPushunitFromSpyUUID(self,spyuuid:str) -> tuple:
        if spyuuid not in self.spy_relate:
            return (False,'此用户不在监测列表中！')
        table = self.getLitsFromTweeUserID(spyuuid)
        if table == []:
            return (True,'移除成功！')
        for pushunit in table:
            self.delPushunit(pushunit)
        return (True,'移除成功！')
    #移除某个推送对象关联的所有推送单元,参数-消息类型，对象ID，CQID 返回值-(布尔型-是否成功,字符串-消息)
    def delPushunitFromPushTo(self,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str) -> tuple:
        table = self.getLitsFromPushTo(bottype,botuuid,receivegroup,receiveuuid)
        if table == []:
            return (True,'移除成功！')
        for pushunit in table:
            self.delPushunit(pushunit)
        return (True,'移除成功！')
    #移除某个推送单元,参数-消息类型，对象ID 返回值-(布尔型-是否成功,字符串-消息)
    def removePushunit(self,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str,spyuuid:str) -> tuple:
        pushunit = self.findPushunit(bottype,botuuid,receivegroup,receiveuuid,spyuuid)
        if not pushunit:
            return (False,'推送单元不存在！')
        res = self.delPushunit(pushunit)
        if not res[0]:
            return res
        return (True,'移除成功！')

    #设置指定推送对象的特定属性
    def PushTo_setAttr(self,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str,setkey,setvalue) -> tuple:
        pushto = self.getPushTo(bottype,botuuid,receivegroup,receiveuuid)
        if not pushto:
            return (False,'推送对象不存在！')
        res = self.setPushToAttr_trigger(pushto['config'],setkey,setvalue)
        return res
    #设置指定推送单元的特定属性
    def setPushunitAttr(self,bottype:str,botuuid:str,receivegroup:str,receiveuuid:str,spyuuid:str,setkey,setvalue):
        pushto = self.getPushTo(bottype,botuuid,receivegroup,receiveuuid)
        if not pushto:
            return (False,'推送对象不存在！')
        pushunit = self.findPushunit(bottype,botuuid,receivegroup,receiveuuid,spyuuid)
        if not pushunit:
            return (False,'推送单元不存在！')
        res = self.setPushUnitAttr_trigger(pushto['config'],pushunit['pushconfig'],setkey,setvalue)
        return res








































