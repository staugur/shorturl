package main

type tplInfo struct {
	Title string
	Code  int16
	Msg   string
}

type apiResp struct {
	code int16
	msg  string
	data map[string]string
}
