# -*- coding: utf-8 -*-
"""
    config
    ~~~~~~~~~~~~~~

    The program configuration file, the preferred configuration item, reads the system environment variable first.

    :copyright: (c) 2018 by staugur.
    :license: MIT, see LICENSE for more details.
"""

from os import getenv

GLOBAL = {

    "ProcessName": "ShortUrl",
    # 自定义进程名.

    "Host": getenv("shorturl_host", "127.0.0.1"),
    # 监听地址

    "Port": getenv("shorturl_port", 16001),
    # 监听端口

    "LogLevel": getenv("shorturl_loglevel", "DEBUG"),
    # 应用日志记录级别, 依次为 DEBUG, INFO, WARNING, ERROR, CRITICAL.
}


REDIS = getenv("shorturl_redis_url") or getenv("pac_redis_url")
# Redis数据库连接信息，格式：
# redis://[:password]@host:port/db
# host,port必填项,如有密码,记得密码前加冒号,比如redis://localhost:6379/0
