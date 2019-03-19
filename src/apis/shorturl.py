# -*- coding: utf-8 -*-
"""
    apis.shorturl
    ~~~~~~~~~~~~~~

    网址缩短/还原接口.

    :copyright: (c) 2019 by staugur.
    :license: BSD, see LICENSE for more details.
"""

from utils.tool import get_redis_connect, url_check, gen_rediskey, encode_b64, decode_b64, err_logger
from redis.exceptions import RedisError

"""
全局信息哈希
    > sid: 自增id
    > shorten: 缩短接口统计
    > reduction: 还原接口统计
"""
GLOBAL_INFO_KEY = gen_rediskey("global")


def shorten_url(long_url):
    """缩短URL::
        1. 校验URL
        2. 查询G_INFO，获取自增id
        3. 编码自增id生成缩短码
    :param: long_url: str: 有效的网址
    :returns: dict:
    """
    res = dict(code=1, msg=None)
    if url_check(long_url):
        try:
            sid = get_redis_connect.hincrby(GLOBAL_INFO_KEY, "sid", 1)
        except RedisError:
            res.update(code=10001, msg="System storage exception")
        except Exception as e:
            err_logger.error(e, exc_info=True)
            res.update(code=10002, msg="System exception")
        else:
            res.update(data=dict(shorten=encode_b64(sid)), code=0)
    else:
        res.update(code=20001, msg="Invalid long_url")
    return res


def reduction_url(shorten_url_string, parseUrl=False):
    """还原缩短的URL
    :param: shorten_url_string: str: 缩短的url或唯一标识的字符串
    :returns: dict
    """
    res = dict(code=1, msg=None)
    checked = False if parseUrl is True and not url_check(shorten_url_string) else True
    if checked:
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
