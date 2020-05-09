# -*- coding: UTF-8 -*-
import nonebot
import tweepy
import traceback
import asyncio
#引入配置
import config
#日志输出
from helper import keepalive,getlogger,msgSendToBot
logger = getlogger(__name__)

#引入推送列表、推送处理模版
from module.twitter import push_list,tweetEventDeal

'''
推特API监听更新的实现类
'''

#事件处理类

#推特API的事件处理类
class tweetApiEventDeal(tweetEventDeal):
    #事件到达
    def deal_event_unit(self,event,Pushunit):
        #事件处理单元-发送
        data = event['data']
        #额外处理
        if event['type'] == 'none' and push_list.getPuslunitAttr(Pushunit,'upimg')[1] == 1:
            self.save_media(data)
        #识别事件类型
        if event['type'] in ['retweet','quoted','reply_to_status','reply_to_user','none']:
            str = self.tweetToStr(
                    data,Pushunit['nick'],
                    push_list.getPuslunitAttr(Pushunit,'upimg')[1],
                    push_list.getPuslunitAttr(Pushunit,event['type']+'_template')[1]
                )
            self.send_msg(Pushunit['type'],Pushunit['pushTo'],str,Pushunit['bindCQID'])
        elif event['type'] in ['change_ID','change_name','change_description','change_headimgchange']:
            self.send_msg(Pushunit['type'],Pushunit['pushTo'],data['str'],Pushunit['bindCQID'])

    #媒体保存-保存推特中携带的媒体(目前仅支持图片-考虑带宽，后期不会增加对视频以及gif支持)
    def save_media(self, tweetinfo):
        if 'extended_entities' not in tweetinfo:
            return
        """
        媒体信息
        media_obj = {}
        media_obj['id'] = media_unit.id
        media_obj['id_str'] = media_unit.id_str
        media_obj['type'] = media_unit.type
        media_obj['media_url'] = media_unit.media_url
        media_obj['media_url_https'] = media_unit.media_url_https
        tweetinfo['extended_entities'].append(media_obj)
        """
        for media_unit in tweetinfo['extended_entities']:
            self.seve_image(media_unit['id_str'],media_unit['media_url'],'tweet')

    #控制台输出侦听到的消息
    def statusPrintToLog(self, tweetinfo):
        if tweetinfo['type'] == 'none':
            str = '推特ID：' +tweetinfo['id_str']+'，'+ \
                tweetinfo['user']['screen_name']+"发送了推文:\n"+ \
                tweetinfo['text']
            logger.info('(！)'+ str)
        elif tweetinfo['type'] == 'retweet':
            pass
        else:
            str = \
            '标识 ' + self.type_to_str(tweetinfo['type']) + \
            '，推特ID：' +tweetinfo['id_str']+'，'+ \
            tweetinfo['user']['screen_name']+'与'+ \
            tweetinfo['Related_user']['screen_name']+"的互动:\n"+ \
            tweetinfo['text']
            if tweetinfo['user']['id_str'] in push_list.spylist:
                logger.info('(！)'+ str)
            else:
                logger.info(str)
    #重新包装推特信息
    def get_tweet_info(self, tweet):
        tweetinfo = {}
        tweetinfo['created_at'] = int(tweet.created_at.timestamp())
        tweetinfo['id'] = tweet.id
        tweetinfo['id_str'] = tweet.id_str
        tweetinfo['text'] = tweet.text

        tweetinfo['user'] = {}
        tweetinfo['user']['id'] = tweet.user.id
        tweetinfo['user']['id_str'] = tweet.user.id_str
        tweetinfo['user']['name'] = tweet.user.name
        tweetinfo['user']['description'] = tweet.user.description
        tweetinfo['user']['screen_name'] = tweet.user.screen_name
        tweetinfo['user']['profile_image_url'] = tweet.user.profile_image_url
        tweetinfo['user']['profile_image_url_https'] = tweet.user.profile_image_url_https
        self.check_userinfo(tweetinfo['user']) #检查用户信息
        return tweetinfo
    def deal_tweet_type(self, status):
        if hasattr(status, 'retweeted_status'):
            return 'retweet' #纯转推
        elif hasattr(status, 'quoted_status'):
            return 'quoted' #推特内含引用推文(带评论转推)
        elif status.in_reply_to_status_id != None:
            return 'reply_to_status' #回复(推特下评论)
        elif status.in_reply_to_screen_name != None:
            return 'reply_to_user' #提及(猜测就是艾特)
        else:
            return 'none' #未分类(估计是主动发推)
    def deal_tweet(self, status):
        tweetinfo = self.get_tweet_info(status)
        tweetinfo['type'] = self.deal_tweet_type(status)
        tweetinfo['status'] = status #原始数据
        if tweetinfo['type'] == 'retweet':
            tweetinfo['retweeted'] = self.get_tweet_info(status.retweeted_status)
            tweetinfo['Related_user'] = tweetinfo['retweeted']['user']
            tweetinfo['Related_tweet'] = tweetinfo['retweeted']
        elif tweetinfo['type'] == 'quoted':
            tweetinfo['quoted'] = self.get_tweet_info(status.quoted_status)
            tweetinfo['Related_user'] = tweetinfo['quoted']['user']
            tweetinfo['Related_tweet'] = tweetinfo['quoted']
        elif tweetinfo['type'] != 'none':
            tweetinfo['Related_user'] = {}
            tweetinfo['Related_user']['id'] = status.in_reply_to_user_id
            tweetinfo['Related_user']['id_str'] = status.in_reply_to_user_id_str
            tweetinfo['Related_user']['screen_name'] = status.in_reply_to_screen_name
            tweetinfo['Related_tweet'] = {}
            tweetinfo['Related_tweet']['id'] = status.in_reply_to_status_id
            tweetinfo['Related_tweet']['id_str'] = status.in_reply_to_status_id_str
            tweetinfo['Related_tweet']['text'] = ''
        #尝试获取全文
        if hasattr(status,'extended_tweet'):
            tweetinfo['text'] = status.extended_tweet['full_text']
        else:
            tweetinfo['text'] = status.text
        #处理媒体信息
        if hasattr(status,'extended_entities'):
            tweetinfo['extended_entities'] = []
            if 'media' in status.extended_entities:
                for media_unit in status.extended_entities['media']:
                    media_obj = {}
                    media_obj['id'] = media_unit['id']
                    media_obj['id_str'] = media_unit['id_str']
                    media_obj['type'] = media_unit['type']
                    media_obj['media_url'] = media_unit['media_url']
                    media_obj['media_url_https'] = media_unit['media_url_https']
                    tweetinfo['extended_entities'].append(media_obj)
        return tweetinfo
