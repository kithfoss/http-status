#!/usr/bin/env python3
"""
http-status — Look up what an HTTP status code means.

Usage:
  http-status 404
  http-status "not found"
  http-status --all
  http-status --category 4xx
  echo 503 | http-status
"""

import argparse
import json
import sys

# RFC 9110 + common extensions
_CODES = {
    # 1xx Informational
    100: ("Continue", "The client should continue the request or ignore the response if done."),
    101: ("Switching Protocols", "The server is switching protocols as requested by the client."),
    102: ("Processing", "The server has received and is processing the request, but no response is available yet."),
    103: ("Early Hints", "Used to return some response headers before final HTTP message."),
    # 2xx Success
    200: ("OK", "The request succeeded."),
    201: ("Created", "The request succeeded and a new resource was created."),
    202: ("Accepted", "The request has been received but not yet acted upon."),
    203: ("Non-Authoritative Information", "The returned metadata is from a local or third-party copy, not the origin."),
    204: ("No Content", "The request succeeded but there is no content to send back."),
    205: ("Reset Content", "The request succeeded; the client should reset the document view."),
    206: ("Partial Content", "The server is delivering only part of the resource due to a range header."),
    207: ("Multi-Status", "Multiple status codes might be appropriate for sub-requests (WebDAV)."),
    208: ("Already Reported", "Members of a DAV binding have already been enumerated (WebDAV)."),
    226: ("IM Used", "The server fulfilled a GET request and the response is a result of instance-manipulations."),
    # 3xx Redirection
    300: ("Multiple Choices", "The request has more than one possible response; the user should choose."),
    301: ("Moved Permanently", "The URL has been permanently changed to the one given in Location."),
    302: ("Found", "The URL has been temporarily changed; continue using the original for future requests."),
    303: ("See Other", "The response to the request can be found at the URL in Location using GET."),
    304: ("Not Modified", "The resource has not been modified since the version specified in headers; use cache."),
    305: ("Use Proxy", "Deprecated. The resource must be accessed through a proxy given in Location."),
    307: ("Temporary Redirect", "The URL is temporarily different; the same method must be used for the new request."),
    308: ("Permanent Redirect", "The resource is now permanently at the URL in Location; same method must be used."),
    # 4xx Client Errors
    400: ("Bad Request", "The server cannot process the request due to a client error (malformed syntax, etc.)."),
    401: ("Unauthorized", "Authentication is required and has failed or not been provided."),
    402: ("Payment Required", "Reserved for future use; sometimes used for digital payment requirements."),
    403: ("Forbidden", "The client does not have permission to access this resource."),
    404: ("Not Found", "The server cannot find the requested resource."),
    405: ("Method Not Allowed", "The request method is not supported for this resource."),
    406: ("Not Acceptable", "No content matching the Accept headers was found."),
    407: ("Proxy Authentication Required", "Authentication with the proxy is required."),
    408: ("Request Timeout", "The server closed the connection because the client took too long to send a request."),
    409: ("Conflict", "The request conflicts with the current state of the server."),
    410: ("Gone", "The content has been permanently deleted from the server."),
    411: ("Length Required", "The server requires the Content-Length header field."),
    412: ("Precondition Failed", "The server does not meet one of the preconditions in the request headers."),
    413: ("Content Too Large", "The request body is larger than limits defined by the server."),
    414: ("URI Too Long", "The URI requested by the client is longer than the server is willing to interpret."),
    415: ("Unsupported Media Type", "The media format is not supported by this server."),
    416: ("Range Not Satisfiable", "The range specified by the Range header cannot be fulfilled."),
    417: ("Expectation Failed", "The expectation indicated by the Expect header cannot be met."),
    418: ("I'm a Teapot", "The server refuses to brew coffee because it is a teapot. (RFC 2324 — April Fools)"),
    421: ("Misdirected Request", "The request was directed at a server that cannot produce a response."),
    422: ("Unprocessable Content", "The request was well-formed but had semantic errors."),
    423: ("Locked", "The resource is locked (WebDAV)."),
    424: ("Failed Dependency", "The request failed because a previous request failed (WebDAV)."),
    425: ("Too Early", "The server is unwilling to risk processing a request that might be replayed."),
    426: ("Upgrade Required", "The client should switch to a different protocol."),
    428: ("Precondition Required", "The server requires the request to be conditional."),
    429: ("Too Many Requests", "The user has sent too many requests in a given amount of time (rate limiting)."),
    431: ("Request Header Fields Too Large", "The server is unwilling to process the request because headers are too large."),
    451: ("Unavailable For Legal Reasons", "The resource cannot legally be provided (censorship, court order, etc.)."),
    # 5xx Server Errors
    500: ("Internal Server Error", "The server encountered an unexpected condition that prevented it from fulfilling the request."),
    501: ("Not Implemented", "The request method is not supported by the server."),
    502: ("Bad Gateway", "The server received an invalid response from an upstream server."),
    503: ("Service Unavailable", "The server is not ready to handle the request — overloaded or down for maintenance."),
    504: ("Gateway Timeout", "The upstream server failed to respond in time."),
    505: ("HTTP Version Not Supported", "The HTTP version used in the request is not supported by the server."),
    506: ("Variant Also Negotiates", "The server has a configuration error in content negotiation."),
    507: ("Insufficient Storage", "The server cannot store the representation needed to complete the request (WebDAV)."),
    508: ("Loop Detected", "The server detected an infinite loop while processing the request (WebDAV)."),
    510: ("Not Extended", "Further extensions to the request are required for the server to fulfill it."),
    511: ("Network Authentication Required", "The client needs to authenticate to gain network access."),
}

