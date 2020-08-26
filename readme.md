# 跨平台BOT插件兼容框架·开发中
[![License](https://img.shields.io/github/license/richardchien/nonebot.svg)](LICENSE)![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)

## 简介

拥有可全平台兼容的BOT兼容层，可以快速接入多个不同平台或相同平台bot。(开发中)

BOT兼容层：多接口、多接口权限模块、多接口消息流-主动发送、多接口插件兼容层-消息获取及响应

已实现内置插件功能：机器翻译、多功能转推、烤推、RSS更新订阅等

主要依赖于模块[tweepy](https://github.com/tweepy/tweepy)进行推特操作

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

原CoolQBot的通信依赖于CQHTTP，由于平台问题已迁移至[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)

特别鸣谢[richardchien](https://github.com/richardchien)对nonebot封装项目的贡献。

CQHTTP协议支持的端：[go-cqhttp](https://github.com/yyuueexxiinngg/cqhttp-mirai)、[mirai](https://github.com/yyuueexxiinngg/cqhttp-mirai)

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



### 使用烤推功能

使用烤推功能需要**安装chrome**及调用chrome的驱动**chromedriver**

#### **安装chrome**并标记为不更新

```shell
apt install chromium-browser
apt-mark hold chromium-browser
```

第二行命令用于标记不更新，防止apt-get upgrade等命令后把chrome更新了导致烤推驱动无法使用。

#### 查询chrome版本(记录一下，之后要用)

```
chromium-browser --version
```

#### 安装**chromedriver**(需要先查询chrome版本)

查找指定版本的[chromedrive](https://chromedriver.storage.googleapis.com/index.html)下载 大版本需要相同，不然无法使用

> chrome版本 Chromium 84.0.4147.105 则ChromeDriver对应版本可以是 ChromeDriver 84.0.4147.30

以下为**添加到全局命令的方法**：

```shell
wget chromedriver的下载地址
unzip chromedriver_linux64.zip
chmod +x chromedriver
mv chromedriver /usr/local/bin
```

**添加到全局命令后可以使用 chromedriver -v 查看驱动版本**

> 不添加全局命令的可以对配置文件**config.py**内的**ChromedriverPath**属性进行配置

##### **※chromedriver需要拥有执行权限**

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



## 关于Docs分支

**此分支为项目文档所在分支 此文档通过Hexo部署。**

### 文档维护(文档维护者请参见，仅部署后端可忽略)

#### 依赖

本文档网站搭建使用[HEXO](https://hexo.io/)，当前页面搭建基于[NodeJS LTS](https://nodejs.org/en/download/)请安装Node.js 12以搭建开发环境。

#### 环境配置

##### 全局HEXO

推荐在全局安装HEXO以搭建其他页面

```
node i -g hexo
```

##### Plugins

进入`/docs`文件夹，在Shell内运行

```shell
npm i
```

安装依赖，并安装Git插件

```shell
npm i hexo-deployer-git --save
```

#### 使用

##### 添加新文档

```Shell
hexo new "<标题(建议英文)>"
```

或直接在`source/_post/`内添加Markdown文档(须仿照其他文档设置抬头)

##### 修改文档

略

##### 编译

hexo文档项目使用

```mermaid
graph LR;

A[本地编辑] --> B[本地编译]
B --> C[本地预览]
E[清理当前项目] --> B
B --> D[部署到GitHub页面]
C --> D
A --> E

```

的模式，故编译时建议先**清理本地静态页面**

```shell
npm run clean
```

或

```shell
hexo clean
```

然后进行**编译生成**

```shell
npm run generate
```

##### 部署

最后部署到GitHub

```shell
npm run deploy
```

之后网页便会自动Push到仓库的`gh-pages`分支，并自动部署到服务器。

