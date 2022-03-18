# coding:utf-8
import json
import os
import ctypes
import collections
import locale
import subprocess

from launcher.config import get_language
from config import app_name, config
from xlog import getLogger
xlog = getLogger("launcher")

current_path = os.path.dirname(os.path.abspath(__file__))
version_path = os.path.abspath(os.path.join(current_path, os.path.pardir))
root_path = os.path.abspath(os.path.join(version_path, os.path.pardir, os.path.pardir))
data_path = os.path.join(root_path, 'data')


class Win10PortReserveSolution(object):
    def __init__(self):
        self.service_ports = self.get_service_ports()

    def check_and_resolve(self):
        if self.is_port_reserve_conflict():
            language = get_language()
            if language == "zh_CN":
                res = self.notify("端口被系统保留", "服务端口被系统保留，是否修改系统保留端口？")
            else:
                res = self.notify("Service Port was Reserved",
                                  "The service ports was reserved by system, Do you want to change the served port?")

            if res == 1:  # Clicked "Yes"
                self.change_reserved_port_range()

                if language == "zh_CN":
                    self.notify("请重启电脑", "系统保留端口已经修改，请重启电脑.")
                else:
                    self.notify("Computer Restart Required",
                                "System port reserve range changed, please restart your computer to make chage.")
                return False

        return True

    @staticmethod
    def run_cmd(cmd):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = proc.stdout
        lines = out.readlines()
        return lines

    @staticmethod
    def get_config_value(fn, key, default_value):
        if not os.path.isfile(fn):
            return default_value

        try:
            with open(fn, "r") as fd:
                dat = json.load(fd)
                value = dat.get(key, default_value)
                return value
        except Exception as e:
            xlog.warn("load config %s except:%r", fn, e)
            return default_value

    def get_service_ports(self):
        web_console_port = config.control_port
        smart_router_config_fn = os.path.join(data_path, "smart_router", "config.json")
        smart_router_socks_port = self.get_config_value(smart_router_config_fn, "proxy_port", 8086)
        smart_router_dns_port = self.get_config_value(smart_router_config_fn, "dns_backup_port", 8083)

        x_tunnel_config_fn = os.path.join(data_path, "x_tunnel", "client.json")
        x_tunnel_port = self.get_config_value(x_tunnel_config_fn, "socks_port", 1080)

        return [web_console_port, smart_router_socks_port, smart_router_dns_port, x_tunnel_port]

    def is_port_reserve_conflict(self):
        cmd = "netsh int ipv4 show excludedportrange protocol=tcp"
        lines = self.run_cmd(cmd)
        for line in lines:
            if not line.startswith(b" "):
                continue

            range_str = line.split()
            try:
                p0 = int(range_str[0])
                p1 = int(range_str[1])
            except Exception as e:
                xlog.warn("parse reserve port fail, line:%s, e:%r", line, e)
                continue

            # xlog.debug("range:%d - %d", p0, p1)
            for port in self.service_ports:
                if p0 < port < p1:
                    return True

        return False

    def search_port_range(self):
        port_number = 16384
        for port_start in range(10000, 45000, 5000):
            port_end = port_start + port_number
            acceptable = True
            for port in self.service_ports:
                if port_start <= port <= port_end:
                    acceptable = False
                    break

            if acceptable:
                return [port_start, port_number]

    def change_reserved_port_range(self):
        ports = self.search_port_range()
        if not ports:
            xlog.warn("Can't found acceptable ports")
            return

        exec = b"netsh"
        args = b"int ipv4 set dynamic tcp start=%d num=%d" % (ports[0], ports[1])
        import win32elevate
        win32elevate.elevateAdminRun(args, exec)

    @staticmethod
    def notify(title="Title", msg="msg"):
        import ctypes
        res = ctypes.windll.user32.MessageBoxW(None, msg, title, 1)
        # Yes:1 No:2
        return res


