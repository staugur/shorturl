# -*- coding: utf-8 -*-

import json
from flask import Flask, request, redirect, render_template
from utils.tool import err_logger, get_redis_connect, gen_rediskey, \
    get_current_timestamp, dfr, reduction_url

# 初始化定义application
app = Flask(__name__)


@app.route("/")
def index():
    """首页跳转到开放平台"""
    return redirect("https://open.saintic.com/openservice/shorturl/", code=302)


@app.route("/<shorten>")
def go(shorten):
    """主页路由，shorten是缩短的唯一标识字符串"""
    res = dfr(reduction_url(shorten))
    if res["code"] == 0:
        # 请求时的统计信息
        ACCESS_DATA = dict(
            ip=request.headers.get('X-Real-Ip', request.remote_addr),
            agent=request.headers.get('User-Agent', ''),
            referer=request.headers.get('Referer', ''),
            ctime=get_current_timestamp(),
            shorten=shorten,
            origin="html"
        )
        COUNT_KEY = gen_rediskey("pv", shorten)
        SHORTURL_KEY = gen_rediskey("s", shorten)
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
        finally:
            if res["data"]["status"] in (1, "1"):
                return redirect(res["data"]["long_url"], code=302)
            else:
                return render_template("go.html", title=u"短网址已禁用", keyword=u"禁用", msg=u"由于某些原因，您的短网址已经被系统禁用，您可以尝试解封或重新生成短网址！")
    else:
        return render_template("go.html", title=u"短网址错误", keyword=res["code"], msg=res["msg"])


if __name__ == '__main__':
    from config import GLOBAL
    app.run(host=GLOBAL["Host"], port=int(GLOBAL["Port"]), debug=True)
