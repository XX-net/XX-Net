from pyasn1 import error

class TagMap:
    def __init__(self, posMap={}, negMap={}, defType=None):
        self.__posMap = posMap.copy()
        self.__negMap = negMap.copy()
        self.__defType = defType

    def __contains__(self, tagSet):
        return tagSet in self.__posMap or \
               self.__defType is not None and tagSet not in self.__negMap

    def __getitem__(self, tagSet):
        if tagSet in self.__posMap:
            return self.__posMap[tagSet]
        elif tagSet in self.__negMap:
            raise error.PyAsn1Error('Key in negative map')
        elif self.__defType is not None:
            return self.__defType
        else:
            raise KeyError()

    def __repr__(self):
        s = '%r/%r' % (self.__posMap, self.__negMap)
        if self.__defType is not None:
            s = s + '/%r' % (self.__defType,)
        return s

    def clone(self, parentType, tagMap, uniq=False):
        if self.__defType is not None and tagMap.getDef() is not None:
            raise error.PyAsn1Error('Duplicate default value at %s' % (self,))
        if tagMap.getDef() is not None:
            defType = tagMap.getDef()
        else:
            defType = self.__defType

        posMap = self.__posMap.copy()
        for k in tagMap.getPosMap():
            if uniq and k in posMap:
                raise error.PyAsn1Error('Duplicate positive key %s' % (k,))
            posMap[k] = parentType

        negMap = self.__negMap.copy()
        negMap.update(tagMap.getNegMap())

        return self.__class__(
            posMap, negMap, defType,
            )

    def getPosMap(self): return self.__posMap.copy()
    def getNegMap(self): return self.__negMap.copy()
    def getDef(self): return self.__defType