def get_process_list():
    process_list = []
    if os.name != "nt":
        return process_list

    Process = collections.namedtuple("Process", "filename name")
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    lpidProcess = (ctypes.c_ulong * 1024)()
    cbNeeded = ctypes.c_ulong()

    ctypes.windll.psapi.EnumProcesses(ctypes.byref(lpidProcess), ctypes.sizeof(lpidProcess), ctypes.byref(cbNeeded))
    nReturned = cbNeeded.value // ctypes.sizeof(cbNeeded)
    pidProcess = [i for i in lpidProcess][:nReturned]
    has_queryimage = hasattr(ctypes.windll.kernel32, "QueryFullProcessImageNameA")

    for pid in pidProcess:
        hProcess = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, 0, pid)
        if hProcess:
            modname = ctypes.create_string_buffer(2048)
            count = ctypes.c_ulong(ctypes.sizeof(modname))
            if has_queryimage:
                ctypes.windll.kernel32.QueryFullProcessImageNameA(hProcess, 0, ctypes.byref(modname),
                                                                  ctypes.byref(count))
            else:
                ctypes.windll.psapi.GetModuleFileNameExA(hProcess, 0, ctypes.byref(modname), ctypes.byref(count))

            path = modname.value.decode("mbcs")
            filename = os.path.basename(path)
            name, ext = os.path.splitext(filename)
            process_list.append(Process(filename=filename, name=name))
            ctypes.windll.kernel32.CloseHandle(hProcess)

    return process_list


_blacklist = {
    # (u"测试", "Test"): [
    #    u"汉字测试",
    #    "explorer",
    #    "Python",
    # ],
    ("渣雷", "Xhunder"): [
        "ThunderPlatform",
        "ThunderFW",
        "ThunderLiveUD",
        "ThunderService",
        "ThunderSmartLimiter",
        "ThunderWelcome",
        "DownloadSDKServer",
        "LimitingDriver",
        "LiteUD",
        "LiteViewBundleInst",
        "XLNXService ",
        "XLServicePlatform",
        "XLGameBoot",
        "XMPBoot",
    ],
    ("百毒", "Baidu"): [
        "BaiduSdSvc",
        "BaiduSdTray",
        "BaiduSd",
        "BaiduAn",
        "bddownloader",
        "baiduansvx",
    ],
    ("流氓 360", "360"): [
        "360sd",
        "360tray",
        "360Safe",
        "safeboxTray",
        "360safebox",
        "360se",
    ],
    ("疼讯复制机", "Tencent"): [
        "QQPCRTP",
        "QQPCTray",
        "QQProtect",
    ],
    ("金山", "Kingsoft"): [
        "kismain",
        "ksafe",
        "KSafeSvc",
        "KSafeTray",
        "KAVStart",
        "KWatch",
        "KMailMon",
    ],
    ("瑞星", "Rising"): [
        "rstray",
        "ravmond",
        "rsmain",
    ],
    ("江民", "Jiangmin"): [
        "UIHost",
        "KVMonXP",
        "kvsrvxp",
        "kvxp",
    ],
    ("2345 不安全", "2345"): [
        "2345MPCSafe",
    ],
    ("天网防火墙", "SkyNet"): [
        "PFW",
    ],
}

_title = app_name + " 兼容性建议", app_name + " compatibility suggest"
_notice = (
    "某些软件可能和 " + app_name + " 存在冲突，导致 CPU 占用过高或者无法正常使用。"
    "如有此现象建议暂时退出以下软件来保证" + app_name + "正常运行：\n",
    "Some software may conflict with This app, "
    "causing the CPU to be overused or not working properly."
    "If this is the case, it is recommended to temporarily quit the following "
    "software to ensure " + app_name + " running:\n",
    "\n你可以在配置页面关闭此建议。",
    "\nYou can close this suggestion on the configuration page.",
)


def main():
    if os.name != "nt":
        return

    lang = 0 if locale.getdefaultlocale()[0] == "zh_CN" else 1
    blacklist = {}
    for k, v in list(_blacklist.items()):
        for name in v:
            blacklist[name] = k[lang]

    processlist = dict((process.name.lower(), process) for process in get_process_list())
    softwares = [name for name in blacklist if name.lower() in processlist]

    if softwares:
        displaylist = {}
        for software in softwares:
            company = blacklist[software]
            if company not in displaylist:
                displaylist[company] = []
            displaylist[company].append(software)

        displaystr = [_notice[lang], ]
        for company, softwares in list(displaylist.items()):
            displaystr.append("    %s: \n\t%s" % (company,
                                                  "\n\t".join(
                                                      processlist[name.lower()].filename for name in softwares)))

        title = _title[lang]
        displaystr.append(_notice[lang + 2])
        error = "\n".join(displaystr)

        ctypes.windll.user32.MessageBoxW(None, error, title, 48)


if "__main__" == __name__:
    if os.name != "nt":
        import sys

        sys.exit(0)
    main()