_CATEGORY_NAMES = {
    1: "Informational",
    2: "Success",
    3: "Redirection",
    4: "Client Error",
    5: "Server Error",
}


def _category(code: int) -> str:
    n = code // 100
    name = _CATEGORY_NAMES.get(n, "Unknown")
    return f"{n}xx {name}"


def _format_one(code: int, name: str, desc: str, *, json_out: bool = False):
    if json_out:
        return json.dumps({
            "code": code,
            "name": name,
            "description": desc,
            "category": _category(code),
        })
    cat = _category(code)
    return f"{code} {name}\n  {desc}\n  [{cat}]"


def _fuzzy_search(query: str) -> list[tuple[int, str, str]]:
    """Find codes whose name contains the query (case-insensitive)."""
    q = query.lower()
    return [
        (code, name, desc)
        for code, (name, desc) in _CODES.items()
        if q in name.lower() or q in desc.lower()
    ]


def _parse_category_filter(cat_str: str) -> int | None:
    """Parse '4xx', '4', '4XX' → 4."""
    s = cat_str.lower().rstrip("x")
    try:
        n = int(s)
        if 1 <= n <= 5:
            return n
    except ValueError:
        pass
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="http-status",
        description="Look up what an HTTP status code means.",
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="HTTP status code (e.g. 404) or text to search (e.g. 'not found')",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="List all known status codes",
    )
    parser.add_argument(
        "--category", "-c",
        metavar="Nxx",
        help="Filter to a category: 1xx, 2xx, 3xx, 4xx, or 5xx",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        dest="json_out",
        help="Output as JSON",
    )
    args = parser.parse_args()

    json_out = args.json_out

    # --all or --category without a query: list mode
    if args.all or (args.category and not args.query):
        cat_filter = None
        if args.category:
            cat_filter = _parse_category_filter(args.category)
            if cat_filter is None:
                print(f"http-status: unrecognized category '{args.category}' — use 1xx, 2xx, 3xx, 4xx, or 5xx", file=sys.stderr)
                return 1

        results = [
            (code, name, desc)
            for code, (name, desc) in sorted(_CODES.items())
            if cat_filter is None or code // 100 == cat_filter
        ]

        if json_out:
            out = [
                {"code": c, "name": n, "description": d, "category": _category(c)}
                for c, n, d in results
            ]
            print(json.dumps(out, indent=2))
        else:
            current_cat = None
            for code, name, desc in results:
                cat = _category(code)
                if cat != current_cat:
                    if current_cat is not None:
                        print()
                    print(f"── {cat} ──")
                    current_cat = cat
                print(f"  {code}  {name}")
        return 0

    # Determine query: argument or stdin
    query = args.query
    if query is None:
        if sys.stdin.isatty():
            parser.print_help()
            return 1
        query = sys.stdin.read().strip()

    if not query:
        print("http-status: no query provided", file=sys.stderr)
        return 1

    # Try numeric lookup first
    if query.isdigit():
        code = int(query)
        if code in _CODES:
            name, desc = _CODES[code]
            print(_format_one(code, name, desc, json_out=json_out))
            return 0
        else:
            # Unknown code — show category if valid range
            cat_n = code // 100
            if 1 <= cat_n <= 5:
                cat = _category(code)
                if json_out:
                    print(json.dumps({"code": code, "name": None, "description": None, "category": cat, "known": False}))
                else:
                    print(f"{code}: unrecognized code in [{cat}]")
            else:
                if json_out:
                    print(json.dumps({"code": code, "name": None, "description": None, "category": None, "known": False}))
                else:
                    print(f"{code}: not a valid HTTP status code")
            return 1

    # Text search
    matches = _fuzzy_search(query)
    if not matches:
        print(f"http-status: no match for '{query}'", file=sys.stderr)
        return 1

    # Apply --category filter if given alongside text query
    if args.category:
        cat_filter = _parse_category_filter(args.category)
        if cat_filter is not None:
            matches = [(c, n, d) for c, n, d in matches if c // 100 == cat_filter]
        if not matches:
            print(f"http-status: no match for '{query}' in {args.category}", file=sys.stderr)
            return 1

    if json_out:
        out = [
            {"code": c, "name": n, "description": d, "category": _category(c)}
            for c, n, d in sorted(matches)
        ]
        print(json.dumps(out, indent=2))
    else:
        for code, name, desc in sorted(matches):
            print(_format_one(code, name, desc))
            if len(matches) > 1:
                print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
