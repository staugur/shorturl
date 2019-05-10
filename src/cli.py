#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    cli
    ~~~~~~~~~~~~~~

    Cli Entrance

    :copyright: (c) 2018 by staugur.
    :license: BSD, see LICENSE for more details.
"""

import click
from utils.tool import gen_rediskey, get_redis_connect, encode_b64, logger


if __name__ == "__main__":

    @click.group()
    def cli():
        pass

    @cli.command()
    @click.confirmation_option(prompt=u'确定要将旧数据转换吗？')
    def change():
        """转换旧数据"""
        data = get_redis_connect.keys(gen_rediskey("s", "*"))
        pipe = get_redis_connect.pipeline()
        INDEX_SHORTEN_KEY = gen_rediskey("index")
        for i in data:
            pipe.sadd(INDEX_SHORTEN_KEY, i)
            d = get_redis_connect.hgetall(i)
            shorten = d["jid"] if d["jid"] else encode_b64(d["sid"])
            pipe.hset(i, 'shorten', shorten)
        try:
            pipe.execute()
        except Exception as e:
            logger.error(e, exc_info=True)
        else:
            click.echo("Change is ok.")

    @cli.command()
    def query():
        """查询所有短网址"""
        INDEX_SHORTEN_KEY = gen_rediskey("index")
        for key in get_redis_connect.smembers(INDEX_SHORTEN_KEY):
            print(get_redis_connect.hgetall(key))

    @cli.command()
    @click.argument('shorten')
    def statistics(shorten):
        """短网址数据统计"""
        SHORTURL_KEY = gen_rediskey("s", shorten)
        COUNT_KEY = gen_rediskey("pv", shorten)
        data = get_redis_connect.hgetall(SHORTURL_KEY)
        pv = get_redis_connect.lrange(COUNT_KEY, 0, -1)
        print "创建数据：\n",data,"\n访问数据："
        for i in pv:
            print(i)

    cli()
