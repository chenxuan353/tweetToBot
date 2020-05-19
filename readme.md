# 可提供一对多转推服务的bot后端

## 简介

本仓库主要依赖于模块[nonebot](https://github.com/nonebot/nonebot)和[tweepy](https://github.com/tweepy/tweepy)，与CoolQ的通信依赖于CQHTTP；

特别鸣谢[richardchien](https://github.com/richardchien)对上述封装项目的贡献。

**本项目目前仅支持 Python 3.7 及 CQHTTP 插件 v4.8+**

目前仍然处于测试状态，功能大部分已经完善，可以对bot深度定制化。

**目前测试中：烤推功能**

支持多个bot远程连接此后端，已经对可能的冲突进行了处理。

目前推特的推送流异常后将尝试5次重启(重启前等待十秒)，五次重启均失败时需要手动重启。

对监听的修改将立刻保存至文件中。

已经保证了每个群就算是多个bot同时存在也只会添加一个相同监听对象的推送。

现在配置文件读取后会以JSON的形式输出到日志中，如果丢失了配置文件，可以凭日志回档。

并且在退群时会自动卸载监听(需要bot在线)，配置异常时可以手动清除检测。

※ 接收推送的接口已经二次封装，只要事件符合推送事件处理器的数据格式，就可以正常推送。

※ 为了保证推送的正常运行使用了多线程。

## 部署

### 部署CoolQ

安装CoolQ并按照帖子内文档部署。

[Air](https://cqp.cc/t/23253) [Pro](https://cqp.cc/t/14901) [Docker](https://cqp.cc/t/34558)

- Docker中部署Air

  ```shell
  mkdir coolq-data
  docker run --name=coolq -d -p <CPDI>:9000 -v /root/coolq-data:/home/user/coolq -e VNC_PASSWD=<CP> -e COOLQ_ACCOUNT=<QQ> coolq/wine-coolq
  ```

  

- Docker中部署Pro

  ```shell
  mkdir coolq
  docker run --name=coolq -d -p <Corresponding Port of Docker Image>:9000 -v `pwd`/coolq:/home/user/coolq -e COOLQ_ACCOUNT=<QQ ID> -e COOLQ_URL=http://dlsec.cqp.me/cqp-full -e VNC_PASSWD=<Console Password> coolq/wine-coolq
  ```



### 启动插件

下载[CQHttp](https://github.com/richardchien/coolq-http-api/releases)的[CPK依赖包](https://github.com/richardchien/coolq-http-api/releases/download/v4.15.0/io.github.richardchien.coolqhttpapi.cpk)并安装(放到依赖包位置并初次启动后配置端口)

**Docker请直接使用wget命令操作**

```shell
wget https://github.com/richardchien/coolq-http-api/releases/download/v4.15.0/io.github.richardchien.coolqhttpapi.cpk
```

*如在Docker中部署请在此处启动插件服务*

### 启动服务

#### 安装依赖

```shell
pip install nonebot[scheduler]
```

```shell
pip install tweepy
```

将config_example.py改名为config.py并填写内部的配置信息

```shell
mv config_example.py config.py
```

```shell
vi config.py
```

然后就可以用start.py启动项目了

```python
python start.py
```

#### 启动插件

在Docker指定的端口通过HTTP访问服务器，在浏览器中键入：

```shell
服务器IP:指定端口
```

访问NoVNC控制台。

输入密码后可进入Docker内置的Wine环境，通过可视化方式操作CoolQ客户端，

请登录后在插件管理中打开CQHTTP插件(请确保配置环节中CQHTTP已正确安装)。

#### 配置本地端口

本BOT采用WebSocket进行传输，故请在CoolQ根目录中打开/data/app/richardchen.../config进行服务器配置，并打开WS传输。

具体操作请参考CQHTTP文档中的[说明](https://cqhttp.cc/docs/4.15/#/Configuration)。

## 本BOT推送命令使用说明

1. **调用命令**实现功能需要以`<命令标识符><命令> <参数表>`的形式调用，具体格式已在各命令中说明。

   - 默认标识符为`!`或`！`，故在调用时请添加命令标识符，例如使用帮助命令时，请在聊天室(群/私聊)中键入：

     ```
     !about
     ```

     而非仅发送`about`。

   - 关于权限，部分命令由于涉及重要推送设置或推送大量信息。为了保护BOT正常运行以及群内使用体验，故操作需要管理权限(超级管理员/群主/管理员)进行操作才会进行响应。

   - 在权限中有`@bot`字段的，群聊消息需要在添加标识符的同时@所使用的的BOT账号，如：

     ```
     @<BOT账号> !getuserinfo shirakamifubuki
     ```

2. 命令和参数表，以及参数表各参数之间需要以**一个半角空格**作为空格，**空参数亦不能省略空格**。

   - 同义格式可以替换`<命令>`使用，功能完全相同(通常提供中文支持或缩写)

3. 参数注释

   - 推文推送命令列表中提到的`<推特用户ID>`是指由英文数字组成的用户名（即在@时会显示的文本）。

   - 烤推命令列表中提到的`<推文ID>`为推文`status`字段后19位(或以上)10进制数码，`<压缩推文ID>`为推文推送时附带的字符串，可使用相关命令互相转换。

4. **!注意!：如果监听列表里没有监听对象则全局设置会被重置。**

## 命令列表

### BOT相关命令

#### 帮助 `about`

- 命令格式：`about`
- 同义格式：`帮助`、`关于`、`help`
- 所需权限：无限制
- 功能说明：返回转推bot的关于消息

#### 信息反馈 `feedback`

- 命令格式：`feedback <信息>`
- 同义格式：`Feedback`、`反馈`
- 所需权限：超级管理员/群管理/群主
- 功能说明：所发送的信息将会反馈到后台日志供开发者查看

### 推文推送命令

#### 启动监听 `runTweetListener`

- 命令格式：`runTweetListener`

- 同义格式：`启动监听`

- 所需权限：超级管理员, @bot

- 功能说明：用于推特流断连后尝试重启监听 如已启动则会警告

#### 移除全部监听 `delall`

- 命令格式：`delall`

- 同义格式：`这里单推bot`

- 所需权限：超级管理员/群主, @bot

- 功能：移除当前私聊/群的所有监听

#### 查看监听列表 `getpushlist`

- 命令格式：`getpushlist <页码-可选>`

- 同义格式：`DD列表`

- 所需权限：超级管理员/群管理/群主/好友私聊

- 功能：获取当前私聊/群的监听列表，页数默认为1。

![image-20200428114040218](https://raw.githubusercontent.com/chenxuan353/tweetToQQbot/master/readme/image-20200428114040218.png)

#### 获取用户信息 `getuserinfo`

- 命令格式：`getuserinfo <推特用户ID>`

- 同义格式：`查询推特用户 <推特用户ID>` 

- 所需权限：超级管理员/好友私聊/群管理/群主, @bot

- 功能：获取当前私聊/群的监听列表

例：``getuserinfo shiranuiflare``

![image-20200428113938381](https://raw.githubusercontent.com/chenxuan353/tweetToQQbot/master/readme/image-20200428113938381.png)

#### 添加监听对象 `addone`

- 命令格式：`addone <推特用户ID> <称呼> <描述>`

- 同义格式：`给俺D一个 <推特用户ID> <称呼> <描述>`

- 所需权限：超级管理员/好友私聊/群管理/群主, @bot

- 功能说明：添加一个用户到本群监听

- 使用例：`给俺D一个 shirakamifubuki 吹雪 我永远喜欢小狐狸`

  (不设置昵称)使用例：`给俺D一个 shirakamifubuki  我永远喜欢小狐狸`
  
  (完全无参数)使用例：`给俺D一个 shirakamifubuki`
  
  **※ 跨参数设置同样需要空格分割，完全不设置参数时可以不添加空格**

![image-20200428113806819](https://raw.githubusercontent.com/chenxuan353/tweetToQQbot/master/readme/image-20200428113806819.png)

#### 删除监听对象 `delone`

- 命令格式：`delone <推特用户ID>`

- 同义格式：`我不想D了`

- 所需权限：超级管理员/群管理/群主/好友私聊, @bot

- 功能说明：移除一个本群监听的用户



#### 显示BOT推送设置 getGroupSetting

- 命令格式：`getGroupSetting`

- 同义格式：`全局设置列表`

- 所需权限：超级管理员/群管理/群主/好友私聊, @bot

- 功能说明：显示当前私聊/群的全局推送设置



#### 显示推送设置 getSetting

- 命令格式：`getSetting <推特用户ID>`

- 同义格式：`对象设置列表`

- 所需权限：超级管理员/群管理/群主/好友私聊, @bot

- 功能说明：显示当前私聊/群的某个监听对象的推送设置



#### 设置推送属性 setGroupAttr

- 命令格式：`setGroupAttr <属性> <值>`

- 同义格式：`全局设置`

- 所需权限：超级管理员/群管理/群主/好友私聊, @bot

- 功能说明：移除一个本群监听的用户

例：setGroupAttr 转推 关

##### 支持的属性列表(大小写不敏感)

**※ 属性名称，别名1，...，别名n**

###### 	携带图片发送

> upimg，图片，img

#####     消息模版(参数为模版字符串)

> retweet_template,转推模版
>
> quoted_template,转推并评论模版
>
> reply_to_status_template,回复模版
>
> reply_to_user_template,被提及模版
>
> none_template,发推模版

#####     推特转发各类型开关

- 属性

> retweet,转推
>
> quoted,转推并评论
>
> reply_to_status,回复
>
> reply_to_user,被提及
>
> none,发推

- 值

> true,开,打开,开启,1
>
> false,关,关闭,0

#####     推特个人信息变动推送开关

###### 	属性

> change_id,ID改变
>
> change_name,名称改变
>
> change_description,描述改变
>
> change_headimgchange,头像改变

###### 	支持的值

> true,开,打开,开启,1
>
> false,关,关闭,0

#### 模版字符串说明

##### 默认模版

###### 	发推

```
推特ID：$tweet_id_min，【$tweet_nick】发布了：\n$tweet_text\n$media_img
```

###### 	转推

```
推特ID：$tweet_id_min，【$tweet_nick】转了【$related_user_name】的推特：\n$tweet_text\n$media_img
```

###### 	转发并评论

```
推特ID：$tweet_id_min，【$tweet_nick】转发并评论了【$related_user_name】的推特：\n$tweet_text\n====================\n$related_tweet_text\n$media_img
```

###### 	回复与被提及

```
推特ID：$tweet_id_min，【$tweet_nick】回复了【$related_user_name】：\n$tweet_text\n$media_img
```

###### 模版支持的变量

​	注：使用`\n`替代换行符，理论上直接换行也可以但是十分不推荐

> $tweet_id 推特ID
>
> $tweet_id_min 压缩推特id
>
> $tweet_nick 操作人昵称
>
> $tweet_user_id 操作人ID
>
> $tweet_text 发送推特的完整内容
>
> $related_user_id 关联用户ID
>
> $related_user_name 关联用户昵称-昵称-昵称查询不到时为ID(被评论/被转发/被提及)
>
> $related_tweet_id 关联推特ID(被评论/被转发)
>
> $related_tweet_id_min 关联推特ID的压缩(被评论/被转发)
>
> $related_tweet_text 关联推特内容(被转发或被转发并评论时存在)
>
> $media_img 推特携带的图片

#### 更改监听对象属性 setAttr

- 命令格式：`setAttr <监听用户UID> <属性> <值>`

- 同义格式：`对象设置`

- 所需权限：超级管理员/群管理/群主/好友私聊, @bot

- 功能说明：设置指定监听对象的属性

例：`setGroupAttr 997786053124616192 转推 关`

​		`setGroupAttr 997786053124616192 昵称 `

​		`setGroupAttr 997786053124616192 昵称 FBKwaring`

※ UID可以通过命令**getpushlist**查看，大部分属性与**setGroupAttr**命令相同

##### 特有的属性支持

**※ 属性名称，别名1，...，别名n**

> nick,昵称
>
> des,描述



#### 删除推送对象 globalRemove

- 命令格式：`globalRemove 消息类型 Q号/群号`

- 同义格式：`全局移除`

- 所需权限：超级管理员/好友私聊, @bot

- 功能说明：移除某个人或某个群的所有监听，用于修复配置错误(退出群/删除好友时不在线)

##### 消息类型

> 私聊,好友,private
>
> 群聊,群,group

例：`globalRemove 群聊 123456`



#### 查询推特用户信息 getuserinfo

- 命令格式：`getuserinfo <用户UID/用户ID>`

- 同义格式：`查询推特用户`

- 所需权限：超级管理员/好友私聊, @bot

- 功能说明：查询某个用户的信息，显示的头像将会更新(新增与减少监听不会重新下载头像)

  

#### 全局移除 globalRemove

- 命令格式：`globalRemove <private/私聊/group/群聊> <QQ号/群号>`
- 同义格式：`全局移除`
- 所需权限：超级管理员, @bot
- 功能说明：移除某个人或某个群的所有监测，用于修复配置错误(退出群/删除好友时不在线)

#### 压缩推特ID `entweetid`

- 命令格式：`entweetid <推文ID>`

- 同义格式：`推特ID压缩`、`压缩ID`

- 所需权限：无限制

- 功能说明：将推文ID压缩为缩写推文ID

#### 解压推特ID `detweetid`

- 命令格式：`detweetid <缩写推文ID>`

- 同义格式：`推特ID解压`、`解压ID`

- 所需权限：无限制

- 功能说明：将缩写推文ID解压为推文ID

### 推文翻译命令列表

#### 烤推授权 `transswitch`

- 命令格式：`globalRemove <private/私聊/group/群聊> <QQ号/群号>`

- 同义格式：`ts`、`烤推授权`

- 所需权限：群聊, 群主/超级管理员, @bot

- 功能说明：为群聊添加/移除烤推授权(开关功能)

#### 翻译推特 `trans`

- 命令格式：`trans <推文ID/缩写推文ID> <翻译文本>`

- 同义格式：`t`、`烤推`

- 所需权限：无限制

- 功能说明：为某条推文添加翻译，由BOT完成嵌字并返回。翻译文本支持多行，不支持转义字符(TODO: 对emoji的支持尚需完善)

#### 获取推特翻译列表 `translist`

- 命令格式：`translist <页数>`或 `translist`(translist默认值为1)

- 同义格式：`tl`、`烤推列表`

- 所需权限：无限制

- 功能说明：获取已翻译推特列表

#### 获取翻译文本 `gettrans`

- 命令格式：`gettrans <推文ID/缩写推文ID>`

- 同义格式：`gt`、`获取翻译`

- 所需权限：无限制

- 功能说明：获取某条推文的翻译文本

#### 获取烤推帮助 `transabout`

- 命令格式：`transabout`

- 同义格式：`ta`、`烤推帮助`

- 所需权限：无限制

- 功能说明：获取烤推流程相关命令帮助说明



### 