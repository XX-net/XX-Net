# CER encoder
from pyasn1.type import univ
from pyasn1.codec.ber import encoder
from pyasn1.compat.octets import int2oct, null

class BooleanEncoder(encoder.IntegerEncoder):
    def encodeValue(self, encodeFun, client, defMode, maxChunkSize):
        if client == 0:
            substrate = int2oct(0)
        else:
            substrate = int2oct(255)
        return substrate, 0

class BitStringEncoder(encoder.BitStringEncoder):
    def encodeValue(self, encodeFun, client, defMode, maxChunkSize):
        return encoder.BitStringEncoder.encodeValue(
            self, encodeFun, client, defMode, 1000
            )

class OctetStringEncoder(encoder.OctetStringEncoder):
    def encodeValue(self, encodeFun, client, defMode, maxChunkSize):
        return encoder.OctetStringEncoder.encodeValue(
            self, encodeFun, client, defMode, 1000
            )

# specialized RealEncoder here
# specialized GeneralStringEncoder here
# specialized GeneralizedTimeEncoder here
# specialized UTCTimeEncoder here

class SetOfEncoder(encoder.SequenceOfEncoder):
    def encodeValue(self, encodeFun, client, defMode, maxChunkSize):
        if isinstance(client, univ.SequenceAndSetBase):
            client.setDefaultComponents()
        client.verifySizeSpec()
        substrate = null; idx = len(client)
        # This is certainly a hack but how else do I distinguish SetOf
        # from Set if they have the same tags&constraints?
        if isinstance(client, univ.SequenceAndSetBase):
            # Set
            comps = []
            while idx > 0:
                idx = idx - 1
                if client[idx] is None:  # Optional component
                    continue
                if client.getDefaultComponentByPosition(idx) == client[idx]:
                    continue
                comps.append(client[idx])
            comps.sort(key=lambda x: isinstance(x, univ.Choice) and \
                                     x.getMinTagSet() or x.getTagSet())
            for c in comps:
                substrate += encodeFun(c, defMode, maxChunkSize)
        else:
            # SetOf
            compSubs = []
            while idx > 0:
                idx = idx - 1
                compSubs.append(
                    encodeFun(client[idx], defMode, maxChunkSize)
                    )
            compSubs.sort()  # perhaps padding's not needed
            substrate = null
            for compSub in compSubs:
                substrate += compSub
        return substrate, 1

tagMap = encoder.tagMap.copy()
tagMap.update({
    univ.Boolean.tagSet: BooleanEncoder(),
    univ.BitString.tagSet: BitStringEncoder(),
    univ.OctetString.tagSet: OctetStringEncoder(),
    univ.SetOf().tagSet: SetOfEncoder()  # conflcts with Set
    })

typeMap = encoder.typeMap.copy()
typeMap.update({
    univ.Set.typeId: SetOfEncoder(),
    univ.SetOf.typeId: SetOfEncoder()
    })

class Encoder(encoder.Encoder):
    def __call__(self, client, defMode=0, maxChunkSize=0):
        return encoder.Encoder.__call__(self, client, defMode, maxChunkSize)

encode = Encoder(tagMap, typeMap)

# EncoderFactory queries class instance and builds a map of tags -> encoders
