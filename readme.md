# 全平台BOT插件兼容框架
[![License](https://img.shields.io/github/license/richardchien/nonebot.svg)](LICENSE)![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)

## 简介

本仓库主要依赖于模块[tweepy](https://github.com/tweepy/tweepy)进行推特操作

拥有全平台BOT兼容层，可以快速接入多个不同平台或相同平台bot。

原CoolQBot的通信依赖于CQHTTP，由于平台问题已迁移至[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)

特别鸣谢[richardchien](https://github.com/richardchien)对nonebot封装项目的贡献。

兼容：[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)(连接使用[nonebot](https://github.com/nonebot/nonebot))，更多接口待开发

BOT兼容层：多接口、多接口权限模块、多接口消息流-主动发送、多接口插件兼容层-消息获取及响应

已实现内置插件功能：机器翻译、多功能转推、烤推、RSS更新订阅等

**项目目前支持 Python 3.7 +**



## 使用文档

### 文档首页(使用者请使用)

[用户文档](https://chenxuan353.github.io/tweetTobot/)



## 部署文档

### 项目使用及配置

直接克隆本项目或到release内克隆稳定版本

需要安装python3用以启动项目，请确保python3在3.7及以上版本以免遭遇兼容性bug

##### 查看python版本

```shell
python -V
```

##### 依赖安装

```shell
pip install -r requirements.txt
```

##### 配置项目

```
cp config_example.py config.py
```

打开项目根目录下的**config.py**文件，然后按照文件里的说明进行配置

*记得将各功能按需求开启或关闭

##### 启动项目

```shell
python3 ./start.py
```



### bot连接到后端

#### Tencent QQ

部署到QQ需要使用支持CQHTTP协议的BOT端

CQHTTP协议支持的端：[go-cqhttp](https://github.com/yyuueexxiinngg/cqhttp-mirai)、[mirai](https://github.com/mamoe/mirai)

连接配置：

在**ws_reverse_servers(反向ws配置)**的配置项内**输入服务器的IP与端口号**即可连上此后端

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