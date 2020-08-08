// ==UserScript==
// @name         推文消息获取与翻译置入测试
// @namespace    http://tampermonkey.net/
// @version      1.1
// @description  try to take over the world!
// @author       You
// @match        https://twitter.com/*
// @grant        none
// @require      https://cdn.staticfile.org/jquery/1.10.2/jquery.min.js

// ==/UserScript==
/*! Copyright Twitter Inc. and other contributors. Licensed under MIT */
var twemoji=function(){"use strict";var twemoji={base:"https://twemoji.maxcdn.com/v/13.0.0/",ext:".png",size:"72x72",className:"emoji",convert:{fromCodePoint:fromCodePoint,toCodePoint:toCodePoint},onerror:function onerror(){if(this.parentNode){this.parentNode.replaceChild(createText(this.alt,false),this)}},parse:parse,replace:replace,test:test},escaper={"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"},re=/(?:\ud83d\udc68\ud83c\udffb\u200d\ud83e\udd1d\u200d\ud83d\udc68\ud83c[\udffc-\udfff]|\ud83d\udc68\ud83c\udffc\u200d\ud83e\udd1d\u200d\ud83d\udc68\ud83c[\udffb\udffd-\udfff]|\ud83d\udc68\ud83c\udffd\u200d\ud83e\udd1d\u200d\ud83d\udc68\ud83c[\udffb\udffc\udffe\udfff]|\ud83d\udc68\ud83c\udffe\u200d\ud83e\udd1d\u200d\ud83d\udc68\ud83c[\udffb-\udffd\udfff]|\ud83d\udc68\ud83c\udfff\u200d\ud83e\udd1d\u200d\ud83d\udc68\ud83c[\udffb-\udffe]|\ud83d\udc69\ud83c\udffb\u200d\ud83e\udd1d\u200d\ud83d\udc68\ud83c[\udffc-\udfff]|\ud83d\udc69\ud83c\udffb\u200d\ud83e\udd1d\u200d\ud83d\udc69\ud83c[\udffc-\udfff]|\ud83d\udc69\ud83c\udffc\u200d\ud83e\udd1d\u200d\ud83d\udc68\ud83c[\udffb\udffd-\udfff]|\ud83d\udc69\ud83c\udffc\u200d\ud83e\udd1d\u200d\ud83d\udc69\ud83c[\udffb\udffd-\udfff]|\ud83d\udc69\ud83c\udffd\u200d\ud83e\udd1d\u200d\ud83d\udc68\ud83c[\udffb\udffc\udffe\udfff]|\ud83d\udc69\ud83c\udffd\u200d\ud83e\udd1d\u200d\ud83d\udc69\ud83c[\udffb\udffc\udffe\udfff]|\ud83d\udc69\ud83c\udffe\u200d\ud83e\udd1d\u200d\ud83d\udc68\ud83c[\udffb-\udffd\udfff]|\ud83d\udc69\ud83c\udffe\u200d\ud83e\udd1d\u200d\ud83d\udc69\ud83c[\udffb-\udffd\udfff]|\ud83d\udc69\ud83c\udfff\u200d\ud83e\udd1d\u200d\ud83d\udc68\ud83c[\udffb-\udffe]|\ud83d\udc69\ud83c\udfff\u200d\ud83e\udd1d\u200d\ud83d\udc69\ud83c[\udffb-\udffe]|\ud83e\uddd1\ud83c\udffb\u200d\ud83e\udd1d\u200d\ud83e\uddd1\ud83c[\udffb-\udfff]|\ud83e\uddd1\ud83c\udffc\u200d\ud83e\udd1d\u200d\ud83e\uddd1\ud83c[\udffb-\udfff]|\ud83e\uddd1\ud83c\udffd\u200d\ud83e\udd1d\u200d\ud83e\uddd1\ud83c[\udffb-\udfff]|\ud83e\uddd1\ud83c\udffe\u200d\ud83e\udd1d\u200d\ud83e\uddd1\ud83c[\udffb-\udfff]|\ud83e\uddd1\ud83c\udfff\u200d\ud83e\udd1d\u200d\ud83e\uddd1\ud83c[\udffb-\udfff]|\ud83e\uddd1\u200d\ud83e\udd1d\u200d\ud83e\uddd1|\ud83d\udc6b\ud83c[\udffb-\udfff]|\ud83d\udc6c\ud83c[\udffb-\udfff]|\ud83d\udc6d\ud83c[\udffb-\udfff]|\ud83d[\udc6b-\udc6d])|(?:\ud83d[\udc68\udc69]|\ud83e\uddd1)(?:\ud83c[\udffb-\udfff])?\u200d(?:\u2695\ufe0f|\u2696\ufe0f|\u2708\ufe0f|\ud83c[\udf3e\udf73\udf7c\udf84\udf93\udfa4\udfa8\udfeb\udfed]|\ud83d[\udcbb\udcbc\udd27\udd2c\ude80\ude92]|\ud83e[\uddaf-\uddb3\uddbc\uddbd])|(?:\ud83c[\udfcb\udfcc]|\ud83d[\udd74\udd75]|\u26f9)((?:\ud83c[\udffb-\udfff]|\ufe0f)\u200d[\u2640\u2642]\ufe0f)|(?:\ud83c[\udfc3\udfc4\udfca]|\ud83d[\udc6e\udc70\udc71\udc73\udc77\udc81\udc82\udc86\udc87\ude45-\ude47\ude4b\ude4d\ude4e\udea3\udeb4-\udeb6]|\ud83e[\udd26\udd35\udd37-\udd39\udd3d\udd3e\uddb8\uddb9\uddcd-\uddcf\uddd6-\udddd])(?:\ud83c[\udffb-\udfff])?\u200d[\u2640\u2642]\ufe0f|(?:\ud83d\udc68\u200d\u2764\ufe0f\u200d\ud83d\udc8b\u200d\ud83d\udc68|\ud83d\udc68\u200d\ud83d\udc68\u200d\ud83d\udc66\u200d\ud83d\udc66|\ud83d\udc68\u200d\ud83d\udc68\u200d\ud83d\udc67\u200d\ud83d[\udc66\udc67]|\ud83d\udc68\u200d\ud83d\udc69\u200d\ud83d\udc66\u200d\ud83d\udc66|\ud83d\udc68\u200d\ud83d\udc69\u200d\ud83d\udc67\u200d\ud83d[\udc66\udc67]|\ud83d\udc69\u200d\u2764\ufe0f\u200d\ud83d\udc8b\u200d\ud83d[\udc68\udc69]|\ud83d\udc69\u200d\ud83d\udc69\u200d\ud83d\udc66\u200d\ud83d\udc66|\ud83d\udc69\u200d\ud83d\udc69\u200d\ud83d\udc67\u200d\ud83d[\udc66\udc67]|\ud83d\udc68\u200d\u2764\ufe0f\u200d\ud83d\udc68|\ud83d\udc68\u200d\ud83d\udc66\u200d\ud83d\udc66|\ud83d\udc68\u200d\ud83d\udc67\u200d\ud83d[\udc66\udc67]|\ud83d\udc68\u200d\ud83d\udc68\u200d\ud83d[\udc66\udc67]|\ud83d\udc68\u200d\ud83d\udc69\u200d\ud83d[\udc66\udc67]|\ud83d\udc69\u200d\u2764\ufe0f\u200d\ud83d[\udc68\udc69]|\ud83d\udc69\u200d\ud83d\udc66\u200d\ud83d\udc66|\ud83d\udc69\u200d\ud83d\udc67\u200d\ud83d[\udc66\udc67]|\ud83d\udc69\u200d\ud83d\udc69\u200d\ud83d[\udc66\udc67]|\ud83c\udff3\ufe0f\u200d\u26a7\ufe0f|\ud83c\udff3\ufe0f\u200d\ud83c\udf08|\ud83c\udff4\u200d\u2620\ufe0f|\ud83d\udc15\u200d\ud83e\uddba|\ud83d\udc3b\u200d\u2744\ufe0f|\ud83d\udc41\u200d\ud83d\udde8|\ud83d\udc68\u200d\ud83d[\udc66\udc67]|\ud83d\udc69\u200d\ud83d[\udc66\udc67]|\ud83d\udc6f\u200d\u2640\ufe0f|\ud83d\udc6f\u200d\u2642\ufe0f|\ud83e\udd3c\u200d\u2640\ufe0f|\ud83e\udd3c\u200d\u2642\ufe0f|\ud83e\uddde\u200d\u2640\ufe0f|\ud83e\uddde\u200d\u2642\ufe0f|\ud83e\udddf\u200d\u2640\ufe0f|\ud83e\udddf\u200d\u2642\ufe0f|\ud83d\udc08\u200d\u2b1b)|[#*0-9]\ufe0f?\u20e3|(?:[©®\u2122\u265f]\ufe0f)|(?:\ud83c[\udc04\udd70\udd71\udd7e\udd7f\ude02\ude1a\ude2f\ude37\udf21\udf24-\udf2c\udf36\udf7d\udf96\udf97\udf99-\udf9b\udf9e\udf9f\udfcd\udfce\udfd4-\udfdf\udff3\udff5\udff7]|\ud83d[\udc3f\udc41\udcfd\udd49\udd4a\udd6f\udd70\udd73\udd76-\udd79\udd87\udd8a-\udd8d\udda5\udda8\uddb1\uddb2\uddbc\uddc2-\uddc4\uddd1-\uddd3\udddc-\uddde\udde1\udde3\udde8\uddef\uddf3\uddfa\udecb\udecd-\udecf\udee0-\udee5\udee9\udef0\udef3]|[\u203c\u2049\u2139\u2194-\u2199\u21a9\u21aa\u231a\u231b\u2328\u23cf\u23ed-\u23ef\u23f1\u23f2\u23f8-\u23fa\u24c2\u25aa\u25ab\u25b6\u25c0\u25fb-\u25fe\u2600-\u2604\u260e\u2611\u2614\u2615\u2618\u2620\u2622\u2623\u2626\u262a\u262e\u262f\u2638-\u263a\u2640\u2642\u2648-\u2653\u2660\u2663\u2665\u2666\u2668\u267b\u267f\u2692-\u2697\u2699\u269b\u269c\u26a0\u26a1\u26a7\u26aa\u26ab\u26b0\u26b1\u26bd\u26be\u26c4\u26c5\u26c8\u26cf\u26d1\u26d3\u26d4\u26e9\u26ea\u26f0-\u26f5\u26f8\u26fa\u26fd\u2702\u2708\u2709\u270f\u2712\u2714\u2716\u271d\u2721\u2733\u2734\u2744\u2747\u2757\u2763\u2764\u27a1\u2934\u2935\u2b05-\u2b07\u2b1b\u2b1c\u2b50\u2b55\u3030\u303d\u3297\u3299])(?:\ufe0f|(?!\ufe0e))|(?:(?:\ud83c[\udfcb\udfcc]|\ud83d[\udd74\udd75\udd90]|[\u261d\u26f7\u26f9\u270c\u270d])(?:\ufe0f|(?!\ufe0e))|(?:\ud83c[\udf85\udfc2-\udfc4\udfc7\udfca]|\ud83d[\udc42\udc43\udc46-\udc50\udc66-\udc69\udc6e\udc70-\udc78\udc7c\udc81-\udc83\udc85-\udc87\udcaa\udd7a\udd95\udd96\ude45-\ude47\ude4b-\ude4f\udea3\udeb4-\udeb6\udec0\udecc]|\ud83e[\udd0c\udd0f\udd18-\udd1c\udd1e\udd1f\udd26\udd30-\udd39\udd3d\udd3e\udd77\uddb5\uddb6\uddb8\uddb9\uddbb\uddcd-\uddcf\uddd1-\udddd]|[\u270a\u270b]))(?:\ud83c[\udffb-\udfff])?|(?:\ud83c\udff4\udb40\udc67\udb40\udc62\udb40\udc65\udb40\udc6e\udb40\udc67\udb40\udc7f|\ud83c\udff4\udb40\udc67\udb40\udc62\udb40\udc73\udb40\udc63\udb40\udc74\udb40\udc7f|\ud83c\udff4\udb40\udc67\udb40\udc62\udb40\udc77\udb40\udc6c\udb40\udc73\udb40\udc7f|\ud83c\udde6\ud83c[\udde8-\uddec\uddee\uddf1\uddf2\uddf4\uddf6-\uddfa\uddfc\uddfd\uddff]|\ud83c\udde7\ud83c[\udde6\udde7\udde9-\uddef\uddf1-\uddf4\uddf6-\uddf9\uddfb\uddfc\uddfe\uddff]|\ud83c\udde8\ud83c[\udde6\udde8\udde9\uddeb-\uddee\uddf0-\uddf5\uddf7\uddfa-\uddff]|\ud83c\udde9\ud83c[\uddea\uddec\uddef\uddf0\uddf2\uddf4\uddff]|\ud83c\uddea\ud83c[\udde6\udde8\uddea\uddec\udded\uddf7-\uddfa]|\ud83c\uddeb\ud83c[\uddee-\uddf0\uddf2\uddf4\uddf7]|\ud83c\uddec\ud83c[\udde6\udde7\udde9-\uddee\uddf1-\uddf3\uddf5-\uddfa\uddfc\uddfe]|\ud83c\udded\ud83c[\uddf0\uddf2\uddf3\uddf7\uddf9\uddfa]|\ud83c\uddee\ud83c[\udde8-\uddea\uddf1-\uddf4\uddf6-\uddf9]|\ud83c\uddef\ud83c[\uddea\uddf2\uddf4\uddf5]|\ud83c\uddf0\ud83c[\uddea\uddec-\uddee\uddf2\uddf3\uddf5\uddf7\uddfc\uddfe\uddff]|\ud83c\uddf1\ud83c[\udde6-\udde8\uddee\uddf0\uddf7-\uddfb\uddfe]|\ud83c\uddf2\ud83c[\udde6\udde8-\udded\uddf0-\uddff]|\ud83c\uddf3\ud83c[\udde6\udde8\uddea-\uddec\uddee\uddf1\uddf4\uddf5\uddf7\uddfa\uddff]|\ud83c\uddf4\ud83c\uddf2|\ud83c\uddf5\ud83c[\udde6\uddea-\udded\uddf0-\uddf3\uddf7-\uddf9\uddfc\uddfe]|\ud83c\uddf6\ud83c\udde6|\ud83c\uddf7\ud83c[\uddea\uddf4\uddf8\uddfa\uddfc]|\ud83c\uddf8\ud83c[\udde6-\uddea\uddec-\uddf4\uddf7-\uddf9\uddfb\uddfd-\uddff]|\ud83c\uddf9\ud83c[\udde6\udde8\udde9\uddeb-\udded\uddef-\uddf4\uddf7\uddf9\uddfb\uddfc\uddff]|\ud83c\uddfa\ud83c[\udde6\uddec\uddf2\uddf3\uddf8\uddfe\uddff]|\ud83c\uddfb\ud83c[\udde6\udde8\uddea\uddec\uddee\uddf3\uddfa]|\ud83c\uddfc\ud83c[\uddeb\uddf8]|\ud83c\uddfd\ud83c\uddf0|\ud83c\uddfe\ud83c[\uddea\uddf9]|\ud83c\uddff\ud83c[\udde6\uddf2\uddfc]|\ud83c[\udccf\udd8e\udd91-\udd9a\udde6-\uddff\ude01\ude32-\ude36\ude38-\ude3a\ude50\ude51\udf00-\udf20\udf2d-\udf35\udf37-\udf7c\udf7e-\udf84\udf86-\udf93\udfa0-\udfc1\udfc5\udfc6\udfc8\udfc9\udfcf-\udfd3\udfe0-\udff0\udff4\udff8-\udfff]|\ud83d[\udc00-\udc3e\udc40\udc44\udc45\udc51-\udc65\udc6a\udc6f\udc79-\udc7b\udc7d-\udc80\udc84\udc88-\udca9\udcab-\udcfc\udcff-\udd3d\udd4b-\udd4e\udd50-\udd67\udda4\uddfb-\ude44\ude48-\ude4a\ude80-\udea2\udea4-\udeb3\udeb7-\udebf\udec1-\udec5\uded0-\uded2\uded5-\uded7\udeeb\udeec\udef4-\udefc\udfe0-\udfeb]|\ud83e[\udd0d\udd0e\udd10-\udd17\udd1d\udd20-\udd25\udd27-\udd2f\udd3a\udd3c\udd3f-\udd45\udd47-\udd76\udd78\udd7a-\uddb4\uddb7\uddba\uddbc-\uddcb\uddd0\uddde-\uddff\ude70-\ude74\ude78-\ude7a\ude80-\ude86\ude90-\udea8\udeb0-\udeb6\udec0-\udec2\uded0-\uded6]|[\u23e9-\u23ec\u23f0\u23f3\u267e\u26ce\u2705\u2728\u274c\u274e\u2753-\u2755\u2795-\u2797\u27b0\u27bf\ue50a])|\ufe0f/g,UFE0Fg=/\uFE0F/g,U200D=String.fromCharCode(8205),rescaper=/[&<>'"]/g,shouldntBeParsed=/^(?:iframe|noframes|noscript|script|select|style|textarea)$/,fromCharCode=String.fromCharCode;return twemoji;function createText(text,clean){return document.createTextNode(clean?text.replace(UFE0Fg,""):text)}function escapeHTML(s){return s.replace(rescaper,replacer)}function defaultImageSrcGenerator(icon,options){return"".concat(options.base,options.size,"/",icon,options.ext)}function grabAllTextNodes(node,allText){var childNodes=node.childNodes,length=childNodes.length,subnode,nodeType;while(length--){subnode=childNodes[length];nodeType=subnode.nodeType;if(nodeType===3){allText.push(subnode)}else if(nodeType===1&&!("ownerSVGElement"in subnode)&&!shouldntBeParsed.test(subnode.nodeName.toLowerCase())){grabAllTextNodes(subnode,allText)}}return allText}function grabTheRightIcon(rawText){return toCodePoint(rawText.indexOf(U200D)<0?rawText.replace(UFE0Fg,""):rawText)}function parseNode(node,options){var allText=grabAllTextNodes(node,[]),length=allText.length,attrib,attrname,modified,fragment,subnode,text,match,i,index,img,rawText,iconId,src;while(length--){modified=false;fragment=document.createDocumentFragment();subnode=allText[length];text=subnode.nodeValue;i=0;while(match=re.exec(text)){index=match.index;if(index!==i){fragment.appendChild(createText(text.slice(i,index),true))}rawText=match[0];iconId=grabTheRightIcon(rawText);i=index+rawText.length;src=options.callback(iconId,options);if(iconId&&src){img=new Image;img.onerror=options.onerror;img.setAttribute("draggable","false");attrib=options.attributes(rawText,iconId);for(attrname in attrib){if(attrib.hasOwnProperty(attrname)&&attrname.indexOf("on")!==0&&!img.hasAttribute(attrname)){img.setAttribute(attrname,attrib[attrname])}}img.className=options.className;img.alt=rawText;img.src=src;modified=true;fragment.appendChild(img)}if(!img)fragment.appendChild(createText(rawText,false));img=null}if(modified){if(i<text.length){fragment.appendChild(createText(text.slice(i),true))}subnode.parentNode.replaceChild(fragment,subnode)}}return node}function parseString(str,options){return replace(str,function(rawText){var ret=rawText,iconId=grabTheRightIcon(rawText),src=options.callback(iconId,options),attrib,attrname;if(iconId&&src){ret="<img ".concat('class="',options.className,'" ','draggable="false" ','alt="',rawText,'"',' src="',src,'"');attrib=options.attributes(rawText,iconId);for(attrname in attrib){if(attrib.hasOwnProperty(attrname)&&attrname.indexOf("on")!==0&&ret.indexOf(" "+attrname+"=")===-1){ret=ret.concat(" ",attrname,'="',escapeHTML(attrib[attrname]),'"')}}ret=ret.concat("/>")}return ret})}function replacer(m){return escaper[m]}function returnNull(){return null}function toSizeSquaredAsset(value){return typeof value==="number"?value+"x"+value:value}function fromCodePoint(codepoint){var code=typeof codepoint==="string"?parseInt(codepoint,16):codepoint;if(code<65536){return fromCharCode(code)}code-=65536;return fromCharCode(55296+(code>>10),56320+(code&1023))}function parse(what,how){if(!how||typeof how==="function"){how={callback:how}}return(typeof what==="string"?parseString:parseNode)(what,{callback:how.callback||defaultImageSrcGenerator,attributes:typeof how.attributes==="function"?how.attributes:returnNull,base:typeof how.base==="string"?how.base:twemoji.base,ext:how.ext||twemoji.ext,size:how.folder||toSizeSquaredAsset(how.size||twemoji.size),className:how.className||twemoji.className,onerror:how.onerror||twemoji.onerror})}function replace(text,callback){return String(text).replace(re,callback)}function test(text){re.lastIndex=0;var result=re.test(text);re.lastIndex=0;return result}function toCodePoint(unicodeSurrogates,sep){var r=[],c=0,p=0,i=0;while(i<unicodeSurrogates.length){c=unicodeSurrogates.charCodeAt(i++);if(p){r.push((65536+(p-55296<<10)+(c-56320)).toString(16));p=0}else if(55296<=c&&c<=56319){p=c}else{r.push(c.toString(16))}}return r.join(sep||"-")}}();

(function() {
    'use strict';
    function getTweets(){
        try{
            let limitHeight = 10000
            let tweets = []
            //推文主元素
            var mainelem = document.querySelector('section[aria-labelledby].css-1dbjc4n')
            if(!mainelem){
                return [false,"推文不存在"]
            }
            let elems = mainelem.querySelectorAll('article')
            function getoffsetTop(elem,relem){
                let resH = 0
                let nowelem = elem
                while(nowelem != relem && nowelem != null){
                    resH = resH + nowelem.offsetTop
                    nowelem = nowelem.parentNode
                }
                if(nowelem == null)return 0;//不存在匹配的上级元素时返回0
                return resH
            }
            for (var i = 0;i<elems.length;i++) {
                let elart = elems[i]
                if(elart){
                    try {
                        //let uie = elart.querySelector('div[data-testid="tweet"]>div')
                        let uid = elart.querySelector('div.r-18kxxzh>div.r-18kxxzh')
                        //头像
                        let headimg = uid.querySelector('img').getAttribute('src')

                        //用户ID
                        //let userid = uie.nextSibling.innerText
                        let userid = uid.querySelector('a').getAttribute('href').slice(1)
                        //昵称
                        //uie = uie.nextSibling.querySelector('a>div>div')
                        //let nick = uie.innerText
                        let nick = elart.querySelector('div.r-vw2c0b').innerText
                        //投票
                        //投票中 定位 .r-p1n3y5.r-aj3cln
                        //投票完成 定位 .r-1g7fiml
                        let elemvotes = elart.querySelectorAll('div.r-p1n3y5.r-aj3cln')
                        let elemvoteends = elart.querySelectorAll('div.r-1g7fiml')
                        let tweetvotes = []
                        for(let j = 0;j<elemvotes.length;j++){
                            tweetvotes.push({
                                elem:elemvotes[j],
                                elemy:getoffsetTop(elemvotes[j],elart),//文字内容相对于推文的高度
                                elemh:elemvotes[j].offsetHeight,//文字内容相对于推文的高度
                                text:elemvotes[j].innerText,
                            })
                        }
                        for(let j = 0;j<elemvoteends.length;j++){
                            tweetvotes.push({
                                elem:elemvoteends[j],
                                elemy:getoffsetTop(elemvoteends[j],elart),//文字内容相对于推文的高度
                                elemh:elemvoteends[j].offsetHeight,//文字内容相对于推文的高度
                                text:elemvoteends[j].innerText,
                            })
                        }
                        //外链及图片
                        let elemitems = elart.querySelectorAll('div.r-9x6qib')
                        let tweetitems = []
                        for(let j = 0;j<elemitems.length;j++){
                            let elemsrcs = elemitems[j].querySelectorAll('[src]')
                            let srcs = []
                            for(let j = 0;j<elemsrcs.length;j++){
                                let tag = elemsrcs[j].tagName
                                let isrc = ''
                                if(tag == 'VIDEO'){
                                    isrc = elemsrcs[j].poster
                                }
                                if(tag == 'IMG'){
                                    isrc = elemsrcs[j].src
                                }
                                srcs.push({
                                    elem:elemsrcs[j],
                                    type:elemsrcs[j].tagName,
                                    src:elemsrcs[j].src,
                                    imgsrc:isrc
                                })
                            }
                            tweetitems.push({
                                elem:elemitems[j],
                                elemy:getoffsetTop(elemitems[j],elart),//文字内容相对于推文的高度
                                elemh:elemitems[j].offsetHeight,//文字内容相对于推文的高度
                                text:elemitems[j].innerText,
                                srcs:srcs
                            })
                        }
                        //推文内容表
                        let elemtexts = elart.querySelectorAll('div.r-bnwqim')
                        let tweettexts = []
                        let tweettext = ""
                        for(let j = 0;j<elemtexts.length;j++){
                            tweettext += elemtexts[j].innerText + "\u000A"
                            tweettexts.push({
                                elem:elemtexts[j],
                                elemy:getoffsetTop(elemtexts[j],elart),//文字内容相对于推文的高度
                                elemh:elemtexts[j].offsetHeight,//文字内容相对于推文的高度
                                text:elemtexts[j].innerText
                            })
                        }
                        let time = ''
                        let t = elart.querySelector('div.r-vpgt9t')
                        if(t){
                            time = t.innerText
                        }
                        //推文相对高度
                        let elemy = getoffsetTop(elems[i],mainelem)
                        //推文宽度
                        let elemh = elems[i].offsetHeight
                        //隐藏翻译蓝链
                        //let elemet = elart.querySelector('[class="css-18t94o4 css-901oao r-1n1174f r-6koalj r-1w6e6rj r-1qd0xha r-n6v787 r-16dba41 r-1sf4r6n r-1g94qm0 r-bcqeeo r-qvutc0"]')
                        //if(elemet)elemet.style.visibility="hidden"
                        tweets.push({
                            code:0,
                            elem:elems[i],//主体元素
                            elemy:elemy,
                            elemh:elemh,
                            headimg:headimg,
                            time:time,
                            nick:nick,
                            userid:userid,
                            tweetvotes:tweetvotes,
                            tweetitems:tweetitems,
                            tweettexts:tweettexts,
                            tweettext:tweettext
                        })
                        //只处理 limitHeight 像素以内的数据
                        if( elemy > limitHeight)break;
                    } catch (e) {
                        //记录错误
                        tweets.push({
                            code:1,
                            elem:elems[i],
                            exp:e.message
                        })
                    }
                }
            }
            function mediaLoadComplete(mainelem){
                try{
                    let elems = mainelem.querySelectorAll('img')
                    for (var i = 0;i<elems.length;i++) {
                        if(!elems[i].complete){
                            return false
                        }
                    }
                    return true
                }catch(e){
                    return true
                }
            }
            function waitLoad(mainelem){
                if(mediaLoadComplete(mainelem)){
                    let node = document.createElement('wait_img')
                    document.body.appendChild(node)
                }else{
                    setTimeout(function(){
                        mediaLoadComplete(mainelem);
                    }, 100);
                }
            }
            setTimeout(function(){
                waitLoad(mainelem);
            }, 100);
            return tweets
        }catch (e) {
            return e.message
        }
    }
    function tweetTrans(){
        let translist={
            type_html:'<p dir="auto" style="color:#1DA1F2;font-size:0.7em;font-weight: 600;">翻译自日文</p>',
            text:{
                '1':["复杂才关😳😳😳\n今天！！！！！咱要来玩这个游戏了！！！！！！！！！\n19点！！！19点开始！！！！（开心地手舞足蹈）" + JSON.parse('"\\u2728Say!Fanfare!\\u2728\\r\\n\\u2728\\u3297100\\u4e07\\u64ad\\u653e\\u3297\\u2728\\r\\n\\u771f\\u7684\\u5f88\\u611f\\u8c22\\u5927\\u5bb6!!!\\r\\nHamu\\u6851\\uff08\\u4f5c\\u8bcd\\u4f5c\\u66f2\\uff09\\uff01iimo\\u6851\\uff08\\u52a8\\u753b\\uff09\\uff01\\u8fd8\\u6709\\u5927\\u5bb6\\u2757\\u2757\\r\\n\\u662f100\\u4e07\\u5440\\u2014\\u2014\\u592a\\u68d2\\u5566\\u2014\\u2014\\u2757\\u2757\\r\\n\\r\\nSay!Fanfare!/\\u767d\\u4e0a\\u30d5\\u30d6\\u30ad\\u3010\\u539f\\u521b\\u66f2\\u3011\\r\\nhttps://youtu.be/pFgUluV_00s\\r\\n#\\u30d5\\u30d6\\u30ad"'),"次节点翻译"],//推文只处理前两个值(主节点，次节点-转发的推文)
                '2':["二层翻译","二层次节点"],
                'main':["主翻译","主翻译节点"],//末端的主推文，置入参数前处理(先搜索对应下标再搜索main-main用于无下标置入)
            }
        }
        translist.text['1'] = ["翻译-えへへ(*´꒳`*)ﾟ*.・♡\n\
みんなのおかげで疲れがとれた(๑╹ᆺ╹)闪片\n\
\n\
【\\#233】\
午後もがんばる୧(๑•̀ㅁ•́๑)૭✧"]
        var name=prompt("请输入模版值","翻译自日文"); // 弹出input框
        if(name != ''){
            if(name.slice(0,10) == 'data:image')
                translist.type_html = "<div style=\"padding:5px;margin:0px\"><img height=\"38\" src=\""+name+"\"></div>"
            else if(name.slice(0,1) == '<'){
                translist.type_html = name
            }
            else{
                translist.type_html = '<p dir="auto" style="color:#1DA1F2;font-size:0.7em;font-weight: 600;">' + name +'</p>'
            }
        }
        //多重回复终止定位
        try {
            function attributesCallback(icon, variant) {
                return {
                    title: 'Emoji: ' + icon + variant,
                    style: 'height: 1em;width: 1em;margin: 0.05em 0.1em;vertical-align: -0.1em;'
                };
            }
            function textparse(text){
                text = text.replace(/(\\#)/gi,'\\&jh; ')
                text = text.replace(/(\S*)(#\S+)/gi,'$1<a style="color:#1DA1F2;">$2</a>')
                text = text.replace(/((https?|ftp|file):\/\/[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|])/g,'<a style="color:#1DA1F2;">$1</a>')
                text = text.replace(/(\\&jh; )/gi,'#')
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
            var mainelem = document.querySelector('section[aria-labelledby].css-1dbjc4n')
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
                if(elart){
                    elart = elart.cloneNode(true)
                    shotelem.append(elart);
                    let trans = []
                    let elemtexts = elart.querySelectorAll('div.r-bnwqim')
                    for(var j = 0;j<elemtexts.length;j++){
                        trans.push({
                            elem:elemtexts[j],
                            text:elemtexts[j].innerText
                        })
                    }
                    tweets.push(trans)
                    //检测推文是否结束
                    //转推喜欢
                    let rtlk = elart.querySelector('div.r-9qu9m4')
                    if(rtlk){
                        //跳出
                        rtlk.remove()
                        break;
                    }
                    //时间
                    let t = elart.querySelector('div.r-vpgt9t')
                    if(t){
                        //跳出
                        break;
                    }
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
                    if(tweets[i][0]){
                        if(!tran_text){
                            tran_text = translist.text['main'] //翻译节点不存在时切换翻译为主翻译
                        }
                        if(tran_text != ''){
                            tweets[i][0].elem.append(node_type)//添加推文标识
                        }
                    }

                }else{
                    //非末推文存在翻译时清空节点
                    if(tran_text && tweets[i][0]){
                        tweets[i][0].elem.innerHTML = "" //存在翻译则清空节点
                    }
                }
                if(tran_text){
                    if(tran_text[0] && tweets[i][0]){
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
        function mediaLoadComplete(mainelem){
            try{
                let elems = mainelem.querySelectorAll('img')
                for (var i = 0;i<elems.length;i++) {
                    if(!elems[i].complete){
                        return false
                    }
                }
                return true
            }catch(e){
                return true
            }
        }
        function waitLoad(mainelem){
            if(mediaLoadComplete(mainelem)){
                let node = document.createElement('wait_img')
                document.body.appendChild(node)
            }else{
                setTimeout(function(){
                    mediaLoadComplete(mainelem);
                }, 100);
            }
        }
        setTimeout(function(){
            waitLoad(mainelem);
        }, 100);
        return [true,tweets,lastelem]
    }
    var res
    function ket(){
        //console.log(getTweets())
        res = tweetTrans()
        console.log("输出:")
        console.log(res)
    }
    function ket1(){
        console.log(getTweets())
    }
    setTimeout(function(){
        let html =  '<div id="script-button-test" class="right-action-ctnr live-skin-normal-a-text pointer dp-i-block btn"><i class="icon-font icon-report v-middle"></i><span class="action-text v-middle dp-i-block">置入推特翻译</span></div>'
        let html1 =  '<div id="script-button-test1" class="right-action-ctnr live-skin-normal-a-text pointer dp-i-block btn"><i class="icon-font icon-report v-middle"></i><span class="action-text v-middle dp-i-block">获取推文列表</span></div>'
        $('a[href="/login"]').parent().append(html)
        $('a[href="/login"]').parent().append(html1)
        $('a[href="/compose/tweet"]').parent().append(html)
        $('a[href="/compose/tweet"]').parent().append(html1)
        $('#script-button-test').click(ket)
        $('#script-button-test1').click(ket1)
    }, 4000);
    // Your code here...
})();