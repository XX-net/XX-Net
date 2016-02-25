# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import absolute_import, division, print_function

import calendar
import collections
import datetime
import itertools
from contextlib import contextmanager

import idna

import six

from cryptography import utils, x509
from cryptography.exceptions import UnsupportedAlgorithm, _Reasons
from cryptography.hazmat.backends.interfaces import (
    CMACBackend, CipherBackend, DERSerializationBackend, DSABackend,
    EllipticCurveBackend, HMACBackend, HashBackend, PBKDF2HMACBackend,
    PEMSerializationBackend, RSABackend, X509Backend
)
from cryptography.hazmat.backends.openssl.ciphers import (
    _AESCTRCipherContext, _CipherContext
)
from cryptography.hazmat.backends.openssl.cmac import _CMACContext
from cryptography.hazmat.backends.openssl.dsa import (
    _DSAParameters, _DSAPrivateKey, _DSAPublicKey
)
from cryptography.hazmat.backends.openssl.ec import (
    _EllipticCurvePrivateKey, _EllipticCurvePublicKey
)
from cryptography.hazmat.backends.openssl.hashes import _HashContext
from cryptography.hazmat.backends.openssl.hmac import _HMACContext
from cryptography.hazmat.backends.openssl.rsa import (
    _RSAPrivateKey, _RSAPublicKey
)
from cryptography.hazmat.backends.openssl.x509 import (
    _CRL_ENTRY_REASON_ENUM_TO_CODE, _Certificate, _CertificateRevocationList,
    _CertificateSigningRequest, _DISTPOINT_TYPE_FULLNAME,
    _DISTPOINT_TYPE_RELATIVENAME, _RevokedCertificate
)
from cryptography.hazmat.bindings._openssl import ffi as _ffi
from cryptography.hazmat.bindings.openssl import binding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dsa, ec, rsa
from cryptography.hazmat.primitives.asymmetric.padding import (
    MGF1, OAEP, PKCS1v15, PSS
)
from cryptography.hazmat.primitives.ciphers.algorithms import (
    AES, ARC4, Blowfish, CAST5, Camellia, IDEA, SEED, TripleDES
)
from cryptography.hazmat.primitives.ciphers.modes import (
    CBC, CFB, CFB8, CTR, ECB, GCM, OFB
)
from cryptography.x509.oid import CRLEntryExtensionOID, ExtensionOID, NameOID


_MemoryBIO = collections.namedtuple("_MemoryBIO", ["bio", "char_ptr"])


def _encode_asn1_int(backend, x):
    """
    Converts a python integer to an ASN1_INTEGER. The returned ASN1_INTEGER
    will not be garbage collected (to support adding them to structs that take
    ownership of the object). Be sure to register it for GC if it will be
    discarded after use.

    """
    # Convert Python integer to OpenSSL "bignum" in case value exceeds
    # machine's native integer limits (note: `int_to_bn` doesn't automatically
    # GC).
    i = backend._int_to_bn(x)
    i = backend._ffi.gc(i, backend._lib.BN_free)

    # Wrap in an ASN.1 integer.  Don't GC -- as documented.
    i = backend._lib.BN_to_ASN1_INTEGER(i, backend._ffi.NULL)
    backend.openssl_assert(i != backend._ffi.NULL)
    return i


def _encode_asn1_int_gc(backend, x):
    i = _encode_asn1_int(backend, x)
    i = backend._ffi.gc(i, backend._lib.ASN1_INTEGER_free)
    return i


def _encode_asn1_str(backend, data, length):
    """
    Create an ASN1_OCTET_STRING from a Python byte string.
    """
    s = backend._lib.ASN1_OCTET_STRING_new()
    res = backend._lib.ASN1_OCTET_STRING_set(s, data, length)
    backend.openssl_assert(res == 1)
    return s


def _encode_asn1_utf8_str(backend, string):
    """
    Create an ASN1_UTF8STRING from a Python unicode string.
    This object will be an ASN1_STRING with UTF8 type in OpenSSL and
    can be decoded with ASN1_STRING_to_UTF8.
    """
    s = backend._lib.ASN1_UTF8STRING_new()
    res = backend._lib.ASN1_STRING_set(
        s, string.encode("utf8"), len(string.encode("utf8"))
    )
    backend.openssl_assert(res == 1)
    return s


def _encode_asn1_str_gc(backend, data, length):
    s = _encode_asn1_str(backend, data, length)
    s = backend._ffi.gc(s, backend._lib.ASN1_OCTET_STRING_free)
    return s


def _encode_extension_to_der(backend, i2d_func, value):
    pp = backend._ffi.new("unsigned char **")
    r = i2d_func(value, pp)
    backend.openssl_assert(r > 0)
    pp = backend._ffi.gc(
        pp, lambda pointer: backend._lib.OPENSSL_free(pointer[0])
    )
    return pp, r


def _encode_inhibit_any_policy(backend, inhibit_any_policy):
    asn1int = _encode_asn1_int_gc(backend, inhibit_any_policy.skip_certs)
    return _encode_extension_to_der(
        backend, backend._lib.i2d_ASN1_INTEGER, asn1int
    )


def _encode_name(backend, attributes):
    """
    The X509_NAME created will not be gc'd. Use _encode_name_gc if needed.
    """
    subject = backend._lib.X509_NAME_new()
    for attribute in attributes:
        value = attribute.value.encode('utf8')
        obj = _txt2obj_gc(backend, attribute.oid.dotted_string)
        if attribute.oid == NameOID.COUNTRY_NAME:
            # Per RFC5280 Appendix A.1 countryName should be encoded as
            # PrintableString, not UTF8String
            type = backend._lib.MBSTRING_ASC
        else:
            type = backend._lib.MBSTRING_UTF8
        res = backend._lib.X509_NAME_add_entry_by_OBJ(
            subject, obj, type, value, -1, -1, 0,
        )
        backend.openssl_assert(res == 1)
    return subject


def _encode_name_gc(backend, attributes):
    subject = _encode_name(backend, attributes)
    subject = backend._ffi.gc(subject, backend._lib.X509_NAME_free)
    return subject


def _encode_crl_number(backend, crl_number):
    asn1int = _encode_asn1_int_gc(backend, crl_number.crl_number)
    return _encode_extension_to_der(
        backend, backend._lib.i2d_ASN1_INTEGER, asn1int
    )


def _encode_crl_reason(backend, crl_reason):
    asn1enum = backend._lib.ASN1_ENUMERATED_new()
    backend.openssl_assert(asn1enum != backend._ffi.NULL)
    asn1enum = backend._ffi.gc(asn1enum, backend._lib.ASN1_ENUMERATED_free)
    res = backend._lib.ASN1_ENUMERATED_set(
        asn1enum, _CRL_ENTRY_REASON_ENUM_TO_CODE[crl_reason.reason]
    )
    backend.openssl_assert(res == 1)

    return _encode_extension_to_der(
        backend, backend._lib.i2d_ASN1_ENUMERATED, asn1enum
    )


def _encode_invalidity_date(backend, invalidity_date):
    time = backend._lib.ASN1_GENERALIZEDTIME_set(
        backend._ffi.NULL, calendar.timegm(
            invalidity_date.invalidity_date.timetuple()
        )
    )
    backend.openssl_assert(time != backend._ffi.NULL)
    time = backend._ffi.gc(time, backend._lib.ASN1_GENERALIZEDTIME_free)

    return _encode_extension_to_der(
        backend, backend._lib.i2d_ASN1_GENERALIZEDTIME, time
    )


def _encode_certificate_policies(backend, certificate_policies):
    cp = backend._lib.sk_POLICYINFO_new_null()
    backend.openssl_assert(cp != backend._ffi.NULL)
    cp = backend._ffi.gc(cp, backend._lib.sk_POLICYINFO_free)
    for policy_info in certificate_policies:
        pi = backend._lib.POLICYINFO_new()
        backend.openssl_assert(pi != backend._ffi.NULL)
        res = backend._lib.sk_POLICYINFO_push(cp, pi)
        backend.openssl_assert(res >= 1)
        oid = _txt2obj(backend, policy_info.policy_identifier.dotted_string)
        pi.policyid = oid
        if policy_info.policy_qualifiers:
            pqis = backend._lib.sk_POLICYQUALINFO_new_null()
            backend.openssl_assert(pqis != backend._ffi.NULL)
            for qualifier in policy_info.policy_qualifiers:
                pqi = backend._lib.POLICYQUALINFO_new()
                backend.openssl_assert(pqi != backend._ffi.NULL)
                res = backend._lib.sk_POLICYQUALINFO_push(pqis, pqi)
                backend.openssl_assert(res >= 1)
                if isinstance(qualifier, six.text_type):
                    pqi.pqualid = _txt2obj(
                        backend, x509.OID_CPS_QUALIFIER.dotted_string
                    )
                    pqi.d.cpsuri = _encode_asn1_str(
                        backend,
                        qualifier.encode("ascii"),
                        len(qualifier.encode("ascii"))
                    )
                else:
                    assert isinstance(qualifier, x509.UserNotice)
                    pqi.pqualid = _txt2obj(
                        backend, x509.OID_CPS_USER_NOTICE.dotted_string
                    )
                    un = backend._lib.USERNOTICE_new()
                    backend.openssl_assert(un != backend._ffi.NULL)
                    pqi.d.usernotice = un
                    if qualifier.explicit_text:
                        un.exptext = _encode_asn1_utf8_str(
                            backend, qualifier.explicit_text
                        )

                    un.noticeref = _encode_notice_reference(
                        backend, qualifier.notice_reference
                    )

            pi.qualifiers = pqis

    return _encode_extension_to_der(
        backend, backend._lib.i2d_CERTIFICATEPOLICIES, cp
    )


def _encode_notice_reference(backend, notice):
    if notice is None:
        return backend._ffi.NULL
    else:
        nr = backend._lib.NOTICEREF_new()
        backend.openssl_assert(nr != backend._ffi.NULL)
        # organization is a required field
        nr.organization = _encode_asn1_utf8_str(backend, notice.organization)

        notice_stack = backend._lib.sk_ASN1_INTEGER_new_null()
        nr.noticenos = notice_stack
        for number in notice.notice_numbers:
            num = _encode_asn1_int(backend, number)
            res = backend._lib.sk_ASN1_INTEGER_push(notice_stack, num)
            backend.openssl_assert(res >= 1)

        return nr


def _txt2obj(backend, name):
    """
    Converts a Python string with an ASN.1 object ID in dotted form to a
    ASN1_OBJECT.
    """
    name = name.encode('ascii')
    obj = backend._lib.OBJ_txt2obj(name, 1)
    backend.openssl_assert(obj != backend._ffi.NULL)
    return obj


def _txt2obj_gc(backend, name):
    obj = _txt2obj(backend, name)
    obj = backend._ffi.gc(obj, backend._lib.ASN1_OBJECT_free)
    return obj


def _encode_ocsp_nocheck(backend, ext):
    """
    The OCSP No Check extension is defined as a null ASN.1 value. Rather than
    calling OpenSSL we can return a Python bytestring value in a list.
    """
    return [b"\x05\x00"], 2


