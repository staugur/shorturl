# -*- coding: utf-8 -*-
"""
    utils.tool
    ~~~~~~~~~~~~~~

    Common function.

    :copyright: (c) 2019 by staugur.
    :license: BSD, see LICENSE for more details.
"""

import re
import time
import hashlib
from log import Logger
from redis import from_url
from config import REDIS as REDIS_URL
from redis.exceptions import RedisError


logger = Logger("sys").getLogger
err_logger = Logger("error").getLogger
shorten_pat = re.compile(r'^[a-zA-Z\_][0-9a-zA-Z\_\.\-]{1,31}$')
get_redis_connect = from_url(REDIS_URL)


def md5(pwd):
    """MD5"""
    return hashlib.md5(pwd).hexdigest()


def gen_rediskey(*args):
    """生成Redis键前缀"""
    return "satic.shorturl:" + ":".join(map(str, args))


def url_check(addr):
    """检测UrlAddr是否为有效格式，例如
    http://ip:port
    https://abc.com
    """
    regex = re.compile(
        r'^(?:http)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    if addr and isinstance(addr, (str, unicode)):
        if regex.match(addr):
            return True
    return False


def get_current_timestamp():
    """ 获取本地当前时间戳(10位): Unix timestamp：是从1970年1月1日（UTC/GMT的午夜）开始所经过的秒数，不考虑闰秒 """
    return int(time.time())


def create_redis_engine(redis_url=None):
    """ 创建redis连接 """
    if not (redis_url or REDIS_URL):
        raise ValueError("No valid redis connection string")
    return from_url(redis_url or REDIS_URL)


def encode_b64(number):
    """10进制编码为64进制"""
    try:
        number = int(number)
    except:
        raise
    table = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_'
    result = []
    temp = number
    if 0 == temp:
        result.append('0')
    else:
        while 0 < temp:
            result.append(table[temp % 64])
            temp /= 64
    return ''.join([x for x in reversed(result)])


def decode_b64(string):
    """64进制解码为10进制"""
    if not string or not isinstance(string, basestring):
        raise TypeError("Invalid string")
    table = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
             "6": 6, "7": 7, "8": 8, "9": 9,
             "a": 10, "b": 11, "c": 12, "d": 13, "e": 14, "f": 15, "g": 16,
             "h": 17, "i": 18, "j": 19, "k": 20, "l": 21, "m": 22, "n": 23,
             "o": 24, "p": 25, "q": 26, "r": 27, "s": 28, "t": 29, "u": 30,
             "v": 31, "w": 32, "x": 33, "y": 34, "z": 35,
             "A": 36, "B": 37, "C": 38, "D": 39, "E": 40, "F": 41, "G": 42,
             "H": 43, "I": 44, "J": 45, "K": 46, "L": 47, "M": 48, "N": 49,
             "O": 50, "P": 51, "Q": 52, "R": 53, "S": 54, "T": 55, "U": 56,
             "V": 57, "W": 58, "X": 59, "Y": 60, "Z": 61,
             "-": 62, "_": 63}
    result = 0
    for i in xrange(len(string)):
        result *= 64
        result += table[string[i]]
    return result


def parseAcceptLanguage(acceptLanguage, defaultLanguage="zh-CN"):
    if not acceptLanguage:
        return defaultLanguage
    languages = acceptLanguage.split(",")
    locale_q_pairs = []
    for language in languages:
        if language.split(";")[0] == language:
            # no q => q = 1
            locale_q_pairs.append((language.strip(), "1"))
        else:
            locale = language.split(";")[0].strip()
            q = language.split(";")[1].split("=")[1]
            locale_q_pairs.append((locale, q))
    return sorted(locale_q_pairs, key=lambda x: x[-1], reverse=True)[0][0] or defaultLanguage


def dfr(res, default='en-US'):
    """定义前端返回，将res中msg字段转换语言
    @param res dict: like {"msg": None, "success": False}, 英文格式
    @param default str: 默认语言
    """
    try:
        from flask import request
        language = parseAcceptLanguage(request.cookies.get("locale", request.headers.get('Accept-Language', default)), default)
        if language == "zh-Hans-CN":
            language = "zh-CN"
    except:
        language = default
    # 翻译转换字典库
    trans = {
        # 简体中文
        "zh-cn": {
            "Hello World": u"世界，你好",
            "System storage exception": u"系统服务异常",
            "System exception": u"系统异常",
            "Invalid long_url": u"无效的长网址参数",
            "Not found shorten url": u"未发现短网址",
            "Invalid shorten url": u"无效的短网址",
            "Invalid short url domain name": u"无效的短网址域名",
            "Invalid long url domain name": u"无效的长网址域名",
            "Custom shortening code is illegal": u"自定义的缩短码不合法",
            "Custom shortening code is existed": u"自定义的缩短码已存在",
        },
    }
    # 此处后续建议改为按照code翻译，code固定含义：
    # 10001 存储异常
    # 10002 系统异常
    if isinstance(res, dict) and not "en" in language:
        if res.get("msg"):
            msg = res["msg"]
            try:
                new = trans[language.lower()][msg]
            except KeyError, e:
                logger.warn(e)
            else:
                res["msg"] = new
    return res


def reduction_url(shorten_url_string, parseUrl=False):
    """还原缩短的URL
    :param: shorten_url_string: str: 缩短的url或唯一标识的字符串
    :returns: dict
    """
    res = dict(code=1, msg=None)
    checked = False if parseUrl is True and not url_check(shorten_url_string) else True
    if checked and shorten_url_string:
        shorten_string = shorten_url_string.split("/")[-1] if parseUrl is True else shorten_url_string
        SHORTURL_KEY = gen_rediskey("s", shorten_string)
        try:
            data = get_redis_connect.hgetall(SHORTURL_KEY)
        except RedisError:
            res.update(code=10001, msg="System storage exception")
        except Exception as e:
            err_logger.error(e, exc_info=True)
            res.update(code=10002, msg="System exception")
        else:
            if data and isinstance(data, dict) and "long_url" in data:
                res.update(code=0, data=dict(long_url=data["long_url"], shorten=shorten_string, status=data["status"], safe=data["safe"], realname=data["realname"]))
            else:
                res.update(code=404, msg="Not found shorten url")
    else:
        res.update(code=20001, msg="Invalid shorten url")
    return res
