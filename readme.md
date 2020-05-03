# **可提供一对多转推服务的bot后端**

目前仍然处于测试状态

已经可用，对大部分异常进行了处理，现在基本不会宕机了

目前推特的推送流异常后将尝试5次重启(重启前等待十秒)，五次重启均失败时需要手动重启。

对监测的修改将立刻保存至文件中

已经保证了每个群就算是多个bot同时存在也只会添加一个相同监测对象的推送

并且在退群时会自动卸载监测(需要bot在线)，配置异常时可以手动清除检测

注：意味着不管是什么方式侦听到的更新，都可以进行推送。

*为了保证推送的正常运行使用了多线程

依赖的模块 nonebot,tweepy

部署：

pip安装 nonebot,tweepy

将config_example.py改名为config.py并填写内部的配置信息

然后就可以用start.py启动项目了

预期加入功能：socket广播推送功能，烤推功能

仅支持 Python 3.7+ 及 CQHTTP 插件 v4.8+。

*接收推送的接口已经二次封装，只要事件符合推送事件处理器的数据格式，就可以正常推送。

## 推特监测目前支持的命令：

注:命令前注意添加前缀，以及注意命令权限要求(@bot在私聊时不需要)

注:命令对空格要求严格，参数间必须只空一个空格，空参数的空格不能省略

！注意：如果监测列表里没有监测对象则全局设置会被重置

### runTweetListener

别名：启动监听

权限：超级管理员,@bot

功能：用于推特流断连后尝试重启监听

### delall

别名：这里单推bot

权限：超级管理员,@bot

功能：移除当前私聊/群的所有监测

### getpushlist

别名：DD列表

权限：无限制

功能：获取当前私聊/群的监测列表

![image-20200428114040218](https://raw.githubusercontent.com/chenxuan353/tweetToQQbot/master/readme/image-20200428114040218.png)

### getuserinfo 推特用户ID/用户名(非昵称)

别名：查询推特用户

权限：超级管理员,@bot

功能：获取当前私聊/群的监测列表

例：getuserinfo shiranuiflare

![image-20200428113938381](https://raw.githubusercontent.com/chenxuan353/tweetToQQbot/master/readme/image-20200428113938381.png)

### addone 推特用户ID/用户名(非昵称) 昵称 描述

别名：给俺D一个

权限：超级管理员,@bot

功能：添加一个用户到本群监测

例如：给俺D一个 shirakamifubuki 吹雪 我永远喜欢小狐狸

不需要设置昵称：给俺D一个 shirakamifubuki  我永远喜欢小狐狸

注意：不需要设置昵称的情况下空格不能省略

![image-20200428113806819](https://raw.githubusercontent.com/chenxuan353/tweetToQQbot/master/readme/image-20200428113806819.png)

### delone 推特用户ID/用户名(非昵称)

别名：我不想D了

权限：超级管理员,@bot

功能：移除一个本群监测的用户



### getGroupSetting

别名：全局设置列表

权限：无限制

功能：显示当前私聊/群的全局推送设置



### getSetting 推特用户ID

别名：对象设置列表

权限：无限制

功能：显示当前私聊/群的某个监测对象的推送设置



### setGroupAttr 属性 值

别名：全局设置

权限：超级管理员,@bot

功能：移除一个本群监测的用户

例：setGroupAttr 转推 关

#### 支持的属性列表(大小写不敏感)：

注：属性名称，别名1，...，别名n

##### 	携带图片发送

​	upimg，图片，img

#####     消息模版(参数为模版字符串)

​    retweet_template,转推模版

​    quoted_template,转推并评论模版

​    reply_to_status_template,回复模版

​    reply_to_user_template,被提及模版

​    none_template,发推模版

#####     推特转发各类型开关

###### 	属性

​    retweet,转推

​    quoted,转推并评论

​    reply_to_status,回复

​    reply_to_user,被提及

​    none,发推

###### 	支持的值

​	true,开,打开,开启,1

​	false,关,关闭,0

#####     推特个人信息变动推送开关

###### 	属性

​    change_id,ID改变

​    change_name,名称改变

​    change_description,描述改变

​    change_headimgchange,头像改变

###### 	支持的值

​	true,开,打开,开启,1

​	false,关,关闭,0

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

​	注：使用\n替代换行符，理论上直接换行也可以但是十分不推荐(

​      $tweet_id 推特ID

​      $tweet_id_min 压缩推特id

​      $tweet_nick 操作人昵称

​      $tweet_user_id 操作人ID

​      $tweet_text 发送推特的完整内容

​      $related_user_id 关联用户ID

​      $related_user_name 关联用户昵称-昵称-昵称查询不到时为ID(被评论/被转发/被提及)

​      $related_tweet_id 关联推特ID(被评论/被转发)

​      $related_tweet_id_min 关联推特ID的压缩(被评论/被转发)

​      $related_tweet_text 关联推特内容(被转发或被转发并评论时存在)



### setAttr 监测用户UID 属性 值

别名：对象设置

权限：超级管理员,@bot

功能：设置指定监测对象的属性

例：setGroupAttr 997786053124616192 转推 关

​		setGroupAttr 997786053124616192 昵称 

​		setGroupAttr 997786053124616192 昵称 FBKwaring

注：UID可以通过命令**getpushlist**查看，大部分属性与**setGroupAttr**命令相同

#### 特有的属性支持：

注：属性名称，别名1，...，别名n

​    nick,昵称

​    des,描述



### globalRemove 消息类型 Q号/群号

别名：全局移除

权限：超级管理员,@bot

功能：移除某个人或某个群的所有监测，用于修复配置错误(退出群/删除好友时不在线)

#### 消息类型

私聊,好友,private

群聊,群,group

例：globalRemove 群聊 123456