def _encode_key_usage(backend, key_usage):
    set_bit = backend._lib.ASN1_BIT_STRING_set_bit
    ku = backend._lib.ASN1_BIT_STRING_new()
    ku = backend._ffi.gc(ku, backend._lib.ASN1_BIT_STRING_free)
    res = set_bit(ku, 0, key_usage.digital_signature)
    backend.openssl_assert(res == 1)
    res = set_bit(ku, 1, key_usage.content_commitment)
    backend.openssl_assert(res == 1)
    res = set_bit(ku, 2, key_usage.key_encipherment)
    backend.openssl_assert(res == 1)
    res = set_bit(ku, 3, key_usage.data_encipherment)
    backend.openssl_assert(res == 1)
    res = set_bit(ku, 4, key_usage.key_agreement)
    backend.openssl_assert(res == 1)
    res = set_bit(ku, 5, key_usage.key_cert_sign)
    backend.openssl_assert(res == 1)
    res = set_bit(ku, 6, key_usage.crl_sign)
    backend.openssl_assert(res == 1)
    if key_usage.key_agreement:
        res = set_bit(ku, 7, key_usage.encipher_only)
        backend.openssl_assert(res == 1)
        res = set_bit(ku, 8, key_usage.decipher_only)
        backend.openssl_assert(res == 1)
    else:
        res = set_bit(ku, 7, 0)
        backend.openssl_assert(res == 1)
        res = set_bit(ku, 8, 0)
        backend.openssl_assert(res == 1)

    return _encode_extension_to_der(
        backend, backend._lib.i2d_ASN1_BIT_STRING, ku
    )


def _encode_authority_key_identifier(backend, authority_keyid):
    akid = backend._lib.AUTHORITY_KEYID_new()
    backend.openssl_assert(akid != backend._ffi.NULL)
    akid = backend._ffi.gc(akid, backend._lib.AUTHORITY_KEYID_free)
    if authority_keyid.key_identifier is not None:
        akid.keyid = _encode_asn1_str(
            backend,
            authority_keyid.key_identifier,
            len(authority_keyid.key_identifier)
        )

    if authority_keyid.authority_cert_issuer is not None:
        akid.issuer = _encode_general_names(
            backend, authority_keyid.authority_cert_issuer
        )

    if authority_keyid.authority_cert_serial_number is not None:
        akid.serial = _encode_asn1_int(
            backend, authority_keyid.authority_cert_serial_number
        )

    return _encode_extension_to_der(
        backend, backend._lib.i2d_AUTHORITY_KEYID, akid
    )


def _encode_basic_constraints(backend, basic_constraints):
    constraints = backend._lib.BASIC_CONSTRAINTS_new()
    constraints = backend._ffi.gc(
        constraints, backend._lib.BASIC_CONSTRAINTS_free
    )
    constraints.ca = 255 if basic_constraints.ca else 0
    if basic_constraints.ca and basic_constraints.path_length is not None:
        constraints.pathlen = _encode_asn1_int(
            backend, basic_constraints.path_length
        )

    return _encode_extension_to_der(
        backend, backend._lib.i2d_BASIC_CONSTRAINTS, constraints
    )


def _encode_authority_information_access(backend, authority_info_access):
    aia = backend._lib.sk_ACCESS_DESCRIPTION_new_null()
    backend.openssl_assert(aia != backend._ffi.NULL)
    aia = backend._ffi.gc(
        aia, backend._lib.sk_ACCESS_DESCRIPTION_free
    )
    for access_description in authority_info_access:
        ad = backend._lib.ACCESS_DESCRIPTION_new()
        method = _txt2obj(
            backend, access_description.access_method.dotted_string
        )
        gn = _encode_general_name(backend, access_description.access_location)
        ad.method = method
        ad.location = gn
        res = backend._lib.sk_ACCESS_DESCRIPTION_push(aia, ad)
        backend.openssl_assert(res >= 1)

    return _encode_extension_to_der(
        backend, backend._lib.i2d_AUTHORITY_INFO_ACCESS, aia
    )


def _encode_general_names(backend, names):
    general_names = backend._lib.GENERAL_NAMES_new()
    backend.openssl_assert(general_names != backend._ffi.NULL)
    for name in names:
        gn = _encode_general_name(backend, name)
        res = backend._lib.sk_GENERAL_NAME_push(general_names, gn)
        backend.openssl_assert(res != 0)

    return general_names


def _encode_alt_name(backend, san):
    general_names = _encode_general_names(backend, san)
    general_names = backend._ffi.gc(
        general_names, backend._lib.GENERAL_NAMES_free
    )
    return _encode_extension_to_der(
        backend, backend._lib.i2d_GENERAL_NAMES, general_names
    )


def _encode_subject_key_identifier(backend, ski):
    asn1_str = _encode_asn1_str_gc(backend, ski.digest, len(ski.digest))
    return _encode_extension_to_der(
        backend, backend._lib.i2d_ASN1_OCTET_STRING, asn1_str
    )


def _encode_general_name(backend, name):
    if isinstance(name, x509.DNSName):
        gn = backend._lib.GENERAL_NAME_new()
        backend.openssl_assert(gn != backend._ffi.NULL)
        gn.type = backend._lib.GEN_DNS

        ia5 = backend._lib.ASN1_IA5STRING_new()
        backend.openssl_assert(ia5 != backend._ffi.NULL)

        if name.value.startswith(u"*."):
            value = b"*." + idna.encode(name.value[2:])
        else:
            value = idna.encode(name.value)

        res = backend._lib.ASN1_STRING_set(ia5, value, len(value))
        backend.openssl_assert(res == 1)
        gn.d.dNSName = ia5
    elif isinstance(name, x509.RegisteredID):
        gn = backend._lib.GENERAL_NAME_new()
        backend.openssl_assert(gn != backend._ffi.NULL)
        gn.type = backend._lib.GEN_RID
        obj = backend._lib.OBJ_txt2obj(
            name.value.dotted_string.encode('ascii'), 1
        )
        backend.openssl_assert(obj != backend._ffi.NULL)
        gn.d.registeredID = obj
    elif isinstance(name, x509.DirectoryName):
        gn = backend._lib.GENERAL_NAME_new()
        backend.openssl_assert(gn != backend._ffi.NULL)
        dir_name = _encode_name(backend, name.value)
        gn.type = backend._lib.GEN_DIRNAME
        gn.d.directoryName = dir_name
    elif isinstance(name, x509.IPAddress):
        gn = backend._lib.GENERAL_NAME_new()
        backend.openssl_assert(gn != backend._ffi.NULL)
        ipaddr = _encode_asn1_str(
            backend, name.value.packed, len(name.value.packed)
        )
        gn.type = backend._lib.GEN_IPADD
        gn.d.iPAddress = ipaddr
    elif isinstance(name, x509.OtherName):
        gn = backend._lib.GENERAL_NAME_new()
        backend.openssl_assert(gn != backend._ffi.NULL)
        other_name = backend._lib.OTHERNAME_new()
        backend.openssl_assert(other_name != backend._ffi.NULL)

        type_id = backend._lib.OBJ_txt2obj(
            name.type_id.dotted_string.encode('ascii'), 1
        )
        backend.openssl_assert(type_id != backend._ffi.NULL)
        data = backend._ffi.new("unsigned char[]", name.value)
        data_ptr_ptr = backend._ffi.new("unsigned char **")
        data_ptr_ptr[0] = data
        value = backend._lib.d2i_ASN1_TYPE(
            backend._ffi.NULL, data_ptr_ptr, len(name.value)
        )
        if value == backend._ffi.NULL:
            backend._consume_errors()
            raise ValueError("Invalid ASN.1 data")
        other_name.type_id = type_id
        other_name.value = value
        gn.type = backend._lib.GEN_OTHERNAME
        gn.d.otherName = other_name
    elif isinstance(name, x509.RFC822Name):
        gn = backend._lib.GENERAL_NAME_new()
        backend.openssl_assert(gn != backend._ffi.NULL)
        asn1_str = _encode_asn1_str(
            backend, name._encoded, len(name._encoded)
        )
        gn.type = backend._lib.GEN_EMAIL
        gn.d.rfc822Name = asn1_str
    elif isinstance(name, x509.UniformResourceIdentifier):
        gn = backend._lib.GENERAL_NAME_new()
        backend.openssl_assert(gn != backend._ffi.NULL)
        asn1_str = _encode_asn1_str(
            backend, name._encoded, len(name._encoded)
        )
        gn.type = backend._lib.GEN_URI
        gn.d.uniformResourceIdentifier = asn1_str
    else:
        raise ValueError(
            "{0} is an unknown GeneralName type".format(name)
        )

    return gn


def _encode_extended_key_usage(backend, extended_key_usage):
    eku = backend._lib.sk_ASN1_OBJECT_new_null()
    eku = backend._ffi.gc(eku, backend._lib.sk_ASN1_OBJECT_free)
    for oid in extended_key_usage:
        obj = _txt2obj(backend, oid.dotted_string)
        res = backend._lib.sk_ASN1_OBJECT_push(eku, obj)
        backend.openssl_assert(res >= 1)

    eku_ptr = backend._ffi.cast("EXTENDED_KEY_USAGE *", eku)
    return _encode_extension_to_der(
        backend, backend._lib.i2d_EXTENDED_KEY_USAGE, eku_ptr
    )


_CRLREASONFLAGS = {
    x509.ReasonFlags.key_compromise: 1,
    x509.ReasonFlags.ca_compromise: 2,
    x509.ReasonFlags.affiliation_changed: 3,
    x509.ReasonFlags.superseded: 4,
    x509.ReasonFlags.cessation_of_operation: 5,
    x509.ReasonFlags.certificate_hold: 6,
    x509.ReasonFlags.privilege_withdrawn: 7,
    x509.ReasonFlags.aa_compromise: 8,
}


def _encode_crl_distribution_points(backend, crl_distribution_points):
    cdp = backend._lib.sk_DIST_POINT_new_null()
    cdp = backend._ffi.gc(cdp, backend._lib.sk_DIST_POINT_free)
    for point in crl_distribution_points:
        dp = backend._lib.DIST_POINT_new()
        backend.openssl_assert(dp != backend._ffi.NULL)

        if point.reasons:
            bitmask = backend._lib.ASN1_BIT_STRING_new()
            backend.openssl_assert(bitmask != backend._ffi.NULL)
            dp.reasons = bitmask
            for reason in point.reasons:
                res = backend._lib.ASN1_BIT_STRING_set_bit(
                    bitmask, _CRLREASONFLAGS[reason], 1
                )
                backend.openssl_assert(res == 1)

        if point.full_name:
            dpn = backend._lib.DIST_POINT_NAME_new()
            backend.openssl_assert(dpn != backend._ffi.NULL)
            dpn.type = _DISTPOINT_TYPE_FULLNAME
            dpn.name.fullname = _encode_general_names(backend, point.full_name)
            dp.distpoint = dpn

        if point.relative_name:
            dpn = backend._lib.DIST_POINT_NAME_new()
            backend.openssl_assert(dpn != backend._ffi.NULL)
            dpn.type = _DISTPOINT_TYPE_RELATIVENAME
            name = _encode_name_gc(backend, point.relative_name)
            relativename = backend._lib.sk_X509_NAME_ENTRY_dup(name.entries)
            backend.openssl_assert(relativename != backend._ffi.NULL)
            dpn.name.relativename = relativename
            dp.distpoint = dpn

        if point.crl_issuer:
            dp.CRLissuer = _encode_general_names(backend, point.crl_issuer)

        res = backend._lib.sk_DIST_POINT_push(cdp, dp)
        backend.openssl_assert(res >= 1)

    return _encode_extension_to_der(
        backend, backend._lib.i2d_CRL_DIST_POINTS, cdp
    )