#推特事件处理对象
tweet_event_deal = tweetApiEventDeal()
#推特监听者
class MyStreamListener(tweepy.StreamListener):
    isrun = False
    #错误处理
    def on_error(self, status_code):
        #推特错误代码https://developer.twitter.com/en/docs/basics/response-codes
        logger.critical(status_code)
        #返回False结束流
        return False
    #开始链接监听
    def on_connect(self):
        msgSendToBot(logger,"推特流链接已就绪")
        keepalive['reboot_tweetListener_cout'] = 0
        self.isrun = True
    #断开链接监听
    def on_disconnect(self, notice):
        msgSendToBot(logger,"推特流已断开链接")
        self.isrun = False
        raise Exception
    #推特事件监听
    def on_status(self, status):
        try:
            #重新组织推特数据
            tweetinfo = tweet_event_deal.deal_tweet(status)
            #推送事件处理，输出到酷Q
            eventunit = tweet_event_deal.bale_event(tweetinfo['type'],tweetinfo['user']['id'],tweetinfo)
            tweet_event_deal.deal_event(eventunit)
            #控制台输出
            tweet_event_deal.statusPrintToLog(tweetinfo)
        except:
            str = traceback.format_exc(limit=5)
            logger.error(str)

#推特认证
auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
auth.set_access_token(config.access_token, config.access_token_secret)
#获取API授权
api = tweepy.API(auth, proxy=config.api_proxy)

#安装测试列表
#test_install_push_list()
#创建监听对象
myStreamListener = MyStreamListener()
def Run():
    #读取推送侦听配置
    res = push_list.readPushList()
    if res[0] == True:
        logger.info('侦听配置读取成功')
    else:
        logger.error('侦听配置读取失败:' + res[1])
    #创建监听流
    myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
    myStream.filter(follow=push_list.spylist,is_async=False)

