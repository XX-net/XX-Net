
import os
import sys
import time

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
top_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir))
data_path = os.path.abspath( os.path.join(top_path, 'data', 'gae_proxy'))

python_path = os.path.abspath(os.path.join(root_path, 'python27', '1.0'))

noarch_lib = os.path.abspath(os.path.join(python_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

if sys.platform == "win32":
    win32_lib = os.path.abspath(os.path.join(python_path, 'lib', 'win32'))
    sys.path.append(win32_lib)
elif sys.platform.startswith("linux"):
    linux_lib = os.path.abspath(os.path.join(python_path, 'lib', 'linux'))
    sys.path.append(linux_lib)


from xlog import getLogger
log_file = os.path.join(data_path, "ipv6_tunnel.log")
xlog = getLogger("gae_proxy", file_name=log_file)


def main():
    for i in range(0, 10):
        xlog.debug("log %d", i)
        time.sleep(1)


if __name__ == '__main__':
    main()