def _encode_name_constraints(backend, name_constraints):
    nc = backend._lib.NAME_CONSTRAINTS_new()
    assert nc != backend._ffi.NULL
    nc = backend._ffi.gc(nc, backend._lib.NAME_CONSTRAINTS_free)
    permitted = _encode_general_subtree(
        backend, name_constraints.permitted_subtrees
    )
    nc.permittedSubtrees = permitted
    excluded = _encode_general_subtree(
        backend, name_constraints.excluded_subtrees
    )
    nc.excludedSubtrees = excluded

    return _encode_extension_to_der(
        backend, backend._lib.Cryptography_i2d_NAME_CONSTRAINTS, nc
    )


def _encode_general_subtree(backend, subtrees):
    if subtrees is None:
        return backend._ffi.NULL
    else:
        general_subtrees = backend._lib.sk_GENERAL_SUBTREE_new_null()
        for name in subtrees:
            gs = backend._lib.GENERAL_SUBTREE_new()
            gs.base = _encode_general_name(backend, name)
            res = backend._lib.sk_GENERAL_SUBTREE_push(general_subtrees, gs)
            assert res >= 1

        return general_subtrees


_EXTENSION_ENCODE_HANDLERS = {
    ExtensionOID.BASIC_CONSTRAINTS: _encode_basic_constraints,
    ExtensionOID.SUBJECT_KEY_IDENTIFIER: _encode_subject_key_identifier,
    ExtensionOID.KEY_USAGE: _encode_key_usage,
    ExtensionOID.SUBJECT_ALTERNATIVE_NAME: _encode_alt_name,
    ExtensionOID.ISSUER_ALTERNATIVE_NAME: _encode_alt_name,
    ExtensionOID.EXTENDED_KEY_USAGE: _encode_extended_key_usage,
    ExtensionOID.AUTHORITY_KEY_IDENTIFIER: _encode_authority_key_identifier,
    ExtensionOID.CERTIFICATE_POLICIES: _encode_certificate_policies,
    ExtensionOID.AUTHORITY_INFORMATION_ACCESS: (
        _encode_authority_information_access
    ),
    ExtensionOID.CRL_DISTRIBUTION_POINTS: _encode_crl_distribution_points,
    ExtensionOID.INHIBIT_ANY_POLICY: _encode_inhibit_any_policy,
    ExtensionOID.OCSP_NO_CHECK: _encode_ocsp_nocheck,
    ExtensionOID.NAME_CONSTRAINTS: _encode_name_constraints,
}

_CRL_EXTENSION_ENCODE_HANDLERS = {
    ExtensionOID.ISSUER_ALTERNATIVE_NAME: _encode_alt_name,
    ExtensionOID.AUTHORITY_KEY_IDENTIFIER: _encode_authority_key_identifier,
    ExtensionOID.AUTHORITY_INFORMATION_ACCESS: (
        _encode_authority_information_access
    ),
    ExtensionOID.CRL_NUMBER: _encode_crl_number,
}

_CRL_ENTRY_EXTENSION_ENCODE_HANDLERS = {
    CRLEntryExtensionOID.CERTIFICATE_ISSUER: _encode_alt_name,
    CRLEntryExtensionOID.CRL_REASON: _encode_crl_reason,
    CRLEntryExtensionOID.INVALIDITY_DATE: _encode_invalidity_date,
}


class _PasswordUserdata(object):
    def __init__(self, password):
        self.password = password
        self.called = 0
        self.exception = None


@binding.ffi_callback("int (char *, int, int, void *)",
                      name="Cryptography_pem_password_cb")
def _pem_password_cb(buf, size, writing, userdata_handle):
    """
    A pem_password_cb function pointer that copied the password to
    OpenSSL as required and returns the number of bytes copied.

    typedef int pem_password_cb(char *buf, int size,
                                int rwflag, void *userdata);

    Useful for decrypting PKCS8 files and so on.

    The userdata pointer must point to a cffi handle of a
    _PasswordUserdata instance.
    """
    ud = _ffi.from_handle(userdata_handle)
    ud.called += 1

    if not ud.password:
        ud.exception = TypeError(
            "Password was not given but private key is encrypted."
        )
        return -1
    elif len(ud.password) < size:
        pw_buf = _ffi.buffer(buf, size)
        pw_buf[:len(ud.password)] = ud.password
        return len(ud.password)
    else:
        ud.exception = ValueError(
            "Passwords longer than {0} bytes are not supported "
            "by this backend.".format(size - 1)
        )
        return 0


