
import os
import sys

import utils
from config import get_language
from xlog import getLogger
xlog = getLogger("launcher")


class SimpleI18N(object):
    def __init__(self):
        self.lang = get_language()
        xlog.debug("lang: %s", self.lang)

    @staticmethod
    def po_loader(file):
        if sys.version_info[0] == 2:
            fp = open(file, "r")
        else:
            fp = open(file, "rb")

        po_dict = {}
        while True:
            line = fp.readline()
            line = utils.to_bytes(line)
            if not line:
                break

            if len(line) < 2:
                continue

            if line.startswith(b"#"):
                continue

            if line.startswith(b"msgid "):
                key = line[7:-2]
                value = b""
                while True:
                    line = fp.readline()
                    line = utils.to_bytes(line)
                    if not line:
                        break

                    if line.startswith(b"\""):
                        key += line[1:-2]
                    elif line.startswith(b"msgstr "):
                        value += line[8:-2]
                        break
                    else:
                        break

                while True:
                    line = fp.readline()
                    line = utils.to_bytes(line)
                    if not line:
                        break

                    if line.startswith(b"\""):
                        value += line[1:-2]
                    else:
                        break

                if key == b"":
                    continue

                po_dict[key] = value

        return po_dict

    @staticmethod
    def _render(po_dict, file):
        if sys.version_info[0] == 2:
            fp = open(file, "r")
            content = fp.read()
        else:
            fp = open(file, "rb")
            content = fp.read()

        out_arr = []

        cp = 0
        while True:
            bp = content.find(b"{{", cp)
            if bp == -1:
                break

            ep = content.find(b"}}", bp)
            if ep == -1:
                # print((content[bp:]))
                break

            b1p = content.find(b"_(", bp, ep)
            if b1p == -1:
                # print((content[bp:]))
                continue
            b2p = content.find(b"\"", b1p + 2, b1p + 4)
            if b2p == -1:
                # print((content[bp:]))
                continue

            e1p = content.find(b")", ep - 2, ep)
            if e1p == -1:
                # print((content[bp:]))
                continue

            e2p = content.find(b"\"", e1p - 2, e1p)
            if e2p == -1:
                # print((content[bp:]))
                continue

            out_arr.append(content[cp:bp])
            key = content[b2p + 1:e2p]
            if po_dict.get(key, b"") == b"":
                out_arr.append(key)
            else:
                out_arr.append(po_dict[key])

            cp = ep + 2

        out_arr.append(content[cp:])

        return b"".join(out_arr)

    def render(self, lang_path, template_file):
        po_file = os.path.join(lang_path, self.lang, "LC_MESSAGES", "messages.po")
        if not os.path.isfile(po_file):
            return self._render(dict(), template_file)
        else:
            po_dict = self.po_loader(po_file)
            return self._render(po_dict, template_file)
