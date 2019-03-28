# -*- coding: utf-8 -*-
"""
    views.ApiView
    ~~~~~~~~~~~~~~

    Api view.

    :copyright: (c) 2019 by staugur.
    :license: BSD, see LICENSE for more details.
"""

import json
from flask import Blueprint, request, url_for
from flask_restful import Api, Resource
from redis.exceptions import RedisError
from apis.shorturl import reduction_url
from utils.tool import gen_rediskey, get_current_timestamp, get_redis_connect, err_logger, dfr, url_check, encode_b64, decode_b64, shorten_pat

"""
全局信息哈希
    > sid: 自增id
    > shorten: 缩短接口统计
    > reduction: 还原接口统计
"""
GLOBAL_INFO_KEY = gen_rediskey("global")


class V1ApiView(Resource):

    def post(self):
        Action = request.args.get("Action")
        if Action == "shorten":
            # 缩短网址
            res = dict(code=1, msg=None)
            # 获取请求参数
            long_url = request.form.get("long_url") or ""
            jid = request.form.get("jid")
            # 不允许缩短本站网址
            if long_url.startswith(request.url_root):
                return dfr(dict(code=-1, msg="Invalid long url domain name"))
            # 生成缩短码
            if url_check(long_url):
                if jid:
                    if shorten_pat.match(jid):
                        pass
                    else:
                        res.update(code=30000)
                ##
                try:
                    sid = get_redis_connect.hincrby(GLOBAL_INFO_KEY, "sid", 1)
                except RedisError:
                    res.update(code=10001, msg="System storage exception")
                except Exception as e:
                    err_logger.error(e, exc_info=True)
                    res.update(code=10002, msg="System exception")
                else:
                    res.update(data=dict(shorten=encode_b64(sid)), code=0)
                    # 当前接口不完整，仍需要api端写入shorten哈希数据，包括创建时间、ip、agent等
            else:
                res.update(code=20001, msg="Invalid long_url")

            ######
            res = shorten_url(long_url, jid)
            if res["code"] == 0:
                # 请求时的统计信息
                SHORT_DATA = dict(
                    ip=request.headers.get('X-Real-Ip', request.remote_addr),
                    agent=request.headers.get('User-Agent',''),
                    referer=request.headers.get('Referer',''),
                    ctime=get_current_timestamp(),
                    etime=0,
                    status=1,
                    realname=0,
                    safe=1,
                    long_url=long_url
                )
                SHORTURL_KEY = gen_rediskey("s", res["data"]["shorten"])
                GLOBAL_INFO_KEY = gen_rediskey("global")
                pipe = get_redis_connect.pipeline()
                pipe.hincrby(GLOBAL_INFO_KEY, "shorten", 1)
                pipe.hmset(SHORTURL_KEY, SHORT_DATA)
                try:
                    pipe.execute()
                except Exception as e:
                    err_logger.error(e, exc_info=True)
                    res = dict(code=-1, msg="System exception")
                else:
                    res["data"]["short_url"] = url_for("go", shorten=res["data"]["shorten"], _external=True)
            return dfr(res)

        elif Action == "reduction":
            # 还原网址
            short_url = request.form.get("short_url") or ""
            if not short_url.startswith(request.url_root):
                res = dict(code=-1, msg="Invalid short url domain name")
                return dfr(res)
            res = reduction_url(short_url, parseUrl=True)
            if res["code"] == 0:
                # 请求时的统计信息
                ACCESS_DATA = dict(
                    ip=request.headers.get('X-Real-Ip', request.remote_addr),
                    agent=request.headers.get('User-Agent',''),
                    referer=request.headers.get('Referer',''),
                    ctime=get_current_timestamp(),
                    short_url=short_url
                )
                COUNT_KEY = gen_rediskey("pv", res["data"]["shorten"])
                SHORTURL_KEY = gen_rediskey("s", res["data"]["shorten"])
                GLOBAL_INFO_KEY = gen_rediskey("global")
                pipe = get_redis_connect.pipeline()
                pipe.hincrby(GLOBAL_INFO_KEY, "reduction", 1)
                pipe.hset(SHORTURL_KEY, "atime", get_current_timestamp())
                pipe.rpush(COUNT_KEY, json.dumps(ACCESS_DATA))
                try:
                    pipe.execute()
                except Exception as e:
                    err_logger.warning(e, exc_info=True)
            return dfr(res)


ApiBlueprint = Blueprint("api", __name__)
api = Api(ApiBlueprint)
api.add_resource(V1ApiView, '/v1', '/v1/', endpoint='api')
