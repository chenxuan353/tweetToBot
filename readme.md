# **可提供一对多转推服务的bot后端**

### 简介

本仓库主要依赖于模块[nonebot](https://github.com/nonebot/nonebot)和[tweepy](https://github.com/tweepy/tweepy) 与CoolQ的通信依赖于CQHttp

特别鸣谢[richardchien](https://github.com/richardchien)对上述封装项目的贡献

**本项目目前仅支持 Python 3.7 及 CQHTTP 插件 v4.8+**

目前仍然处于测试状态，功能大部分已经完善，可以对bot深度定制化

**预期加入功能：烤推功能**

支持多个bot远程连接此后端，已经对可能的冲突进行了处理

目前推特的推送流异常后将尝试5次重启(重启前等待十秒)，五次重启均失败时需要手动重启。

对监听的修改将立刻保存至文件中

已经保证了每个群就算是多个bot同时存在也只会添加一个相同监听对象的推送

现在配置文件读取后会以JSON的形式输出到日志中，如果丢失了配置文件，可以凭日志回档。

并且在退群时会自动卸载监听(需要bot在线)，配置异常时可以手动清除检测

※ 接收推送的接口已经二次封装，只要事件符合推送事件处理器的数据格式，就可以正常推送。

※ 为了保证推送的正常运行使用了多线程

### 部署

#### 部署CoolQ

安装CoolQ并按照帖子内文档部署

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



#### 启动插件

下载[CQHttp](https://github.com/richardchien/coolq-http-api/releases)的[CPK依赖包](https://github.com/richardchien/coolq-http-api/releases/download/v4.15.0/io.github.richardchien.coolqhttpapi.cpk)并安装(放到依赖包位置并初次启动后配置端口)

**Docker请直接使用wget命令操作**

```shell
wget https://github.com/richardchien/coolq-http-api/releases/download/v4.15.0/io.github.richardchien.coolqhttpapi.cpk
```

*如在Docker中部署请在此处启动插件服务*

#### 启动服务

安装依赖

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

## 推特监听目前支持的功能/命令

### 使用说明

1. **调用命令**实现功能需要以`<命令> <参数表>`的形式调用，具体格式已在各命令中说明。
2. 命令和参数表，以及参数表各参数之间需要以**一个半角空格**作为空格。**空参数亦不能省略空格**
3. 命令列表中提到的`<推特用户ID>`是指由英文数字组成的用户名（即在@时会显示的文本）
4. **!注意!：如果监听列表里没有监听对象则全局设置会被重置**

### 命令列表

#### 帮助 `about`

- 命令格式：`about`

- 同义格式：`帮助`、`关于`、`help`

- 所需权限：无限制

- 功能说明：返回转推bot的关于消息

#### 恢复监听 `runTweetListener`

- 命令格式：`runTweetListener`

- 同义格式：`启动监听`

- 所需权限：超级管理员, @bot

- 功能说明：用于推特流断连后尝试重启监听

#### 移除全部监听 `delall`

- 命令格式：`delall`

- 同义格式：`这里单推bot`

- 所需权限：超级管理员/群主, @bot

- 功能：移除当前私聊/群的所有监听

#### 查看监听列表 `getpushlist`

- 命令格式：`getpushlist`

- 同义格式：`DD列表`

- 所需权限：超级管理员/群管理/群主/好友私聊

- 功能：获取当前私聊/群的监听列表

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
推特ID：$tweet_id_min，【$tweet_nick】发布了：\n$tweet_text
```

###### 	转推

```
推特ID：$tweet_id_min，【$tweet_nick】转了【$related_user_name】的推特：\n$tweet_text
```

###### 	转发并评论

```
推特ID：$tweet_id_min，【$tweet_nick】转发并评论了【$related_user_name】的推特：\n$tweet_text\n====================\n$related_tweet_text
```

###### 	回复与被提及

```
推特ID：$tweet_id_min，【$tweet_nick】回复了【$related_user_name】：\n$tweet_text
```

##### 模版支持的变量

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
>  $related_tweet_id_min 关联推特ID的压缩(被评论/被转发)
>
> $related_tweet_text 关联推特内容(被转发或被转发并评论时存在)

### 更改监听对象属性 setAttr

- 命令格式：`setAttr <监听用户UID> <属性> <值>`

- 同义格式：`对象设置`

- 所需权限：超级管理员/群管理/群主/好友私聊, @bot

- 功能说明：设置指定监听对象的属性

例：`setGroupAttr 997786053124616192 转推 关`

​		`setGroupAttr 997786053124616192 昵称 `

​		`setGroupAttr 997786053124616192 昵称 FBKwaring`

※ UID可以通过命令**getpushlist**查看，大部分属性与**setGroupAttr**命令相同

#### 特有的属性支持

**※ 属性名称，别名1，...，别名n**

> nick,昵称
>
> des,描述



### 删除推送对象 globalRemove

- 命令格式：`globalRemove 消息类型 Q号/群号`

- 同义格式：`全局移除`

- 所需权限：超级管理员/好友私聊, @bot

- 功能说明：移除某个人或某个群的所有监听，用于修复配置错误(退出群/删除好友时不在线)

#### 消息类型

> 私聊,好友,private
>
> 群聊,群,group

例：`globalRemove 群聊 123456`



### 查询推特用户信息 getuserinfo

- 命令格式：`getuserinfo <用户UID/用户ID>`

- 同义格式：`查询推特用户`

- 所需权限：超级管理员/好友私聊, @bot

- 功能说明：查询某个用户的信息，显示的头像将会更新(新增与减少监听不会重新下载头像)



### 全局移除 globalRemove

- 命令格式：`globalRemove <private/私聊/group/群聊> <QQ号/群号>`

- 同义格式：`全局移除`

- 所需权限：超级管理员, @bot

- 功能说明：移除某个人或某个群的所有监测，用于修复配置错误(退出群/删除好友时不在线)