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
from uuid import uuid4
from log import Logger
from redis import from_url
from config import REDIS as REDIS_URL


logger = Logger("sys").getLogger
err_logger = Logger("error").getLogger
get_redis_connect = from_url(REDIS_URL)


def md5(pwd):
    return hashlib.md5(pwd).hexdigest()


def gen_requestId():
    return str(uuid4())


def gen_rediskey(*args):
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
