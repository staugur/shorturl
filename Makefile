.PHONY: help

BINARY=shorturl
CommitID=$(shell git log --pretty=format:"%h" -1)
Built=$(shell date -u "+%Y-%m-%dT%H:%M:%SZ")
LDFLAGS=-ldflags "-s -w -X main.commitID=${CommitID} -X main.built=${Built}"

help:
	@echo "  make clean  - Remove binaries and vim swap files"
	@echo "  make gotool - Run go tool 'fmt' and 'vet'"
	@echo "  make build  - Compile go code and generate binary file"
	@echo "  make dev    - Run dev server"

gotool:
	go fmt ./
	go vet ./

build: gotool
	go build ${LDFLAGS} -o $(BINARY) && chmod +x $(BINARY)

docker:
	docker build -t staugur/shorturl .

dev:
	@echo Starting service...
	@go run ./
