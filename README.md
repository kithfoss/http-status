# http-status

Look up what an HTTP status code means.

```
http-status 404
http-status "not found"
http-status --all
http-status --category 5xx
echo 503 | http-status
```

## Install

```bash
bash install.sh           # installs to /usr/local/bin/http-status
bash install.sh ~/bin/http-status  # custom path
```

## Usage

**Look up a code:**
```
$ http-status 404
404 Not Found
  The server cannot find the requested resource.
  [4xx Client Error]
```

**Search by name or description:**
```
$ http-status "not found"
404 Not Found
  The server cannot find the requested resource.
  [4xx Client Error]

$ http-status timeout
408 Request Timeout
  The server closed the connection because the client took too long to send a request.
  [4xx Client Error]

504 Gateway Timeout
  The upstream server failed to respond in time.
  [5xx Server Error]
```

**List by category:**
```
$ http-status --category 5xx
── 5xx Server Error ──
  500  Internal Server Error
  501  Not Implemented
  502  Bad Gateway
  503  Service Unavailable
  ...
```

**List all codes:**
```
$ http-status --all
── 1xx Informational ──
  100  Continue
  ...
```

**JSON output:**
```
$ http-status 200 --json
{"code": 200, "name": "OK", "description": "The request succeeded.", "category": "2xx Success"}

$ http-status --all --category 2xx --json
[{"code": 200, ...}, {"code": 201, ...}, ...]
```

**Stdin:**
```
$ echo 503 | http-status
503 Service Unavailable
  The server is not ready to handle the request — overloaded or down for maintenance.
  [5xx Server Error]
```

## Exit codes

| Exit | Meaning |
|------|---------|
| 0    | Code found and displayed |
| 1    | Code unknown, no search match, or invalid input |

## Flags

| Flag | Description |
|------|-------------|
| `--all`, `-a` | List all known status codes |
| `--category Nxx`, `-c` | Filter to a category (1xx–5xx) |
| `--json`, `-j` | Output as JSON |

## Coverage

Covers all codes from RFC 9110 plus common extensions (WebDAV, rate limiting, legal restrictions, Easter eggs).

## Requirements

Python 3.8+. No external dependencies.

## License

Free. MIT.
