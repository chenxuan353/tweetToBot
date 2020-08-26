# -*- coding: UTF-8 -*-
import re
import traceback
from module.msgStream import SendMessage
from pluginsinterface.TypeExtension import PlugMsgTypeEnum
from helper import getlogger
logger = getlogger(__name__)
"""
插件消息过滤类
"""

class PlugMsgFilter:
    """
        使用正则表达式匹配消息起始部分，会忽略标准数据段以外的数据段
        正则表达式起始不为(时将使用()包裹参数
    """
    def __init__(self,filterstr:str = ''):
        if type(filterstr) != str:
            raise Exception('过滤参数不为文本')
        if not filterstr.startswith('('):
            filterstr = '(' + filterstr + ')'
        if filterstr.find(r'\b)') == -1:
            filterstr = filterstr.replace(')',r'\b)')
        self.filterstr = filterstr
    def filter(self,smsg:SendMessage) -> list:
        msg = smsg
        if type(msg) != str:
            msg = smsg.toStandStr()
        return self.reDealStr(self.filterstr,msg)
    def replace(self,msg:str):
        res = self.reDealStr(self.filterstr,msg)
        if type(res) == str:
            return msg.replace(res,'',1)
        return msg
    @staticmethod
    def reDealStr(pat:str,msg:str) -> list:
        #使用正则表达式捕获组处理字符串
        res = []
        try:
            resm = re.match(pat,msg, re.M | re.S)
        except:
            logger.info(pat)
            logger.info(msg)
            return []
        if resm is None:
            return []
        for reg in resm.groups():
            if reg is not None:
                res.append(reg)
        if len(res) == 1:
            return res[0]
        return res
