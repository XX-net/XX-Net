
import os
import sys
import platform

if "arm" in platform.machine():
    from .unknown import state, enable, disable
elif sys.platform == "win32":
    # TODO: WinXP should be different
    from .win10 import state, enable, disable
elif sys.platform.startswith("linux"):
    from .linux import state, enable, disable
elif sys.platform == "darwin":
    from .darwin import state, enable, disable
else:
    from .unknown import state, enable, disable