@utils.register_interface(CipherBackend)
@utils.register_interface(CMACBackend)
@utils.register_interface(DERSerializationBackend)
@utils.register_interface(DSABackend)
@utils.register_interface(EllipticCurveBackend)
@utils.register_interface(HashBackend)
@utils.register_interface(HMACBackend)
@utils.register_interface(PBKDF2HMACBackend)
@utils.register_interface(RSABackend)
@utils.register_interface(PEMSerializationBackend)
@utils.register_interface(X509Backend)
class Backend(object):
    """
    OpenSSL API binding interfaces.
    """
    name = "openssl"

    def __init__(self):
        self._binding = binding.Binding()
        self._ffi = self._binding.ffi
        self._lib = self._binding.lib

        # Set the default string mask for encoding ASN1 strings to UTF8. This
        # is the default for newer OpenSSLs for several years and is
        # recommended in RFC 2459.
        res = self._lib.ASN1_STRING_set_default_mask_asc(b"utf8only")
        self.openssl_assert(res == 1)

        self._cipher_registry = {}
        self._register_default_ciphers()
        self.activate_osrandom_engine()

    def openssl_assert(self, ok):
        return binding._openssl_assert(self._lib, ok)

    def activate_builtin_random(self):
        # Obtain a new structural reference.
        e = self._lib.ENGINE_get_default_RAND()
        if e != self._ffi.NULL:
            self._lib.ENGINE_unregister_RAND(e)
            # Reset the RNG to use the new engine.
            self._lib.RAND_cleanup()
            # decrement the structural reference from get_default_RAND
            res = self._lib.ENGINE_finish(e)
            self.openssl_assert(res == 1)

    def activate_osrandom_engine(self):
        # Unregister and free the current engine.
        self.activate_builtin_random()
        # Fetches an engine by id and returns it. This creates a structural
        # reference.
        e = self._lib.ENGINE_by_id(self._binding._osrandom_engine_id)
        self.openssl_assert(e != self._ffi.NULL)
        # Initialize the engine for use. This adds a functional reference.
        res = self._lib.ENGINE_init(e)
        self.openssl_assert(res == 1)
        # Set the engine as the default RAND provider.
        res = self._lib.ENGINE_set_default_RAND(e)
        self.openssl_assert(res == 1)
        # Decrement the structural ref incremented by ENGINE_by_id.
        res = self._lib.ENGINE_free(e)
        self.openssl_assert(res == 1)
        # Decrement the functional ref incremented by ENGINE_init.
        res = self._lib.ENGINE_finish(e)
        self.openssl_assert(res == 1)
        # Reset the RNG to use the new engine.
        self._lib.RAND_cleanup()

    def openssl_version_text(self):
        """
        Friendly string name of the loaded OpenSSL library. This is not
        necessarily the same version as it was compiled against.

        Example: OpenSSL 1.0.1e 11 Feb 2013
        """
        return self._ffi.string(
            self._lib.SSLeay_version(self._lib.SSLEAY_VERSION)
        ).decode("ascii")

    def create_hmac_ctx(self, key, algorithm):
        return _HMACContext(self, key, algorithm)

    def hash_supported(self, algorithm):
        digest = self._lib.EVP_get_digestbyname(algorithm.name.encode("ascii"))
        return digest != self._ffi.NULL

    def hmac_supported(self, algorithm):
        return self.hash_supported(algorithm)

    def create_hash_ctx(self, algorithm):
        return _HashContext(self, algorithm)

    def cipher_supported(self, cipher, mode):
        if self._evp_cipher_supported(cipher, mode):
            return True
        elif isinstance(mode, CTR) and isinstance(cipher, AES):
            return True
        else:
            return False

    def _evp_cipher_supported(self, cipher, mode):
        try:
            adapter = self._cipher_registry[type(cipher), type(mode)]
        except KeyError:
            return False
        evp_cipher = adapter(self, cipher, mode)
        return self._ffi.NULL != evp_cipher

    def register_cipher_adapter(self, cipher_cls, mode_cls, adapter):
        if (cipher_cls, mode_cls) in self._cipher_registry:
            raise ValueError("Duplicate registration for: {0} {1}.".format(
                cipher_cls, mode_cls)
            )
        self._cipher_registry[cipher_cls, mode_cls] = adapter

    def _register_default_ciphers(self):
        for mode_cls in [CBC, CTR, ECB, OFB, CFB, CFB8]:
            self.register_cipher_adapter(
                AES,
                mode_cls,
                GetCipherByName("{cipher.name}-{cipher.key_size}-{mode.name}")
            )
        for mode_cls in [CBC, CTR, ECB, OFB, CFB]:
            self.register_cipher_adapter(
                Camellia,
                mode_cls,
                GetCipherByName("{cipher.name}-{cipher.key_size}-{mode.name}")
            )
        for mode_cls in [CBC, CFB, CFB8, OFB]:
            self.register_cipher_adapter(
                TripleDES,
                mode_cls,
                GetCipherByName("des-ede3-{mode.name}")
            )
        self.register_cipher_adapter(
            TripleDES,
            ECB,
            GetCipherByName("des-ede3")
        )
        for mode_cls in [CBC, CFB, OFB, ECB]:
            self.register_cipher_adapter(
                Blowfish,
                mode_cls,
                GetCipherByName("bf-{mode.name}")
            )
        for mode_cls in [CBC, CFB, OFB, ECB]:
            self.register_cipher_adapter(
                SEED,
                mode_cls,
                GetCipherByName("seed-{mode.name}")
            )
        for cipher_cls, mode_cls in itertools.product(
            [CAST5, IDEA],
            [CBC, OFB, CFB, ECB],
        ):
            self.register_cipher_adapter(
                cipher_cls,
                mode_cls,
                GetCipherByName("{cipher.name}-{mode.name}")
            )
        self.register_cipher_adapter(
            ARC4,
            type(None),
            GetCipherByName("rc4")
        )
        self.register_cipher_adapter(
            AES,
            GCM,
            GetCipherByName("{cipher.name}-{cipher.key_size}-{mode.name}")
        )

    def create_symmetric_encryption_ctx(self, cipher, mode):
        if (isinstance(mode, CTR) and isinstance(cipher, AES) and
                not self._evp_cipher_supported(cipher, mode)):
            # This is needed to provide support for AES CTR mode in OpenSSL
            # 0.9.8. It can be removed when we drop 0.9.8 support (RHEL 5
            # extended life ends 2020).
            return _AESCTRCipherContext(self, cipher, mode)
        else:
            return _CipherContext(self, cipher, mode, _CipherContext._ENCRYPT)

    def create_symmetric_decryption_ctx(self, cipher, mode):
        if (isinstance(mode, CTR) and isinstance(cipher, AES) and
                not self._evp_cipher_supported(cipher, mode)):
            # This is needed to provide support for AES CTR mode in OpenSSL
            # 0.9.8. It can be removed when we drop 0.9.8 support (RHEL 5
            # extended life ends 2020).
            return _AESCTRCipherContext(self, cipher, mode)
        else:
            return _CipherContext(self, cipher, mode, _CipherContext._DECRYPT)

    def pbkdf2_hmac_supported(self, algorithm):
        if self._lib.Cryptography_HAS_PBKDF2_HMAC:
            return self.hmac_supported(algorithm)
        else:
            # OpenSSL < 1.0.0 has an explicit PBKDF2-HMAC-SHA1 function,
            # so if the PBKDF2_HMAC function is missing we only support
            # SHA1 via PBKDF2_HMAC_SHA1.
            return isinstance(algorithm, hashes.SHA1)

    def derive_pbkdf2_hmac(self, algorithm, length, salt, iterations,
                           key_material):
        buf = self._ffi.new("char[]", length)
        if self._lib.Cryptography_HAS_PBKDF2_HMAC:
            evp_md = self._lib.EVP_get_digestbyname(
                algorithm.name.encode("ascii"))
            self.openssl_assert(evp_md != self._ffi.NULL)
            res = self._lib.PKCS5_PBKDF2_HMAC(
                key_material,
                len(key_material),
                salt,
                len(salt),
                iterations,
                evp_md,
                length,
                buf
            )
            self.openssl_assert(res == 1)
        else:
            if not isinstance(algorithm, hashes.SHA1):
                raise UnsupportedAlgorithm(
                    "This version of OpenSSL only supports PBKDF2HMAC with "
                    "SHA1.",
                    _Reasons.UNSUPPORTED_HASH
                )
            res = self._lib.PKCS5_PBKDF2_HMAC_SHA1(
                key_material,
                len(key_material),
                salt,
                len(salt),
                iterations,
                length,
                buf
            )
            self.openssl_assert(res == 1)

        return self._ffi.buffer(buf)[:]

    def _consume_errors(self):
        return binding._consume_errors(self._lib)

    def _bn_to_int(self, bn):
        assert bn != self._ffi.NULL
        if six.PY3:
            # Python 3 has constant time from_bytes, so use that.
            bn_num_bytes = self._lib.BN_num_bytes(bn)
            bin_ptr = self._ffi.new("unsigned char[]", bn_num_bytes)
            bin_len = self._lib.BN_bn2bin(bn, bin_ptr)
            # A zero length means the BN has value 0
            self.openssl_assert(bin_len >= 0)
            return int.from_bytes(self._ffi.buffer(bin_ptr)[:bin_len], "big")
        else:
            # Under Python 2 the best we can do is hex()
            hex_cdata = self._lib.BN_bn2hex(bn)
            self.openssl_assert(hex_cdata != self._ffi.NULL)
            hex_str = self._ffi.string(hex_cdata)
            self._lib.OPENSSL_free(hex_cdata)
            return int(hex_str, 16)

    def _int_to_bn(self, num, bn=None):
        """
        Converts a python integer to a BIGNUM. The returned BIGNUM will not
        be garbage collected (to support adding them to structs that take
        ownership of the object). Be sure to register it for GC if it will
        be discarded after use.
        """
        assert bn is None or bn != self._ffi.NULL

        if bn is None:
            bn = self._ffi.NULL

        if six.PY3:
            # Python 3 has constant time to_bytes, so use that.

            binary = num.to_bytes(int(num.bit_length() / 8.0 + 1), "big")
            bn_ptr = self._lib.BN_bin2bn(binary, len(binary), bn)
            self.openssl_assert(bn_ptr != self._ffi.NULL)
            return bn_ptr

        else:
            # Under Python 2 the best we can do is hex()

            hex_num = hex(num).rstrip("L").lstrip("0x").encode("ascii") or b"0"
            bn_ptr = self._ffi.new("BIGNUM **")
            bn_ptr[0] = bn
            res = self._lib.BN_hex2bn(bn_ptr, hex_num)
            self.openssl_assert(res != 0)
            self.openssl_assert(bn_ptr[0] != self._ffi.NULL)
            return bn_ptr[0]

    def generate_rsa_private_key(self, public_exponent, key_size):
        rsa._verify_rsa_parameters(public_exponent, key_size)

        rsa_cdata = self._lib.RSA_new()
        self.openssl_assert(rsa_cdata != self._ffi.NULL)
        rsa_cdata = self._ffi.gc(rsa_cdata, self._lib.RSA_free)

        bn = self._int_to_bn(public_exponent)
        bn = self._ffi.gc(bn, self._lib.BN_free)

        res = self._lib.RSA_generate_key_ex(
            rsa_cdata, key_size, bn, self._ffi.NULL
        )
        self.openssl_assert(res == 1)
        evp_pkey = self._rsa_cdata_to_evp_pkey(rsa_cdata)

        return _RSAPrivateKey(self, rsa_cdata, evp_pkey)

    def generate_rsa_parameters_supported(self, public_exponent, key_size):
        return (public_exponent >= 3 and public_exponent & 1 != 0 and
                key_size >= 512)

    def load_rsa_private_numbers(self, numbers):
        rsa._check_private_key_components(
            numbers.p,
            numbers.q,
            numbers.d,
            numbers.dmp1,
            numbers.dmq1,
            numbers.iqmp,
            numbers.public_numbers.e,
            numbers.public_numbers.n
        )
        rsa_cdata = self._lib.RSA_new()
        self.openssl_assert(rsa_cdata != self._ffi.NULL)
        rsa_cdata = self._ffi.gc(rsa_cdata, self._lib.RSA_free)
        rsa_cdata.p = self._int_to_bn(numbers.p)
        rsa_cdata.q = self._int_to_bn(numbers.q)
        rsa_cdata.d = self._int_to_bn(numbers.d)
        rsa_cdata.dmp1 = self._int_to_bn(numbers.dmp1)
        rsa_cdata.dmq1 = self._int_to_bn(numbers.dmq1)
        rsa_cdata.iqmp = self._int_to_bn(numbers.iqmp)
        rsa_cdata.e = self._int_to_bn(numbers.public_numbers.e)
        rsa_cdata.n = self._int_to_bn(numbers.public_numbers.n)
        res = self._lib.RSA_blinding_on(rsa_cdata, self._ffi.NULL)
        self.openssl_assert(res == 1)
        evp_pkey = self._rsa_cdata_to_evp_pkey(rsa_cdata)

        return _RSAPrivateKey(self, rsa_cdata, evp_pkey)

    def load_rsa_public_numbers(self, numbers):
        rsa._check_public_key_components(numbers.e, numbers.n)
        rsa_cdata = self._lib.RSA_new()
        self.openssl_assert(rsa_cdata != self._ffi.NULL)
        rsa_cdata = self._ffi.gc(rsa_cdata, self._lib.RSA_free)
        rsa_cdata.e = self._int_to_bn(numbers.e)
        rsa_cdata.n = self._int_to_bn(numbers.n)
        res = self._lib.RSA_blinding_on(rsa_cdata, self._ffi.NULL)
        self.openssl_assert(res == 1)
        evp_pkey = self._rsa_cdata_to_evp_pkey(rsa_cdata)

        return _RSAPublicKey(self, rsa_cdata, evp_pkey)

    def _create_evp_pkey_gc(self):
        evp_pkey = self._lib.EVP_PKEY_new()
        self.openssl_assert(evp_pkey != self._ffi.NULL)
        evp_pkey = self._ffi.gc(evp_pkey, self._lib.EVP_PKEY_free)
        return evp_pkey

    def _rsa_cdata_to_evp_pkey(self, rsa_cdata):
        evp_pkey = self._create_evp_pkey_gc()
        res = self._lib.EVP_PKEY_set1_RSA(evp_pkey, rsa_cdata)
        self.openssl_assert(res == 1)
        return evp_pkey

    def _bytes_to_bio(self, data):
        """
        Return a _MemoryBIO namedtuple of (BIO, char*).

        The char* is the storage for the BIO and it must stay alive until the
        BIO is finished with.
        """
        data_char_p = self._ffi.new("char[]", data)
        bio = self._lib.BIO_new_mem_buf(
            data_char_p, len(data)
        )
        self.openssl_assert(bio != self._ffi.NULL)

        return _MemoryBIO(self._ffi.gc(bio, self._lib.BIO_free), data_char_p)

    def _create_mem_bio_gc(self):
        """
        Creates an empty memory BIO.
        """
        bio_method = self._lib.BIO_s_mem()
        self.openssl_assert(bio_method != self._ffi.NULL)
        bio = self._lib.BIO_new(bio_method)
        self.openssl_assert(bio != self._ffi.NULL)
        bio = self._ffi.gc(bio, self._lib.BIO_free)
        return bio

    def _read_mem_bio(self, bio):
        """
        Reads a memory BIO. This only works on memory BIOs.
        """
        buf = self._ffi.new("char **")
        buf_len = self._lib.BIO_get_mem_data(bio, buf)
        self.openssl_assert(buf_len > 0)
        self.openssl_assert(buf[0] != self._ffi.NULL)
        bio_data = self._ffi.buffer(buf[0], buf_len)[:]
        return bio_data

    def _evp_pkey_to_private_key(self, evp_pkey):
        """
        Return the appropriate type of PrivateKey given an evp_pkey cdata
        pointer.
        """

        key_type = self._lib.Cryptography_EVP_PKEY_id(evp_pkey)

        if key_type == self._lib.EVP_PKEY_RSA:
            rsa_cdata = self._lib.EVP_PKEY_get1_RSA(evp_pkey)
            self.openssl_assert(rsa_cdata != self._ffi.NULL)
            rsa_cdata = self._ffi.gc(rsa_cdata, self._lib.RSA_free)
            return _RSAPrivateKey(self, rsa_cdata, evp_pkey)
        elif key_type == self._lib.EVP_PKEY_DSA:
            dsa_cdata = self._lib.EVP_PKEY_get1_DSA(evp_pkey)
            self.openssl_assert(dsa_cdata != self._ffi.NULL)
            dsa_cdata = self._ffi.gc(dsa_cdata, self._lib.DSA_free)
            return _DSAPrivateKey(self, dsa_cdata, evp_pkey)
        elif (self._lib.Cryptography_HAS_EC == 1 and
              key_type == self._lib.EVP_PKEY_EC):
            ec_cdata = self._lib.EVP_PKEY_get1_EC_KEY(evp_pkey)
            self.openssl_assert(ec_cdata != self._ffi.NULL)
            ec_cdata = self._ffi.gc(ec_cdata, self._lib.EC_KEY_free)
            return _EllipticCurvePrivateKey(self, ec_cdata, evp_pkey)
        else:
            raise UnsupportedAlgorithm("Unsupported key type.")

    def _evp_pkey_to_public_key(self, evp_pkey):
        """
        Return the appropriate type of PublicKey given an evp_pkey cdata
        pointer.
        """

        key_type = self._lib.Cryptography_EVP_PKEY_id(evp_pkey)

        if key_type == self._lib.EVP_PKEY_RSA:
            rsa_cdata = self._lib.EVP_PKEY_get1_RSA(evp_pkey)
            self.openssl_assert(rsa_cdata != self._ffi.NULL)
            rsa_cdata = self._ffi.gc(rsa_cdata, self._lib.RSA_free)
            return _RSAPublicKey(self, rsa_cdata, evp_pkey)
        elif key_type == self._lib.EVP_PKEY_DSA:
            dsa_cdata = self._lib.EVP_PKEY_get1_DSA(evp_pkey)
            self.openssl_assert(dsa_cdata != self._ffi.NULL)
            dsa_cdata = self._ffi.gc(dsa_cdata, self._lib.DSA_free)
            return _DSAPublicKey(self, dsa_cdata, evp_pkey)
        elif (self._lib.Cryptography_HAS_EC == 1 and
              key_type == self._lib.EVP_PKEY_EC):
            ec_cdata = self._lib.EVP_PKEY_get1_EC_KEY(evp_pkey)
            self.openssl_assert(ec_cdata != self._ffi.NULL)
            ec_cdata = self._ffi.gc(ec_cdata, self._lib.EC_KEY_free)
            return _EllipticCurvePublicKey(self, ec_cdata, evp_pkey)
        else:
            raise UnsupportedAlgorithm("Unsupported key type.")

    def _pem_password_cb(self, password):
        """
        Generate a pem_password_cb function pointer that copied the password to
        OpenSSL as required and returns the number of bytes copied.

        typedef int pem_password_cb(char *buf, int size,
                                    int rwflag, void *userdata);

        Useful for decrypting PKCS8 files and so on.

        Returns a tuple of (cdata function pointer, userdata).
        """
        # Forward compatibility for new static callbacks:
        # _pem_password_cb is not a nested function because closures don't
        # work well with static callbacks. Static callbacks are registered
        # globally. The backend is passed in as userdata argument.

        userdata = _PasswordUserdata(password=password)
        return _pem_password_cb, userdata

    def _mgf1_hash_supported(self, algorithm):
        if self._lib.Cryptography_HAS_MGF1_MD:
            return self.hash_supported(algorithm)
        else:
            return isinstance(algorithm, hashes.SHA1)

    def rsa_padding_supported(self, padding):
        if isinstance(padding, PKCS1v15):
            return True
        elif isinstance(padding, PSS) and isinstance(padding._mgf, MGF1):
            return self._mgf1_hash_supported(padding._mgf._algorithm)
        elif isinstance(padding, OAEP) and isinstance(padding._mgf, MGF1):
            return isinstance(padding._mgf._algorithm, hashes.SHA1)
        else:
            return False

    def generate_dsa_parameters(self, key_size):
        if key_size not in (1024, 2048, 3072):
            raise ValueError("Key size must be 1024 or 2048 or 3072 bits.")

        if (self._lib.OPENSSL_VERSION_NUMBER < 0x1000000f and
                key_size > 1024):
            raise ValueError(
                "Key size must be 1024 because OpenSSL < 1.0.0 doesn't "
                "support larger key sizes.")

        ctx = self._lib.DSA_new()
        self.openssl_assert(ctx != self._ffi.NULL)
        ctx = self._ffi.gc(ctx, self._lib.DSA_free)

        res = self._lib.DSA_generate_parameters_ex(
            ctx, key_size, self._ffi.NULL, 0,
            self._ffi.NULL, self._ffi.NULL, self._ffi.NULL
        )

        self.openssl_assert(res == 1)

        return _DSAParameters(self, ctx)

    def generate_dsa_private_key(self, parameters):
        ctx = self._lib.DSA_new()
        self.openssl_assert(ctx != self._ffi.NULL)
        ctx = self._ffi.gc(ctx, self._lib.DSA_free)
        ctx.p = self._lib.BN_dup(parameters._dsa_cdata.p)
        ctx.q = self._lib.BN_dup(parameters._dsa_cdata.q)
        ctx.g = self._lib.BN_dup(parameters._dsa_cdata.g)

        self._lib.DSA_generate_key(ctx)
        evp_pkey = self._dsa_cdata_to_evp_pkey(ctx)

        return _DSAPrivateKey(self, ctx, evp_pkey)

    def generate_dsa_private_key_and_parameters(self, key_size):
        parameters = self.generate_dsa_parameters(key_size)
        return self.generate_dsa_private_key(parameters)

    def load_dsa_private_numbers(self, numbers):
        dsa._check_dsa_private_numbers(numbers)
        parameter_numbers = numbers.public_numbers.parameter_numbers

        dsa_cdata = self._lib.DSA_new()
        self.openssl_assert(dsa_cdata != self._ffi.NULL)
        dsa_cdata = self._ffi.gc(dsa_cdata, self._lib.DSA_free)

        dsa_cdata.p = self._int_to_bn(parameter_numbers.p)
        dsa_cdata.q = self._int_to_bn(parameter_numbers.q)
        dsa_cdata.g = self._int_to_bn(parameter_numbers.g)
        dsa_cdata.pub_key = self._int_to_bn(numbers.public_numbers.y)
        dsa_cdata.priv_key = self._int_to_bn(numbers.x)

        evp_pkey = self._dsa_cdata_to_evp_pkey(dsa_cdata)

        return _DSAPrivateKey(self, dsa_cdata, evp_pkey)

    def load_dsa_public_numbers(self, numbers):
        dsa._check_dsa_parameters(numbers.parameter_numbers)
        dsa_cdata = self._lib.DSA_new()
        self.openssl_assert(dsa_cdata != self._ffi.NULL)
        dsa_cdata = self._ffi.gc(dsa_cdata, self._lib.DSA_free)

        dsa_cdata.p = self._int_to_bn(numbers.parameter_numbers.p)
        dsa_cdata.q = self._int_to_bn(numbers.parameter_numbers.q)
        dsa_cdata.g = self._int_to_bn(numbers.parameter_numbers.g)
        dsa_cdata.pub_key = self._int_to_bn(numbers.y)

        evp_pkey = self._dsa_cdata_to_evp_pkey(dsa_cdata)

        return _DSAPublicKey(self, dsa_cdata, evp_pkey)

    def load_dsa_parameter_numbers(self, numbers):
        dsa._check_dsa_parameters(numbers)
        dsa_cdata = self._lib.DSA_new()
        self.openssl_assert(dsa_cdata != self._ffi.NULL)
        dsa_cdata = self._ffi.gc(dsa_cdata, self._lib.DSA_free)

        dsa_cdata.p = self._int_to_bn(numbers.p)
        dsa_cdata.q = self._int_to_bn(numbers.q)
        dsa_cdata.g = self._int_to_bn(numbers.g)

        return _DSAParameters(self, dsa_cdata)

    def _dsa_cdata_to_evp_pkey(self, dsa_cdata):
        evp_pkey = self._create_evp_pkey_gc()
        res = self._lib.EVP_PKEY_set1_DSA(evp_pkey, dsa_cdata)
        self.openssl_assert(res == 1)
        return evp_pkey

    def dsa_hash_supported(self, algorithm):
        if self._lib.OPENSSL_VERSION_NUMBER < 0x1000000f:
            return isinstance(algorithm, hashes.SHA1)
        else:
            return self.hash_supported(algorithm)

    def dsa_parameters_supported(self, p, q, g):
        if self._lib.OPENSSL_VERSION_NUMBER < 0x1000000f:
            return utils.bit_length(p) <= 1024 and utils.bit_length(q) <= 160
        else:
            return True

    def cmac_algorithm_supported(self, algorithm):
        return (
            self._lib.Cryptography_HAS_CMAC == 1 and
            self.cipher_supported(
                algorithm, CBC(b"\x00" * algorithm.block_size)
            )
        )

    def create_cmac_ctx(self, algorithm):
        return _CMACContext(self, algorithm)

    def create_x509_csr(self, builder, private_key, algorithm):
        if not isinstance(algorithm, hashes.HashAlgorithm):
            raise TypeError('Algorithm must be a registered hash algorithm.')

        if self._lib.OPENSSL_VERSION_NUMBER <= 0x10001000:
            if isinstance(private_key, _DSAPrivateKey):
                raise NotImplementedError(
                    "Certificate signing requests aren't implemented for DSA"
                    " keys on OpenSSL versions less than 1.0.1."
                )
            if isinstance(private_key, _EllipticCurvePrivateKey):
                raise NotImplementedError(
                    "Certificate signing requests aren't implemented for EC"
                    " keys on OpenSSL versions less than 1.0.1."
                )

        # Resolve the signature algorithm.
        evp_md = self._lib.EVP_get_digestbyname(
            algorithm.name.encode('ascii')
        )
        self.openssl_assert(evp_md != self._ffi.NULL)

        # Create an empty request.
        x509_req = self._lib.X509_REQ_new()
        self.openssl_assert(x509_req != self._ffi.NULL)
        x509_req = self._ffi.gc(x509_req, self._lib.X509_REQ_free)

        # Set x509 version.
        res = self._lib.X509_REQ_set_version(x509_req, x509.Version.v1.value)
        self.openssl_assert(res == 1)

        # Set subject name.
        res = self._lib.X509_REQ_set_subject_name(
            x509_req, _encode_name_gc(self, builder._subject_name)
        )
        self.openssl_assert(res == 1)

        # Set subject public key.
        public_key = private_key.public_key()
        res = self._lib.X509_REQ_set_pubkey(
            x509_req, public_key._evp_pkey
        )
        self.openssl_assert(res == 1)

        # Add extensions.
        sk_extension = self._lib.sk_X509_EXTENSION_new_null()
        self.openssl_assert(sk_extension != self._ffi.NULL)
        sk_extension = self._ffi.gc(
            sk_extension, self._lib.sk_X509_EXTENSION_free
        )
        # gc is not necessary for CSRs, as sk_X509_EXTENSION_free
        # will release all the X509_EXTENSIONs.
        self._create_x509_extensions(
            extensions=builder._extensions,
            handlers=_EXTENSION_ENCODE_HANDLERS,
            x509_obj=sk_extension,
            add_func=self._lib.sk_X509_EXTENSION_insert,
            gc=False
        )
        res = self._lib.X509_REQ_add_extensions(x509_req, sk_extension)
        self.openssl_assert(res == 1)

        # Sign the request using the requester's private key.
        res = self._lib.X509_REQ_sign(
            x509_req, private_key._evp_pkey, evp_md
        )
        if res == 0:
            errors = self._consume_errors()
            self.openssl_assert(errors[0][1] == self._lib.ERR_LIB_RSA)
            self.openssl_assert(
                errors[0][3] == self._lib.RSA_R_DIGEST_TOO_BIG_FOR_RSA_KEY
            )
            raise ValueError("Digest too big for RSA key")

        return _CertificateSigningRequest(self, x509_req)

    def create_x509_certificate(self, builder, private_key, algorithm):
        if not isinstance(builder, x509.CertificateBuilder):
            raise TypeError('Builder type mismatch.')
        if not isinstance(algorithm, hashes.HashAlgorithm):
            raise TypeError('Algorithm must be a registered hash algorithm.')

        if self._lib.OPENSSL_VERSION_NUMBER <= 0x10001000:
            if isinstance(private_key, _DSAPrivateKey):
                raise NotImplementedError(
                    "Certificate signatures aren't implemented for DSA"
                    " keys on OpenSSL versions less than 1.0.1."
                )
            if isinstance(private_key, _EllipticCurvePrivateKey):
                raise NotImplementedError(
                    "Certificate signatures aren't implemented for EC"
                    " keys on OpenSSL versions less than 1.0.1."
                )

        # Resolve the signature algorithm.
        evp_md = self._lib.EVP_get_digestbyname(
            algorithm.name.encode('ascii')
        )
        self.openssl_assert(evp_md != self._ffi.NULL)

        # Create an empty certificate.
        x509_cert = self._lib.X509_new()
        x509_cert = self._ffi.gc(x509_cert, backend._lib.X509_free)

        # Set the x509 version.
        res = self._lib.X509_set_version(x509_cert, builder._version.value)
        self.openssl_assert(res == 1)

        # Set the subject's name.
        res = self._lib.X509_set_subject_name(
            x509_cert, _encode_name_gc(self, list(builder._subject_name))
        )
        self.openssl_assert(res == 1)

        # Set the subject's public key.
        res = self._lib.X509_set_pubkey(
            x509_cert, builder._public_key._evp_pkey
        )
        self.openssl_assert(res == 1)

        # Set the certificate serial number.
        serial_number = _encode_asn1_int_gc(self, builder._serial_number)
        res = self._lib.X509_set_serialNumber(x509_cert, serial_number)
        self.openssl_assert(res == 1)

        # Set the "not before" time.
        res = self._lib.ASN1_TIME_set(
            self._lib.X509_get_notBefore(x509_cert),
            calendar.timegm(builder._not_valid_before.timetuple())
        )
        self.openssl_assert(res != self._ffi.NULL)

        # Set the "not after" time.
        res = self._lib.ASN1_TIME_set(
            self._lib.X509_get_notAfter(x509_cert),
            calendar.timegm(builder._not_valid_after.timetuple())
        )
        self.openssl_assert(res != self._ffi.NULL)

        # Add extensions.
        self._create_x509_extensions(
            extensions=builder._extensions,
            handlers=_EXTENSION_ENCODE_HANDLERS,
            x509_obj=x509_cert,
            add_func=self._lib.X509_add_ext,
            gc=True
        )

        # Set the issuer name.
        res = self._lib.X509_set_issuer_name(
            x509_cert, _encode_name_gc(self, list(builder._issuer_name))
        )
        self.openssl_assert(res == 1)

        # Sign the certificate with the issuer's private key.
        res = self._lib.X509_sign(
            x509_cert, private_key._evp_pkey, evp_md
        )
        if res == 0:
            errors = self._consume_errors()
            self.openssl_assert(errors[0][1] == self._lib.ERR_LIB_RSA)
            self.openssl_assert(
                errors[0][3] == self._lib.RSA_R_DIGEST_TOO_BIG_FOR_RSA_KEY
            )
            raise ValueError("Digest too big for RSA key")

        return _Certificate(self, x509_cert)

    def create_x509_crl(self, builder, private_key, algorithm):
        if not isinstance(builder, x509.CertificateRevocationListBuilder):
            raise TypeError('Builder type mismatch.')
        if not isinstance(algorithm, hashes.HashAlgorithm):
            raise TypeError('Algorithm must be a registered hash algorithm.')

        if self._lib.OPENSSL_VERSION_NUMBER <= 0x10001000:
            if isinstance(private_key, _DSAPrivateKey):
                raise NotImplementedError(
                    "CRL signatures aren't implemented for DSA"
                    " keys on OpenSSL versions less than 1.0.1."
                )
            if isinstance(private_key, _EllipticCurvePrivateKey):
                raise NotImplementedError(
                    "CRL signatures aren't implemented for EC"
                    " keys on OpenSSL versions less than 1.0.1."
                )

        evp_md = self._lib.EVP_get_digestbyname(
            algorithm.name.encode('ascii')
        )
        self.openssl_assert(evp_md != self._ffi.NULL)

        # Create an empty CRL.
        x509_crl = self._lib.X509_CRL_new()
        x509_crl = self._ffi.gc(x509_crl, backend._lib.X509_CRL_free)

        # Set the x509 CRL version. We only support v2 (integer value 1).
        res = self._lib.X509_CRL_set_version(x509_crl, 1)
        self.openssl_assert(res == 1)

        # Set the issuer name.
        res = self._lib.X509_CRL_set_issuer_name(
            x509_crl, _encode_name_gc(self, list(builder._issuer_name))
        )
        self.openssl_assert(res == 1)

        # Set the last update time.
        last_update = self._lib.ASN1_TIME_set(
            self._ffi.NULL, calendar.timegm(builder._last_update.timetuple())
        )
        self.openssl_assert(last_update != self._ffi.NULL)
        last_update = self._ffi.gc(last_update, self._lib.ASN1_TIME_free)
        res = self._lib.X509_CRL_set_lastUpdate(x509_crl, last_update)
        self.openssl_assert(res == 1)

        # Set the next update time.
        next_update = self._lib.ASN1_TIME_set(
            self._ffi.NULL, calendar.timegm(builder._next_update.timetuple())
        )
        self.openssl_assert(next_update != self._ffi.NULL)
        next_update = self._ffi.gc(next_update, self._lib.ASN1_TIME_free)
        res = self._lib.X509_CRL_set_nextUpdate(x509_crl, next_update)
        self.openssl_assert(res == 1)

        # Add extensions.
        self._create_x509_extensions(
            extensions=builder._extensions,
            handlers=_CRL_EXTENSION_ENCODE_HANDLERS,
            x509_obj=x509_crl,
            add_func=self._lib.X509_CRL_add_ext,
            gc=True
        )

        # add revoked certificates
        for revoked_cert in builder._revoked_certificates:
            # Duplicating because the X509_CRL takes ownership and will free
            # this memory when X509_CRL_free is called.
            revoked = self._lib.Cryptography_X509_REVOKED_dup(
                revoked_cert._x509_revoked
            )
            self.openssl_assert(revoked != self._ffi.NULL)
            res = self._lib.X509_CRL_add0_revoked(x509_crl, revoked)
            self.openssl_assert(res == 1)

        res = self._lib.X509_CRL_sign(
            x509_crl, private_key._evp_pkey, evp_md
        )
        if res == 0:
            errors = self._consume_errors()
            self.openssl_assert(errors[0][1] == self._lib.ERR_LIB_RSA)
            self.openssl_assert(
                errors[0][3] == self._lib.RSA_R_DIGEST_TOO_BIG_FOR_RSA_KEY
            )
            raise ValueError("Digest too big for RSA key")

        return _CertificateRevocationList(self, x509_crl)

    def _create_x509_extensions(self, extensions, handlers, x509_obj,
                                add_func, gc):
        for i, extension in enumerate(extensions):
            try:
                encode = handlers[extension.oid]
            except KeyError:
                raise NotImplementedError(
                    'Extension not supported: {0}'.format(extension.oid)
                )

            pp, r = encode(self, extension.value)
            obj = _txt2obj_gc(self, extension.oid.dotted_string)
            x509_extension = self._lib.X509_EXTENSION_create_by_OBJ(
                self._ffi.NULL,
                obj,
                1 if extension.critical else 0,
                _encode_asn1_str_gc(self, pp[0], r)
            )
            self.openssl_assert(x509_extension != self._ffi.NULL)
            if gc:
                x509_extension = self._ffi.gc(
                    x509_extension, self._lib.X509_EXTENSION_free
                )
            res = add_func(x509_obj, x509_extension, i)
            self.openssl_assert(res >= 1)

    def create_x509_revoked_certificate(self, builder):
        if not isinstance(builder, x509.RevokedCertificateBuilder):
            raise TypeError('Builder type mismatch.')

        x509_revoked = self._lib.X509_REVOKED_new()
        self.openssl_assert(x509_revoked != self._ffi.NULL)
        x509_revoked = self._ffi.gc(x509_revoked, self._lib.X509_REVOKED_free)
        serial_number = _encode_asn1_int_gc(self, builder._serial_number)
        res = self._lib.X509_REVOKED_set_serialNumber(
            x509_revoked, serial_number
        )
        self.openssl_assert(res == 1)
        res = self._lib.ASN1_TIME_set(
            x509_revoked.revocationDate,
            calendar.timegm(builder._revocation_date.timetuple())
        )
        self.openssl_assert(res != self._ffi.NULL)
        # add CRL entry extensions
        self._create_x509_extensions(
            extensions=builder._extensions,
            handlers=_CRL_ENTRY_EXTENSION_ENCODE_HANDLERS,
            x509_obj=x509_revoked,
            add_func=self._lib.X509_REVOKED_add_ext,
            gc=True
        )
        return _RevokedCertificate(self, None, x509_revoked)

    def load_pem_private_key(self, data, password):
        return self._load_key(
            self._lib.PEM_read_bio_PrivateKey,
            self._evp_pkey_to_private_key,
            data,
            password,
        )

    def load_pem_public_key(self, data):
        mem_bio = self._bytes_to_bio(data)
        evp_pkey = self._lib.PEM_read_bio_PUBKEY(
            mem_bio.bio, self._ffi.NULL, self._ffi.NULL, self._ffi.NULL
        )
        if evp_pkey != self._ffi.NULL:
            evp_pkey = self._ffi.gc(evp_pkey, self._lib.EVP_PKEY_free)
            return self._evp_pkey_to_public_key(evp_pkey)
        else:
            # It's not a (RSA/DSA/ECDSA) subjectPublicKeyInfo, but we still
            # need to check to see if it is a pure PKCS1 RSA public key (not
            # embedded in a subjectPublicKeyInfo)
            self._consume_errors()
            res = self._lib.BIO_reset(mem_bio.bio)
            self.openssl_assert(res == 1)
            rsa_cdata = self._lib.PEM_read_bio_RSAPublicKey(
                mem_bio.bio, self._ffi.NULL, self._ffi.NULL, self._ffi.NULL
            )
            if rsa_cdata != self._ffi.NULL:
                rsa_cdata = self._ffi.gc(rsa_cdata, self._lib.RSA_free)
                evp_pkey = self._rsa_cdata_to_evp_pkey(rsa_cdata)
                return _RSAPublicKey(self, rsa_cdata, evp_pkey)
            else:
                self._handle_key_loading_error()

    def load_der_private_key(self, data, password):
        # OpenSSL has a function called d2i_AutoPrivateKey that can simplify
        # this. Unfortunately it doesn't properly support PKCS8 on OpenSSL
        # 0.9.8 so we can't use it. Instead we sequentially try to load it 3
        # different ways. First we'll try to load it as a traditional key
        bio_data = self._bytes_to_bio(data)
        key = self._evp_pkey_from_der_traditional_key(bio_data, password)
        if not key:
            # Okay so it's not a traditional key. Let's try
            # PKCS8 unencrypted. OpenSSL 0.9.8 can't load unencrypted
            # PKCS8 keys using d2i_PKCS8PrivateKey_bio so we do this instead.
            # Reset the memory BIO so we can read the data again.
            res = self._lib.BIO_reset(bio_data.bio)
            self.openssl_assert(res == 1)
            key = self._evp_pkey_from_der_unencrypted_pkcs8(bio_data, password)

        if key:
            return self._evp_pkey_to_private_key(key)
        else:
            # Finally we try to load it with the method that handles encrypted
            # PKCS8 properly.
            return self._load_key(
                self._lib.d2i_PKCS8PrivateKey_bio,
                self._evp_pkey_to_private_key,
                data,
                password,
            )

    def _evp_pkey_from_der_traditional_key(self, bio_data, password):
        key = self._lib.d2i_PrivateKey_bio(bio_data.bio, self._ffi.NULL)
        if key != self._ffi.NULL:
            key = self._ffi.gc(key, self._lib.EVP_PKEY_free)
            if password is not None:
                raise TypeError(
                    "Password was given but private key is not encrypted."
                )

            return key
        else:
            self._consume_errors()
            return None

    def _evp_pkey_from_der_unencrypted_pkcs8(self, bio_data, password):
        info = self._lib.d2i_PKCS8_PRIV_KEY_INFO_bio(
            bio_data.bio, self._ffi.NULL
        )
        info = self._ffi.gc(info, self._lib.PKCS8_PRIV_KEY_INFO_free)
        if info != self._ffi.NULL:
            key = self._lib.EVP_PKCS82PKEY(info)
            self.openssl_assert(key != self._ffi.NULL)
            key = self._ffi.gc(key, self._lib.EVP_PKEY_free)
            if password is not None:
                raise TypeError(
                    "Password was given but private key is not encrypted."
                )
            return key
        else:
            self._consume_errors()
            return None

    def load_der_public_key(self, data):
        mem_bio = self._bytes_to_bio(data)
        evp_pkey = self._lib.d2i_PUBKEY_bio(mem_bio.bio, self._ffi.NULL)
        if evp_pkey != self._ffi.NULL:
            evp_pkey = self._ffi.gc(evp_pkey, self._lib.EVP_PKEY_free)
            return self._evp_pkey_to_public_key(evp_pkey)
        else:
            # It's not a (RSA/DSA/ECDSA) subjectPublicKeyInfo, but we still
            # need to check to see if it is a pure PKCS1 RSA public key (not
            # embedded in a subjectPublicKeyInfo)
            self._consume_errors()
            res = self._lib.BIO_reset(mem_bio.bio)
            self.openssl_assert(res == 1)
            rsa_cdata = self._lib.d2i_RSAPublicKey_bio(
                mem_bio.bio, self._ffi.NULL
            )
            if rsa_cdata != self._ffi.NULL:
                rsa_cdata = self._ffi.gc(rsa_cdata, self._lib.RSA_free)
                evp_pkey = self._rsa_cdata_to_evp_pkey(rsa_cdata)
                return _RSAPublicKey(self, rsa_cdata, evp_pkey)
            else:
                self._handle_key_loading_error()

    def load_pem_x509_certificate(self, data):
        mem_bio = self._bytes_to_bio(data)
        x509 = self._lib.PEM_read_bio_X509(
            mem_bio.bio, self._ffi.NULL, self._ffi.NULL, self._ffi.NULL
        )
        if x509 == self._ffi.NULL:
            self._consume_errors()
            raise ValueError("Unable to load certificate")

        x509 = self._ffi.gc(x509, self._lib.X509_free)
        return _Certificate(self, x509)

    def load_der_x509_certificate(self, data):
        mem_bio = self._bytes_to_bio(data)
        x509 = self._lib.d2i_X509_bio(mem_bio.bio, self._ffi.NULL)
        if x509 == self._ffi.NULL:
            self._consume_errors()
            raise ValueError("Unable to load certificate")

        x509 = self._ffi.gc(x509, self._lib.X509_free)
        return _Certificate(self, x509)

    def load_pem_x509_crl(self, data):
        mem_bio = self._bytes_to_bio(data)
        x509_crl = self._lib.PEM_read_bio_X509_CRL(
            mem_bio.bio, self._ffi.NULL, self._ffi.NULL, self._ffi.NULL
        )
        if x509_crl == self._ffi.NULL:
            self._consume_errors()
            raise ValueError("Unable to load CRL")

        x509_crl = self._ffi.gc(x509_crl, self._lib.X509_CRL_free)
        return _CertificateRevocationList(self, x509_crl)

    def load_der_x509_crl(self, data):
        mem_bio = self._bytes_to_bio(data)
        x509_crl = self._lib.d2i_X509_CRL_bio(mem_bio.bio, self._ffi.NULL)
        if x509_crl == self._ffi.NULL:
            self._consume_errors()
            raise ValueError("Unable to load CRL")

        x509_crl = self._ffi.gc(x509_crl, self._lib.X509_CRL_free)
        return _CertificateRevocationList(self, x509_crl)

    def load_pem_x509_csr(self, data):
        mem_bio = self._bytes_to_bio(data)
        x509_req = self._lib.PEM_read_bio_X509_REQ(
            mem_bio.bio, self._ffi.NULL, self._ffi.NULL, self._ffi.NULL
        )
        if x509_req == self._ffi.NULL:
            self._consume_errors()
            raise ValueError("Unable to load request")

        x509_req = self._ffi.gc(x509_req, self._lib.X509_REQ_free)
        return _CertificateSigningRequest(self, x509_req)

    def load_der_x509_csr(self, data):
        mem_bio = self._bytes_to_bio(data)
        x509_req = self._lib.d2i_X509_REQ_bio(mem_bio.bio, self._ffi.NULL)
        if x509_req == self._ffi.NULL:
            self._consume_errors()
            raise ValueError("Unable to load request")

        x509_req = self._ffi.gc(x509_req, self._lib.X509_REQ_free)
        return _CertificateSigningRequest(self, x509_req)

    def _load_key(self, openssl_read_func, convert_func, data, password):
        mem_bio = self._bytes_to_bio(data)

        password_cb, userdata = self._pem_password_cb(password)
        userdata_handle = self._ffi.new_handle(userdata)

        evp_pkey = openssl_read_func(
            mem_bio.bio,
            self._ffi.NULL,
            password_cb,
            userdata_handle,
        )

        if evp_pkey == self._ffi.NULL:
            if userdata.exception is not None:
                errors = self._consume_errors()
                self.openssl_assert(errors)
                raise userdata.exception
            else:
                self._handle_key_loading_error()

        evp_pkey = self._ffi.gc(evp_pkey, self._lib.EVP_PKEY_free)

        if password is not None and userdata.called == 0:
            raise TypeError(
                "Password was given but private key is not encrypted.")

        assert (
            (password is not None and userdata.called == 1) or
            password is None
        )

        return convert_func(evp_pkey)

    def _handle_key_loading_error(self):
        errors = self._consume_errors()

        if not errors:
            raise ValueError("Could not unserialize key data.")

        elif errors[0][1:] in (
            (
                self._lib.ERR_LIB_EVP,
                self._lib.EVP_F_EVP_DECRYPTFINAL_EX,
                self._lib.EVP_R_BAD_DECRYPT
            ),
            (
                self._lib.ERR_LIB_PKCS12,
                self._lib.PKCS12_F_PKCS12_PBE_CRYPT,
                self._lib.PKCS12_R_PKCS12_CIPHERFINAL_ERROR,
            )
        ):
            raise ValueError("Bad decrypt. Incorrect password?")

        elif errors[0][1:] in (
            (
                self._lib.ERR_LIB_PEM,
                self._lib.PEM_F_PEM_GET_EVP_CIPHER_INFO,
                self._lib.PEM_R_UNSUPPORTED_ENCRYPTION
            ),

            (
                self._lib.ERR_LIB_EVP,
                self._lib.EVP_F_EVP_PBE_CIPHERINIT,
                self._lib.EVP_R_UNKNOWN_PBE_ALGORITHM
            )
        ):
            raise UnsupportedAlgorithm(
                "PEM data is encrypted with an unsupported cipher",
                _Reasons.UNSUPPORTED_CIPHER
            )

        elif any(
            error[1:] == (
                self._lib.ERR_LIB_EVP,
                self._lib.EVP_F_EVP_PKCS82PKEY,
                self._lib.EVP_R_UNSUPPORTED_PRIVATE_KEY_ALGORITHM
            )
            for error in errors
        ):
            raise UnsupportedAlgorithm(
                "Unsupported public key algorithm.",
                _Reasons.UNSUPPORTED_PUBLIC_KEY_ALGORITHM
            )

        else:
            assert errors[0][1] in (
                self._lib.ERR_LIB_EVP,
                self._lib.ERR_LIB_PEM,
                self._lib.ERR_LIB_ASN1,
            )
            raise ValueError("Could not unserialize key data.")

    def elliptic_curve_supported(self, curve):
        if self._lib.Cryptography_HAS_EC != 1:
            return False

        try:
            curve_nid = self._elliptic_curve_to_nid(curve)
        except UnsupportedAlgorithm:
            curve_nid = self._lib.NID_undef

        ctx = self._lib.EC_GROUP_new_by_curve_name(curve_nid)

        if ctx == self._ffi.NULL:
            errors = self._consume_errors()
            self.openssl_assert(
                curve_nid == self._lib.NID_undef or
                errors[0][1:] == (
                    self._lib.ERR_LIB_EC,
                    self._lib.EC_F_EC_GROUP_NEW_BY_CURVE_NAME,
                    self._lib.EC_R_UNKNOWN_GROUP
                )
            )
            return False
        else:
            self.openssl_assert(curve_nid != self._lib.NID_undef)
            self._lib.EC_GROUP_free(ctx)
            return True

    def elliptic_curve_signature_algorithm_supported(
        self, signature_algorithm, curve
    ):
        if self._lib.Cryptography_HAS_EC != 1:
            return False

        # We only support ECDSA right now.
        if not isinstance(signature_algorithm, ec.ECDSA):
            return False

        # Before 0.9.8m OpenSSL can't cope with digests longer than the curve.
        if (
            self._lib.OPENSSL_VERSION_NUMBER < 0x009080df and
            curve.key_size < signature_algorithm.algorithm.digest_size * 8
        ):
            return False

        return self.elliptic_curve_supported(curve)

    def generate_elliptic_curve_private_key(self, curve):
        """
        Generate a new private key on the named curve.
        """

        if self.elliptic_curve_supported(curve):
            curve_nid = self._elliptic_curve_to_nid(curve)

            ec_cdata = self._lib.EC_KEY_new_by_curve_name(curve_nid)
            self.openssl_assert(ec_cdata != self._ffi.NULL)
            ec_cdata = self._ffi.gc(ec_cdata, self._lib.EC_KEY_free)

            res = self._lib.EC_KEY_generate_key(ec_cdata)
            self.openssl_assert(res == 1)

            res = self._lib.EC_KEY_check_key(ec_cdata)
            self.openssl_assert(res == 1)

            evp_pkey = self._ec_cdata_to_evp_pkey(ec_cdata)

            return _EllipticCurvePrivateKey(self, ec_cdata, evp_pkey)
        else:
            raise UnsupportedAlgorithm(
                "Backend object does not support {0}.".format(curve.name),
                _Reasons.UNSUPPORTED_ELLIPTIC_CURVE
            )

    def load_elliptic_curve_private_numbers(self, numbers):
        public = numbers.public_numbers

        curve_nid = self._elliptic_curve_to_nid(public.curve)

        ec_cdata = self._lib.EC_KEY_new_by_curve_name(curve_nid)
        self.openssl_assert(ec_cdata != self._ffi.NULL)
        ec_cdata = self._ffi.gc(ec_cdata, self._lib.EC_KEY_free)

        ec_cdata = self._ec_key_set_public_key_affine_coordinates(
            ec_cdata, public.x, public.y)

        res = self._lib.EC_KEY_set_private_key(
            ec_cdata, self._int_to_bn(numbers.private_value))
        self.openssl_assert(res == 1)
        evp_pkey = self._ec_cdata_to_evp_pkey(ec_cdata)

        return _EllipticCurvePrivateKey(self, ec_cdata, evp_pkey)

    def load_elliptic_curve_public_numbers(self, numbers):
        curve_nid = self._elliptic_curve_to_nid(numbers.curve)

        ec_cdata = self._lib.EC_KEY_new_by_curve_name(curve_nid)
        self.openssl_assert(ec_cdata != self._ffi.NULL)
        ec_cdata = self._ffi.gc(ec_cdata, self._lib.EC_KEY_free)

        ec_cdata = self._ec_key_set_public_key_affine_coordinates(
            ec_cdata, numbers.x, numbers.y)
        evp_pkey = self._ec_cdata_to_evp_pkey(ec_cdata)

        return _EllipticCurvePublicKey(self, ec_cdata, evp_pkey)

    def elliptic_curve_exchange_algorithm_supported(self, algorithm, curve):
        return (
            self.elliptic_curve_supported(curve) and
            self._lib.Cryptography_HAS_ECDH == 1 and
            isinstance(algorithm, ec.ECDH)
        )

    def _ec_cdata_to_evp_pkey(self, ec_cdata):
        evp_pkey = self._create_evp_pkey_gc()
        res = self._lib.EVP_PKEY_set1_EC_KEY(evp_pkey, ec_cdata)
        self.openssl_assert(res == 1)
        return evp_pkey

    def _elliptic_curve_to_nid(self, curve):
        """
        Get the NID for a curve name.
        """

        curve_aliases = {
            "secp192r1": "prime192v1",
            "secp256r1": "prime256v1"
        }

        curve_name = curve_aliases.get(curve.name, curve.name)

        curve_nid = self._lib.OBJ_sn2nid(curve_name.encode())
        if curve_nid == self._lib.NID_undef:
            raise UnsupportedAlgorithm(
                "{0} is not a supported elliptic curve".format(curve.name),
                _Reasons.UNSUPPORTED_ELLIPTIC_CURVE
            )
        return curve_nid

    @contextmanager
    def _tmp_bn_ctx(self):
        bn_ctx = self._lib.BN_CTX_new()
        self.openssl_assert(bn_ctx != self._ffi.NULL)
        bn_ctx = self._ffi.gc(bn_ctx, self._lib.BN_CTX_free)
        self._lib.BN_CTX_start(bn_ctx)
        try:
            yield bn_ctx
        finally:
            self._lib.BN_CTX_end(bn_ctx)

    def _ec_key_determine_group_get_set_funcs(self, ctx):
        """
        Given an EC_KEY determine the group and what methods are required to
        get/set point coordinates.
        """
        self.openssl_assert(ctx != self._ffi.NULL)

        nid_two_field = self._lib.OBJ_sn2nid(b"characteristic-two-field")
        self.openssl_assert(nid_two_field != self._lib.NID_undef)

        group = self._lib.EC_KEY_get0_group(ctx)
        self.openssl_assert(group != self._ffi.NULL)

        method = self._lib.EC_GROUP_method_of(group)
        self.openssl_assert(method != self._ffi.NULL)

        nid = self._lib.EC_METHOD_get_field_type(method)
        self.openssl_assert(nid != self._lib.NID_undef)

        if nid == nid_two_field and self._lib.Cryptography_HAS_EC2M:
            set_func = self._lib.EC_POINT_set_affine_coordinates_GF2m
            get_func = self._lib.EC_POINT_get_affine_coordinates_GF2m
        else:
            set_func = self._lib.EC_POINT_set_affine_coordinates_GFp
            get_func = self._lib.EC_POINT_get_affine_coordinates_GFp

        assert set_func and get_func

        return set_func, get_func, group

    def _ec_key_set_public_key_affine_coordinates(self, ctx, x, y):
        """
        This is a port of EC_KEY_set_public_key_affine_coordinates that was
        added in 1.0.1.

        Sets the public key point in the EC_KEY context to the affine x and y
        values.
        """

        if x < 0 or y < 0:
            raise ValueError(
                "Invalid EC key. Both x and y must be non-negative."
            )

        set_func, get_func, group = (
            self._ec_key_determine_group_get_set_funcs(ctx)
        )

        point = self._lib.EC_POINT_new(group)
        self.openssl_assert(point != self._ffi.NULL)
        point = self._ffi.gc(point, self._lib.EC_POINT_free)

        bn_x = self._int_to_bn(x)
        bn_y = self._int_to_bn(y)

        with self._tmp_bn_ctx() as bn_ctx:
            check_x = self._lib.BN_CTX_get(bn_ctx)
            check_y = self._lib.BN_CTX_get(bn_ctx)

            res = set_func(group, point, bn_x, bn_y, bn_ctx)
            self.openssl_assert(res == 1)

            res = get_func(group, point, check_x, check_y, bn_ctx)
            self.openssl_assert(res == 1)

            res = self._lib.BN_cmp(bn_x, check_x)
            if res != 0:
                self._consume_errors()
                raise ValueError("Invalid EC Key X point.")
            res = self._lib.BN_cmp(bn_y, check_y)
            if res != 0:
                self._consume_errors()
                raise ValueError("Invalid EC Key Y point.")

        res = self._lib.EC_KEY_set_public_key(ctx, point)
        self.openssl_assert(res == 1)

        res = self._lib.EC_KEY_check_key(ctx)
        if res != 1:
            self._consume_errors()
            raise ValueError("Invalid EC key.")

        return ctx

    def _private_key_bytes(self, encoding, format, encryption_algorithm,
                           evp_pkey, cdata):
        if not isinstance(format, serialization.PrivateFormat):
            raise TypeError(
                "format must be an item from the PrivateFormat enum"
            )

        if not isinstance(encryption_algorithm,
                          serialization.KeySerializationEncryption):
            raise TypeError(
                "Encryption algorithm must be a KeySerializationEncryption "
                "instance"
            )

        if isinstance(encryption_algorithm, serialization.NoEncryption):
            password = b""
            passlen = 0
            evp_cipher = self._ffi.NULL
        elif isinstance(encryption_algorithm,
                        serialization.BestAvailableEncryption):
            # This is a curated value that we will update over time.
            evp_cipher = self._lib.EVP_get_cipherbyname(
                b"aes-256-cbc"
            )
            password = encryption_algorithm.password
            passlen = len(password)
            if passlen > 1023:
                raise ValueError(
                    "Passwords longer than 1023 bytes are not supported by "
                    "this backend"
                )
        else:
            raise ValueError("Unsupported encryption type")

        key_type = self._lib.Cryptography_EVP_PKEY_id(evp_pkey)
        if encoding is serialization.Encoding.PEM:
            if format is serialization.PrivateFormat.PKCS8:
                write_bio = self._lib.PEM_write_bio_PKCS8PrivateKey
                key = evp_pkey
            else:
                assert format is serialization.PrivateFormat.TraditionalOpenSSL
                if key_type == self._lib.EVP_PKEY_RSA:
                    write_bio = self._lib.PEM_write_bio_RSAPrivateKey
                elif key_type == self._lib.EVP_PKEY_DSA:
                    write_bio = self._lib.PEM_write_bio_DSAPrivateKey
                else:
                    assert self._lib.Cryptography_HAS_EC == 1
                    assert key_type == self._lib.EVP_PKEY_EC
                    write_bio = self._lib.PEM_write_bio_ECPrivateKey

                key = cdata
        elif encoding is serialization.Encoding.DER:
            if format is serialization.PrivateFormat.TraditionalOpenSSL:
                if not isinstance(
                    encryption_algorithm, serialization.NoEncryption
                ):
                    raise ValueError(
                        "Encryption is not supported for DER encoded "
                        "traditional OpenSSL keys"
                    )

                return self._private_key_bytes_traditional_der(key_type, cdata)
            else:
                assert format is serialization.PrivateFormat.PKCS8
                write_bio = self._lib.i2d_PKCS8PrivateKey_bio
                key = evp_pkey
        else:
            raise TypeError("encoding must be an item from the Encoding enum")

        bio = self._create_mem_bio_gc()
        res = write_bio(
            bio,
            key,
            evp_cipher,
            password,
            passlen,
            self._ffi.NULL,
            self._ffi.NULL
        )
        self.openssl_assert(res == 1)
        return self._read_mem_bio(bio)

    def _private_key_bytes_traditional_der(self, key_type, cdata):
        if key_type == self._lib.EVP_PKEY_RSA:
            write_bio = self._lib.i2d_RSAPrivateKey_bio
        elif (self._lib.Cryptography_HAS_EC == 1 and
              key_type == self._lib.EVP_PKEY_EC):
            write_bio = self._lib.i2d_ECPrivateKey_bio
        else:
            self.openssl_assert(key_type == self._lib.EVP_PKEY_DSA)
            write_bio = self._lib.i2d_DSAPrivateKey_bio

        bio = self._create_mem_bio_gc()
        res = write_bio(bio, cdata)
        self.openssl_assert(res == 1)
        return self._read_mem_bio(bio)

    def _public_key_bytes(self, encoding, format, evp_pkey, cdata):
        if not isinstance(encoding, serialization.Encoding):
            raise TypeError("encoding must be an item from the Encoding enum")

        if format is serialization.PublicFormat.SubjectPublicKeyInfo:
            if encoding is serialization.Encoding.PEM:
                write_bio = self._lib.PEM_write_bio_PUBKEY
            else:
                assert encoding is serialization.Encoding.DER
                write_bio = self._lib.i2d_PUBKEY_bio

            key = evp_pkey
        elif format is serialization.PublicFormat.PKCS1:
            # Only RSA is supported here.
            assert self._lib.Cryptography_EVP_PKEY_id(
                evp_pkey
            ) == self._lib.EVP_PKEY_RSA
            if encoding is serialization.Encoding.PEM:
                write_bio = self._lib.PEM_write_bio_RSAPublicKey
            else:
                assert encoding is serialization.Encoding.DER
                write_bio = self._lib.i2d_RSAPublicKey_bio

            key = cdata
        else:
            raise TypeError(
                "format must be an item from the PublicFormat enum"
            )

        bio = self._create_mem_bio_gc()
        res = write_bio(bio, key)
        self.openssl_assert(res == 1)
        return self._read_mem_bio(bio)

    def _asn1_integer_to_int(self, asn1_int):
        bn = self._lib.ASN1_INTEGER_to_BN(asn1_int, self._ffi.NULL)
        self.openssl_assert(bn != self._ffi.NULL)
        bn = self._ffi.gc(bn, self._lib.BN_free)
        return self._bn_to_int(bn)

    def _asn1_string_to_bytes(self, asn1_string):
        return self._ffi.buffer(asn1_string.data, asn1_string.length)[:]

    def _asn1_string_to_ascii(self, asn1_string):
        return self._asn1_string_to_bytes(asn1_string).decode("ascii")

    def _asn1_string_to_utf8(self, asn1_string):
        buf = self._ffi.new("unsigned char **")
        res = self._lib.ASN1_STRING_to_UTF8(buf, asn1_string)
        self.openssl_assert(res >= 0)
        self.openssl_assert(buf[0] != self._ffi.NULL)
        buf = self._ffi.gc(
            buf, lambda buffer: self._lib.OPENSSL_free(buffer[0])
        )
        return self._ffi.buffer(buf[0], res)[:].decode('utf8')

    def _asn1_to_der(self, asn1_type):
        buf = self._ffi.new("unsigned char **")
        res = self._lib.i2d_ASN1_TYPE(asn1_type, buf)
        self.openssl_assert(res >= 0)
        self.openssl_assert(buf[0] != self._ffi.NULL)
        buf = self._ffi.gc(
            buf, lambda buffer: self._lib.OPENSSL_free(buffer[0])
        )
        return self._ffi.buffer(buf[0], res)[:]

    def _parse_asn1_time(self, asn1_time):
        self.openssl_assert(asn1_time != self._ffi.NULL)
        generalized_time = self._lib.ASN1_TIME_to_generalizedtime(
            asn1_time, self._ffi.NULL
        )
        self.openssl_assert(generalized_time != self._ffi.NULL)
        generalized_time = self._ffi.gc(
            generalized_time, self._lib.ASN1_GENERALIZEDTIME_free
        )
        return self._parse_asn1_generalized_time(generalized_time)

    def _parse_asn1_generalized_time(self, generalized_time):
        time = self._asn1_string_to_ascii(
            self._ffi.cast("ASN1_STRING *", generalized_time)
        )
        return datetime.datetime.strptime(time, "%Y%m%d%H%M%SZ")


class GetCipherByName(object):
    def __init__(self, fmt):
        self._fmt = fmt

    def __call__(self, backend, cipher, mode):
        cipher_name = self._fmt.format(cipher=cipher, mode=mode).lower()
        return backend._lib.EVP_get_cipherbyname(cipher_name.encode("ascii"))


backend = Backend()
