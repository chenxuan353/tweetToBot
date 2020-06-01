# -*- coding: UTF-8 -*-
from helper import check_path
from module.twitter import push_list,tweetEventDeal,tweetToStrTemplate,encode_b64,mintweetID
from html.parser import HTMLParser
from os import path
import os
import requests
import xmltodict
import threading
import traceback
import time
import queue
#引入配置
import config
#日志输出
from helper import data_read,data_save,getlogger,TempMemory
logger = getlogger(__name__)

check_path(os.path.join('templist','RSShub','twitter'))

silent_start = config.RSShub_silent_start #静默启动(启动时不推送更新)
base_url = config.RSShub_base
proxy = config.RSShub_proxy
headers = {
    'User-Agent': 'CQpy'
}
proxies = {
        "http": proxy,
        "https": proxy
        }
tmemorys = {}

tweetuserlist_filename = 'RSShub_tweetuserlist.json'
tweetuserlist = {}
res = data_read(tweetuserlist_filename)
if res[0]:
    tweetuserlist = res[2]


class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.text = ""
        self.media = [].copy()
        self.links = [].copy()
    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.media.append(dict(attrs)['src'])
        elif tag == 'a':
            self.links.append(dict(attrs)['href'])

    def handle_endtag(self, tag):
        #logger.info("Encountered an end tag :" + tag)
        pass

    def handle_data(self, data):
        #logger.info("Encountered some data  :")
        #logger.info(data)
        self.text = self.text + data


