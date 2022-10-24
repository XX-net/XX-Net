"""Abstract class for DSA."""

class DSAKey(object):
    """This is an abstract base class for DSA keys.

    Particular implementations of DSA keys, such as
    :py:class:`~.python_dsakey.Python_DSAKey`
    ... more coming
    inherit from this.

    To create or parse an DSA key, don't use one of these classes
    directly.  Instead, use the factory functions in
    :py:class:`~tlslite.utils.keyfactory`.
    """

    def __init__(self, p, q, g, x, y):
        """Create a new DSA key.
        :type p: int
        :param p: domain parameter, prime num defining Gaolis Field
        :type q: int
        :param q: domain parameter, prime factor of p-1
        :type g: int
        :param g: domain parameter, generator of q-order cyclic group GP(p)
        :type x: int
        :param x: private key
        :type y: int
        :param y: public key
        """
        raise NotImplementedError()

    def __len__(self):
        """Return the size of the order of the curve of this key, in bits.

        :rtype: int
        """
        raise NotImplementedError()

    def hasPrivateKey(self):
        """Return whether or not this key has a private component.

        :rtype: bool
        """
        raise NotImplementedError()

    def hashAndSign(self, data, hAlg):
        """Hash and sign the passed-in bytes.

        This requires the key to have a private component and
        global parameters. It performs a signature on the passed-in data
        with selected hash algorithm.

        :type data: str
        :param data: The data which will be hashed and signed.

        :type hAlg: str
        :param hAlg: The hash algorithm that will be used to hash data

        :rtype: bytearray
        :returns: An DSA signature on the passed-in data.
        """
        raise NotImplementedError()

    def sign(self, data):
        raise NotImplementedError()

    def hashAndVerify(self, signature, data, hAlg="sha1"):
        """Hash and verify the passed-in bytes with signature.

        :type signature: ASN1 bytearray
        :param signature: the r, s dsa signature

        :type data: str
        :param data: The data which will be hashed and verified.

        :type hAlg: str
        :param hAlg: The hash algorithm that will be used to hash data

        :rtype: bool
        :returns: return True if verification is OK.
        """
        raise NotImplementedError()

    @staticmethod
    def generate(L, N):
        """Generate new key given by bit lengths L, N.

        :type L: int
        :param L: length of parameter p in bits

        :type N: int
        :param N: length of parameter q in bits

        :rtype: DSAkey
        :returns: DSAkey(domain parameters, private key, public key)
        """
        raise NotImplementedError()

    @staticmethod
    def generate_qp(L, N):
        """Generate new (p, q) given by bit lengths L, N.

        :type L: int
        :param L: length of parameter p in bits

        :type N: int
        :param N: length of parameter q in bits

        :rtype: (int, int)
        :returns: new p and q key parameters
        """
        raise NotImplementedError()
