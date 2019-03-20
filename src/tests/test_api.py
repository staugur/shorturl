# -*- coding: utf-8 -*-

import unittest
from main import app
from utils.tool import url_check, gen_rediskey, get_redis_connect
from apis.shorturl import shorten_url, reduction_url


class ApiTest(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_errindex(self):
        rv = self.client.get("/xxxxxxx")
        assert "短网址错误" in rv.data

    def test_web_api(self):
        with self.client as c:
            long_url = "http://sainic.com"
            rv = c.post("/api/v1/?Action=shorten", data=dict(long_url=long_url))
            data = rv.get_json()
            shorten = data["data"]["shorten"]
            short_url = data["data"]["short_url"]
            self.assertIsInstance(data, dict)
            self.assertEqual(data["code"], 0)
            self.assertTrue(url_check(short_url))
            SHORTURL_KEY = gen_rediskey("s", shorten)

            rv2 = c.post("/api/v1/?Action=reduction", data=dict(short_url=short_url))
            data2 = rv2.get_json()
            self.assertIsInstance(data2, dict)
            self.assertEqual(long_url, data2["data"]["long_url"])
            self.assertEqual(shorten, data2["data"]["shorten"])

            get_redis_connect.hset(SHORTURL_KEY, "status", 0)
            rv3 = c.get("/" + shorten)
            assert "短网址已禁用" in rv3.data

    def test_func_api(self):
        res = shorten_url("abc")
        self.assertEqual(res["code"], 20001)

        long_url = "https://open.sainic.com"
        res = shorten_url(long_url)
        self.assertEqual(res["code"], 0)
        shorten = res["data"]["shorten"]

        res = reduction_url(shorten)
        self.assertEqual(res["code"], 404)

        res = reduction_url("abc", parseUrl=True)
        self.assertEqual(res["code"], 20001)

        res = reduction_url("abc", parseUrl=False)
        self.assertEqual(res["code"], 404)

        res = reduction_url("http://abc.", parseUrl=True)
        self.assertEqual(res["code"], 20001)

        res = reduction_url("http://go.satic.io/xxxx", parseUrl=True)
        self.assertEqual(res["code"], 404)


if __name__ == '__main__':
    unittest.main()
