# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import absolute_import, division, print_function


def cryptography_has_ec2m():
    return [
        "EC_POINT_set_affine_coordinates_GF2m",
        "EC_POINT_get_affine_coordinates_GF2m",
        "EC_POINT_set_compressed_coordinates_GF2m",
    ]


def cryptography_has_ec_1_0_2():
    return [
        "EC_curve_nid2nist",
    ]


def cryptography_has_set_ecdh_auto():
    return [
        "SSL_CTX_set_ecdh_auto",
    ]


def cryptography_has_rsa_r_pkcs_decoding_error():
    return [
        "RSA_R_PKCS_DECODING_ERROR"
    ]


def cryptography_has_rsa_oaep_md():
    return [
        "EVP_PKEY_CTX_set_rsa_oaep_md",
    ]


def cryptography_has_rsa_oaep_label():
    return [
        "EVP_PKEY_CTX_set0_rsa_oaep_label",
    ]


def cryptography_has_ssl3_method():
    return [
        "SSLv3_method",
        "SSLv3_client_method",
        "SSLv3_server_method",
    ]


def cryptography_has_alpn():
    return [
        "SSL_CTX_set_alpn_protos",
        "SSL_set_alpn_protos",
        "SSL_CTX_set_alpn_select_cb",
        "SSL_get0_alpn_selected",
    ]


def cryptography_has_compression():
    return [
        "SSL_get_current_compression",
        "SSL_get_current_expansion",
        "SSL_COMP_get_name",
    ]


def cryptography_has_get_server_tmp_key():
    return [
        "SSL_get_server_tmp_key",
    ]


def cryptography_has_102_verification_error_codes():
    return [
        'X509_V_ERR_SUITE_B_INVALID_VERSION',
        'X509_V_ERR_SUITE_B_INVALID_ALGORITHM',
        'X509_V_ERR_SUITE_B_INVALID_CURVE',
        'X509_V_ERR_SUITE_B_INVALID_SIGNATURE_ALGORITHM',
        'X509_V_ERR_SUITE_B_LOS_NOT_ALLOWED',
        'X509_V_ERR_SUITE_B_CANNOT_SIGN_P_384_WITH_P_256',
        'X509_V_ERR_HOSTNAME_MISMATCH',
        'X509_V_ERR_EMAIL_MISMATCH',
        'X509_V_ERR_IP_ADDRESS_MISMATCH'
    ]


def cryptography_has_102_verification_params():
    return [
        "X509_V_FLAG_SUITEB_128_LOS_ONLY",
        "X509_V_FLAG_SUITEB_192_LOS",
        "X509_V_FLAG_SUITEB_128_LOS",
        "X509_VERIFY_PARAM_set1_host",
        "X509_VERIFY_PARAM_set1_email",
        "X509_VERIFY_PARAM_set1_ip",
        "X509_VERIFY_PARAM_set1_ip_asc",
        "X509_VERIFY_PARAM_set_hostflags",
    ]


def cryptography_has_x509_v_flag_trusted_first():
    return [
        "X509_V_FLAG_TRUSTED_FIRST",
    ]


def cryptography_has_x509_v_flag_partial_chain():
    return [
        "X509_V_FLAG_PARTIAL_CHAIN",
    ]


def cryptography_has_set_cert_cb():
    return [
        "SSL_CTX_set_cert_cb",
        "SSL_set_cert_cb",
    ]


def cryptography_has_ssl_st():
    return [
        "SSL_ST_BEFORE",
        "SSL_ST_OK",
        "SSL_ST_INIT",
        "SSL_ST_RENEGOTIATE",
    ]


def cryptography_has_tls_st():
    return [
        "TLS_ST_BEFORE",
        "TLS_ST_OK",
    ]


def cryptography_has_locking_callbacks():
    return [
        "CRYPTO_LOCK",
        "CRYPTO_UNLOCK",
        "CRYPTO_READ",
        "CRYPTO_LOCK_SSL",
        "CRYPTO_lock",
    ]


def cryptography_has_scrypt():
    return [
        "EVP_PBE_scrypt",
    ]


def cryptography_has_generic_dtls_method():
    return [
        "DTLS_method",
        "DTLS_server_method",
        "DTLS_client_method",
        "SSL_OP_NO_DTLSv1",
        "SSL_OP_NO_DTLSv1_2",
        "DTLS_set_link_mtu",
        "DTLS_get_link_min_mtu",
    ]


def cryptography_has_evp_pkey_dhx():
    return [
        "EVP_PKEY_DHX",
    ]


def cryptography_has_mem_functions():
    return [
        "Cryptography_CRYPTO_set_mem_functions",
    ]


def cryptography_has_sct():
    return [
        "SCT_get_version",
        "SCT_get_log_entry_type",
        "SCT_get0_log_id",
        "SCT_get_timestamp",
        "SCT_set_source",
        "sk_SCT_num",
        "sk_SCT_value",
        "SCT_LIST_free",
    ]


