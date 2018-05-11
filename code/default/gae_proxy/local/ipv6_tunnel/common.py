import os
import shlex
import subprocess
from .pteredor import teredo_prober

from xlog import getLogger
xlog = getLogger("gae_proxy")

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data', "gae_proxy"))
if not os.path.isdir(data_path):
    data_path = current_path

log_file = os.path.join(data_path, "ipv6_tunnel.log")

if os.path.isfile(log_file):
    os.remove(log_file)


class Log(object):
    def __init__(self):
        self.fd = open(log_file, "w")

    def write(self, content):
        self.fd.write(content + "\n")
        self.fd.flush()

    def close(self):
        self.fd.close()


def new_pteredor(clear_log=True):
    if clear_log and os.path.isfile(log_file):
        try:
            os.remove(log_file)
        except Exception as e:
            xlog.warn("remove %s fail:%r", log_file, e)

    prober = teredo_prober()
    log = Log()
    log.write('qualified: %s\nNAT type: %s' % (prober.qualified, prober.nat_type))
    log.close()
    return prober


def test_teredo():
    qualified = new_pteredor().qualified
    return 'teredo test result is %s.' % ('qualified' if qualified else 'unknown')


def best_server(clear_log=True):
    prober = new_pteredor(clear_log)
    prober.qualified = True
    server_list = prober.eval_servers()
    for qualified, server, _, _ in server_list:
        if qualified:
            return server[0]
    xlog.warning('no server detected, return default: teredo.remlab.net.')
    log = Log()
    log.write('no server detected, return default: teredo.remlab.net.')
    log.close()
    return "teredo.remlab.net"


def run(cmd):
    cmd = shlex.split(cmd)

    try:
        # hide console in MS windows
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        #out = subprocess.check_output(cmd, startupinfo=startupinfo)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, startupinfo=startupinfo)
        out, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            return out + "\n retcode:%s\n unused_err:%s\n" % (retcode, unused_err)
    except Exception as e:
        out = "Exception:%r" % e

    return out


def run_cmds(cmds):
    log = Log()
    cmd_pl = cmds.split("\n")
    outs = []
    for cmd in cmd_pl:
        if not cmd:
            continue

        if cmd.startswith("#"):
            log.write("%s" % cmd)
            continue

        log.write("\n>: %s\n------------------------------------" % cmd)
        out = run(cmd)
        log.write(out)
        outs.append(out)
    log.close()
    return "\r\n".join(outs)


def get_line_value(r, n):
    rls = r.split("\r\n")
    if len(rls) < n + 1:
        return None

    lp = rls[n].split(":")
    if len(lp) < 2:
        return None

    value = lp[1].strip()
    return value
