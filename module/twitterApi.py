# -*- coding: UTF-8 -*-
import nonebot
import tweepy
import traceback
import os
import start
import urllib
#引入配置
import config
#日志输出
from helper import log_print,data_read,data_save
#引入推送列表
from module.PushList import push_list,tweetToStrTemplate

#引入测试方法
try:
    import test
except:
    pass
'''
推特API载入测试
'''
#10进制转64进制
def encode_b64(n:int) -> str:
    table = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ$_'
    result = []
    temp = n - 1253881609540800000
    if 0 == temp:
        result.append('0')
    else:
        while 0 < temp:
            result.append(table[int(temp) % 64])
            temp = int(temp)/64
    return ''.join([x for x in reversed(result)])
def decode_b64(str):
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
                "$": 62, "_": 63}
    result = 0
    for i in range(len(str)):
        result *= 64
        result += table[str[i]]
    return result + 1253881609540800000

#推特监听流
class MyStreamListener(tweepy.StreamListener):
    userinfolist = {}
    isrun = False
    #错误处理
    def on_error(self, status_code):
        #推特错误代码https://developer.twitter.com/en/docs/basics/response-codes
        log_print(1,status_code)
        #返回False结束流
        return False
    #开始链接监听
    def on_connect(self):
        log_print(6,"推送流链接已就绪")
        start.reboot_tweetListener_cout = 0
        self.isrun = True
    #断开链接监听
    def on_disconnect(self, notice):
        log_print(6,"推送流已断开链接")
        self.isrun = False
        raise Exception
    #尝试从缓存中获取昵称
    def tryGetNick(self, tweet_user_id,nick):
        if tweet_user_id in self.userinfolist:
            return self.userinfolist[tweet_user_id]['name']
        return nick
    #尝试从缓存中获取用户信息,返回用户信息表
    def tryGetUserInfo(self, tweet_user_id) -> list:
        if tweet_user_id in self.userinfolist:
            return self.userinfolist[tweet_user_id]['name']
        return {}
    #图片保存（待优化）
    def seve_image(self, name, url, file_path='img'):
        #保存图片到磁盘文件夹 cache/file_path中，默认为当前脚本运行目录下的 cache/img 文件夹
            base_path = 'cache/' #基准路径
            try:
                if not os.path.exists(base_path + file_path):
                    log_print(4,'文件夹' + base_path + file_path + '不存在，重新建立')
                    #os.mkdir(file_path)
                    os.makedirs(base_path + file_path)
                #获得图片后缀
                file_suffix = os.path.splitext(url)[1]
                #拼接图片名（包含路径）
                filename = '{}{}{}{}'.format(base_path + file_path,os.sep,name,file_suffix)
                #下载图片，并保存到文件夹中
                if not os.path.isfile(filename):
                    urllib.request.urlretrieve(url,filename=filename)
            except IOError:
                s = traceback.format_exc(limit=5)
                log_print(2,'文件操作失败'+s)
            except Exception:
                s = traceback.format_exc(limit=5)
                log_print(2,s)
    #媒体保存-保存推特中携带的媒体(目前仅支持图片-考虑带宽，后期可能不会增加支持)
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

    #消息发送(消息类型，消息发送到，消息内容)
    def send_msg(self, message_type:str, send_id:int, message:str,bindCQID:int = config.default_bot_QQ):
        bot = nonebot.get_bot()
        try:
            if message_type == 'private':
                bot.sync.send_msg_rate_limited(self_id=bindCQID,user_id=send_id,message=message)
            elif message_type == 'group':
                bot.sync.send_msg_rate_limited(self_id=bindCQID,group_id=send_id,message=message)
        except:
            s = traceback.format_exc(limit=5)
            log_print(2,s)
            pass
    #控制台输出侦听到的消息
    def statusPrintToLog(self, tweetinfo):
        if tweetinfo['type'] == 'none':
            str = '推特ID：' +tweetinfo['id_str']+'，'+ \
                tweetinfo['user']['screen_name']+"发送了推文:\n"+ \
                tweetinfo['text']
            log_print(5,'(！)'+ str)
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
                log_print(5,'(！)'+ str)
            else:
                log_print(4,str)
    #推特事件监听
    def on_status(self, status):
        try:
            #重新组织推特数据
            tweetinfo = self.deal_tweet(status)
            #酷Q输出
            eventunit = self.bale_event(tweetinfo['type'],tweetinfo['user']['id'],tweetinfo)
            self.deal_event(eventunit)
            #控制台输出
            self.statusPrintToLog(tweetinfo)
        except:
            str = traceback.format_exc(limit=5)
            log_print(2,str)
    
    #重新包装推特信息
    def get_tweet_info(self, tweet):
        tweetinfo = {}
        tweetinfo['created_at'] = tweet.created_at
        tweetinfo['id'] = tweet.id
        tweetinfo['id_str'] = tweet.id_str
        tweetinfo['text'] = tweet.text
        tweetinfo['user'] = {}
        self.check_userinfo(tweet.user) #检查用户信息
        tweetinfo['user']['id'] = tweet.user.id
        tweetinfo['user']['id_str'] = tweet.user.id_str
        tweetinfo['user']['name'] = tweet.user.name
        tweetinfo['user']['description'] = tweet.user.description
        tweetinfo['user']['screen_name'] = tweet.user.screen_name
        tweetinfo['user']['profile_image_url'] = tweet.user.profile_image_url
        tweetinfo['user']['profile_image_url_https'] = tweet.user.profile_image_url_https
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
    def type_to_str(self, tweettype):
        if tweettype == 'retweet':
            return '转推' #纯转推
        elif tweettype == 'quoted':
            return '转推并评论' #推特内含引用推文(带评论转推)
        elif tweettype == 'reply_to_status':
            return '回复' #回复(推特下评论)
        elif tweettype == 'reply_to_user':
            return '提及' #提及(猜测就是艾特)
        else:
            return '发推' #未分类(估计是主动发推)
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

    #检测个人信息更新
    def check_userinfo(self, user):
        """
            运行数据比较
            用于监测用户的信息修改
            用户ID screen_name
            用户昵称 name
            描述 description
            头像 profile_image_url
        """
        if user.id in self.userinfolist:
            userinfo = self.userinfolist[user.id]
            data = {}
            str = ''
            if userinfo['name'] != user.name:
                data['type'] = 'change_name'
                str = userinfo['name'] + "(" + userinfo['screen_name'] + ")" + \
                ' 的昵称已更新为 ' + user.name + "(" + user.screen_name + ")"
                userinfo['name'] = user.name
            if userinfo['description'] != user.description:
                data['type'] = 'change_description'
                str = userinfo['name'] + "(" + userinfo['screen_name'] + ")" + ' 的描述已更新为 ' + user.description
                userinfo['description'] = user.description
            if userinfo['screen_name'] != user.screen_name:
                data['type'] = 'change_ID'
                str = userinfo['name'] + "(" + userinfo['screen_name'] + ")" + \
                    ' 的ID已更新为 ' + user.name + "(" + user.screen_name + ")"
                userinfo['screen_name'] = user.screen_name
            if userinfo['profile_image_url_https'] != user.profile_image_url_https:
                data['type'] = 'change_headimgchange'
                str = userinfo['name'] + "(" + userinfo['screen_name'] + ")" + '的头像已更新'
                userinfo['profile_image_url'] = user.profile_image_url
                userinfo['profile_image_url_https'] = user.profile_image_url_https

            if str != '':
                data['user_id'] = user.id
                data['user_id_str'] = user.id_str
                data['str'] = str
                eventunit = self.bale_event(data['type'],data['user_id'],data)
                self.deal_event(eventunit)
        else:
            if user.id_str in push_list.spylist:
                userinfo = {}
                userinfo['id'] = user.id
                userinfo['id_str'] = user.id_str
                userinfo['name'] = user.name
                userinfo['description'] = user.description
                userinfo['screen_name'] = user.screen_name
                userinfo['profile_image_url'] = user.profile_image_url
                userinfo['profile_image_url_https'] = user.profile_image_url_https
                self.userinfolist[user.id] = userinfo
    #打包事件(事件类型，引起变化的用户ID，事件数据)
    def bale_event(self, event_type,user_id:int,event_data):
        eventunit = {
            'type':event_type,
            'user_id':user_id,
            'data':event_data
        }
        return eventunit
    #事件预处理-发送事件
    def deal_event(self, event):
        table = push_list.getLitsFromTweeUserID(event['user_id'])
        if test:
            test.event_push(event)
        for Pushunit in table:
            #获取属性判断是否可以触发事件
            res = push_list.getPuslunitAttr(Pushunit,event['type'])
            if res[0] == False:
                raise Exception("获取Pushunit属性值失败",Pushunit)
            if res[1] == 1:
                self.deal_event_unit(event,Pushunit)
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
            self.send_msg(Pushunit['type'],Pushunit['pushTo'],str)
        elif event['type'] in ['change_ID','change_name','change_description','change_headimgchange']:
            self.send_msg(Pushunit['type'],Pushunit['pushTo'],data['str'])

    #将推特数据应用到模版
    def tweetToStr(self, tweetinfo, nick, upimg=config.pushunit_default_config['upimg'], template_text=''):
        if nick == '':
            if tweetinfo['user']['name']:
                nick = tweetinfo['user']['name']
            else:
                nick = tweetinfo['user']['screen_name']
        #模版变量初始化
        template_value = {
            'tweet_id':tweetinfo['id_str'], #推特ID
            'tweet_id_min':encode_b64(tweetinfo['id']),#压缩推特id
            'tweet_nick':nick, #操作人昵称
            'tweet_user_id':tweetinfo['user']['screen_name'], #操作人ID
            'tweet_text':tweetinfo['text'], #发送推特的完整内容
            'related_user_id':'', #关联用户ID
            'related_user_name':'', #关联用户昵称-昵称-昵称查询不到时为ID(被评论/被转发/被提及)
            'related_tweet_id':'', #关联推特ID(被评论/被转发)
            'related_tweet_id_min':'', #关联推特ID的压缩(被评论/被转发)
            'related_tweet_text':'', #关联推特内容(被转发或被转发并评论时存在)
        }
        if tweetinfo['type'] != 'none':
            template_value['related_tweet_id'] = tweetinfo['Related_tweet']['id_str']
            template_value['related_tweet_id_min'] = encode_b64(tweetinfo['Related_tweet']['id'])
            template_value['related_tweet_text'] = tweetinfo['Related_tweet']['text']

        if tweetinfo['type'] != 'none':
            template_value['related_user_id'] = tweetinfo['Related_user']['screen_name']
            if tweetinfo['Related_user']['id'] in self.userinfolist:
                template_value['related_user_name'] = self.userinfolist[tweetinfo['Related_user']['id']]['name']
            else:
                if hasattr(tweetinfo['Related_user'],'name'):
                    template_value['related_user_name'] = tweetinfo['Related_user']['name']
                else:
                    template_value['related_user_name'] = tweetinfo['Related_user']['screen_name']

        #生成模版类
        s = ""
        t = None
        if template_text == '':
            #默认模版
            if tweetinfo['type'] == 'none':
                deftemplate_none = "推特ID：$tweet_id_min，【$tweet_nick】发布了：\n$tweet_text"
                t = tweetToStrTemplate(deftemplate_none)
            elif tweetinfo['type'] == 'retweet':
                deftemplate_another = "推特ID：$tweet_id_min，【$tweet_nick】转了【$related_user_name】的推特：\n$tweet_text\n====================\n$related_tweet_text"
                t = tweetToStrTemplate(deftemplate_another)
            elif tweetinfo['type'] == 'quoted':
                deftemplate_another = "推特ID：$tweet_id_min，【$tweet_nick】转发并评论了【$related_user_name】的推特：\n$tweet_text\n====================\n$related_tweet_text"
                t = tweetToStrTemplate(deftemplate_another)
            else:
                deftemplate_another = "推特ID：$tweet_id_min，【$tweet_nick】回复了【$related_user_name】：\n$tweet_text"
                t = tweetToStrTemplate(deftemplate_another)
        else:
            #自定义模版
            t = tweetToStrTemplate(template_text)

        #转换为字符串
        s = t.safe_substitute(template_value)
        #组装图片
        if upimg == 1:
            s = s + "\n"
            if 'extended_entities' in tweetinfo:
                for media_unit in tweetinfo['extended_entities']:
                    #组装CQ码
                    file_suffix = os.path.splitext(media_unit['media_url'])[1]
                    s = s + '[CQ:image,file=tweet/' + media_unit['id_str'] + file_suffix + ']'
        return s

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
    log_print(2,('侦听配置读取成功' if res[0] == True else '侦听配置读取失败:' + res[1]))
    #创建监听流
    myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
    myStream.filter(follow=push_list.spylist,is_async=False)

