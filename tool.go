/*
   Copyright 2021 Hiroshi.tao

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/

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
		res = apiResp{code: 404, msg: "未发现短网址"}
	}
	return res, nil
}
