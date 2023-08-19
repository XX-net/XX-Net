import sys
import os

current_path = os.path.dirname(os.path.abspath(__file__))
local_path = os.path.abspath(os.path.join(current_path, os.pardir))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
python_path = root_path

sys.path.append(root_path)
sys.path.append(local_path)

noarch_lib = os.path.abspath(os.path.join(python_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

if sys.platform == "win32":
    win32_lib = os.path.abspath(os.path.join(python_path, 'lib', 'win32'))
    sys.path.append(win32_lib)
elif sys.platform.startswith("linux"):
    linux_lib = os.path.abspath(os.path.join(python_path, 'lib', 'linux'))
    sys.path.append(linux_lib)
elif sys.platform == "darwin":
    darwin_lib = os.path.abspath(os.path.join(python_path, 'lib', 'darwin'))
    sys.path.append(darwin_lib)
    extra_lib = "/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python"
    sys.path.append(extra_lib)

import env_info
import xlog
logger = xlog.getLogger("stress")

from front_base.openssl_wrap import SSLContext
from front_base.connect_creator import ConnectCreator
from front_base.check_ip import CheckIp


from x_tunnel.local.tls_relay_front.front import front
from x_tunnel.local.tls_relay_front.config import Config
from x_tunnel.local.tls_relay_front.host_manager import HostManager

module_data_path = os.path.join(env_info.data_path, 'x_tunnel')


def round():
    ip = "127.0.0.1"
    top_domain = "agentnobody.pics"
    wait_time = 0

    config_path = os.path.join(module_data_path, "tls_relay.json")
    config = Config(config_path)

    openssl_context = SSLContext(logger)

    host_fn = os.path.join(module_data_path, "tls_host.json")
    host_manager = HostManager(host_fn)
    connect_creator = ConnectCreator(logger, config, openssl_context, host_manager)
    check_ip = CheckIp(logger, config, connect_creator)

    res = check_ip.check_ip(ip, sni=top_domain, host=top_domain, wait_time=wait_time)
    logger.info("res: %s", res)
    front.stop()


def loop():
    while True:
        round()
        # time.sleep(1)


loop()

