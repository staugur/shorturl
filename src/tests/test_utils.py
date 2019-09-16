# -*- coding: utf-8 -*-

import unittest
from utils.tool import url_check, decode_b64, gen_rediskey, shorten_pat, reduction_url


class UtilsTest(unittest.TestCase):

    def test_checkurl(self):
        self.assertTrue(url_check("http://satic.io"))
        self.assertTrue(url_check("https://abc.com"))
        self.assertTrue(url_check("http://192.168.1.1"))
        self.assertTrue(url_check("http://192.168.1.2:8000"))
        self.assertFalse(url_check("http://demo."))
        self.assertTrue(url_check("ftp://ftp.example.com"))

    def test_b64(self):
        self.assertEqual(decode_b64("0"), 0)
        self.assertEqual(decode_b64("a"), 10)
        self.assertEqual(decode_b64("-"), 62)
        self.assertEqual(decode_b64("_"), 63)
        self.assertEqual(decode_b64("10"), 64)

        self.assertRaises(TypeError, decode_b64, 0)
        self.assertRaises(TypeError, decode_b64, [])
        self.assertRaises(TypeError, decode_b64, None)
        self.assertRaises(TypeError, decode_b64, tuple())
        self.assertRaises(TypeError, decode_b64, dict())

    def test_other(self):
        self.assertEqual(gen_rediskey("a", "b"), "satic.shorturl:a:b")
        self.assertEqual(gen_rediskey(1, 2), "satic.shorturl:1:2")

    def test_shorten_pat(self):
        self.assertIsNone(shorten_pat.match("0"))
        self.assertIsNone(shorten_pat.match("-"))
        self.assertIsNone(shorten_pat.match("_"))
        self.assertIsNone(shorten_pat.match("."))
        self.assertIsNone(shorten_pat.match("#"))
        self.assertIsNone(shorten_pat.match("%"))
        self.assertIsNone(shorten_pat.match("*"))
        self.assertIsNone(shorten_pat.match("a#"))
        self.assertIsNone(shorten_pat.match("0@"))
        self.assertIsNone(shorten_pat.match("B&"))
        self.assertIsNone(shorten_pat.match("B"*33))
        self.assertIsNone(shorten_pat.match("_,"))
        self.assertIsNotNone(shorten_pat.match("a1"))
        self.assertIsNotNone(shorten_pat.match("B2"))
        self.assertIsNotNone(shorten_pat.match("SB"))
        self.assertIsNotNone(shorten_pat.match("__"))
        self.assertIsNotNone(shorten_pat.match("_-"))
        self.assertIsNotNone(shorten_pat.match("_."))
        self.assertIsNotNone(shorten_pat.match("c4"))

    def test_func_api(self):
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