dealTweetsQueue = queue.Queue(64)
class twitterListener(tweetEventDeal):
    #事件到达
    def deal_event_unit(self,event,Pushunit):
        #事件处理单元-发送
        data = event['data']
        #识别事件类型
        if event['type'] in ['retweet','quoted','reply_to_status','reply_to_user','none']:
            s = self.tweetToStr(
                    data,Pushunit['nick'],
                    push_list.getPuslunitAttr(Pushunit,'upimg')[1],
                    push_list.getPuslunitAttr(Pushunit,event['type']+'_template')[1]
                )
            self.send_msg(Pushunit['type'],Pushunit['pushTo'],s,Pushunit['bindCQID'])
        elif event['type'] in ['change_ID','change_name','change_description','change_headimgchange']:
            self.send_msg(Pushunit['type'],Pushunit['pushTo'],data['str'],Pushunit['bindCQID'])

    #将推特数据应用到模版
    def tweetToStr(self, tweetinfo, nick, upimg=config.pushunit_default_config['upimg'], template_text=''):
        if nick == '':
            if tweetinfo['user']['name']:
                nick = tweetinfo['user']['name']
            else:
                nick = tweetinfo['user']['screen_name']
        temptweetID = mintweetID.find(lambda item,val:item[0] == val,tweetinfo['id'])
        #模版变量初始化
        template_value = {
            'tweet_id':tweetinfo['id_str'], #推特ID
            'tweet_id_min':encode_b64(tweetinfo['id']),#压缩推特id
            'tweet_id_temp':('未生成' if temptweetID == None else ('#' + str(temptweetID[1]))),#临时推特id
            'tweet_nick':nick, #操作人昵称
            'tweet_user_id':tweetinfo['user']['screen_name'], #操作人ID
            'tweet_text':tweetinfo['text'], #发送推特的完整内容
            'related_user_id':'当前模式不支持', #关联用户ID
            'related_user_name':'当前模式不支持', #关联用户昵称-昵称-昵称查询不到时为ID(被评论/被转发/被提及)
            'related_tweet_id':'当前模式不支持', #关联推特ID(被评论/被转发)
            'related_tweet_id_min':'当前模式不支持', #关联推特ID的压缩(被评论/被转发)
            'related_tweet_text':'当前模式不支持', #关联推特内容(被转发或被转发并评论时存在)
            'media_img':'', #媒体
        }
        
        #组装图片
        if upimg == 1:
            if 'extended_entities' in tweetinfo:
                mis = ''
                for media_unit in tweetinfo['extended_entities']:
                    #组装CQ码
                    #file_suffix = os.path.splitext(media_unit['media_url'])[1]
                    #s = s + '[CQ:image,timeout='+config.img_time_out+',file='+config.img_path+'tweet/' + media_unit['id_str'] + file_suffix + ']'
                    mis = mis + '[CQ:image,timeout='+str(config.img_time_out)+',file='+ media_unit + ']'
                if mis != '':
                    mis = "\n媒体：" + str(len(tweetinfo['extended_entities']))+ "个\n" + mis
            template_value['media_img'] = mis
        #生成模版类
        s = ""
        t = None
        if template_text == '':
            #默认模版
            if tweetinfo['type'] == 'none':
                deftemplate_none = "推特ID：$tweet_id_min，【$tweet_nick】发布了：\n$tweet_text\n$media_img\nhttps://twitter.com/$tweet_user_id/status/$tweet_id"
                deftemplate_none = deftemplate_none + "\n临时推文ID：$tweet_id_temp"
                t = tweetToStrTemplate(deftemplate_none)
            elif tweetinfo['type'] == 'retweet':
                deftemplate_another = "推特ID：$tweet_id_min，【$tweet_nick】转了推文：\n$tweet_text\n$media_img\nhttps://twitter.com/$tweet_user_id/status/$tweet_id"
                deftemplate_another = deftemplate_another + "\n临时推文ID：$tweet_id_temp"
                t = tweetToStrTemplate(deftemplate_another)
            elif tweetinfo['type'] == 'quoted':
                deftemplate_another = "推特ID：$tweet_id_min，【$tweet_nick】转发并评论了推文：\n$tweet_text\n====================\n$related_tweet_text\n$media_img\nhttps://twitter.com/$tweet_user_id/status/$tweet_id"
                deftemplate_another = deftemplate_another + "\n临时推文ID：$tweet_id_temp"
                t = tweetToStrTemplate(deftemplate_another)
            else:
                deftemplate_another = "推特ID：$tweet_id_min，【$tweet_nick】回复了推文：\n$tweet_text\n$media_img\nhttps://twitter.com/$tweet_user_id/status/$tweet_id"
                deftemplate_another = deftemplate_another + "\n临时推文ID：$tweet_id_temp"
                t = tweetToStrTemplate(deftemplate_another)
        else:
            #自定义模版
            template_text = template_text.replace("\\n","\n")
            t = tweetToStrTemplate(template_text)

        #转换为字符串
        s = t.safe_substitute(template_value)
        return s

    def getData(self,path:str):
        try:
            url = base_url + path
            r = requests.get(url,headers=headers,proxies=proxies)
            data = xmltodict.parse(r.text)
        except:
            s = traceback.format_exc(limit=10)
            logger.warning(s)
            return (False,'读取页面时出错')
        return (True,data)
    
    def updateArrives(self,data):
        global dealTweetsQueue
        s = "标识：" + data['type'] + "\n" + \
        "推文ID：" + data['id_str'] + "\n" + \
        "推文内容：" + data['text'] + "\n" + \
        "更新时间：" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data['created_at']))
        if data['notable']:
            dealTweetsQueue.put(data)
        logger.info(s)
    
    def dealText(self,text):
        text = text.replace("<br>","\n")
        parser = MyHTMLParser()
        parser.feed("<body>"+text+"</body>")
        resText = parser.text
        extended_entities = parser.media
        return (resText,extended_entities)
    
    def dealTweet(self,tweetitem,userinfo,tmemory):
        val = tweetitem
        tweet_id = val['link'].split("/")[-1]
        tweetinfo = {}
        tweetinfo['id'] = int(tweet_id)
        tweetinfo['id_str'] = str(tweet_id)
        tweetinfo['created_at'] = int(time.mktime(time.strptime(val['pubDate'],"%a, %d %b %Y %H:%M:%S GMT")))

        #RSShub模式仅能识别纯转推与回复
        tweetinfo['isRetweet'] = (val['author'] != userinfo['name'])
        tweetinfo['notable'] = not tweetinfo['isRetweet']
        tweetinfo['reply_to_status'] = (val['description'][0:2] == 'Re')

        if tweetinfo['isRetweet']:
            tweetinfo['type'] = 'retweeted'
        elif tweetinfo['reply_to_status']:
            tweetinfo['type'] = 'reply_to_status'
        else:
            tweetinfo['type'] = 'none'

        res = self.dealText(val['description'])
        tweetinfo['text'] = res[0]
        tweetinfo['extended_entities'] = res[1] #媒体
        tweetinfo['link'] = val['link']

        tweetinfo['user'] = {}
        if not tweetinfo['isRetweet']:
            tweetinfo['user']['id'] = userinfo['id']
            tweetinfo['user']['id'] = userinfo['id_str']
        tweetinfo['user']['name'] = val['author']
        tweetinfo['user']['screen_name'] = val['link'].split("/")[-3]

        #更新推文到缓存中
        tmemory.join(tweetinfo)
        return tweetinfo

    def mergeTweetUser(self,ID:str):
        global tweetuserlist,tweetuserlist_filename
        if ID in tweetuserlist:
            t = tweetuserlist[str(ID)]
        else:
            t = int(time.time())
            tweetuserlist[str(ID)] = t
            data_save(tweetuserlist_filename,tweetuserlist)
        return t
    def dataGetUserInfo(self,data,sid,ID):
        userinfo = {
            'id':sid,
            'id_str':str(sid),
            'screen_name':ID,
            'name':data['rss']['channel']['title'][:-10],
            'profile_image_url':data['rss']['channel']['image']['url'],
            'profile_image_url_https':'https'+data['rss']['channel']['image']['url'][4:],
            'description':data['rss']['channel']['description']
        }
        self.check_userinfo(userinfo)
        return userinfo
    def getUserInfo(self,ID):
        #获取数据
        res=self.getData('/twitter/user/'+ID)
        if not res[0]:
            return res
        data = res[1]
        sid = self.mergeTweetUser(ID)
        userinfo = self.dataGetUserInfo(data,sid,ID)
        return (True,userinfo)
    def dealData(self,data,ID,trigger : bool):
        global tmemorys
        sid = self.mergeTweetUser(ID)
        userinfo = self.dataGetUserInfo(data,sid,ID)

        if ID not in tmemorys:
            tmemorys[ID] = TempMemory(path.join('RSShub','twitter',ID+'.json'),limit=30,autoload=True,autosave=True)
            if tmemorys[ID].tm == []:
                trigger = False
        tmemory = tmemorys[ID]
        sources = data['rss']['channel']['item']
        length = len(sources) - 1
        if length > 30:
            length = 30
        
        func = lambda val,fval:val['link'] == fval
        for i in range(length,-1,-1):
            val = sources[i]
            res = tmemory.find(func,val['link'])
            if res == None:
                tweetinfo = self.dealTweet(val,userinfo,tmemory)
                if trigger:
                    self.updateArrives(tweetinfo)

    def findUpdata(self,ID,trigger:bool = True):
        #获取数据
        res=self.getData('/twitter/user/'+ID)
        if not res[0]:
            return res
        data = res[1]
        try:
            #处理数据
            self.dealData(data,ID,trigger)
            return (True,'成功')
        except:
            s = traceback.format_exc(limit=5)
            logger.error(s)
            return (False,'异常，未知错误(10564)')

