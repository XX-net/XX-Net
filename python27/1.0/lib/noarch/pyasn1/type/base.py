# Base classes for ASN.1 types
import sys
from pyasn1.type import constraint, tagmap
from pyasn1 import error

class Asn1Item: pass

class Asn1ItemBase(Asn1Item):
    # Set of tags for this ASN.1 type
    tagSet = ()
    
    # A list of constraint.Constraint instances for checking values
    subtypeSpec = constraint.ConstraintsIntersection()

    # Used for ambiguous ASN.1 types identification
    typeId = None
    
    def __init__(self, tagSet=None, subtypeSpec=None):
        if tagSet is None:
            self._tagSet = self.tagSet
        else:
            self._tagSet = tagSet
        if subtypeSpec is None:
            self._subtypeSpec = self.subtypeSpec
        else:
            self._subtypeSpec = subtypeSpec

    def _verifySubtypeSpec(self, value, idx=None):
        try:
            self._subtypeSpec(value, idx)
        except error.PyAsn1Error:
            c, i, t = sys.exc_info()
            raise c('%s at %s' % (i, self.__class__.__name__))
        
    def getSubtypeSpec(self): return self._subtypeSpec
    
    def getTagSet(self): return self._tagSet
    def getEffectiveTagSet(self): return self._tagSet  # used by untagged types
    def getTagMap(self): return tagmap.TagMap({self._tagSet: self})
    
    def isSameTypeWith(self, other):
        return self is other or \
               self._tagSet == other.getTagSet() and \
               self._subtypeSpec == other.getSubtypeSpec()
    def isSuperTypeOf(self, other):
        """Returns true if argument is a ASN1 subtype of ourselves"""
        return self._tagSet.isSuperTagSetOf(other.getTagSet()) and \
               self._subtypeSpec.isSuperTypeOf(other.getSubtypeSpec())

class __NoValue:
    def __getattr__(self, attr):
        raise error.PyAsn1Error('No value for %s()' % attr)
    def __getitem__(self, i):
        raise error.PyAsn1Error('No value')
    
noValue = __NoValue()

# Base class for "simple" ASN.1 objects. These are immutable.
class AbstractSimpleAsn1Item(Asn1ItemBase):    
    defaultValue = noValue
    def __init__(self, value=None, tagSet=None, subtypeSpec=None):
        Asn1ItemBase.__init__(self, tagSet, subtypeSpec)
        if value is None or value is noValue:
            value = self.defaultValue
        if value is None or value is noValue:
            self.__hashedValue = value = noValue
        else:
            value = self.prettyIn(value)
            self._verifySubtypeSpec(value)
            self.__hashedValue = hash(value)
        self._value = value
        self._len = None
        
    def __repr__(self):
        if self._value is noValue:
            return self.__class__.__name__ + '()'
        else:
            return self.__class__.__name__ + '(%s)' % (self.prettyOut(self._value),)
    def __str__(self): return str(self._value)
    def __eq__(self, other):
        return self is other and True or self._value == other
    def __ne__(self, other): return self._value != other
    def __lt__(self, other): return self._value < other
    def __le__(self, other): return self._value <= other
    def __gt__(self, other): return self._value > other
    def __ge__(self, other): return self._value >= other
    if sys.version_info[0] <= 2:
        def __nonzero__(self): return bool(self._value)
    else:
        def __bool__(self): return bool(self._value)
    def __hash__(self): return self.__hashedValue

    def clone(self, value=None, tagSet=None, subtypeSpec=None):
        if value is None and tagSet is None and subtypeSpec is None:
            return self
        if value is None:
            value = self._value
        if tagSet is None:
            tagSet = self._tagSet
        if subtypeSpec is None:
            subtypeSpec = self._subtypeSpec
        return self.__class__(value, tagSet, subtypeSpec)

    def subtype(self, value=None, implicitTag=None, explicitTag=None,
                subtypeSpec=None):
        if value is None:
            value = self._value
        if implicitTag is not None:
            tagSet = self._tagSet.tagImplicitly(implicitTag)
        elif explicitTag is not None:
            tagSet = self._tagSet.tagExplicitly(explicitTag)
        else:
            tagSet = self._tagSet
        if subtypeSpec is None:
            subtypeSpec = self._subtypeSpec
        else:
            subtypeSpec = subtypeSpec + self._subtypeSpec
        return self.__class__(value, tagSet, subtypeSpec)

    def prettyIn(self, value): return value
    def prettyOut(self, value): return str(value)

    def prettyPrint(self, scope=0):
        if self._value is noValue:
            return '<no value>'
        else:
            return self.prettyOut(self._value)

    # XXX Compatibility stub
    def prettyPrinter(self, scope=0): return self.prettyPrint(scope)
    
