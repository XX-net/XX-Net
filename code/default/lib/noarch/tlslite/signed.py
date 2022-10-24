"""Base class that represents any signed object"""

from .utils.cryptomath import numBytes

RSA_SIGNATURE_HASHES = ["sha512", "sha384", "sha256", "sha224", "sha1"]
ALL_RSA_SIGNATURE_HASHES = RSA_SIGNATURE_HASHES + ["md5"]
RSA_SCHEMES = ["pss", "pkcs1"]


class SignatureSettings(object):
    def __init__(self, min_key_size=None, max_key_size=None,
                 rsa_sig_hashes=None, rsa_schemes=None):
        """Create default variables for key-related settings."""
        self.min_key_size = min_key_size or 1023
        self.max_key_size = max_key_size or 8193
        self.rsa_sig_hashes = rsa_sig_hashes or list(RSA_SIGNATURE_HASHES)
        self.rsa_schemes = rsa_schemes or list(RSA_SCHEMES)

    def _copy_settings(self, other):
        other.min_key_size = self.min_key_size
        other.max_key_size = self.max_key_size
        other.rsa_sig_hashes = self.rsa_sig_hashes
        other.rsa_schemes = self.rsa_schemes

    @staticmethod
    def _sanityCheckKeySizes(other):
        if other.min_key_size < 512:
            raise ValueError("min_key_size too small")
        if other.min_key_size > 16384:
            raise ValueError("min_key_size too large")
        if other.max_key_size < 512:
            raise ValueError("max_key_size too small")
        if other.max_key_size > 16384:
            raise ValueError("max_key_size too large")
        if other.max_key_size < other.min_key_size:
            raise ValueError("max_key_size smaller than min_key_size")

    @staticmethod
    def _sanityCheckSignatureAlgs(other):
        not_allowed = [alg for alg in other.rsa_sig_hashes
                       if alg not in ALL_RSA_SIGNATURE_HASHES]
        if len(not_allowed) > 0:
            raise ValueError("Following signature algorithms are not allowed: "
                             "{0}".format(", ".join(not_allowed)))

    def validate(self):
        other = SignatureSettings()
        self._copy_settings(other)
        self._sanityCheckKeySizes(other)
        self._sanityCheckSignatureAlgs(other)
        return other


class SignedObject(object):
    def __init__(self):
        self.tbs_data = None
        self.signature = None
        self.signature_alg = None

    _hash_algs_OIDs = {
        tuple([0x2a, 0x86, 0x48, 0x86, 0xf7, 0xd, 0x1, 0x1, 0x4]): 'md5',
        tuple([0x2a, 0x86, 0x48, 0x86, 0xf7, 0xd, 0x1, 0x1, 0x5]): 'sha1',
        tuple([0x2a, 0x86, 0x48, 0x86, 0xf7, 0xd, 0x1, 0x1, 0xe]): 'sha224',
        tuple([0x2a, 0x86, 0x48, 0x86, 0xf7, 0xd, 0x1, 0x1, 0xc]): 'sha384',
        tuple([0x2a, 0x86, 0x48, 0x86, 0xf7, 0xd, 0x1, 0x1, 0xb]): 'sha256',
        tuple([0x2a, 0x86, 0x48, 0x86, 0xf7, 0xd, 0x1, 0x1, 0xd]): 'sha512'
    }

    def verify_signature(self, publicKey, settings=None):
        """ Verify signature in a reponse"""
        offset = 0
        settings = settings or SignatureSettings()

        # workaround as some signature encodings could be zero left-padded
        if (self.signature[0] == 0 and
                numBytes(publicKey.n) + 1 == len(self.signature)):
            offset = 1

        alg = self._hash_algs_OIDs[tuple(self.signature_alg)]
        if alg not in settings.rsa_sig_hashes:
            raise ValueError("Invalid signature algorithm: {0}".format(alg))
        verified = publicKey.hashAndVerify(self.signature[offset:],
                                           self.tbs_data, hAlg=alg)
        if not verified:
            raise ValueError("Signature could not be verified for {0}"
                             .format(alg))
        return True
