package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"html/template"
	"log"
	"net/http"
	"os"
	"strings"

	"github.com/go-redis/redis/v8"
)

const version = "0.3.0"

var (
	h        bool
	v        bool
	host     string
	port     int
	redisurl string

	commitID string // git commit id when building
	built    string // UTC time when building

	rc *redis.Client
)

func init() {
	flag.BoolVar(&h, "h", false, "show help and exit")
	flag.BoolVar(&v, "v", false, "show version and exit")
	flag.StringVar(&host, "host", "127.0.0.1", "set http listen host")
	flag.IntVar(&port, "port", 16001, "set http listen port")
	flag.StringVar(&redisurl, "redis", "", "set redis url")
}

func main() {
	flag.Parse()
	if h {
		flag.Usage()
	} else if v {
		fmt.Printf("v%s commit/%s built/%s\n", version, commitID, built)
	} else {
		startServer()
	}
}

func startServer() {
	if redisurl == "" {
		redisurl = os.Getenv("shorturl_redis_url")
	}
	if redisurl == "" {
		fmt.Println("No valid redis url")
		return
	}
	opt, err := redis.ParseURL(redisurl)
	if err != nil {
		fmt.Println(err)
		return
	}
	// init redis connect client
	rc = redis.NewClient(opt)
	http.HandleFunc("/", bindRoute)
	listen := fmt.Sprintf("%s:%d", host, port)
	log.Println("Http listen on " + listen)
	log.Fatal(http.ListenAndServe(listen, nil))
}

func bindRoute(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path

	fmt.Println(path)
	fmt.Println(r.RemoteAddr)
	fmt.Println(r.Header)

	if path == "/" {
		url := "https://open.saintic.com/openservice/shorturl/"
		http.Redirect(w, r, url, 302)
	} else if strings.Count(path, "/") > 1 {
		renderErrPage(w, tplInfo{"地址错误", 404, "嵌套层级过多"})
	} else {
		shorten := strings.TrimLeft(path, "/")
		fmt.Println(shorten)
		res, err := reduction(shorten, rc)
		fmt.Println(res)
		if err != nil {
			fmt.Println(err)
			renderErrPage(w, tplInfo{"程序错误", 500, err.Error()})
			return
		}
		if res.code == 200 {
			renderRedirect(res, shorten, w, r)

		} else {
			renderErrPage(w, tplInfo{"短网址错误", res.code, res.msg})
		}
	}
}

func renderErrPage(w http.ResponseWriter, data tplInfo) {
	tmpl, err := template.ParseFiles("./error.tmpl")
	if err != nil {
		fmt.Println("create template failed, err:", err)
		return
	}
	tmpl.Execute(w, data)
}

func renderRedirect(res apiResp, shorten string, w http.ResponseWriter, r *http.Request) {
	ip := r.Header.Get("X-Real-Ip")
	if ip == "" {
		ip = strings.Split(r.RemoteAddr, ":")[0]
	}
	accessData := map[string]string{
		"ip":      ip,
		"agent":   r.Header.Get("User-Agent"),
		"referer": r.Header.Get("Referer"),
		"ctime":   fmt.Sprintf("%d", nowTimestamp()),
		"shorten": shorten,
		"origin":  "html",
	}
	accessJSON, _ := json.Marshal(accessData)
	countKey := genRedisKey("pv", shorten)
	shorturlKey := genRedisKey("s", shorten)
	globalInfoKey := genRedisKey("global")

	ctx := context.Background()
	pipe := rc.TxPipeline()
	pipe.HIncrBy(ctx, globalInfoKey, "reduction", 1)
	pipe.HSet(ctx, shorturlKey, "atime", nowTimestamp())
	pipe.RPush(ctx, countKey, accessJSON)
	pipe.Exec(ctx)

	if res.data["status"] == "1" {
		http.Redirect(w, r, res.data["longurl"], 302)
	} else {
		renderErrPage(w, tplInfo{"短网址已禁用", 400, "由于某些原因，您的短网址已经被系统禁用，您可以尝试解封或重新生成短网址！"})
	}
}
