# DER encoder
from pyasn1.type import univ
from pyasn1.codec.cer import encoder

class SetOfEncoder(encoder.SetOfEncoder):
    def _cmpSetComponents(self, c1, c2):
        tagSet1 = isinstance(c1, univ.Choice) and \
                  c1.getEffectiveTagSet() or c1.getTagSet()
        tagSet2 = isinstance(c2, univ.Choice) and \
                  c2.getEffectiveTagSet() or c2.getTagSet()
        return cmp(tagSet1, tagSet2)

tagMap = encoder.tagMap.copy()
tagMap.update({
    # Overload CER encodrs with BER ones (a bit hackerish XXX)
    univ.BitString.tagSet: encoder.encoder.BitStringEncoder(),
    univ.OctetString.tagSet: encoder.encoder.OctetStringEncoder(),
    # Set & SetOf have same tags
    univ.SetOf().tagSet: SetOfEncoder()
    })

typeMap = encoder.typeMap

class Encoder(encoder.Encoder):
    def __call__(self, client, defMode=1, maxChunkSize=0):
        return encoder.Encoder.__call__(self, client, defMode, maxChunkSize)

encode = Encoder(tagMap, typeMap)
