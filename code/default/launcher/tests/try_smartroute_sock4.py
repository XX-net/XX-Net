import simple_http_client


def smart_route_proxy_socks4():
    proxy = "socks4://localhost:8086"
    res = simple_http_client.request("GET", "https://github.com/", proxy=proxy, timeout=1000)
    return res


if __name__ == "__main__":
    smart_route_proxy_socks4()
