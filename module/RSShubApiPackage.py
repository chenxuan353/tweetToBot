# -*- coding: UTF-8 -*-
import time
import requests
import xmltodict
import traceback
from datetime import datetime
from html.parser import HTMLParser
import config
from helper import getlogger,TokenBucket
logger = getlogger(__name__)

"""
用于支持RSS操作
解析RSS及打包RSS数据
支持RSShub及指定RSS源
"""
proxy = config.RSS_proxy
headers = {
    'User-Agent': 'RSSReadBot V1.0'
}
proxies = {
        "http": proxy,
        "https": proxy
        }
#RSS源访问及处理,支持更换根url
class RSSDealPackage:
    def __init__(self,url:str,path:str,rssLastBuild:int = 0,useUpdataCache = True,headers = headers,proxies = proxies,timelimit:int = 15):
        #源URL,每次访问最短时限-单位秒-默认15
        #useUpdataCache:使用更新缓存，开启后将使用缓存
        #rssLastBuild:最后
        self.url = url
        self.path = path
        self.timelimit = timelimit
        self.headers = headers
        self.proxies = proxies
        #上次阅读时间
        self.lastReadTime = 0
        #RSS数据的上次更新时间(用于查找更新)
        self.rssLastBuild = rssLastBuild
        #启用缓存
        self.useUpdataCache = useUpdataCache
        #最近一次阅读的完整数据缓存
        self.data = {}
        self.lasttest = False
    def getLastReadTime(self):
        return self.lastReadTime
    def setUrl(self,url:str,timelimit:int = None):
        self.url = url
        if timelimit:
            self.timelimit = timelimit
    def test(self) -> bool:
        #测试rss源可用性
        res = self.getData(updatacache=False)
        if not res[0]:
            self.lasttest = False
            return self.lasttest
        data = res[1]
        res = True
        standpkg = self.baleToStandRssPkg(data)
        if 'item' in standpkg and standpkg['item']:
            res = self.itempkgCanGetUpdates(standpkg['item'][0])
        self.lasttest = res and self.pkgCanGetUpdates(standpkg)
        return self.lasttest
    def getTimeLimit(self) -> int:
        return self.timelimit
    def getWaitTime(self) -> int:
        interval = int(time.time() - self.lastReadTime)
        if interval >= self.timelimit:
            return 0
        return self.timelimit - interval
    def getData(self,updatacache = True) -> tuple:
        #获取页面数据(是否更新缓存)
        try:
            r = requests.get(self.url+self.path,headers=self.headers,proxies=self.proxies)
            if r.status_code != 200:
                return (False,'页面错误 {code}'.format(code=r.status_code))
            data = xmltodict.parse(r.text)
        except:
            s = traceback.format_exc(limit=10)
            logger.warning(s)
            return (False,'读取页面时出错')
        if updatacache and self.useUpdataCache:
            self.data = data
        return (True,data)
    def pkgCanGetUpdates(self,pkg):
        return 'lastBuildDate' in pkg and pkg['lastBuildDate'] != 0
    def itempkgCanGetUpdates(self,pkg):
        return 'pubDate' in pkg and pkg['pubDate'] != 0
    def baleItemToStandRssPkg(self,item):
        """
            <item>
                <title>标题</title>
                <link>链接地址</link>
                <description>内容简要描述</description>
                <pubDate>发布时间</pubDate>
                <category>所属目录</category>
                <author>作者</author>
            </item>
        """
        #将item数据打包到标准RSS数据包
        checkfunc = (lambda item,key:item[key] if key in item else '')
        return {
            'title':checkfunc(item,'title'),
            'link':checkfunc(item,'link'),
            'description':checkfunc(item,'description'),
            'pubDate':checkfunc(item,'pubDate'),
            'pubTimestamp':(int(datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S GMT').timestamp()) if 'pubDate' in item else 0),
            'category':checkfunc(item,'category'),
            'author':checkfunc(item,'author')
        }
    def baleToStandRssPkg(self,data):
        """
            <title>网站标题</title>
            <link>网站首页地址</link>
            <description>描述</description>
            <copyright>授权信息</copyright>
            <language>使用的语言（zh-cn表示简体中文）</language>
            <pubDate>发布的时间</pubDate>
            <lastBuildDate>最后更新的时间</lastBuildDate>
            <generator>生成器</generator>
        """
        #将数据打包到标准RSS数据包
        checkfunc = (lambda item,key:item[key] if key in item else '')
        channel = data['rss']['channel']
        res = {
            'title':checkfunc(channel,'title'),
            'link':checkfunc(channel,'link'),
            'description':checkfunc(channel,'description'),
            'copyright':checkfunc(channel,'copyright'),
            'language':checkfunc(channel,'language'),
            'pubDate':checkfunc(channel,'pubDate'),
            'lastBuildDate':checkfunc(channel,'lastBuildDate'),
            'lastBuildTimestamp':(int(datetime.strptime(channel['lastBuildDate'], '%a, %d %b %Y %H:%M:%S GMT').timestamp()) if 'lastBuildDate' in channel else 0),
            'generator':checkfunc(channel,'generator'),
            'item':[]
        }
        if 'item' in channel:
            for i in range(0,len(channel['item'])):
                item = channel['item'][i]
                data = self.baleItemToStandRssPkg(item)
                res['item'].append(data)
        return res
    def findUpdata(self,updatareadtime = True) -> tuple:
        #查找更新(是否更新阅读时间-默认是)
        #仅查找item更新(仅适用于标准数据集)
        #首次启动将推送所有item
        res = self.getData()
        if not res[0]:
            return res
        rsspkg = self.baleToStandRssPkg(res[1])
        if self.rssLastBuild != 0 and self.rssLastBuild >= rsspkg['lastBuildTimestamp']:
            return (True,[])
        updatalist = []
        for item in rsspkg['item']:
            if item['pubTimestamp'] > self.rssLastBuild:
                updatalist.append(item)
        if updatareadtime:
            self.rssLastBuild = rsspkg['lastBuildTimestamp']
        self.lastReadTime = time.time()
        return (True,updatalist)

defaultUrls = config.RSShub_urls if config.RSShub_urls else {}
class RSShubsPackage:
    def __init__(self,urls:list = defaultUrls):
        self.urls = urls
        if len(self.urls) == 0:
            raise Exception('RSShub链接url未配置')
        #处理包列表
        self.paths = {}
        #urls循环计数
        self.nowcount = 0
    def getWaitTime(self):
        #单位秒
        t = 0
        lurls = len(self.urls)
        for urlunit in self.urls:
            t += urlunit[1]/lurls
        return t+1
    def getUrl(self) -> str:
        url = self.urls[self.nowcount]
        self.nowcount += 1
        if self.nowcount >= len(self.urls):
            self.nowcount = 0
        return url
    def hasPath(self,path:str) -> bool:
        return path in self.paths
    def delPath(self,path:str) -> bool:
        if self.hasPath(path):
            del self.paths[path]
        return True
    def getPath(self,path:str) -> RSSDealPackage:
        if self.hasPath(path):
            return self.paths[path]
        return None
    def clear(self):
        self.paths.clear()
    def getPath_createnew(self,path:str) -> RSSDealPackage:
        #获取rss包，不存在时创建新的包
        pkg = self.getPath(path)
        if not pkg:
            pkg = RSSDealPackage(self.urls[0],path)
            pkg.findUpdata() #进行初始化，初始化将忽略更新
            self.paths[path] = pkg
        return pkg
    def getUpdata(self,path:str) -> tuple:
        #获取指定路径的更新
        pkg:RSSDealPackage = self.getPath_createnew(path)
        url = self.getUrl()
        pkg.setUrl(url)
        return pkg.findUpdata()
        
