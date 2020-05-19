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
        chrome_options.add_argument('-lang=zh-cn')
        chrome_options.add_argument('accept-language="zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6"')
        chrome_options.add_argument('x-twitter-active-user=yes')
        chrome_options.add_argument('dnt=1')
        chrome_options.add_argument('x-twitter-client-language=zh-cn')
        #chrome_options.add_argument('--disk-cache-dir=./cache/chromecache')
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
        JS = """
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
                re = /(?:[9876543210#])️?⃣|🇨🇳|🇩🇪|🇪🇸|🇫🇷|🇬🇧|🇮🇹|🇯🇵|🇰🇷|🇷🇺|🇺🇸|�[�-���-��-��-��-��-��-��-�]|�[���-��-���-��-����-��-��-��-��-��-��-�]|[➿➰➗➖➕❕❔❓❎❌✨✋✊✅⛎⏳⏰⏬⏫⏪⏩]|(?:�[���������]|[㊙㊗〽〰⭕⭐⬜⬛⬇⬆⬅⤵⤴➡❤❗❇❄✴✳✖✔✒✏✌✉✈✂⛽⛺⛵⛳⛲⛪⛔⛅⛄⚾⚽⚫⚪⚡⚠⚓♿♻♨♦♥♣♠♓♒♑♐♏♎♍♌♋♊♉♈☺☝☕☔☑☎☁☀◾◽◼◻◀▶▫▪Ⓜ⌛⌚↪↩↙↘↗↖↕↔ℹ™⁉‼®©])(?:️|(?!︎))/g,
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
        JS = JS + """
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
                    text = text.replace(/((https?|ftp|file):\/\/[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|])/,'<a style="color:#1DA1F2;">$1</a>')
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
                            //置入推文主节点的翻译
                            node_trans.innerHTML = textparse(tran_text[0],transclass)
                            tweets[i][0].elem.appendChild(node_trans)

                        }
                        //次节点的翻译与次节点同时存在时
                        if(tran_text[1] && tweets[i][1]){
                            let node_trans = document.createElement('div');//翻译节点
                            //注 入 样 式
                            node_trans.className = transclass
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