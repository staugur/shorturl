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
	"strconv"
	"strings"

	"github.com/go-redis/redis/v8"
)

const version = "0.3.2"

var (
	h           bool
	v           bool
	host        string
	port        int
	redisurl    string
	domainTitle string
	homePage    string

	commitID string // git commit id when building
	built    string // UTC time when building

	rc *redis.Client
)

func init() {
	flag.BoolVar(&h, "h", false, "show help and exit")
	flag.BoolVar(&v, "v", false, "show version and exit")
	flag.StringVar(&host, "host", "0.0.0.0", "http listen host")
	flag.IntVar(&port, "port", 16001, "http listen port")
	flag.StringVar(&redisurl, "redis", "", "redis url, format: redis://:<password>@<host>:<port>/<db>")
	flag.StringVar(&domainTitle, "title", "SaintIC - 诏预开放平台", "domain title suffix")
	flag.StringVar(&homePage, "home", "https://open.saintic.com/openservice/shorturl/", "home page for redirect")
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

func newTplInfo(title string, code int16, msg string) tplInfo {
	return tplInfo{title, code, msg, domainTitle}
}

func startServer() {
	if redisurl == "" {
		redisurl = os.Getenv("shorturl_redis_url")
	}
	if redisurl == "" {
		fmt.Println("No valid redis url")
		return
	}
	envhost := os.Getenv("shorturl_host")
	envport := os.Getenv("shorturl_port")
	if envhost != "" {
		host = envhost
	}
	if envport != "" {
		envport, err := strconv.Atoi(envport)
		if err != nil {
			fmt.Println("Invalid environment shorturl_port")
			return
		}
		port = envport
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
	log.Println("HTTP listen on " + listen)
	log.Fatal(http.ListenAndServe(listen, nil))
}

func bindRoute(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path
	if path == "/" {
		http.Redirect(w, r, homePage, 302)
	} else if strings.Count(path, "/") > 1 {
		renderErrPage(w, newTplInfo("地址错误", 404, "嵌套层级过多"))
	} else {
		shorten := strings.TrimLeft(path, "/")
		res, err := reduction(shorten, rc)
		if err != nil {
			fmt.Println(err)
			renderErrPage(w, newTplInfo("程序错误", 500, err.Error()))
			return
		}
		if res.code == 200 {
			renderRedirect(res, shorten, w, r)

		} else {
			renderErrPage(w, newTplInfo("短网址错误", res.code, res.msg))
		}
	}
}

func renderErrPage(w http.ResponseWriter, data tplInfo) {
	tpl := `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <meta name="author" content="staugur">
    <title>{{ .Title }} | {{ .DomainTitle }}</title>
    <link href="https://static.saintic.com/cdn/images/favicon-32.png" rel="icon" type="image/x-icon">
    <link href="https://static.saintic.com/cdn/images/favicon-32.png" rel="shortcut icon" type="image/x-icon">
    <style>
        *{font-family:"Helvetica Neue",Helvetica,Arial,"PingFang SC","Hiragino Sans GB","Heiti SC",MicrosoftYaHei,"WenQuanYi Micro Hei",sans-serif;margin:0;font-weight:lighter;text-decoration:none;text-align:center;line-height:2.2em}body,html{height:100%}h1{font-size:100px;line-height:1em}table{width:100%;height:100%;border:0}
    </style>
</head>
<body>
    <table cellspacing="0" cellpadding="0">
        <tr><td><table cellspacing="0" cellpadding="0">
            <tr><td><h1>{{ .Code }}</h1><h3>-- 哎吆 --</h3><p>{{ .Msg }}<br><a href="/">返回主页</a></p></td></tr>
        </table></td></tr>
    </table>
</body>
</html>`
	tmpl, err := template.New("errpage").Parse(tpl)
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
		renderErrPage(w, newTplInfo("短网址已禁用", 404, "由于某些原因，您的短网址已经被系统禁用，您可以尝试解封或重新生成短网址！"))
	}
}
