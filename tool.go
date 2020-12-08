package main

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/go-redis/redis/v8"
)

func genRedisKey(args ...string) string {
	return "satic.shorturl:" + strings.Join(args, ":")
}

func nowTimestamp() int64 {
	return time.Now().Unix()
}

func reduction(shorten string, rc *redis.Client) (res apiResp, err error) {
	ctx := context.Background()
	data, err := rc.HGetAll(ctx, genRedisKey("s", shorten)).Result()
	if err != nil {
		fmt.Println(err)
		return
	}
	if longurl, ok := data["long_url"]; ok {
		res = apiResp{200, "ok", map[string]string{
			"longurl":  longurl,
			"shorten":  shorten,
			"status":   data["status"],
			"safe":     data["safe"],
			"realname": data["realname"],
		}}
	} else {
		res = apiResp{code: 404, msg: "Not found shorten"}
	}
	return res, nil
}
