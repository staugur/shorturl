# -*- coding: utf-8 -*-
"""
    satic.shorturl
    ~~~~~~~~~~~~~~

    Entrance

    Docstring conventions:
    http://flask.pocoo.org/docs/0.10/styleguide/#docstrings

    Comments:
    http://flask.pocoo.org/docs/0.10/styleguide/#comments

    Cache:
    http://docs.jinkan.org/docs/flask/patterns/caching.html

    :copyright: (c) 2019 by staugur.
    :license: MIT, see LICENSE for more details.
"""

import json
from flask import Flask, request, jsonify, redirect, render_template
from version import __version__
from views import ApiBlueprint
from utils.tool import err_logger, get_redis_connect, gen_rediskey, get_current_timestamp, dfr
from apis.shorturl import reduction_url

__author__ = 'staugur'
__email__ = 'staugur@saintic.com'
__doc__ = 'Simple short url service'
__date__ = '2019-03-19'

# 初始化定义application
app = Flask(__name__)

# 注册蓝图
app.register_blueprint(ApiBlueprint, url_prefix="/api")


@app.route("/<shorten>")
def index(shorten):
    """主页路由，shorten是缩短的唯一标识字符串"""
    res = dfr(reduction_url(shorten))
    if res["code"] == 0:
        # 请求时的统计信息
        ACCESS_DATA = dict(
            ip=request.headers.get('X-Real-Ip', request.remote_addr),
            agent=request.headers.get("User-Agent"),
            referer=request.headers.get('Referer'),
            ctime=get_current_timestamp(),
            shorten=shorten
        )
        COUNT_KEY = gen_rediskey("pv", shorten)
        SHORTURL_KEY = gen_rediskey("s", shorten)
        GLOBAL_INFO_KEY = gen_rediskey("global")
        pipe = get_redis_connect.pipeline()
        pipe.hincrby(GLOBAL_INFO_KEY, "reduction", 1)
        pipe.hset(SHORTURL_KEY, "atime", get_current_timestamp())
        pipe.rpush(COUNT_KEY, json.dumps(ACCESS_DATA))
        try:
            pipe.execute()
        except Exception as e:
            err_logger.warning(e, exc_info=True)
        finally:
            if res["data"]["status"] in (1, "1"):
                return redirect(res["data"]["long_url"], code=302)
            else:
                return render_template("index.html", title=u"短网址已禁用", keyword=u"禁用", msg=u"由于某些原因，您的短网址已经被系统禁用，您可以尝试解封或重新生成短网址！")
    else:
        return render_template("index.html", title=u"短网址错误", keyword=res["code"], msg=res["msg"])


@app.errorhandler(500)
def server_error(error=None):
    if error:
        err_logger.error(error, exc_info=True)
    return jsonify(dict(code=500, msg="Server Error")), 500


@app.errorhandler(404)
def not_found(error=None):
    return jsonify(dict(code=404, msg='Not Found: ' + request.url)), 404


@app.errorhandler(403)
def Permission_denied(error=None):
    return jsonify(dict(code=403, msg="Authentication failed, permission denied.")), 403


if __name__ == '__main__':
    from config import GLOBAL
    app.run(host=GLOBAL["Host"], port=int(GLOBAL["Port"]), debug=True)
