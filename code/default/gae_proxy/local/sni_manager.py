import random
import os


current_path = os.path.dirname(os.path.abspath(__file__))


class SniManager(object):
    plus = ['-', '', "."]
    end = ["com", "net", "ml", "org", "us"]

    def __init__(self, logger):
        self.logger = logger

        fn = os.path.join(current_path, "sni_slice.txt")
        self.fd = open(fn, "r")
        self.fsize = os.path.getsize(fn)

    def get_slice(self):
        max_slice_len = 20

        position = random.randint(0, self.fsize - max_slice_len)
        self.fd.seek(position)
        slice = self.fd.read(max_slice_len * 2)

        if slice is None or len(slice) < max_slice_len:
            self.logger.warn("get_public_appid fail")
            raise Exception()

        ns = slice.split("|")
        slice = ns[1]
        return slice

    def get(self):
        n = random.randint(2, 3)
        ws = []
        for i in range(0, n):
            w = self.get_slice()
            ws.append(w)

        p = random.choice(self.plus)

        name = p.join(ws)
        name += "." + random.choice(self.end)

        return name
