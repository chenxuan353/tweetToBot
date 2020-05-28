import os
import traceback
import time
import json
from helper import check_path,keepalive
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from helper import getlogger,data_save,data_read
logger = getlogger(__name__)
check_path(os.path.join('transtweet','error'))
check_path(os.path.join('transtweet','unknownimg'))
check_path(os.path.join('transtweet','tweetimg'))
check_path(os.path.join('transtweet','tweetsimg'))
check_path(os.path.join('transtweet','transimg'))

class TweetTrans:
    driver : webdriver.Chrome = None
    def __init__(self):
        keepalive['clear_chrome'] = False
        keepalive['last_trans'] = int(time.time())
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('-lang=zh_CN.UTF-8')
        chrome_options.add_argument('accept-language="zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6"')
        chrome_options.add_argument('x-twitter-active-user=yes')
        chrome_options.add_argument('dnt=1')
        chrome_options.add_argument('x-twitter-client-language=zh-cn')
        #chrome_options.add_argument('--disk-cache-dir='+os.path.join('.','cache','chromecache'))
        chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36")
        self.driver = webdriver.Chrome(options=chrome_options)
    def __del__(self):
        self.driver.close()
        self.driver.quit()
    #打开页面
    def get(self,url:str):
        driver = self.driver
        driver.get(url)
        driver.maximize_window()
        scroll_width = driver.execute_script('return document.body.parentNode.scrollWidth')
        driver.set_window_size(scroll_width, 4000)
        return scroll_width
    #等待推文加载(参数：任务标识)
    def waitForTweetLoad(self,tasktype:str):
        driver = self.driver
        main_type = "section[aria-labelledby].css-1dbjc4n>div>div"
        load_type = "div[role='progressbar']"
        error_save_filename = os.path.join('cache','transtweet','error','waitForTweetLoad-'+tasktype+'.png')
        JS_get_errormsg = """
            elem = document.querySelector('[data-testid="error-detail"]')
            if(elem)return elem.innerText
            return "未查找到错误信息，可能是网络波动造成的"
        """
        #等待主元素出现
        try:
            WebDriverWait(driver, 60, 0.5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, main_type))
                )
        except:
            driver.save_screenshot(error_save_filename)
            s = traceback.format_exc(limit=10)
            logger.warning(s+"\n filename="+error_save_filename + ';url=' + driver.current_url)
            rmsg = driver.execute_script(JS_get_errormsg)
            return (False,error_save_filename,rmsg)
        #等待加载结束
        try:
            WebDriverWait(driver, 60, 0.5).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, load_type))
                )
        except:
            driver.save_screenshot(error_save_filename)
            s = traceback.format_exc(limit=10)
            logger.warning(s+"\n filename="+error_save_filename + ';url=' + driver.current_url)
            rmsg = driver.execute_script(JS_get_errormsg)
            return (False,error_save_filename,rmsg)
        return (True,'success!')
    #二次加载(加载更多推文)
    def waitForTweetLoad2(self,tasktype:str,limit_scroll_height:int = 2000):
        driver = self.driver
        load_type = "div[role='progressbar']"
        error_save_filename = os.path.join('cache','transtweet','error','waitForTweetLoad2-'+tasktype+'.png')
        JS_get_errormsg = """
            elem = document.querySelector('[data-testid="error-detail"]')
            if(elem)return elem.innerText
            return "未查找到错误信息"
        """
        scroll_height = driver.execute_script('return document.body.parentNode.scrollHeight')
        if scroll_height > limit_scroll_height:
            scroll_height = limit_scroll_height
        driver.execute_script("window.scrollTo(0,"+str(scroll_height)+")")
        try:
            WebDriverWait(driver, 60, 0.5).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, load_type))
                )
        except:
            driver.save_screenshot(error_save_filename)
            s = traceback.format_exc(limit=10)
            logger.warning(s+"\n filename="+error_save_filename + ';url=' + driver.current_url)
            rmsg = driver.execute_script(JS_get_errormsg)
            return (False,error_save_filename,rmsg)
    #推文最终初始化 
    def tweetEndInit(self,tasktype:str):
        driver = self.driver
        error_save_filename = os.path.join('cache','transtweet','error','tweetEndInit-'+tasktype+'.png')
        JS_scroll = "window.scrollTo(0,0)\n"
        JS_hideHead = """
            var elem = document.querySelector('header[role="banner"]')
            if(elem)elem.style.display="none"
        """
        try:
            driver.execute_script(JS_scroll+JS_hideHead)
        except:
            driver.save_screenshot(error_save_filename)
            s = traceback.format_exc(limit=10)
            logger.warning(s+"\n filename="+error_save_filename + ';url=' + driver.current_url)
            return (False,error_save_filename,'页面初始化失败')
        return (True,'success!')
    #头部高度(推文开始显示的高度),必须在存在推文的页面上获取
    def getStartHeight(self,tasktype:str):
        driver = self.driver
        error_save_filename = os.path.join('cache','transtweet','error','getStartHeight-'+tasktype+'.png')
        JS_getStartHeight = """
            　　function getElementTop(element){
            　　　　var actualTop = element.offsetTop;
            　　　　var current = element.offsetParent;
            　　　　while (current !== null){
            　　　　　　actualTop += current.offsetTop;
            　　　　　　current = current.offsetParent;
            　　　　}
            　　　　return actualTop;
            　　}
                var sec = document.querySelector('section[aria-labelledby].css-1dbjc4n')
                startHeight = getElementTop(sec)
                return startHeight
        """
        try:
            startheight = driver.execute_script(JS_getStartHeight)
            return (True,startheight)
        except:
            driver.save_screenshot(error_save_filename)
            s = traceback.format_exc(limit=10)
            logger.warning(s+"\n filename="+error_save_filename + ';url=' + driver.current_url)
            return (False,error_save_filename,'获取推文列表异常')
    #推文列表,必须在存在推文的页面上获取
    def getTweets(self,tasktype:str,limitHeight:str="4000"):
        driver = self.driver
        error_save_filename = os.path.join('cache','transtweet','error','getTweets-'+tasktype+'.png')
        JS_getTweets = """
            tweets = []
            //推文主元素
            elems = document.querySelector('section[aria-labelledby].css-1dbjc4n>div>div').children
            lastelemy = "0"
            for (var i = 0;i<elems.length;i++) {
                elart = elems[i].querySelector('article')
                if(elart){
                    try {
                        uie = elart.querySelector('div[data-testid="tweet"]>div')
                        //头像
                        headimg = uie.querySelector('img').getAttribute('src')

                        //昵称
                        uie = uie.nextSibling.querySelector('a>div>div')
                        nick = uie.innerText
                        //用户ID
                        userid = uie.nextSibling.innerText
                        //推文内容表

                        elemtexts = elart.querySelectorAll('div[dir="auto"][lang]')
                        tweettexts = []
                        tweettext = ""
                        for(var j = 0;j<elemtexts.length;j++){
                            tweettext += elemtexts[j].innerText + "\\u000A"
                            tweettexts.push({
                                elem:elemtexts[j],
                                text:elemtexts[j].innerText
                            })
                        }
                        tweettext = tweettext
                        //推文相对高度
                        elemy = elems[i].style.transform.slice(11,-3)
                        lastelemy = elemy
                        //推文宽度
                        elemh = elems[i].offsetHeight
                        //推文翻译截断部分
                        elemEnd = elart.querySelector('div[data-testid="tweet"]').querySelector('div[aria-label][role="group"]') //回复转推喜欢
                        if(!elemEnd)
                            elemEnd = elems[i].querySelector('div[aria-label][role="group"]') //回复转推喜欢
                        elemEnd = elemEnd.offsetTop

                        //隐藏翻译蓝链
                        elemet = elart.querySelector('[aria-expanded]')
                        if(elemet)elemet.style.visibility="hidden"
                        tweets.push({
                            relem:elems[i],//原始元素
                            elem:elart,//主体元素
                            elemEnd:elemEnd,//推文翻译隔断线
                            elemy:elemy,
                            elemh:elemh,
                            headimg:headimg,
                            nick:nick,
                            userid:userid,
                            tweettexts:tweettexts,
                            tweettext:tweettext
                        })
                        //只处理 limitHeight 像素以内的数据
                        if( elemy > limitHeight)break;
                    } catch (e) {
                        //记录错误
                        tweets.push({
                            relem:elems[i],
                            exp:e.message,
                            elemy:lastelemy,
                            tweettexts:{
                                text:e.message
                            },
                            tweettext:e.message
                        })
                    }
                }
            }
            return tweets
        """
        JS_getTweets = "limitHeight = " + limitHeight + "\n" + JS_getTweets
        
        try:
            res = driver.execute_script(JS_getTweets)
            return (True,res)
        except:
            driver.save_screenshot(error_save_filename)
            s = traceback.format_exc(limit=10)
            logger.warning(s+"\n filename="+error_save_filename + ';url=' + driver.current_url)
            return (False,error_save_filename,'获取推文列表异常')
    #保存推文主显示元素到图片
    def saveMainElemToImg(self,filename:str,op:int=0):
        driver = self.driver
        filepath = os.path.join('cache','transtweet',('unknownimg','tweetimg','tweetsimg')[op],filename+'.png')
        elem = driver.find_element_by_css_selector('section[aria-labelledby].css-1dbjc4n')
        file = open(filepath,'wb')
        file.write(elem.screenshot_as_png)
        file.close()
    #保存图片到文件(主要用于保存单一推文)
    def savePngToFile(self,data,filename:str,path=os.path.join('cache','transtweet','tweetimg')):
        file = open(os.path.join('cache',path,filename+'.png'),'wb')
        file.write(data)
        file.close()
    #获取推文数据
    def getTweetsData(self,tasktype:str,scroll_width,op:int=0):
        driver = self.driver
        tres = self.waitForTweetLoad(tasktype)
        if not tres[0]:
            return tres
        tres = self.waitForTweetLoad2(tasktype)
        if not tres[0]:
            return tres
        tres = self.tweetEndInit(tasktype)
        if not tres[0]:
            return tres
        tres = self.getStartHeight(tasktype)
        if not tres[0]:
            return tres
        startheight = tres[1]
        tres = self.getTweets(tasktype)
        if not tres[0]:
            return tres
        tweets = tres[1]
        scroll_height = int(tweets[len(tweets)-1]['elemy']) + int(tweets[len(tweets)-1]['elemh']) + int(startheight) + 300
        driver.set_window_size(scroll_width, scroll_height)
        self.saveMainElemToImg(tasktype,op)
        #额外处理
        self.saveTweetsToJson(tweets,tasktype)
        self.saveTweetsToImg(tweets,tasktype)
        self.web_screenshot(tasktype)
        return (True,tweets)
    #获取时间线推文列表
    def getTimeLine(self,tweet_user_sname:str,tasktype:str = 'def'):
        scroll_width = self.get('https://twitter.com/'+tweet_user_sname+'/with_replies')
        return self.getTweetsData(tasktype,scroll_width,2)
    #获取指定推文ID的推文列表
    def getTweetID(self,TweetID:str,tweet_user_sname:str='s',tasktype:str = 'def'):
        scroll_width = self.get('https://twitter.com/'+tweet_user_sname+'/status/'+TweetID)
        return self.getTweetsData(tasktype,scroll_width,1)
    #执行推文搜索，并置入数据
    def getSingelTweet(self,trans:dict = {},tasktype:str = 'def'):
        driver = self.driver
        error_save_filename = os.path.join('cache','transtweet','error','getSingelTweet-'+tasktype+'.png')
        JS = r"""
            var twemoji = function() {
                "use strict";
                var twemoji = {
                    base: "https://twemoji.maxcdn.com/",
                    ext: ".png",
                    size: "72x72",
                    className: "emoji",
                    convert: {
                        fromCodePoint: fromCodePoint,
                        toCodePoint: toCodePoint
                    },
                    onerror: function onerror() {
                        if (this.parentNode) {
                            this.parentNode.replaceChild(createText(this.alt), this)
                        }
                    },
                    parse: parse,
                    replace: replace,
                    test: test
                },
                escaper = {
                    "&": "&amp;",
                    "<": "&lt;",
                    ">": "&gt;",
                    "'": "&#39;",
                    '"': "&quot;"
                },
                ustr = "(?:\\ud83d\\udc68\\ud83c\\udffb\\u200d\\ud83e\\udd1d\\u200d\\ud83d\\udc68\\ud83c[\\udffc-\\udfff]|\\ud83d\\udc68\\ud83c\\udffc\\u200d\\ud83e\\udd1d\\u200d\\ud83d\\udc68\\ud83c[\\udffb\\udffd-\\udfff]|\\ud83d\\udc68\\ud83c\\udffd\\u200d\\ud83e\\udd1d\\u200d\\ud83d\\udc68\\ud83c[\\udffb\\udffc\\udffe\\udfff]|\\ud83d\\udc68\\ud83c\\udffe\\u200d\\ud83e\\udd1d\\u200d\\ud83d\\udc68\\ud83c[\\udffb-\\udffd\\udfff]|\\ud83d\\udc68\\ud83c\\udfff\\u200d\\ud83e\\udd1d\\u200d\\ud83d\\udc68\\ud83c[\\udffb-\\udffe]|\\ud83d\\udc69\\ud83c\\udffb\\u200d\\ud83e\\udd1d\\u200d\\ud83d\\udc68\\ud83c[\\udffc-\\udfff]|\\ud83d\\udc69\\ud83c\\udffb\\u200d\\ud83e\\udd1d\\u200d\\ud83d\\udc69\\ud83c[\\udffc-\\udfff]|\\ud83d\\udc69\\ud83c\\udffc\\u200d\\ud83e\\udd1d\\u200d\\ud83d\\udc68\\ud83c[\\udffb\\udffd-\\udfff]|\\ud83d\\udc69\\ud83c\\udffc\\u200d\\ud83e\\udd1d\\u200d\\ud83d\\udc69\\ud83c[\\udffb\\udffd-\\udfff]|\\ud83d\\udc69\\ud83c\\udffd\\u200d\\ud83e\\udd1d\\u200d\\ud83d\\udc68\\ud83c[\\udffb\\udffc\\udffe\\udfff]|\\ud83d\\udc69\\ud83c\\udffd\\u200d\\ud83e\\udd1d\\u200d\\ud83d\\udc69\\ud83c[\\udffb\\udffc\\udffe\\udfff]|\\ud83d\\udc69\\ud83c\\udffe\\u200d\\ud83e\\udd1d\\u200d\\ud83d\\udc68\\ud83c[\\udffb-\\udffd\\udfff]|\\ud83d\\udc69\\ud83c\\udffe\\u200d\\ud83e\\udd1d\\u200d\\ud83d\\udc69\\ud83c[\\udffb-\\udffd\\udfff]|\\ud83d\\udc69\\ud83c\\udfff\\u200d\\ud83e\\udd1d\\u200d\\ud83d\\udc68\\ud83c[\\udffb-\\udffe]|\\ud83d\\udc69\\ud83c\\udfff\\u200d\\ud83e\\udd1d\\u200d\\ud83d\\udc69\\ud83c[\\udffb-\\udffe]|\\ud83e\\uddd1\\ud83c\\udffb\\u200d\\ud83e\\udd1d\\u200d\\ud83e\\uddd1\\ud83c[\\udffb-\\udfff]|\\ud83e\\uddd1\\ud83c\\udffc\\u200d\\ud83e\\udd1d\\u200d\\ud83e\\uddd1\\ud83c[\\udffb-\\udfff]|\\ud83e\\uddd1\\ud83c\\udffd\\u200d\\ud83e\\udd1d\\u200d\\ud83e\\uddd1\\ud83c[\\udffb-\\udfff]|\\ud83e\\uddd1\\ud83c\\udffe\\u200d\\ud83e\\udd1d\\u200d\\ud83e\\uddd1\\ud83c[\\udffb-\\udfff]|\\ud83e\\uddd1\\ud83c\\udfff\\u200d\\ud83e\\udd1d\\u200d\\ud83e\\uddd1\\ud83c[\\udffb-\\udfff]|\\ud83e\\uddd1\\u200d\\ud83e\\udd1d\\u200d\\ud83e\\uddd1|\\ud83d\\udc6b\\ud83c[\\udffb-\\udfff]|\\ud83d\\udc6c\\ud83c[\\udffb-\\udfff]|\\ud83d\\udc6d\\ud83c[\\udffb-\\udfff]|\\ud83d[\\udc6b-\\udc6d])|(?:\\ud83d[\\udc68\\udc69]|\\ud83e\\uddd1)(?:\\ud83c[\\udffb-\\udfff])?\\u200d(?:\\u2695\\ufe0f|\\u2696\\ufe0f|\\u2708\\ufe0f|\\ud83c[\\udf3e\\udf73\\udf7c\\udf84\\udf93\\udfa4\\udfa8\\udfeb\\udfed]|\\ud83d[\\udcbb\\udcbc\\udd27\\udd2c\\ude80\\ude92]|\\ud83e[\\uddaf-\\uddb3\\uddbc\\uddbd])|(?:\\ud83c[\\udfcb\\udfcc]|\\ud83d[\\udd74\\udd75]|\\u26f9)((?:\\ud83c[\\udffb-\\udfff]|\\ufe0f)\\u200d[\\u2640\\u2642]\\ufe0f)|(?:\\ud83c[\\udfc3\\udfc4\\udfca]|\\ud83d[\\udc6e\\udc70\\udc71\\udc73\\udc77\\udc81\\udc82\\udc86\\udc87\\ude45-\\ude47\\ude4b\\ude4d\\ude4e\\udea3\\udeb4-\\udeb6]|\\ud83e[\\udd26\\udd35\\udd37-\\udd39\\udd3d\\udd3e\\uddb8\\uddb9\\uddcd-\\uddcf\\uddd6-\\udddd])(?:\\ud83c[\\udffb-\\udfff])?\\u200d[\\u2640\\u2642]\\ufe0f|(?:\\ud83d\\udc68\\u200d\\u2764\\ufe0f\\u200d\\ud83d\\udc8b\\u200d\\ud83d\\udc68|\\ud83d\\udc68\\u200d\\ud83d\\udc68\\u200d\\ud83d\\udc66\\u200d\\ud83d\\udc66|\\ud83d\\udc68\\u200d\\ud83d\\udc68\\u200d\\ud83d\\udc67\\u200d\\ud83d[\\udc66\\udc67]|\\ud83d\\udc68\\u200d\\ud83d\\udc69\\u200d\\ud83d\\udc66\\u200d\\ud83d\\udc66|\\ud83d\\udc68\\u200d\\ud83d\\udc69\\u200d\\ud83d\\udc67\\u200d\\ud83d[\\udc66\\udc67]|\\ud83d\\udc69\\u200d\\u2764\\ufe0f\\u200d\\ud83d\\udc8b\\u200d\\ud83d[\\udc68\\udc69]|\\ud83d\\udc69\\u200d\\ud83d\\udc69\\u200d\\ud83d\\udc66\\u200d\\ud83d\\udc66|\\ud83d\\udc69\\u200d\\ud83d\\udc69\\u200d\\ud83d\\udc67\\u200d\\ud83d[\\udc66\\udc67]|\\ud83d\\udc68\\u200d\\u2764\\ufe0f\\u200d\\ud83d\\udc68|\\ud83d\\udc68\\u200d\\ud83d\\udc66\\u200d\\ud83d\\udc66|\\ud83d\\udc68\\u200d\\ud83d\\udc67\\u200d\\ud83d[\\udc66\\udc67]|\\ud83d\\udc68\\u200d\\ud83d\\udc68\\u200d\\ud83d[\\udc66\\udc67]|\\ud83d\\udc68\\u200d\\ud83d\\udc69\\u200d\\ud83d[\\udc66\\udc67]|\\ud83d\\udc69\\u200d\\u2764\\ufe0f\\u200d\\ud83d[\\udc68\\udc69]|\\ud83d\\udc69\\u200d\\ud83d\\udc66\\u200d\\ud83d\\udc66|\\ud83d\\udc69\\u200d\\ud83d\\udc67\\u200d\\ud83d[\\udc66\\udc67]|\\ud83d\\udc69\\u200d\\ud83d\\udc69\\u200d\\ud83d[\\udc66\\udc67]|\\ud83c\\udff3\\ufe0f\\u200d\\u26a7\\ufe0f|\\ud83c\\udff3\\ufe0f\\u200d\\ud83c\\udf08|\\ud83c\\udff4\\u200d\\u2620\\ufe0f|\\ud83d\\udc15\\u200d\\ud83e\\uddba|\\ud83d\\udc3b\\u200d\\u2744\\ufe0f|\\ud83d\\udc41\\u200d\\ud83d\\udde8|\\ud83d\\udc68\\u200d\\ud83d[\\udc66\\udc67]|\\ud83d\\udc69\\u200d\\ud83d[\\udc66\\udc67]|\\ud83d\\udc6f\\u200d\\u2640\\ufe0f|\\ud83d\\udc6f\\u200d\\u2642\\ufe0f|\\ud83e\\udd3c\\u200d\\u2640\\ufe0f|\\ud83e\\udd3c\\u200d\\u2642\\ufe0f|\\ud83e\\uddde\\u200d\\u2640\\ufe0f|\\ud83e\\uddde\\u200d\\u2642\\ufe0f|\\ud83e\\udddf\\u200d\\u2640\\ufe0f|\\ud83e\\udddf\\u200d\\u2642\\ufe0f|\\ud83d\\udc08\\u200d\\u2b1b)|[#*0-9]\\ufe0f?\\u20e3|(?:[©®\\u2122\\u265f]\\ufe0f)|(?:\\ud83c[\\udc04\\udd70\\udd71\\udd7e\\udd7f\\ude02\\ude1a\\ude2f\\ude37\\udf21\\udf24-\\udf2c\\udf36\\udf7d\\udf96\\udf97\\udf99-\\udf9b\\udf9e\\udf9f\\udfcd\\udfce\\udfd4-\\udfdf\\udff3\\udff5\\udff7]|\\ud83d[\\udc3f\\udc41\\udcfd\\udd49\\udd4a\\udd6f\\udd70\\udd73\\udd76-\\udd79\\udd87\\udd8a-\\udd8d\\udda5\\udda8\\uddb1\\uddb2\\uddbc\\uddc2-\\uddc4\\uddd1-\\uddd3\\udddc-\\uddde\\udde1\\udde3\\udde8\\uddef\\uddf3\\uddfa\\udecb\\udecd-\\udecf\\udee0-\\udee5\\udee9\\udef0\\udef3]|[\\u203c\\u2049\\u2139\\u2194-\\u2199\\u21a9\\u21aa\\u231a\\u231b\\u2328\\u23cf\\u23ed-\\u23ef\\u23f1\\u23f2\\u23f8-\\u23fa\\u24c2\\u25aa\\u25ab\\u25b6\\u25c0\\u25fb-\\u25fe\\u2600-\\u2604\\u260e\\u2611\\u2614\\u2615\\u2618\\u2620\\u2622\\u2623\\u2626\\u262a\\u262e\\u262f\\u2638-\\u263a\\u2640\\u2642\\u2648-\\u2653\\u2660\\u2663\\u2665\\u2666\\u2668\\u267b\\u267f\\u2692-\\u2697\\u2699\\u269b\\u269c\\u26a0\\u26a1\\u26a7\\u26aa\\u26ab\\u26b0\\u26b1\\u26bd\\u26be\\u26c4\\u26c5\\u26c8\\u26cf\\u26d1\\u26d3\\u26d4\\u26e9\\u26ea\\u26f0-\\u26f5\\u26f8\\u26fa\\u26fd\\u2702\\u2708\\u2709\\u270f\\u2712\\u2714\\u2716\\u271d\\u2721\\u2733\\u2734\\u2744\\u2747\\u2757\\u2763\\u2764\\u27a1\\u2934\\u2935\\u2b05-\\u2b07\\u2b1b\\u2b1c\\u2b50\\u2b55\\u3030\\u303d\\u3297\\u3299])(?:\\ufe0f|(?!\\ufe0e))|(?:(?:\\ud83c[\\udfcb\\udfcc]|\\ud83d[\\udd74\\udd75\\udd90]|[\\u261d\\u26f7\\u26f9\\u270c\\u270d])(?:\\ufe0f|(?!\\ufe0e))|(?:\\ud83c[\\udf85\\udfc2-\\udfc4\\udfc7\\udfca]|\\ud83d[\\udc42\\udc43\\udc46-\\udc50\\udc66-\\udc69\\udc6e\\udc70-\\udc78\\udc7c\\udc81-\\udc83\\udc85-\\udc87\\udcaa\\udd7a\\udd95\\udd96\\ude45-\\ude47\\ude4b-\\ude4f\\udea3\\udeb4-\\udeb6\\udec0\\udecc]|\\ud83e[\\udd0c\\udd0f\\udd18-\\udd1c\\udd1e\\udd1f\\udd26\\udd30-\\udd39\\udd3d\\udd3e\\udd77\\uddb5\\uddb6\\uddb8\\uddb9\\uddbb\\uddcd-\\uddcf\\uddd1-\\udddd]|[\\u270a\\u270b]))(?:\\ud83c[\\udffb-\\udfff])?|(?:\\ud83c\\udff4\\udb40\\udc67\\udb40\\udc62\\udb40\\udc65\\udb40\\udc6e\\udb40\\udc67\\udb40\\udc7f|\\ud83c\\udff4\\udb40\\udc67\\udb40\\udc62\\udb40\\udc73\\udb40\\udc63\\udb40\\udc74\\udb40\\udc7f|\\ud83c\\udff4\\udb40\\udc67\\udb40\\udc62\\udb40\\udc77\\udb40\\udc6c\\udb40\\udc73\\udb40\\udc7f|\\ud83c\\udde6\\ud83c[\\udde8-\\uddec\\uddee\\uddf1\\uddf2\\uddf4\\uddf6-\\uddfa\\uddfc\\uddfd\\uddff]|\\ud83c\\udde7\\ud83c[\\udde6\\udde7\\udde9-\\uddef\\uddf1-\\uddf4\\uddf6-\\uddf9\\uddfb\\uddfc\\uddfe\\uddff]|\\ud83c\\udde8\\ud83c[\\udde6\\udde8\\udde9\\uddeb-\\uddee\\uddf0-\\uddf5\\uddf7\\uddfa-\\uddff]|\\ud83c\\udde9\\ud83c[\\uddea\\uddec\\uddef\\uddf0\\uddf2\\uddf4\\uddff]|\\ud83c\\uddea\\ud83c[\\udde6\\udde8\\uddea\\uddec\\udded\\uddf7-\\uddfa]|\\ud83c\\uddeb\\ud83c[\\uddee-\\uddf0\\uddf2\\uddf4\\uddf7]|\\ud83c\\uddec\\ud83c[\\udde6\\udde7\\udde9-\\uddee\\uddf1-\\uddf3\\uddf5-\\uddfa\\uddfc\\uddfe]|\\ud83c\\udded\\ud83c[\\uddf0\\uddf2\\uddf3\\uddf7\\uddf9\\uddfa]|\\ud83c\\uddee\\ud83c[\\udde8-\\uddea\\uddf1-\\uddf4\\uddf6-\\uddf9]|\\ud83c\\uddef\\ud83c[\\uddea\\uddf2\\uddf4\\uddf5]|\\ud83c\\uddf0\\ud83c[\\uddea\\uddec-\\uddee\\uddf2\\uddf3\\uddf5\\uddf7\\uddfc\\uddfe\\uddff]|\\ud83c\\uddf1\\ud83c[\\udde6-\\udde8\\uddee\\uddf0\\uddf7-\\uddfb\\uddfe]|\\ud83c\\uddf2\\ud83c[\\udde6\\udde8-\\udded\\uddf0-\\uddff]|\\ud83c\\uddf3\\ud83c[\\udde6\\udde8\\uddea-\\uddec\\uddee\\uddf1\\uddf4\\uddf5\\uddf7\\uddfa\\uddff]|\\ud83c\\uddf4\\ud83c\\uddf2|\\ud83c\\uddf5\\ud83c[\\udde6\\uddea-\\udded\\uddf0-\\uddf3\\uddf7-\\uddf9\\uddfc\\uddfe]|\\ud83c\\uddf6\\ud83c\\udde6|\\ud83c\\uddf7\\ud83c[\\uddea\\uddf4\\uddf8\\uddfa\\uddfc]|\\ud83c\\uddf8\\ud83c[\\udde6-\\uddea\\uddec-\\uddf4\\uddf7-\\uddf9\\uddfb\\uddfd-\\uddff]|\\ud83c\\uddf9\\ud83c[\\udde6\\udde8\\udde9\\uddeb-\\udded\\uddef-\\uddf4\\uddf7\\uddf9\\uddfb\\uddfc\\uddff]|\\ud83c\\uddfa\\ud83c[\\udde6\\uddec\\uddf2\\uddf3\\uddf8\\uddfe\\uddff]|\\ud83c\\uddfb\\ud83c[\\udde6\\udde8\\uddea\\uddec\\uddee\\uddf3\\uddfa]|\\ud83c\\uddfc\\ud83c[\\uddeb\\uddf8]|\\ud83c\\uddfd\\ud83c\\uddf0|\\ud83c\\uddfe\\ud83c[\\uddea\\uddf9]|\\ud83c\\uddff\\ud83c[\\udde6\\uddf2\\uddfc]|\\ud83c[\\udccf\\udd8e\\udd91-\\udd9a\\udde6-\\uddff\\ude01\\ude32-\\ude36\\ude38-\\ude3a\\ude50\\ude51\\udf00-\\udf20\\udf2d-\\udf35\\udf37-\\udf7c\\udf7e-\\udf84\\udf86-\\udf93\\udfa0-\\udfc1\\udfc5\\udfc6\\udfc8\\udfc9\\udfcf-\\udfd3\\udfe0-\\udff0\\udff4\\udff8-\\udfff]|\\ud83d[\\udc00-\\udc3e\\udc40\\udc44\\udc45\\udc51-\\udc65\\udc6a\\udc6f\\udc79-\\udc7b\\udc7d-\\udc80\\udc84\\udc88-\\udca9\\udcab-\\udcfc\\udcff-\\udd3d\\udd4b-\\udd4e\\udd50-\\udd67\\udda4\\uddfb-\\ude44\\ude48-\\ude4a\\ude80-\\udea2\\udea4-\\udeb3\\udeb7-\\udebf\\udec1-\\udec5\\uded0-\\uded2\\uded5-\\uded7\\udeeb\\udeec\\udef4-\\udefc\\udfe0-\\udfeb]|\\ud83e[\\udd0d\\udd0e\\udd10-\\udd17\\udd1d\\udd20-\\udd25\\udd27-\\udd2f\\udd3a\\udd3c\\udd3f-\\udd45\\udd47-\\udd76\\udd78\\udd7a-\\uddb4\\uddb7\\uddba\\uddbc-\\uddcb\\uddd0\\uddde-\\uddff\\ude70-\\ude74\\ude78-\\ude7a\\ude80-\\ude86\\ude90-\\udea8\\udeb0-\\udeb6\\udec0-\\udec2\\uded0-\\uded6]|[\\u23e9-\\u23ec\\u23f0\\u23f3\\u267e\\u26ce\\u2705\\u2728\\u274c\\u274e\\u2753-\\u2755\\u2795-\\u2797\\u27b0\\u27bf\\ue50a])|\\ufe0f",
                re = RegExp(ustr,'g'),
                UFE0Fg = /\uFE0F/g,
                U200D = String.fromCharCode(8205),
                rescaper = /[&<>'"]/g,
                shouldntBeParsed = /IFRAME|NOFRAMES|NOSCRIPT|SCRIPT|SELECT|STYLE|TEXTAREA|[a-z]/,
                fromCharCode = String.fromCharCode;
                return twemoji;
                function createText(text) {
                    return document.createTextNode(text)
                }
                function escapeHTML(s) {
                    return s.replace(rescaper, replacer)
                }
                function defaultImageSrcGenerator(icon, options) {
                    return "".concat(options.base, options.size, "/", icon, options.ext)
                }
                function grabAllTextNodes(node, allText) {
                    var childNodes = node.childNodes,
                    length = childNodes.length,
                    subnode, nodeType;
                    while (length--) {
                        subnode = childNodes[length];
                        nodeType = subnode.nodeType;
                        if (nodeType === 3) {
                            allText.push(subnode)
                        } else if (nodeType === 1 && !shouldntBeParsed.test(subnode.nodeName)) {
                            grabAllTextNodes(subnode, allText)
                        }
                    }
                    return allText
                }
                function grabTheRightIcon(rawText) {
                    return toCodePoint(rawText.indexOf(U200D) < 0 ? rawText.replace(UFE0Fg, "") : rawText)
                }
                function parseNode(node, options) {
                    var allText = grabAllTextNodes(node, []),
                    length = allText.length,
                    attrib,
                    attrname,
                    modified,
                    fragment,
                    subnode,
                    text,
                    match,
                    i,
                    index,
                    img,
                    rawText,
                    iconId,
                    src;
                    while (length--) {
                        modified = false;
                        fragment = document.createDocumentFragment();
                        subnode = allText[length];
                        text = subnode.nodeValue;
                        i = 0;
                        while (match = re.exec(text)) {
                            index = match.index;
                            if (index !== i) {
                                fragment.appendChild(createText(text.slice(i, index)))
                            }
                            rawText = match[0];
                            iconId = grabTheRightIcon(rawText);
                            i = index + rawText.length;
                            src = options.callback(iconId, options);
                            if (src) {
                                img = new Image;
                                img.onerror = options.onerror;
                                img.setAttribute("draggable", "false");
                                attrib = options.attributes(rawText, iconId);
                                for (attrname in attrib) {
                                    if (attrib.hasOwnProperty(attrname) && attrname.indexOf("on") !== 0 && !img.hasAttribute(attrname)) {
                                        img.setAttribute(attrname, attrib[attrname])
                                    }
                                }
                                img.className = options.className;
                                img.alt = rawText;
                                img.src = src;
                                modified = true;
                                fragment.appendChild(img)
                            }
                            if (!img) fragment.appendChild(createText(rawText));
                            img = null
                        }
                        if (modified) {
                            if (i < text.length) {
                                fragment.appendChild(createText(text.slice(i)))
                            }
                            subnode.parentNode.replaceChild(fragment, subnode)
                        }
                    }
                    return node
                }
                function parseString(str, options) {
                    return replace(str,
                    function(rawText) {
                        var ret = rawText,
                        iconId = grabTheRightIcon(rawText),
                        src = options.callback(iconId, options),
                        attrib,
                        attrname;
                        if (src) {
                            ret = "<img ".concat('class="', options.className, '" ', 'draggable="false" ', 'alt="', rawText, '"', ' src="', src, '"');
                            attrib = options.attributes(rawText, iconId);
                            for (attrname in attrib) {
                                if (attrib.hasOwnProperty(attrname) && attrname.indexOf("on") !== 0 && ret.indexOf(" " + attrname + "=") === -1) {
                                    ret = ret.concat(" ", attrname, '="', escapeHTML(attrib[attrname]), '"')
                                }
                            }
                            ret = ret.concat(">")
                        }
                        return ret
                    })
                }
                function replacer(m) {
                    return escaper[m]
                }
                function returnNull() {
                    return null
                }
                function toSizeSquaredAsset(value) {
                    return typeof value === "number" ? value + "x" + value: value
                }
                function fromCodePoint(codepoint) {
                    var code = typeof codepoint === "string" ? parseInt(codepoint, 16) : codepoint;
                    if (code < 65536) {
                        return fromCharCode(code)
                    }
                    code -= 65536;
                    return fromCharCode(55296 + (code >> 10), 56320 + (code & 1023))
                }
                function parse(what, how) {
                    if (!how || typeof how === "function") {
                        how = {
                            callback: how
                        }
                    }
                    return (typeof what === "string" ? parseString: parseNode)(what, {
                        callback: how.callback || defaultImageSrcGenerator,
                        attributes: typeof how.attributes === "function" ? how.attributes: returnNull,
                        base: typeof how.base === "string" ? how.base: twemoji.base,
                        ext: how.ext || twemoji.ext,
                        size: how.folder || toSizeSquaredAsset(how.size || twemoji.size),
                        className: how.className || twemoji.className,
                        onerror: how.onerror || twemoji.onerror
                    })
                }
                function replace(text, callback) {
                    return String(text).replace(re, callback)
                }
                function test(text) {
                    re.lastIndex = 0;
                    var result = re.test(text);
                    re.lastIndex = 0;
                    return result
                }
                function toCodePoint(unicodeSurrogates, sep) {
                    var r = [],
                    c = 0,
                    p = 0,
                    i = 0;
                    while (i < unicodeSurrogates.length) {
                        c = unicodeSurrogates.charCodeAt(i++);
                        if (p) {
                            r.push((65536 + (p - 55296 << 10) + (c - 56320)).toString(16));
                            p = 0
                        } else if (55296 <= c && c <= 56319) {
                            p = c
                        } else {
                            r.push(c.toString(16))
                        }
                    }
                    return r.join(sep || "-")
                }
            } ();

        """
        JS = JS + r"""
            let translist=arguments[0]
            //多重回复终止定位
            try {
                function attributesCallback(icon, variant) {
                    return {
                        title: 'Emoji: ' + icon + variant,
                        style: 'height: 1em;width: 1em;margin: 0.05em 0.1em;vertical-align: -0.1em;'
                    };
                }
                function textparse(text){
                    text = text.replace(/(\S*)(#\S+)/gi,'$1<a style="color:#1DA1F2;">$2</a>')
                    text = text.replace(/((https?|ftp|file):\/\/[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|])/g,'<a style="color:#1DA1F2;">$1</a>')
                    return twemoji.parse(text,{
                        attributes:attributesCallback,
                        base:'https://abs-0.twimg.com/emoji/v2/',
                        folder: 'svg',
                        ext: '.svg'
                    });
                }
                var shotelem = document.createElement('div')
                shotelem.id = 'shot_elem'
                //可翻译推文的列表
                var tweets = []
                //推文主元素
                let mainelem = document.querySelector('section[aria-labelledby].css-1dbjc4n')
                if(!mainelem){
                    return [false,"推文不存在"]
                }
                let elems = mainelem.querySelectorAll('article')
                var lastelem = null
                if(elems.length == 0){
                    return [false,"未发现推文，请重试"]
                }
                //搜索可翻译元素
                for (var i = 0;1==1;i++) {
                    //发现元素不存在时
                    if(typeof(elems[i])== 'undefined'){
                        return [false,"未搜索到推文结束位置，请联系制作者反馈！"]
                    }
                    //搜索推文
                    let elart = elems[i]
                    console.log(elart)
                    if(elart){
                        elart = elart.cloneNode(true)
                        shotelem.append(elart);
                        let trans = []
                        let elemet = elart.querySelector('[aria-expanded]')
                        if(elemet)elemet.style.visibility="hidden" //隐藏翻译蓝链
                        let elemtexts = elart.querySelectorAll('div[lang][dir="auto"]')
                        for(var j = 0;j<elemtexts.length;j++){
                            trans.push({
                                elem:elemtexts[j],
                                text:elemtexts[j].innerText
                            })
                        }
                        tweets.push(trans)
                        //检测推文是否结束
                        //转推
                        let rt = elart.querySelector('a[dir][role="link"][href$="retweets"]')
                        if(rt){
                            //跳出
                            break;
                        }
                        //喜欢
                        let lk = elart.querySelector('a[dir][role="link"][href$="likes"]')
                        if(lk){
                            //跳出
                            break;
                        }
                        //时间
                        let t = elart.querySelector('a[href$="how-to-tweet#source-labels"]')
                        if(t){
                            //跳出
                            break;
                        }
                        //喜欢 lk = document.querySelectorAll('a[dir][role="link"][href$="likes"]')
                        //时间检测(有危险) t = document.querySelectorAll('a[rel][role="link"][target="_blank"][href="https://help.twitter.com/using-twitter/how-to-tweet#source-labels"]')[0]
                    }
                }
                //翻译用的class transclass = elems[0].querySelector('div[lang][dir="auto"]>span').className
                let transclass = 'tweetadd css-901oao css-16my406 r-1qd0xha r-ad9z0x r-bcqeeo r-qvutc0'
                let frontf = "font-family:\"Source Han Sans CN\", system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, Ubuntu, \"Helvetica Neue\", sans-serif;"
                //翻译标识
                let node_type = document.createElement('span')
                node_type.className = transclass
                node_type.innerHTML = translist.type_html //同步设置
                //置入翻译(遍历推文)
                for (let i = 0;i < tweets.length;i++) {
                    //此次推文对应的翻译组(有可能不存在)
                    let tran_text = null
                    if(typeof(translist.text[(i+1)])!= 'undefined'){
                        tran_text = translist.text[i+1]
                    }
                    //处理推文主节点,次要节点一般为转发的推文
                    //最末的推文(需要置入翻译标识)
                    if(i == (tweets.length-1)){
                        tweets[i][0].elem.append(node_type)//添加推文标识
                        if(!tran_text){
                            tran_text = translist.text['main'] //翻译节点不存在时切换翻译为主翻译
                        }
                    }else{
                        //非末推文存在翻译时清空节点
                        if(tran_text){
                            tweets[i][0].elem.innerHTML = "" //存在翻译则清空节点
                        }
                    }
                    console.log(tran_text)
                    if(tran_text){
                        if(tran_text[0]){
                            let node_trans = document.createElement('div');//翻译节点
                            //注 入 样 式
                            node_trans.className = transclass
                            node_trans.setAttribute('style',frontf)
                            //置入推文主节点的翻译
                            node_trans.innerHTML = textparse(tran_text[0],transclass)
                            tweets[i][0].elem.appendChild(node_trans)

                        }
                        //次节点的翻译与次节点同时存在时
                        if(tran_text[1] && tweets[i][1]){
                            let node_trans = document.createElement('div');//翻译节点
                            //注 入 样 式
                            node_trans.className = transclass
                            node_trans.setAttribute('style',frontf)
                            //清空次节点
                            tweets[i][1].elem.innerHTML = ""
                            //置入推文次节点的翻译
                            node_trans.innerHTML = textparse(tran_text[1],transclass)
                            tweets[i][1].elem.appendChild(node_trans)

                        }
                    }
                }
                //锁定推文高度以便截取元素
                //overflow:hidden;min-height:xxpx;
                mainelem.innerHTML = ""
                mainelem.append(shotelem)
            } catch (e) {
                //返回错误
                console.log(tweets)
                console.log(e)
                return [false,"推文分析出现异常，请联系作者"]
            }
            return [true,tweets,lastelem]
        """   
        res = None
        try:
            res = driver.execute_script(JS,trans)
        except:
            driver.save_screenshot(error_save_filename)
            s = traceback.format_exc(limit=10)
            logger.warning(s+"\n filename="+error_save_filename + ';url=' + driver.current_url)
            return (False,error_save_filename,'页面调度异常')
        if res == None:
            res = (False,"推文分析未返回数据")
        if res[0] == False:
            driver.save_screenshot(error_save_filename)
            logger.warning("推文分析未返回数据，filename="+error_save_filename + ';url=' + driver.current_url)
            return (False,error_save_filename,res[1])
        time.sleep(1.5)
        return (True,res)
    #对指定推文置入翻译并获取截图
    def getTransFromTweetID(self,TweetID:str,trans:list,tweet_user_sname:str='s',tasktype:str = 'def'):
        """
        trans={
            'type_html':翻译标识html,
            'text':{
                '1':["测试翻译","次节点翻译"],//推文只处理前两个值(主节点，次节点-转发的推文)
                '2':["二层翻译","二层次节点"],
                'main':["主翻译","主翻译节点"],//末端的主推文，置入参数前处理(先搜索对应下标再搜索main-main用于无下标置入)
            }
        }
        """
        scroll_width = self.get('https://twitter.com/'+tweet_user_sname+'/status/'+TweetID)
        driver = self.driver
        error_save_filename = os.path.join('cache','transtweet','error','getTransFromTweetID-'+tasktype+'.png')
        tres = self.waitForTweetLoad(tasktype)
        if not tres[0]:
            return tres
        tres = self.getSingelTweet(trans,tasktype)
        if not tres[0]:
            return tres
        time.sleep(1.5)
        try:
            #scroll_width = driver.execute_script('return document.body.parentNode.scrollWidth')
            elem = driver.find_element_by_css_selector('section[aria-labelledby].css-1dbjc4n')
            driver.set_window_size(scroll_width, elem.size['height']+300)
        except:
            driver.save_screenshot(error_save_filename)
            s = traceback.format_exc(limit=10)
            logger.warning(s+"\n filename="+error_save_filename + ';url=' + driver.current_url)
            return (False,error_save_filename,'更改渲染宽高时异常')
        filepath = os.path.join('cache','transtweet','transimg',tasktype+'.png')
        try:
            file = open(filepath,'wb')
            file.write(elem.screenshot_as_png)
            file.close()
        except:
            if file:
                file.close()
            driver.save_screenshot(error_save_filename)
            s = traceback.format_exc(limit=10)
            logger.warning(s+"\n filename="+error_save_filename + ';url=' + driver.current_url)
            return (False,error_save_filename,'保存推文翻译图片时异常')
        return (True,filepath,'保存成功')
    #处理tweets，使tweets可以json化
    def dealTweets(self,tweets):
        ttweets = []
        cout_id = 0
        for tweet in tweets:
            if 'elem' in tweet:
                ttweet = tweet.copy()
                cout_id = cout_id + 1
                ttweet['cout_id'] = cout_id
                del ttweet['relem']
                del ttweet['elem']
                ttweet['tweettexts'] = ttweet['tweettexts'].copy()
                tts = ttweet['tweettexts']
                for tt in tts:
                    del tt['elem']
                ttweets.append(ttweet)
        return ttweets
    #保存推文列表到json
    def saveTweetsToJson(self,tweets,tasktype:str):
        path = os.path.join('transtweet','res_tweets_json')
        check_path(path)
        filename = tasktype+'.json'
        ttweets = self.dealTweets(tweets)
        data_save(filename,ttweets,path)
    #保存推文列表的每个推文元素到图片
    def saveTweetsToImg(self,tweets,tasktype:str):
        driver = self.driver
        path = os.path.join('transtweet','res_tweets',tasktype)
        check_path(path)
        cout_id = 0
        for tweet in tweets:
            if 'elem' in tweet:
                cout_id = cout_id + 1
                #tweet['base64'] = tweet['elem'].screenshot_as_base64
                self.savePngToFile(tweet['relem'].screenshot_as_png,str(cout_id),path=path)
        driver.execute_script('window.scrollTo(0,0)')
        return 'success!'
    #保存浏览器全页面到图片
    def web_screenshot(self,tasktype:str):
        driver = self.driver
        path = os.path.join('transtweet','web_screenshot')
        check_path(path)
        save_filename = os.path.join('cache',path,tasktype+'.png')
        driver.get_screenshot_as_file(save_filename)
    #缩放
    def doczoom(self,zoom):
        driver = self.driver
        driver.execute_script("document.body.style.zoom='"+str(zoom)+"'")