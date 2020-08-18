from module.PushList import PushList
import module.msgStream as msgStream
from module.msgStream import SendMessage

from html.parser import HTMLParser
import time
import re
#日志输出
from helper import getlogger
logger = getlogger(__name__)

"""
RSShub 推送识别码为path
"""

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
class RssPushList(PushList):
    def __init__(self,configfilename = 'RSShubPushlist.json'):
        super().__init__('RSShub',configfilename=configfilename)
        self.load()
    def baleForConfig(self,nick,unitdes,options:dict):
        return {
            'nick':nick,
            'unitdes':unitdes,
            'options':options
        }
    @staticmethod
    def getSourceWeb(path):
        res = path.split('/')
        for s in res:
            if s.strip():
                return s
        return ''
    @staticmethod
    def dealOption(path:str,option:str) -> tuple:
        options = {}
        if path.startswith('/bilibili/user/dynamic/'):
            options = {
                're':False,
                'onlyjp':False,
                'notupload':False,
            }
            if option:
                res = option.split('+')
                for s in res:
                    if s.strip() == '看转发':
                        options['re'] = True
                    elif s.strip() == '仅日语':
                        options['onlyjp'] = True
                    elif s.strip() == '不看投稿':
                        options['notupload'] = True
                    elif s.strip() == '看投稿':
                        options['notupload'] = False
                    else:
                        return (False,'选项错误,选项 {0} 不存在,可用选项 看转发、仅日语、看投稿'.format(s))
        else:
            if option:
                return (False,'当前路径无选项')
        return (True,options)

class RSShubEvenDeal:
    def __init__(self,pushlist):
        self.pushlist = pushlist
    def bale_event(self,spypath:str,data):
        return {
            'path':spypath,
            'data':data
        }
    def eventSourceAllow(self,event,pushunit) -> bool:
        """
            判断来源是否允许转发
        """
        path = event['path']
        data = event['data']
        if path.startswith('/bilibili/user/dynamic/'):
            """
                're':False,
                'onlyjp':False,
                'notupload':False,
            """
            if data['title'] == '转发动态' or data['title'] == '分享动态':
                if not pushunit['pushconfig']['options']['re']:
                    return False
            else:
                #仅日语
                if pushunit['pushconfig']['options']['onlyjp'] and not re.search(r'[\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7A3]',data['description']):
                    return False
                #不看投稿
                if data['description'].find('/bfs/archive/') != -1 and not pushunit['pushconfig']['options']['notupload']:
                    return False
        return True
    #事件分发
    def deal_event(self,event):
        pushlist = self.pushlist
        units = pushlist.getLitsFromSpyID(event['path'])
        if units != []:
            for pushunit in units:
                if self.eventSourceAllow(event,pushunit):
                    self.eventTrigger(event,pushunit)
    #事件到达(触发)
    def eventTrigger(self,event,pushunit):
        msg = self.evenToStr(event['path'],event['data'],pushunit)
        self.send_msg_pushunit(pushunit,msg)
    #标准RSS事件转文本
    def dealText(self,text):
        """
            处理HTML标签
        """
        text = text.replace("<br>","\n")
        parser = MyHTMLParser()
        parser.feed("<body>"+text+"</body>")
        resText = parser.text
        extended_entities = parser.media
        return (resText,extended_entities)
    def evenToStr(self,path:str,rssdata,pushunit) -> str:
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
        sourceWeb = RssPushList.getSourceWeb(path)
        if 'channel_title' in rssdata:
            source = rssdata['channel_title']
        else:
            source = sourceWeb
        nick = rssdata['author']
        unitdes = source #订阅描述
        if 'nick' in pushunit['pushconfig']:
            nick = pushunit['pushconfig']['nick']
        if 'unitdes' in pushunit['pushconfig'] and pushunit['pushconfig']['unitdes']:
            unitdes = pushunit['pushconfig']['unitdes']
        if nick == '':
            nick = '(未命名)'
        rdes = self.dealText(rssdata['description'])
        
        if path.startswith('/bilibili/user/dynamic/'):
            msg = "来自 {0} 的更新\n{1}\n{2}".format(
                    unitdes,
                    ('   --' + nick if nick != '(未命名)' else ''),
                    rdes[0]
                )
        elif path.startswith('/bilibili/live/room/'):
            msg = "{0} 更新了\n{1}\n{2}".format(
                    unitdes,
                    ('   --' + nick if nick != '(未命名)' else ''),
                    rdes[0][:15].strip() + ('...' if len(rdes[0])>15 else '')
                )
        else:
            msg = "来自 {0} 的更新\n{1}{2}\n{3}".format(
                    unitdes,
                    rssdata['title'],
                    ('   --' + nick if nick != '(未命名)' else ''),
                    rdes[0]
                )
        msg = SendMessage(msg)
        if rdes[1]:
            msg.append('\n媒体：\n')
        for src in rdes[1]:
            msg.append(msg.baleImgObj(src))
        msg.append("{0}{1}".format(
                    (('\n'+rssdata['link']) if rssdata['link'] else ''),
                    ('\n'+time.strftime("%Y{0}%m{1}%d{2} %H:%M:%S",time.localtime(int(rssdata['pubTimestamp']))).format('年','月','日') if rssdata['pubTimestamp'] else '')
                ))
        return msg
    def send_msg_pushunit(self,pushunit,message:SendMessage):
        return msgStream.send_msg_kw(**pushlist.baleSendTarget(pushunit,message))


pushlist = RssPushList()
rsshubevendeal = RSShubEvenDeal(pushlist)