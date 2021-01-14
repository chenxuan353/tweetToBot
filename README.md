# 跨平台 BOT 插件兼容框架·开发中

[![License](https://img.shields.io/github/license/richardchien/nonebot.svg)](LICENSE)&nbsp;![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)

## 简介

拥有可全平台兼容的 BOT 兼容层，可以快速接入多个不同平台或相同平台 bot。(开发中)

BOT 兼容层：多接口、多接口权限模块、多接口消息流-主动发送、多接口插件兼容层-消息获取及响应

已实现内置插件功能：机器翻译、多功能转推、烤推、RSS 更新订阅等

主要依赖于模块[tweepy](https://github.com/tweepy/tweepy)进行推特操作

**项目目前支持 Python 3.7 +**

## 使用文档

[文档](https://github.com/bothbot/OneTweBot-Docs)

[用户文档](https://chenxuan353.github.io/tweetTobot/)(停止维护)

## 部署文档

### 项目使用及配置

本分支使用支持Docker部署，可自行根据Dockerfile构建，也可以使用Hub上已经构建好的镜像

##### 配置项目

首先服务器需安装好Docker环境以及docker-compose

接着新建一个文件夹用于存放配置文件

```shell
mkdir tweetToBot
mkdir tweetToBot/conf
cd tweetToBot
touch docker-compose.yml
wget -O conf/config.hjson https://raw.githubusercontent.com/chenxuan353/tweetToBot/v3/conf/config_example.hjson
```

打开项目根目录下的`docker-compose.yml`文件，写入以下内容：

```yml
version: "3.9"
services:
  bot_1:
    container_name: bot_1
    hostname: bot_1
    volumes:
      - ./conf:/conf
    image: lonelyion/tweetToBot:latest
    ports:
      - 80:80       # 烤推图片
      - 8091:8091   # NoneBot
```

接下来打开`conf/config.hjson`，然后按照文件里的说明进行配置，记得将各功能按需求开启或关闭

##### 启动项目

```shell
docker-compose up -d
```

### bot 连接到后端

#### Tencent QQ

部署到 QQ 需要使用支持 CQHTTP 协议的 BOT 端

原 CoolQBot 的通信依赖于 CQHTTP，由于平台问题已迁移至[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)

特别鸣谢[richardchien](https://github.com/richardchien)对 nonebot 封装项目的贡献。

CQHTTP 协议支持的端：[go-cqhttp](https://github.com/yyuueexxiinngg/cqhttp-mirai)、[mirai](https://github.com/yyuueexxiinngg/cqhttp-mirai)

连接配置：

在**ws_reverse_servers(反向 ws 配置)**的配置项内**输入服务器的 IP 与端口号**即可连上此后端

示例：

```json
    "ws_reverse_servers": [
        {
            "enabled": true,
            "reverse_url": "",
            "reverse_api_url": "ws://127.0.0.1:8100/ws/api/",
            "reverse_event_url": "ws://127.0.0.1:8100/ws/event/",
            "reverse_reconnect_interval": 3000
        }
    ],
```

### 使用烤推功能

使用烤推功能需要**安装 chrome**及调用 chrome 的驱动**chromedriver**

#### **安装 chrome**并标记为不更新

```shell
apt install chromium-browser
apt-mark hold chromium-browser
```

第二行命令用于标记不更新，防止 apt-get upgrade 等命令后把 chrome 更新了导致烤推驱动无法使用。

#### 查询 chrome 版本(记录一下，之后要用)

```
chromium-browser --version
```

#### 安装**chromedriver**(需要先查询 chrome 版本)

查找指定版本的[chromedrive](https://chromedriver.storage.googleapis.com/index.html)下载 大版本需要相同，不然无法使用

> chrome 版本 Chromium 84.0.4147.105 则 ChromeDriver 对应版本可以是 ChromeDriver 84.0.4147.30

以下为**添加到全局命令的方法**：

```shell
wget chromedriver的下载地址
unzip chromedriver_linux64.zip
chmod +x chromedriver
mv chromedriver /usr/local/bin
```

**添加到全局命令后可以使用 chromedriver -v 查看驱动版本**

> 不添加全局命令的可以对配置文件**config.py**内的**ChromedriverPath**属性进行配置

##### **※chromedriver 需要拥有执行权限**

##### 安装字体

烤推使用字体 Source Han Sans CN

##### 设置时区

```
timedatectl set-timezone Asia/Shanghai
```

##### 设置语言

```
export LANG="zh_CN.UTF-8"
```
