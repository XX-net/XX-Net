import os

gp_regpol_file = os.environ['windir'] + r'\System32\GroupPolicy\Machine\Registry.pol'
gp_split = b'[\x00'
gp_teredo = b'v\x006\x00T\x00r\x00a\x00n\x00s\x00i\x00t\x00i\x00o\x00n\x00\x00\x00;\x00T\x00e\x00r\x00e\x00d\x00o\x00'

def win32_notify( msg="msg", title="Title"):
    import ctypes
    res = ctypes.windll.user32.MessageBoxW(None, msg, title, 1)
    # Yes:1 No:2
    return res

with open(gp_regpol_file, 'rb') as f:
    gp_regpol_old = f.read()

gp_regpol_new = gp_split.join(gp for gp in gp_regpol_old.split(gp_split) if gp_teredo not in gp)

if gp_regpol_new != gp_regpol_old and \
        win32_notify(u'发现组策略 Teredo 设置，是否重置？', u'提醒') == 1:
    with open(gp_regpol_file, 'wb') as f:
        f.write(gp_regpol_new)
    import platform
    if platform.version() < '5.1':
        # Windows 5.0
        os.system('secedit /refreshpolicy machine_policy /enforce')
    else:
        os.system('gpupdate /target:computer /force')
