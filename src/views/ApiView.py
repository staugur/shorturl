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
from apis.shorturl import shorten_url, reduction_url
from utils.tool import gen_rediskey, get_current_timestamp, get_redis_connect, err_logger, dfr


class V1ApiView(Resource):

    def post(self):
        Action = request.args.get("Action")
        if Action == "shorten":
            # 缩短网址
            long_url = request.form.get("long_url")
            res = shorten_url(long_url)
            if res["code"] == 0:
                # 请求时的统计信息
                SHORT_DATA = dict(
                    ip=request.headers.get('X-Real-Ip', request.remote_addr),
                    agent=request.headers.get("User-Agent"),
                    referer=request.headers.get('Referer'),
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
                    res["data"]["short_url"] = url_for("index", shorten=res["data"]["shorten"], _external=True)
            return dfr(res)

        elif Action == "reduction":
            # 还原网址
            short_url = request.form.get("short_url")
            res = reduction_url(short_url, parseUrl=True)
            if res["code"] == 0:
                # 请求时的统计信息
                ACCESS_DATA = dict(
                    ip=request.headers.get('X-Real-Ip', request.remote_addr),
                    agent=request.headers.get("User-Agent"),
                    referer=request.headers.get('Referer'),
                    ctime=get_current_timestamp(),
                    short_url=short_url
                )
                COUNT_KEY = gen_rediskey("pv", res["data"]["shorten"])
                SHORTURL_KEY = gen_rediskey("s", res["data"]["shorten"])
                GLOBAL_INFO_KEY = gen_rediskey("global")
                pipe = get_redis_connect.pipeline()
                pipe.hincrby(GLOBAL_INFO_KEY, "reduction", 1)
                pipe.hset(SHORTURL_KEY, "ltime", get_current_timestamp())
                pipe.rpush(COUNT_KEY, json.dumps(ACCESS_DATA))
                try:
                    pipe.execute()
                except Exception as e:
                    err_logger.warning(e, exc_info=True)
            return dfr(res)


ApiBlueprint = Blueprint("api", __name__)
api = Api(ApiBlueprint)
api.add_resource(V1ApiView, '/v1', '/v1/', endpoint='api')
