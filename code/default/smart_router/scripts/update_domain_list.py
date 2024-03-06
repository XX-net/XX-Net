import os
import sys
from os.path import join

current_path = os.path.dirname(os.path.abspath(__file__))
local_path = os.path.abspath( os.path.join(current_path, os.pardir, "local"))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
noarch_path = join(root_path, "lib", "noarch")
sys.path.append(noarch_path)


import simple_http_client
import utils


def download_list(url):
    res = simple_http_client.request("GET", url)
    content = res.text
    return utils.to_str(content)


def parse_list(content):
    black_suffix = []
    black_keyword = []
    black_ipmask = []
    for line in content.split():
        if not line or line.startswith("#"):
            continue

        if line.startswith("DOMAIN-SUFFIX,") and line.endswith(",Proxy"):
            _, suffix, _ = line.split(",")[0:3]
            black_suffix.append(suffix)

        if line.startswith("DOMAIN-KEYWORD,") and line.endswith(",Proxy"):
            _, keyword, _ = line.split(",")[0:3]
            black_keyword.append(keyword)

        if line.startswith("IP-CIDR,") and line.endswith(",Proxy"):
            _, ipmask, _ = line.split(",")[0:3]
            black_ipmask.append(ipmask)

    black_suffix.sort()
    black_keyword.sort()
    black_ipmask.sort()

    return black_suffix, black_keyword, black_ipmask


def update_blacklist():
    # url = "https://github.com/Johnshall/Shadowrocket-ADBlock-Rules-Forever/raw/release/sr_top500_banlist.conf"
    url = "https://raw.githubusercontent.com/Johnshall/Shadowrocket-ADBlock-Rules-Forever/release/sr_top500_banlist.conf"
    content = download_list(url)
    black_suffix, black_keyword, black_ipmask = parse_list(content)

    with open(join(local_path, "gfw_black_list.txt"), "w") as fd:
        fd.write("\r\n".join(black_suffix))

    with open(join(local_path, "gfw_black_keywords.txt"), "w") as fd:
        fd.write("\r\n".join(black_keyword))


if __name__ == "__main__":
    update_blacklist()
