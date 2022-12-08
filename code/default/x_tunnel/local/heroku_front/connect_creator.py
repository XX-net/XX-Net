
import socket

import utils


from front_base.connect_creator import ConnectCreator as ConnectCreatorBase


class ConnectCreator(ConnectCreatorBase):

    def check_cert(self, ssl_sock):
        try:
            peer_cert = ssl_sock.get_cert()
        except Exception as e:
            self.logger.exception("check_cert %r", e)
            raise e

        if self.debug:
            self.logger.debug("cert:%r", peer_cert)

        ip = utils.to_str(ssl_sock.ip_str.split(b":")[0])
        sni_check = self.host_manager.ip_map[ip]["sni_check"]
        policy = sni_check["policy"]

        if policy == "check_commonname":
            if not peer_cert["issuer_commonname"].startswith(sni_check["sni_check"]):
                raise socket.error(' certificate is issued by %r' % (peer_cert["issuer_commonname"]))
        elif policy == "check_altName":
            alt_name = sni_check["alt_name"]
            if alt_name not in peer_cert["altName"]:
                raise socket.error('check sni check_altName failed, alt_names:%s' % (peer_cert["altName"]))

        elif policy == "check_altName_postfix":
            alt_name = peer_cert["altName"]
            if isinstance(alt_name, str):
                if not ssl_sock.sni.endswith(alt_name):
                    raise socket.error('check %s sni:%s fail, alt_names:%s' % (ssl_sock.ip_str, ssl_sock.sni, alt_name))
            elif isinstance(alt_name, list):
                for alt_name_n in alt_name:
                    if ssl_sock.sni.endswith(alt_name_n):
                        return
                raise socket.error(
                    'check %s sni:%s fail, alt_names:%s' % (ssl_sock.ip_str, ssl_sock.sni, alt_name))