#
# Constructed types:
# * There are five of them: Sequence, SequenceOf/SetOf, Set and Choice
# * ASN1 types and values are represened by Python class instances
# * Value initialization is made for defaulted components only
# * Primary method of component addressing is by-position. Data model for base
#   type is Python sequence. Additional type-specific addressing methods
#   may be implemented for particular types.
# * SequenceOf and SetOf types do not implement any additional methods
# * Sequence, Set and Choice types also implement by-identifier addressing
# * Sequence, Set and Choice types also implement by-asn1-type (tag) addressing
# * Sequence and Set types may include optional and defaulted
#   components
# * Constructed types hold a reference to component types used for value
#   verification and ordering.
# * Component type is a scalar type for SequenceOf/SetOf types and a list
#   of types for Sequence/Set/Choice.
#

class AbstractConstructedAsn1Item(Asn1ItemBase):
    componentType = None
    sizeSpec = constraint.ConstraintsIntersection()
    def __init__(self, componentType=None, tagSet=None,
                 subtypeSpec=None, sizeSpec=None):
        Asn1ItemBase.__init__(self, tagSet, subtypeSpec)
        if componentType is None:
            self._componentType = self.componentType
        else:
            self._componentType = componentType
        if sizeSpec is None:
            self._sizeSpec = self.sizeSpec
        else:
            self._sizeSpec = sizeSpec
        self._componentValues = []
        self._componentValuesSet = 0

    def __repr__(self):
        r = self.__class__.__name__ + '()'
        for idx in range(len(self._componentValues)):
            if self._componentValues[idx] is None:
                continue
            r = r + '.setComponentByPosition(%s, %r)' % (
                idx, self._componentValues[idx]
                )
        return r

    def __eq__(self, other):
        return self is other and True or self._componentValues == other
    def __ne__(self, other): return self._componentValues != other
    def __lt__(self, other): return self._componentValues < other
    def __le__(self, other): return self._componentValues <= other
    def __gt__(self, other): return self._componentValues > other
    def __ge__(self, other): return self._componentValues >= other
    if sys.version_info[0] <= 2:
        def __nonzero__(self): return bool(self._componentValues)
    else:
        def __bool__(self): return bool(self._componentValues)

    def getComponentTagMap(self):
        raise error.PyAsn1Error('Method not implemented')

    def _cloneComponentValues(self, myClone, cloneValueFlag): pass

    def clone(self, tagSet=None, subtypeSpec=None, sizeSpec=None, 
              cloneValueFlag=None):
        if tagSet is None:
            tagSet = self._tagSet
        if subtypeSpec is None:
            subtypeSpec = self._subtypeSpec
        if sizeSpec is None:
            sizeSpec = self._sizeSpec
        r = self.__class__(self._componentType, tagSet, subtypeSpec, sizeSpec)
        if cloneValueFlag:
            self._cloneComponentValues(r, cloneValueFlag)
        return r

    def subtype(self, implicitTag=None, explicitTag=None, subtypeSpec=None,
                sizeSpec=None, cloneValueFlag=None):
        if implicitTag is not None:
            tagSet = self._tagSet.tagImplicitly(implicitTag)
        elif explicitTag is not None:
            tagSet = self._tagSet.tagExplicitly(explicitTag)
        else:
            tagSet = self._tagSet
        if subtypeSpec is None:
            subtypeSpec = self._subtypeSpec
        else:
            subtypeSpec = subtypeSpec + self._subtypeSpec
        if sizeSpec is None:
            sizeSpec = self._sizeSpec
        else:
            sizeSpec = sizeSpec + self._sizeSpec
        r = self.__class__(self._componentType, tagSet, subtypeSpec, sizeSpec)
        if cloneValueFlag:
            self._cloneComponentValues(r, cloneValueFlag)
        return r

    def _verifyComponent(self, idx, value): pass

    def verifySizeSpec(self): self._sizeSpec(self)

    def getComponentByPosition(self, idx):
        raise error.PyAsn1Error('Method not implemented')
    def setComponentByPosition(self, idx, value, verifyConstraints=True):
        raise error.PyAsn1Error('Method not implemented')

    def getComponentType(self): return self._componentType

    def __getitem__(self, idx): return self.getComponentByPosition(idx)
    def __setitem__(self, idx, value): self.setComponentByPosition(idx, value)

    def __len__(self): return len(self._componentValues)
    
    def clear(self):
        self._componentValues = []
        self._componentValuesSet = 0

    def setDefaultComponents(self): pass
