# Authors:
#   Karel Srot
#
# See the LICENSE file for legal information regarding use of this file.

"""Class with various handshake helpers."""

from .extensions import PaddingExtension, PreSharedKeyExtension
from .utils.cryptomath import derive_secret, secureHMAC, HKDF_expand_label
from .utils.constanttime import ct_compare_digest
from .errors import TLSIllegalParameterException


class HandshakeHelpers(object):
    """
    This class encapsulates helper functions to be used with a TLS handshake.
    """

    @staticmethod
    def alignClientHelloPadding(clientHello):
        """
        Align ClientHello using the Padding extension to 512 bytes at least.

        :param ClientHello clientHello: ClientHello to be aligned
        """
        # Check clientHello size if padding extension should be added
        # we want to add the extension even when using just SSLv3
        # cut-off 4 bytes with the Hello header (ClientHello type + Length)
        clientHelloLength = len(clientHello.write()) - 4
        if 256 <= clientHelloLength <= 511:
            if clientHello.extensions is None:
                clientHello.extensions = []
                # we need to recalculate the size after extension list addition
                # results in extra 2 bytes, equals to
                # clientHelloLength = len(clientHello.write()) - 4
                clientHelloLength += 2
            # we want to get 512 bytes in total, including the padding
            # extension header (4B)
            paddingExtensionInstance = PaddingExtension().create(
                max(512 - clientHelloLength - 4, 0))
            clientHello.extensions.append(paddingExtensionInstance)

    @staticmethod
    def _calc_binder(prf, psk, handshake_hash, external=True):
        """
        Calculate the binder value for a given HandshakeHash (that includes
        a truncated client hello already)
        """
        assert prf in ('sha256', 'sha384')
        key_len = 32 if prf == 'sha256' else 48

        # HKDF-Extract(0, PSK)
        early_secret = secureHMAC(bytearray(key_len), psk, prf)
        if external:
            binder_key = derive_secret(early_secret, b"ext binder", None, prf)
        else:
            binder_key = derive_secret(early_secret, b"res binder", None, prf)
        finished_key = HKDF_expand_label(binder_key, b"finished", b"", key_len,
                                         prf)
        binder = secureHMAC(finished_key, handshake_hash.digest(prf), prf)
        return binder

    @staticmethod
    def calc_res_binder_psk(iden, res_master_secret, tickets):
        """Calculate PSK associated with provided ticket identity."""
        ticket = [i for i in tickets if i.ticket == iden.identity][0]

        ticket_hash = 'sha256' if len(res_master_secret) == 32 else 'sha384'

        psk = HKDF_expand_label(res_master_secret, b"resumption",
                                ticket.ticket_nonce, len(res_master_secret),
                                ticket_hash)
        return psk

    @staticmethod
    def update_binders(client_hello, handshake_hashes, psk_configs,
                       tickets=None, res_master_secret=None):
        """
        Sign the Client Hello using TLS 1.3 PSK binders.

        note: the psk_configs should be in the same order as the ones in the
        PreSharedKeyExtension extension (extra ones are ok)

        :param client_hello: ClientHello to sign
        :param handshake_hashes: hashes of messages exchanged so far
        :param psk_configs: PSK identities and secrets
        :param tickets: optional list of tickets received from server
        :param bytearray res_master_secret: secret associated with the
            tickets
        """
        ext = client_hello.extensions[-1]
        if not isinstance(ext, PreSharedKeyExtension):
            raise ValueError("Last extension in client_hello must be "
                             "PreSharedKeyExtension")
        if tickets and not res_master_secret:
            raise ValueError("Tickets require setting res_master_secret")

        hh = handshake_hashes.copy()

        hh.update(client_hello.psk_truncate())

        configs_iter = iter(psk_configs)
        ticket_idens = []
        if tickets:
            ticket_idens = [i.ticket for i in tickets]

        for i, iden in enumerate(ext.identities):
            # identities that are tickets don't carry PSK directly
            if iden.identity in ticket_idens:
                binder_hash = 'sha256' if len(res_master_secret) == 32 \
                    else 'sha384'
                psk = HandshakeHelpers.calc_res_binder_psk(
                    iden, res_master_secret, tickets)
                external = False
            else:
                try:
                    config = next(configs_iter)
                    while config[0] != iden.identity:
                        config = next(configs_iter)
                except StopIteration:
                    raise ValueError("psk_configs don't match the "
                                     "PreSharedKeyExtension")

                binder_hash = config[2] if len(config) > 2 else 'sha256'
                psk = config[1]
                external = True

            binder = HandshakeHelpers._calc_binder(binder_hash,
                                                   psk,
                                                   hh,
                                                   external)

            # replace the fake value with calculated one
            ext.binders[i] = binder

    @staticmethod
    def verify_binder(client_hello, handshake_hashes, position, secret, prf,
                      external=True):
        """Verify the PSK binder value in client hello.

        :param client_hello: ClientHello to verify
        :param handshake_hashes: hashes of messages exchanged so far
        :param position: binder at which position should be verified
        :param secret: the secret PSK
        :param prf: name of the hash used as PRF
        """
        ext = client_hello.extensions[-1]
        if not isinstance(ext, PreSharedKeyExtension):
            raise TLSIllegalParameterException(
                "Last extension in client_hello must be "
                "PreSharedKeyExtension")

        hh = handshake_hashes.copy()
        hh.update(client_hello.psk_truncate())

        binder = HandshakeHelpers._calc_binder(prf,
                                               secret,
                                               hh,
                                               external)

        if not ct_compare_digest(binder, ext.binders[position]):
            raise TLSIllegalParameterException("Binder does not verify")

        return True
