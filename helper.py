# -*- coding: UTF-8 -*-
import config
import time
import requests
import traceback
import nonebot
import json
"""
帮助函数
"""
config_file_base_path = 'cache\\config\\'
bindCQID = config.default_bot_QQ
bot_error_printID = config.bot_error_printID


#参数截断
def commandHeadtail(s:str):
    return s.partition(" ")
#处理日志输出
def log_print(level,message,*arg):
    for value in arg:
        message = message + str(value)
    time_str = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    if level == 0:
        print('[致命错误]['+ time_str + ']' +message)
        if bot_error_printID != '':
            try:
                bot = nonebot.get_bot()
                bot.sync.send_msg_rate_limited(
                    self_id=bindCQID,
                    user_id=bot_error_printID,
                    message=message)
            except ValueError:
                log_print(2,'BOT未初始化,错误消息未发送')
            except:
                log_print(1,'BOT状态异常')
                s = traceback.format_exc(limit=10)
                log_print(2,s)
            #requests.post('http://127.0.0.1:5700/send_msg_rate_limited',data={'user_id': bot_error_printID, 'message': time_str})
    elif level == 1:
        print('[!!错误!!]['+ time_str + ']' +message)
    elif level == 2:
        print('[!警告!]['+ time_str + ']'+message)
    elif level == 3:
        print('[调试]['+ time_str + ']'+message)
    elif level == 4:
        print('[信息]['+ time_str + ']'+message)
    elif level == 5:
        print('[值得注意]['+ time_str + ']'+message)
    elif level == 6:
        print('[信息]['+ time_str + ']'+message)
        if bot_error_printID != '':
            try:
                bot = nonebot.get_bot()
                bot.sync.send_msg_rate_limited(
                    self_id=bindCQID,
                    user_id=bot_error_printID,
                    message=message)
            except ValueError:
                log_print(2,'BOT未初始化,错误消息未发送')
            except:
                log_print(1,'BOT状态异常')
                s = traceback.format_exc(limit=10)
                log_print(2,s)

#数据文件操作,返回(逻辑值T/F,dict数据/错误信息)
def data_read(filename:str) -> tuple:
    try:
        f = open(config_file_base_path + filename,mode = 'r',encoding='utf-8')
        data = json.load(f)
    except IOError:
        log_print(1,'IOError: 未找到文件或文件不存在-',filename)
        return (False,'配置文件读取失败')
    except:
        log_print(1,'数据文件读取解析异常')
        s = traceback.format_exc(limit=10)
        log_print(2,s)
        return (False,'配置文件解析异常')
    else:
        f.close()
    return (True,'读取成功',data)
def data_save(filename:str,data):
    try:
        fw = open(config_file_base_path + filename,mode = 'w',encoding='utf-8')
        json.dump(data,fw,ensure_ascii=False,indent=4)
    except IOError:
        log_print(1,'IOError: 未找到文件或文件不存在-',filename)
        pass
        return (False,'配置文件写入失败')
    except:
        log_print(1,'数据文件写入异常')
        s = traceback.format_exc(limit=10)
        log_print(2,s)
        return (False,'配置文件写入异常')
    else:
        fw.close()
    return (True,'保存成功')

#配置文件读取

