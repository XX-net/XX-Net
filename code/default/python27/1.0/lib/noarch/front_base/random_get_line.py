import os
import random


class RandomGetLine(object):
    def __init__(self, fn, line_max_size=80):
        self.fn = fn
        self.line_max_size = line_max_size
        self.fd = open(fn, "r")
        self.fsize = os.path.getsize(fn)

    def get_line(self):
        position = random.randint(0, self.fsize - self.line_max_size)
        self.fd.seek(position)
        slice = self.fd.read(self.line_max_size * 2)

        if slice is None or len(slice) < self.line_max_size:
            raise Exception("read fail")

        ns = slice.split("\n")
        line = ns[1]
        return line
