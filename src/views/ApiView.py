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
from utils.tool import gen_rediskey, get_current_timestamp, get_redis_connect, err_logger, dfr, url_check, encode_b64, decode_b64, shorten_pat, reduction_url


class V1ApiView(Resource):

    def post(self):
        Action = request.args.get("Action")
        if Action == "shorten":
            # 缩短网址
            res = dict(code=1, msg=None)
            # 获取请求参数
            long_url = request.form.get("long_url") or ""
            jid = request.form.get("jid") or ""
            # 不允许缩短本站网址
            if long_url.startswith(request.url_root):
                return dfr(dict(code=-1, msg="Invalid long url domain name"))
            # 生成缩短码
            if url_check(long_url):
                is_jid = False
                if jid:
                    if shorten_pat.match(jid):
                        is_jid = True
                    else:
                        res.update(code=30001, msg="Custom shortening code is illegal")
                        return dfr(res)
                """全局信息哈希
                    > sid: 自增id
                    > shorten: 缩短接口统计
                    > reduction: 还原接口统计
                """
                GLOBAL_INFO_KEY = gen_rediskey("global")
                try:
                    sid = get_redis_connect.hincrby(GLOBAL_INFO_KEY, "sid", 1)
                except RedisError:
                    res.update(code=10001, msg="System storage exception")
                except Exception as e:
                    err_logger.error(e, exc_info=True)
                    res.update(code=10002, msg="System exception")
                else:
                    # 生成缩短码
                    shorten = jid if is_jid else encode_b64(sid)
                    # 由于自定义短网址存在，此处需要检测是否存在shorten，且GLOBAL_INFO_KEY中sid不能做减法
                    if get_redis_connect.exists(gen_rediskey("s", shorten)):
                        res.update(code=30002, msg="Shorten code is existed")
                        return dfr(res)
                    # 短网址hash键
                    SHORTURL_KEY = gen_rediskey("s", shorten)
                    # 短网址hash值
                    SHORTURL_DATA = dict(
                        sid=sid,
                        jid=jid,
                        ip=request.headers.get('X-Real-Ip', request.remote_addr),
                        agent=request.headers.get('User-Agent', ''),
                        referer=request.headers.get('Referer', ''),
                        ctime=get_current_timestamp(),
                        etime=0,
                        status=1,
                        realname=0,
                        safe=1,
                        long_url=long_url
                    )
                    try:
                        pipe = get_redis_connect.pipeline()
                        pipe.hincrby(GLOBAL_INFO_KEY, "shorten", 1)
                        pipe.hmset(SHORTURL_KEY, SHORTURL_DATA)
                        pipe.execute()
                    except RedisError:
                        res.update(code=10001, msg="System storage exception")
                    except Exception as e:
                        err_logger.error(e, exc_info=True)
                        res = dict(code=10002, msg="System exception")
                    else:
                        res.update(data=dict(shorten=shorten, short_url=url_for("go", shorten=shorten, _external=True)), code=0)
                    finally:
                        if res["code"] == 0:
                            # 成功请求
                            uid = request.form.get("uid")
                            if uid:
                                try:
                                    USER_KEY = gen_rediskey("u", uid)
                                    get_redis_connect.sadd(USER_KEY, shorten)
                                except:
                                    pass
            else:
                res.update(code=20001, msg="Invalid long_url")
            return dfr(res)

        elif Action == "reduction":
            # 还原网址
            short_url = request.form.get("short_url") or ""
            if not short_url.startswith(request.url_root):
                return dfr(dict(code=-1, msg="Invalid short url domain name"))
            res = reduction_url(short_url, parseUrl=True)
            if res["code"] == 0:
                # 请求时的统计信息
                ACCESS_DATA = dict(
                    ip=request.headers.get('X-Real-Ip', request.remote_addr),
                    agent=request.headers.get('User-Agent', ''),
                    referer=request.headers.get('Referer', ''),
                    ctime=get_current_timestamp(),
                    short_url=short_url,
                    origin="api"
                )
                COUNT_KEY = gen_rediskey("pv", res["data"]["shorten"])
                SHORTURL_KEY = gen_rediskey("s", res["data"]["shorten"])
                GLOBAL_INFO_KEY = gen_rediskey("global")
                try:
                    pipe = get_redis_connect.pipeline()
                    pipe.hincrby(GLOBAL_INFO_KEY, "reduction", 1)
                    # 更新短网址最后一次访问时间
                    pipe.hset(SHORTURL_KEY, "atime", get_current_timestamp())
                    # 短网址访问记录
                    pipe.rpush(COUNT_KEY, json.dumps(ACCESS_DATA))
                    pipe.execute()
                except Exception as e:
                    err_logger.warning(e, exc_info=True)
            return dfr(res)


ApiBlueprint = Blueprint("api", __name__)
api = Api(ApiBlueprint)
api.add_resource(V1ApiView, '/v1', '/v1/', endpoint='api')
