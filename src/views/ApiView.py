# -*- coding: utf-8 -*-
"""
    views.ApiView
    ~~~~~~~~~~~~~~

    Api view.

    :copyright: (c) 2019 by staugur.
    :license: BSD, see LICENSE for more details.
"""

from flask import Blueprint, request, current_app
from flask_restful import Api, Resource
from apis.shorturl import shorten_url, reduction_url
from utils.tool import gen_rediskey, get_current_timestamp, err_logger


class ApiView(Resource):

    def post(self):
        Action = request.args.get("Action")

        if Action == "shorten":
            # 缩短网址
            url = request.form.get("url")
            res = shorten_url(url)
            if res["code"] == 0:
                # 请求时的统计信息
                SHORT_DATA = dict(
                    ip=request.headers.get('X-Real-Ip', request.remote_addr),
                    agent=request.headers.get("User-Agent"),
                    referer=request.headers.get('Referer'),
                    ctime=get_current_timestamp(),
                    status=1,
                    realname=0,
                    safe=1
                )
                SHORTURL_KEY = gen_rediskey("s", res["shorten"])
                GLOBAL_INFO_KEY = gen_rediskey("global")
                pipe = current_app.rc.pipeline()
                pipe.hincrby(GLOBAL_INFO_KEY, "shorten", 1)
                pipe.hmset(SHORTURL_KEY, SHORT_DATA)
                try:
                    pipe.execute()
                except Exception as e:
                    err_logger.error(e, exc_info=True)
            return res

        elif Action == "reduction":
            # 还原网址
            url = request.form.get("url")
            res = reduction_url(url)


ApiBlueprint = Blueprint("api", __name__)
api = Api(ApiBlueprint)
api.add_resource(ApiView, '/api', '/api/', endpoint='api')