class PlugArgFilter:
    """
        对参数部分进行处理(参数为SendMessage时会调用SendMessage的toSimpleStr)
            参数默认使用全角空格或半角空格进行每一段的分割
            每段会执行首尾置空以最大化兼容
            例：aaa bbb ccc ->{'arg1':'aaa','arg2':'bbb','arg3':'ccc'}
            参数分离
                以参数限制表的name为键
                以处理结果为值
                处理后剩余文本固定为tail键的值
        :param filterstr: 
            文本形过滤参数，每参数以一个半角空格分割
            default
                默认值，存在时参数可跳过
            verif 
                预先定义的验证规则(str、int、float、uint、dict、list、bool、other-不验证)
            格式
                argname1:verifstr argname2:verifstr:default
    """
    def __init__(self,filterstr:str = ''):
        if type(filterstr) != str:
            raise Exception('过滤参数不为文本')
        self.arglimits = []
        try:
            if filterstr == '':
                return
            args = filterstr.split(' ')
            for arg in args:
                argunit = arg.split(':')
                self.addArg(
                    argunit[0],
                    argunit[0],
                    argunit[0],
                    canSkip=(False if len(argunit) <= 2 else True),
                    vlimit=(None if len(argunit) <= 2 else {'':argunit[2]}),
                    verif = argunit[1]
                    )
        except:
            s = traceback.format_exc(limit=10)
            logger.error(s)
            raise Exception('过滤参数序列化时异常，请检查参数->{filterstr}'.format(filterstr = filterstr))
    def filter(self,smsg:SendMessage) -> list:
        """
            参数处理函数，通过简单配置自动切分参数
            参数
                :param msg: 待处理数据
                :param arglimits: 参数配置表，类型list，配置表单元详见addArg
            返回值 
                正常时 (True,参数表)
                异常时 (False,参数昵称,错误描述,参数描述)
        """
        msg = smsg
        if isinstance(msg,SendMessage):
            msg = msg.toStandStr()
        return self.argDeal(msg,self.arglimits)
    def addArgLimit(self,arglimit:dict):
        self.arglimits.append(arglimit)
    def addArg(self,
                    name:str,nick:str,des:str,
                    canSkip:bool = False,prefunc = None,
                    verif:str = 'str',vlimit:dict = None,
                    re:str = None,re_error:str = '',
                    func = None):
        """
            打包并添加参数分离限制表

            执行顺序 prefunc -> vlimit -> verif|类型验证 -> re -> func -> verif|类型转换
            :param name: 参数名，作为返回表的键值，不能重复
            :param nick: 错误时返回的参数昵称
            :param des: 参数介绍，错误时作为返回参数之一，也作为自动参数列表依据()
            :param canSkip: 定义为可跳过时参数不符合验证规则将使用默认值
            :param prefunc: 
                预处理函数，参数被分离后，处理前的阶段，例:(lambda arg:arg.strip())
                返回值为None或(False,"")时认定为参数无效
                返回值为(True,更新值)时使用更新值将作为此段arg的新值
                其他返回值将作为此段arg的新值
            :param verif: 预先定义的验证规则(str、int、float、uint、dict、list、bool、other-不验证)
            :param vlimit: 
                参数限制表(限制参数内容,空表则不限制),类型为dict
                为list或tuple时将被转换 例(1,2,3)或[1,2,3] -> {1:'',2:'',3:''}
                若list或tuple中不存在空字符串时默认值将设为第一个元素，没有元素或存在''时设置为{'':''}
                '*':''表示允许任意字符串,键值不为空时任意字符串将被转变为对应值
                '匹配值':'修正值'修正值为空时不进行修正
            :param re: 正则表达式匹配(match函数)
            :param re_error: 正则匹配不通过时的错误信息
            :param func: 
                函数，做返回前的处理，倒数第二步处理，最后一步为类型verif转换
                函数签名：fun(arg,arglimit)
            :return: ArgLimit
        """
        if type(vlimit) == list or type(vlimit) == tuple:
            newvlimit = {}
            for v in vlimit:
                newvlimit[v] = ''
            if '' not in newvlimit:
                newvlimit[''] = ('' if len(vlimit) == 0 else vlimit[0])
            vlimit = newvlimit
        arglimit = self.baleArgLimit(name,nick,des,
                    canSkip = canSkip,prefunc = prefunc,
                    verif = verif,vlimit = vlimit,
                    re = re,re_error = re_error,
                    func = func)
        self.arglimits.append(arglimit)
    @staticmethod
    def baleArgLimit(
                    name:str,nick:str,des:str,
                    canSkip:bool = False,prefunc = None,
                    verif:str = 'str',vlimit:dict = None,
                    re:str = None,re_error:str = '',
                    func = None):
        """
            打包参数分离限制表
            见addArg
        """
        if name == 'tail':
            raise Exception('参数名不能为tail')
        if canSkip:
            if not vlimit or '' not in vlimit:
                raise Exception('参数为可跳过时vlimit必须有默认值{\'\':\'默认值\'}')
        return {
            'name':name,
            'nick':nick,
            'des':des,
            'canSkip':canSkip,
            'prefunc':prefunc,
            'verif':verif,
            'vlimit':vlimit,
            're':re,
            're_error':re_error,
            'func':func
        }
    @staticmethod
    def arglimitdeal(ls:dict):
        """
            反向字典映射，最后声明的映射会将之前的声明覆盖
                {
                    a:[a1,b1,c1],
                    b:[b1]
                }=>{
                    a1:a,
                    b1:b,
                    c1:a
                }
        """
        res = {}
        for k in ls.keys():
            res[k]=k
            if type(ls[k]) is list:
                for v in ls[k]:
                    res[v]=k
            else:
                res[res[k]]=k
        return res
    @staticmethod
    def reDealStr(pat:str,msg:str) -> list:
        #使用正则表达式处理字符串
        res = []
        resm = re.match(pat,msg, re.M | re.S)
        if resm == None:
            return None
        for reg in resm.groups():
            res.append(reg)
        if len(res) == 1:
            return res[0]
        return res
    @staticmethod
    def argDeal(msg:str,arglimits:list) ->tuple:
        """
            参数处理函数，通过简单配置自动切分参数
            参数
                :param msg: 待处理数据
                :param arglimits: 参数配置表，类型list，配置表单元详见addArg
            返回值 
                正常时 (True,参数表)
                异常时 (False,参数昵称,错误描述,参数描述)
        """
        if not arglimits:
            return (True,{'tail':msg.strip()})
        def vfloat(arg):
            try:
                float(hmsg)
            except:
                return False
            return True
        veriffun = {
            'int':{
                'verif':(lambda arg:type(arg) is int or type(arg) is str and arg.isdecimal()),
                'res':int
            },
            'uint':{
                'verif':(lambda arg:(type(arg) is int or type(arg) is str and arg.isdecimal()) and int(arg) >= 0),
                'res':int
            },
            'uintnozero':{
                'verif':(lambda arg:(type(arg) is int or type(arg) is str and arg.isdecimal()) and int(arg) > 0),
                'res':int
            },
            'float':{'verif':vfloat,'res':float},
            'str':{'verif':None,'res':str},
            'list':{'verif':None,'res':list},
            'dict':{'verif':None,'res':dict},
            'other':{}
            }
        if 'tail' in arglimits:
            raise Exception("参数解析器异常：tail不能作为参数名")
        tailmsg = msg.strip()
        arglists = {'tail':tailmsg} #参数列表,尾参数固定命名为tail
        pat = re.compile('[　 \n]{1}') #分割正则
        try:
            larglimits = len(arglimits)
            i = 0
            while i < larglimits:
                #预处理
                if tailmsg != '':
                    res = pat.split(tailmsg,maxsplit=1)
                    arg = res[0]
                    tailmsg = (res[1] if len(res) == 2 else '')
                else:
                    arg = ''
                #执行顺序 prefunc->verif|验证->vlimit->re->func->verif|类型转换
                identify = False
                backuparg = arg
                while True and i < larglimits:
                    arg = backuparg
                    ad = arglimits[i]
                    i += 1
                    if ad['prefunc'] is not None:
                        newarg = ad['prefunc'](arg)
                        if newarg is None or type(newarg) == tuple and not newarg[0]:
                            if ad['canSkip']:
                                arglists[ad['name']] = ad['vlimit']['']
                                continue
                            else:
                                return (False,ad['nick'],'数值无效(PF)',ad['des'])
                        arg = (newarg if type(newarg) != tuple else newarg[1])
                    
                    if ad['vlimit'] is not None and len(ad['vlimit']) > 1:
                        if arg in ad['vlimit']:
                            if ad['vlimit'][arg] != '':
                                arg = ad['vlimit'][arg]
                        elif '*' in ad['vlimit']:
                            if ad['vlimit']['*'] != '':
                                if ad['vlimit']['*'] == '*':
                                    arg = arg
                                else:
                                    arg = ad['vlimit']['*']
                        else:
                            if ad['canSkip']:
                                arglists[ad['name']] = ad['vlimit']['']
                                continue
                            else:
                                return (False,ad['nick'],'非法参数(不被允许的值)',ad['des'])

                    if ad['verif'] in veriffun:
                        vf = veriffun[ad['verif']]
                    else:
                        vf = veriffun['other']
                    if 'verif' in vf and vf['verif'] is not None and not vf['verif'](arg):
                        if ad['canSkip']:
                            arglists[ad['name']] = ad['vlimit']['']
                            continue
                        else:
                            return (False,ad['nick'],'数值无效(VP)',ad['des'])

                    if ad['re'] is not None:
                        arg = reDealStr(ad['re'],arg)
                        if arg is None:
                            if ad['canSkip']:
                                arglists[ad['name']] = ad['vlimit']['']
                                continue
                            else:
                                return (False,ad['des'],(ad['re_error'] if ad['re_error'] else '参数不符合规则(re)'),ad['des'])

                    if ad['func'] is not None:
                        arg = ad['func'](arg,ad)
                        #处理函数返回格式
                        #其一 None/合法值 其二 tuple对象 -> (参数是否合法,处理后的参数/错误文本)
                        if type(res) is tuple:
                            if res[0]:
                                arg = arg[1]
                            else:
                                return (False,ad['des'],arg[1],ad['des'])
                        elif arg is None:
                            return (False,ad['des'],'参数不符合规则(fun)',ad['des'])
                        
                    if 'res' in vf and vf['res'] is not None:
                        try:
                            arg = vf['res'](arg)
                        except:
                            return (False,ad['des'],'参数类型错误(VT)',ad['des'])
                    identify = True
                    arglists[ad['name']] = arg
                    break
            if identify:
                #只有参数被识别才更新tail
                arglists['tail'] = tailmsg
        except:
            s = traceback.format_exc(limit=10)
            logger.error(s)
            return (False,'异常','参数提取时异常！','Exception')
        return (True,arglists)
