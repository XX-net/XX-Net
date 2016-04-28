from weakref import ref


class GcWeakrefs(object):
    # code copied and adapted from WeakKeyDictionary.

    def __init__(self, ffi):
        self.ffi = ffi
        self.data = data = {}
        def remove(k):
            destructor, cdata = data.pop(k)
            destructor(cdata)
        self.remove = remove

    def build(self, cdata, destructor):
        # make a new cdata of the same type as the original one
        new_cdata = self.ffi.cast(self.ffi._backend.typeof(cdata), cdata)
        self.data[ref(new_cdata, self.remove)] = destructor, cdata
        return new_cdata