tweet_event_deal = twitterListener()

def init():
    #读取推送侦听配置
    res = push_list.readPushList()
    if res[0] == True:
        logger.info('侦听配置读取成功')
    else:
        logger.error('侦听配置读取失败:' + res[1])
init()
run_info = {
    'DealDataThread':None,
    'queque':dealTweetsQueue,
    'Thread':None,
    'keepRun':True,
}
def setStreamOpen(b:bool):
    run_info['keepRun'] = b

def Run():
    #使用RSS推送源接收更新
    logger.info("RSS_push")
    spylist = push_list.spylist
    IDs = []
    for spy in spylist:
        for username in tweetuserlist:
            if tweetuserlist[username] == int(spy):
                IDs.append(username)
    time.sleep(2 if silent_start else 10)
    logger.info("RSShub 启动检测正在运行")
    for ID in IDs:
        logger.info("RSShub 检测:" + ID)
        res = tweet_event_deal.findUpdata(ID,trigger=not silent_start)
    logger.info("RSShub 启动检测结束")
    while True:
        time.sleep(config.RSShub_updata_interval)
        if run_info['keepRun']:
            logger.info("RSShub 自动检测正在运行")
            for ID in IDs:
                logger.info("RSShub 检测:" + ID)
                res = tweet_event_deal.findUpdata(ID,queue)
                time.sleep(1)
            logger.info("RSShub 自动检测结束")
#处理推特数据(独立线程)
def dealTweetData():
    while True:
        tweetinfo = run_info['queque'].get()
        try:
            #推送事件处理，输出到酷Q
            eventunit = tweet_event_deal.bale_event(tweetinfo['type'],tweetinfo['user']['id'],tweetinfo)
            tweet_event_deal.deal_event(eventunit)
            #控制台输出
            #tweet_event_deal.statusPrintToLog(tweetinfo)
        except:
            s = traceback.format_exc(limit=5)
            logger.warning(s)
        run_info['queque'].task_done()

#运行推送线程
def runTwitterListenerThread():
    run_info['Thread'] = threading.Thread(
        group=None, 
        target=Run, 
        name='RSShub_tweetListener_thread', 
        daemon=True
    )
    run_info['DealDataThread'] = threading.Thread(
        group=None, 
        target=dealTweetData, 
        name='RSShub_tweetListener_DealDataThread',
        daemon=True
    )
    run_info['Thread'].start()
    run_info['DealDataThread'].start()
    return run_info