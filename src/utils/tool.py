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


logger = err_logger = Logger("error").getLogger
shorten_pat = re.compile(r'^[a-zA-Z\_][0-9a-zA-Z\_\.\-]{1,31}$')
get_redis_connect = from_url(REDIS_URL)


def gen_rediskey(*args):
    """生成Redis键前缀"""
    return "satic.shorturl:" + ":".join(map(str, args))


def get_current_timestamp():
    """ 获取本地当前时间戳(10位): Unix timestamp：是从1970年1月1日（UTC/GMT的午夜）开始所经过的秒数，不考虑闰秒 """
    return int(time.time())


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
        language = parseAcceptLanguage(request.cookies.get(
            "locale", request.headers.get('Accept-Language', default)), default)
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
            "Shorten code is existed": u"缩短码已存在",
            "Shorten code parameter illegal": u"缩短码参数非法",
            "In the service adjustment, the short domain name is suspended": u"服务调整中，暂时不能生成短网址",
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
                err_logger.debug(e)
            else:
                res["msg"] = new
    return res


def reduction_url(shorten_string):
    """还原缩短的URL
    :param: shorten_url_string: str: 缩短的url或唯一标识的字符串
    :returns: dict
    """
    res = dict(code=1, msg=None)
    if True:
        try:
            SHORTURL_KEY = gen_rediskey("s", shorten_string)
        except UnicodeEncodeError:
            res.update(code=-1, msg="Shorten code parameter illegal")
        else:
            try:
                data = get_redis_connect.hgetall(SHORTURL_KEY)
            except RedisError:
                res.update(code=10001, msg="System storage exception")
            except Exception as e:
                err_logger.error(e, exc_info=True)
                res.update(code=10002, msg="System exception")
            else:
                if data and isinstance(data, dict) and "long_url" in data:
                    res.update(code=0, data=dict(
                        long_url=data["long_url"], shorten=shorten_string, status=data["status"], safe=data["safe"], realname=data["realname"]))
                else:
                    res.update(code=404, msg="Not found shorten url")
    return res
