# -*- coding: utf-8 -*-
"""
    apis.shorturl
    ~~~~~~~~~~~~~~

    网址缩短/还原接口.

    :copyright: (c) 2019 by staugur.
    :license: BSD, see LICENSE for more details.
"""

from utils.tool import create_redis_engine, url_check, gen_rediskey, encode_b64, decode_b64, err_logger
from redis.exceptions import RedisError

"""
全局信息哈希
    > sid: 自增id
    > shorten: 缩短接口统计
    > reduction: 还原接口统计
    > last: 最后一次缩短时间戳
"""
GLOBAL_INFO_KEY = gen_rediskey("global")


def shorten_url(url):
    """缩短URL::
        1. 校验URL
        2. 查询G_INFO，获取自增id
        3. 编码自增id生成缩短码
    :param: url: str: 有效的网址
    :returns: str: url在系统中唯一标识字符串
    """
    res = dict(code=1, msg=None)
    if url_check(url):
        try:
            rc = create_redis_engine()
            sid = rc.hincrby(GLOBAL_INFO_KEY, "sid", 1)
        except RedisError:
            res.update(code=10001, msg="System storage exception")
        except Exception as e:
            err_logger.error(e, exc_info=True)
            res.update(code=10002, msg="System exception")
        else:
            res.update(shorten=encode_b64(sid), code=0)
    else:
        res.update(code=20001, msg="Invalid url")
    return res

def reduction_url(shorten_string):
    pass

def get_shorturl_data(shorten_string):
    pass
