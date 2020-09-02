from .lang_conv import Converter
"""
    来自https://raw.githubusercontent.com/skydark/nstools/master/zhtools
    的繁简转换代码
"""
def simple2tradition(line):
    """
        将简体转换成繁体
    """
    line = Converter('zh-hant').convert(line)
    return line
def tradition2simple(line):
    """
        将繁体转换成简体
    """
    line = Converter('zh-hans').convert(line)
    return line
def isSimple(line):
    """
        判断是否为简体
    """
    res = Converter('zh-hans').convert(line)
    return res == line
def isTradition(line):
    """
        判断是否为繁体
    """
    res = Converter('zh-hant').convert(line)
    return res == line