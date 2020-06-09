---
title: 部署文档
date: 2020-06-08 10:16:57
categories:
 - 项目文档
tags:
 - 部署
 - 使用
 - 文档
 - 注意事项
---

## 部署

### 部署CoolQ

安装CoolQ并按照帖子内文档部署。

[Air](https://cqp.cc/t/23253) [Pro](https://cqp.cc/t/14901) [Docker](https://cqp.cc/t/34558)

- Docker中部署Air

  ```shell
  mkdir coolq-data
  docker run --name=coolq -d -p <VNC Port>:9000 -v /root/coolq-data:/home/user/coolq -e VNC_PASSWD=<Password> -e COOLQ_ACCOUNT=<QQ> coolq/wine-coolq
  ```


- Docker中部署Pro

  ```shell
  mkdir coolq
  docker run --name=coolq -d -p <VNC Port>:9000 -v `pwd`/coolq:/home/user/coolq -e COOLQ_ACCOUNT=<QQ ID> -e COOLQ_URL=http://dlsec.cqp.me/cqp-full -e VNC_PASSWD=<Password> coolq/wine-coolq
  ```

※ 其中9000为默认内部端口 映射到指定的VNC端口 故在后面操作图形化界面时 需通过

```
HOST IP:VNC Port
```

的地址打开。

**如需使用除搬运推文以外的其他功能(烤推等涉及图片发送的功能) **

**请务必[捐赠CQP项目](https://cqp.me/user/)以使用[CoolQ Pro](https://cqp.cc/t/14901)**



### 启动插件

#### 下载CPK依赖
- Windows平台

下载[CQHttp](https://github.com/richardchien/coolq-http-api/releases)的[CPK依赖包](https://github.com/richardchien/coolq-http-api/releases/download/v4.15.0/io.github.richardchien.coolqhttpapi.cpk)并安装(放到依赖包位置并**初次启动后进行配置**)

- Docker for Linux

```shell
wget https://github.com/richardchien/coolq-http-api/releases/download/v4.15.0/io.github.richardchien.coolqhttpapi.cpk
```

*如在Docker中部署请在此处启动插件服务*

#### 配置CPK插件

在CQ根目录下`data/app/io.github.richardchien.coolqhttpapi/config/`文件夹内，找到`<QQ号>.json`的JSON配置文件（须初次启动后自动生成）

**在其中添加两行以打开消息推送**

```JSON
"rate_limit_interval":500,
"enable_rate_limited_actions": true,
```

本插件支持HTTP和WS两种模式，故可根据官方文档中[配置](https://cqhttp.cc/docs/4.15/#/Configuration)部分进行操作。

绝大部分参数无需修改，但请保证打开http/ws_reverse/ws其中之一，并打开heartbeat以确保全部功能可用。基本操作也可参见Nonebot文档中的[基本配置说明](https://nonebot.cqp.moe/guide/getting-started.html#%E9%85%8D%E7%BD%AE-cqhttp-%E6%8F%92%E4%BB%B6)

下面给出一个配置范例

```JSON
{
    "$schema": "https://cqhttp.cc/config-schema.json",
    "host": "0.0.0.0",
    "port": 5700,
    "use_http": true,
    "ws_host": "0.0.0.0",
    "ws_port": 6700,
    "use_ws": false,
    "ws_reverse_url": "ws://127.0.0.1:8087/ws/",
    "ws_reverse_api_url": "",
    "ws_reverse_event_url": "",
    "ws_reverse_reconnect_interval": 3000,
    "ws_reverse_reconnect_on_code_1000": true,
    "use_ws_reverse": true,
    "post_url": "http://0.0.0.0:8890",
    "access_token": "",
    "rate_limit_interval":500,
    "enable_rate_limited_actions": true,
    "enable_heartbeat": true,
    "secret": "",
    "post_message_format": "string",
    "serve_data_files": false,
    "update_source": "global",
    "update_channel": "stable",
    "auto_check_update": false,
    "auto_perform_update": false,
    "show_log_console": true,
    "log_level": "info"
}
```

##### 

| 配置文件                                                     | 注释说明                                              |
| ------------------------------------------------------------ | ----------------------------------------------------- |
| "$schema": "https://cqhttp.cc/config-schema.json"            |                                                       |
| "host": "0.0.0.0"                                            | HTTP协议 事件上报IP（监听IP）**开启时须正确配置**     |
| "port": 5700                                                 | HTTP协议 事件上报接口（监听接口）**开启时须正确配置** |
| "use_http": true                                             | 启用HTTP **使用时开启**                               |
| "ws_host": "0.0.0.0"                                         | 正向WS IP                                             |
| "ws_port": 6700                                              | 正向WS端口                                            |
| "use_ws": false                                              | 启用正向WS **本项目不使用 建议关闭**                  |
| "ws_reverse_url": "ws://127.0.0.1:8087/ws/"                  | 反向WS地址 **务必正确填写**                           |
| "ws_reverse_api_url": ""                                     | 反向WS API地址 **如填写反向WS地址则无需填写**         |
| "ws_reverse_event_url": ""                                   | 反向WS 事件上报地址 **如填写反向WS地址则无需填写**    |
| "ws_reverse_reconnect_interval": 3000                        | 重连间隔 **无需修改**                                 |
| "ws_reverse_reconnect_on_code_1000": true                    | 是否重连 **无需修改**                                 |
| "use_ws_reverse": true                                       | 启用反向WS **使用时开启 建议优先使用**                |
| "post_url": "http://0.0.0.0:8890"                            | HTTP POST地址 **使用HTTP协议填写**                    |
| "access_token": ""                                           | CQHTTP TOKEN **无需填写**                             |
| "rate_limit_interval":500                                    | 频率限制 **务必添加**                                 |
| "enable_rate_limited_actions": true                          | 开启频率限制 **务必打开**                             |
| "enable_heartbeat": true                                     | 开启心跳 **务必打开**                                 |
| "secret": "",<br/>"post_message_format": "string",<br/>"serve_data_files": false,<br/>"update_source": "global",<br/>"update_channel": "stable",<br/>"auto_check_update": false,<br/>"auto_perform_update": false,<br/>"show_log_console": true,<br/>"log_level": "info" | 各项均可保持默认 **无需修改**                         |

##### 关于协议

本项目支持使用HTTP或反向WS协议进行通信，其中

- 使用HTTP协议
  - 事件上报地址 "host"与"port"
  - POST通信地址 "post_url"(host:port)
- 使用反向WS协议
  - API地址 "ws_reverse_url"

简单来说，HTTP的收发分别使用两个地址，而反向WS协议使用同一个地址。

因此可以通过同时打开HTTP和反向WS协议实现使用一个BOT同时连接两个后端服务。

**具体配置过程在[多服务配置](https://github.com/chenxuan353/tweetToQQbot/blob/master/readme.md#多服务配置)中说明。**



### 启动服务

#### 安装依赖

##### PYPI依赖

手动安装依赖

```shell
pip install nonebot[scheduler] selenium xmltodict threading urllib tweepy
```

或者可以使用

```
pip -r requirement.txt
```

进行一键安装

**如进行一键依赖安装时发送报错 请检查Python版本是否为3.7**

##### Chrome浏览器与ChromeDriver

您可以参考[本教程](https://blog.csdn.net/Fiverya/article/details/98869750)

#### 添加配置

将config_example.py改名为config.py并填写内部的配置信息

```shell
mv config_example.py config.py
```

```shell
vi config.py
```
**内部各项均已注明 请根据注释进行配置（不填请保留字段 不推荐删除）**

##### 多服务配置

CQHTTP为nonebot提供了HTTP和反向WS两种通信协议 具体配置方法如下

> 为方便书写与描述
>
> 称呼`data/app/io.github.richardchien.coolqhttpapi/config/`文件夹内含有QQ号的JSON文件为**插件配置**
>
> 称呼本项目中`config.py`文件为**项目配置**

###### HTTP协议

- 事件上报地址

  编辑插件配置中`host`与`port`字段

  并与项目配置中`API_ROOT`字段保持一致

- POST通信地址

  编辑插件配置中`post_url`字段 **※ 须添加`http://`作为前缀**

  并与项目配置中`NONEBOT_HOST`和`NONEBOT_PORT`所指向地址保持一致

###### 反向WS协议

- API地址

  编辑插件配置中`ws_reverse_url`字段（只修改IP和端口即可）

  并与项目配置中`NONEBOT_HOST`和`NONEBOT_PORT`所指向地址保持一致

  （API_ROOT与反向WS无关 如**在使用反向WS后端** **必须**注释掉本变量）

#### 启动项目

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