def cryptography_has_x509_store_ctx_get_issuer():
    return [
        "X509_STORE_get_get_issuer",
        "X509_STORE_set_get_issuer",
    ]


def cryptography_has_x25519():
    return [
        "EVP_PKEY_X25519",
        "NID_X25519",
    ]


def cryptography_has_evp_pkey_get_set_tls_encodedpoint():
    return [
        "EVP_PKEY_get1_tls_encodedpoint",
        "EVP_PKEY_set1_tls_encodedpoint",
    ]


def cryptography_has_fips():
    return [
        "FIPS_set_mode",
        "FIPS_mode",
    ]


def cryptography_has_ssl_sigalgs():
    return [
        "SSL_CTX_set1_sigalgs_list",
        "SSL_get_sigalgs",
    ]


def cryptography_has_psk():
    return [
        "SSL_CTX_use_psk_identity_hint",
        "SSL_CTX_set_psk_server_callback",
        "SSL_CTX_set_psk_client_callback",
    ]


def cryptography_has_custom_ext():
    return [
        "SSL_CTX_add_client_custom_ext",
        "SSL_CTX_add_server_custom_ext",
        "SSL_extension_supported",
    ]


def cryptography_has_openssl_cleanup():
    return [
        "OPENSSL_cleanup",
    ]


# This is a mapping of
# {condition: function-returning-names-dependent-on-that-condition} so we can
# loop over them and delete unsupported names at runtime. It will be removed
# when cffi supports #if in cdef. We use functions instead of just a dict of
# lists so we can use coverage to measure which are used.
CONDITIONAL_NAMES = {
    "Cryptography_HAS_EC2M": cryptography_has_ec2m,
    "Cryptography_HAS_EC_1_0_2": cryptography_has_ec_1_0_2,
    "Cryptography_HAS_SET_ECDH_AUTO": cryptography_has_set_ecdh_auto,
    "Cryptography_HAS_RSA_R_PKCS_DECODING_ERROR": (
        cryptography_has_rsa_r_pkcs_decoding_error
    ),
    "Cryptography_HAS_RSA_OAEP_MD": cryptography_has_rsa_oaep_md,
    "Cryptography_HAS_RSA_OAEP_LABEL": cryptography_has_rsa_oaep_label,
    "Cryptography_HAS_SSL3_METHOD": cryptography_has_ssl3_method,
    "Cryptography_HAS_ALPN": cryptography_has_alpn,
    "Cryptography_HAS_COMPRESSION": cryptography_has_compression,
    "Cryptography_HAS_GET_SERVER_TMP_KEY": cryptography_has_get_server_tmp_key,
    "Cryptography_HAS_102_VERIFICATION_ERROR_CODES": (
        cryptography_has_102_verification_error_codes
    ),
    "Cryptography_HAS_102_VERIFICATION_PARAMS": (
        cryptography_has_102_verification_params
    ),
    "Cryptography_HAS_X509_V_FLAG_TRUSTED_FIRST": (
        cryptography_has_x509_v_flag_trusted_first
    ),
    "Cryptography_HAS_X509_V_FLAG_PARTIAL_CHAIN": (
        cryptography_has_x509_v_flag_partial_chain
    ),
    "Cryptography_HAS_SET_CERT_CB": cryptography_has_set_cert_cb,
    "Cryptography_HAS_SSL_ST": cryptography_has_ssl_st,
    "Cryptography_HAS_TLS_ST": cryptography_has_tls_st,
    "Cryptography_HAS_LOCKING_CALLBACKS": cryptography_has_locking_callbacks,
    "Cryptography_HAS_SCRYPT": cryptography_has_scrypt,
    "Cryptography_HAS_GENERIC_DTLS_METHOD": (
        cryptography_has_generic_dtls_method
    ),
    "Cryptography_HAS_EVP_PKEY_DHX": cryptography_has_evp_pkey_dhx,
    "Cryptography_HAS_MEM_FUNCTIONS": cryptography_has_mem_functions,
    "Cryptography_HAS_SCT": cryptography_has_sct,
    "Cryptography_HAS_X509_STORE_CTX_GET_ISSUER": (
        cryptography_has_x509_store_ctx_get_issuer
    ),
    "Cryptography_HAS_X25519": cryptography_has_x25519,
    "Cryptography_HAS_EVP_PKEY_get_set_tls_encodedpoint": (
        cryptography_has_evp_pkey_get_set_tls_encodedpoint
    ),
    "Cryptography_HAS_FIPS": cryptography_has_fips,
    "Cryptography_HAS_SIGALGS": cryptography_has_ssl_sigalgs,
    "Cryptography_HAS_PSK": cryptography_has_psk,
    "Cryptography_HAS_CUSTOM_EXT": cryptography_has_custom_ext,
    "Cryptography_HAS_OPENSSL_CLEANUP": cryptography_has_openssl_cleanup,
}
