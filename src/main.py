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

from flask import Flask, request, jsonify
from version import __version__
from utils.tool import err_logger, create_redis_engine, gen_requestId, gen_rediskey
from apis.shorturl import shorten_url, reduction_url

__author__ = 'staugur'
__email__ = 'staugur@saintic.com'
__doc__ = 'Simple short url service'
__date__ = '2019-03-19'


# 初始化定义application
app = Flask(__name__)

# 更新app配置
app.config.update(
    rc=create_redis_engine(),
    SECRET_KEY=gen_requestId()
)

# 注册蓝图
app.register_blueprint(ApiBlueprint)

@app.route("/<>"):
def index():
    pass

@app.errorhandler(500)
def server_error(error=None):
    if error:
        err_logger.error(error, exc_info=True)
    return jsonify(dict(code=500, msg="Server Error")), 500


@app.errorhandler(404)
def not_found():
    return jsonify(dict(code=404, msg='Not Found: ' + request.url)), 404


@app.errorhandler(403)
def Permission_denied():
    return jsonify(dict(code=403, msg="Authentication failed, permission denied.")), 403


if __name__ == '__main__':
    from config import GLOBAL
    app.run(host=GLOBAL["Host"], port=int(GLOBAL["Port"]), debug=True)
