#!/usr/bin/env python
# coding:utf-8

import os
import sys
import glob
import binascii
import time
import random
import base64
import hashlib
import threading

import logging


current_path = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, os.pardir, 'python27', '1.0'))
if sys.platform == "win32":
    win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
    sys.path.append(win32_lib)
elif sys.platform == "linux" or sys.platform == "linux2":
    linux_lib = os.path.abspath( os.path.join(python_path, 'lib', 'linux'))
    sys.path.append(linux_lib)

import OpenSSL


class CertUtil(object):
    """CertUtil module, based on mitmproxy"""

    ca_vendor = 'GoAgent'
    ca_keyfile = 'CA.crt'
    ca_thumbprint = ''
    ca_certdir = 'certs'
    ca_lock = threading.Lock()

    @staticmethod
    def create_ca():
        key = OpenSSL.crypto.PKey()
        key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
        req = OpenSSL.crypto.X509Req()
        subj = req.get_subject()
        subj.countryName = 'CN'
        subj.stateOrProvinceName = 'Internet'
        subj.localityName = 'Cernet'
        subj.organizationName = CertUtil.ca_vendor
        subj.organizationalUnitName = '%s Root' % CertUtil.ca_vendor
        subj.commonName = '%s CA' % CertUtil.ca_vendor
        req.set_pubkey(key)
        req.sign(key, 'sha1')
        ca = OpenSSL.crypto.X509()
        ca.set_serial_number(0)
        ca.gmtime_adj_notBefore(0)
        ca.gmtime_adj_notAfter(24 * 60 * 60 * 3652)
        ca.set_issuer(req.get_subject())
        ca.set_subject(req.get_subject())
        ca.set_pubkey(req.get_pubkey())
        ca.sign(key, 'sha1')
        return key, ca

    @staticmethod
    def dump_ca():
        key, ca = CertUtil.create_ca()
        with open(CertUtil.ca_keyfile, 'wb') as fp:
            fp.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, ca))
            fp.write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key))

    @staticmethod
    def get_cert_serial_number(commonname):
        assert CertUtil.ca_thumbprint
        saltname = '%s|%s' % (CertUtil.ca_thumbprint, commonname)
        return int(hashlib.md5(saltname.encode('utf-8')).hexdigest(), 16)

    @staticmethod
    def _get_cert(commonname, sans=()):
        with open(CertUtil.ca_keyfile, 'rb') as fp:
            content = fp.read()
            key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, content)
            ca = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, content)

        pkey = OpenSSL.crypto.PKey()
        pkey.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)

        req = OpenSSL.crypto.X509Req()
        subj = req.get_subject()
        subj.countryName = 'CN'
        subj.stateOrProvinceName = 'Internet'
        subj.localityName = 'Cernet'
        subj.organizationalUnitName = '%s Branch' % CertUtil.ca_vendor
        if commonname[0] == '.':
            subj.commonName = '*' + commonname
            subj.organizationName = '*' + commonname
            sans = ['*'+commonname] + [x for x in sans if x != '*'+commonname]
        else:
            subj.commonName = commonname
            subj.organizationName = commonname
            sans = [commonname] + [x for x in sans if x != commonname]
        #req.add_extensions([OpenSSL.crypto.X509Extension(b'subjectAltName', True, ', '.join('DNS: %s' % x for x in sans)).encode()])
        req.set_pubkey(pkey)
        req.sign(pkey, 'sha1')

        cert = OpenSSL.crypto.X509()
        cert.set_version(2)
        try:
            cert.set_serial_number(CertUtil.get_cert_serial_number(commonname))
        except OpenSSL.SSL.Error:
            cert.set_serial_number(int(time.time()*1000))
        cert.gmtime_adj_notBefore(-600) #avoid crt time error warning
        cert.gmtime_adj_notAfter(60 * 60 * 24 * 3652)
        cert.set_issuer(ca.get_subject())
        cert.set_subject(req.get_subject())
        cert.set_pubkey(req.get_pubkey())
        if commonname[0] == '.':
            sans = ['*'+commonname] + [s for s in sans if s != '*'+commonname]
        else:
            sans = [commonname] + [s for s in sans if s != commonname]
        #cert.add_extensions([OpenSSL.crypto.X509Extension(b'subjectAltName', True, ', '.join('DNS: %s' % x for x in sans))])
        cert.sign(key, 'sha1')

        certfile = os.path.join(CertUtil.ca_certdir, commonname + '.crt')
        with open(certfile, 'wb') as fp:
            fp.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert))
            fp.write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, pkey))
        return certfile

    @staticmethod
    def get_cert(commonname, sans=()):
        if commonname.count('.') >= 2 and [len(x) for x in reversed(commonname.split('.'))] > [2, 4]:
            commonname = '.'+commonname.partition('.')[-1]
        certfile = os.path.join(CertUtil.ca_certdir, commonname + '.crt')
        if os.path.exists(certfile):
            return certfile
        elif OpenSSL is None:
            return CertUtil.ca_keyfile
        else:
            with CertUtil.ca_lock:
                if os.path.exists(certfile):
                    return certfile
                return CertUtil._get_cert(commonname, sans)

    @staticmethod
    def win32_notify( msg="msg", title="Title"):
        import ctypes
        res = ctypes.windll.user32.MessageBoxW(None, msg, title, 1)
        # Yes:1 No:2
        return res

    @staticmethod
    def import_ca(certfile):
        commonname = os.path.splitext(os.path.basename(certfile))[0]
        if sys.platform.startswith('win'):
            import ctypes
            with open(certfile, 'rb') as fp:
                certdata = fp.read()
                if certdata.startswith(b'-----'):
                    begin = b'-----BEGIN CERTIFICATE-----'
                    end = b'-----END CERTIFICATE-----'
                    certdata = base64.b64decode(b''.join(certdata[certdata.find(begin)+len(begin):certdata.find(end)].strip().splitlines()))
                crypt32 = ctypes.WinDLL(b'crypt32.dll'.decode())
                store_handle = crypt32.CertOpenStore(10, 0, 0, 0x4000 | 0x20000, b'ROOT'.decode())
                if not store_handle:
                    return -1
                CERT_FIND_SUBJECT_STR = 0x00080007
                CERT_FIND_HASH = 0x10000
                X509_ASN_ENCODING = 0x00000001
                class CRYPT_HASH_BLOB(ctypes.Structure):
                    _fields_ = [('cbData', ctypes.c_ulong), ('pbData', ctypes.c_char_p)]
                assert CertUtil.ca_thumbprint
                crypt_hash = CRYPT_HASH_BLOB(20, binascii.a2b_hex(CertUtil.ca_thumbprint.replace(':', '')))
                crypt_handle = crypt32.CertFindCertificateInStore(store_handle, X509_ASN_ENCODING, 0, CERT_FIND_HASH, ctypes.byref(crypt_hash), None)
                if crypt_handle:
                    crypt32.CertFreeCertificateContext(crypt_handle)
                    return 0

                ret = crypt32.CertAddEncodedCertificateToStore(store_handle, 0x1, certdata, len(certdata), 4, None)
                crypt32.CertCloseStore(store_handle, 0)
                del crypt32


                if not ret and __name__ != "__main__":
                    #res = CertUtil.win32_notify(msg=u'Import GoAgent Ca?', title=u'Authority need')
                    #if res == 2:
                    #    return -1

                    import win32elevate
                    win32elevate.elevateAdminRun(os.path.abspath(__file__))
                    return 0

                return 0 if ret else -1
        elif sys.platform == 'darwin':
            return os.system(('security find-certificate -a -c "%s" | grep "%s" >/dev/null || security add-trusted-cert -d -r trustRoot -k "/Library/Keychains/System.keychain" "%s"' % (commonname, commonname, certfile.decode('utf-8'))).encode('utf-8'))
        elif sys.platform.startswith('linux'):
            import platform
            platform_distname = platform.dist()[0]
            if platform_distname == 'Ubuntu':
                pemfile = "/etc/ssl/certs/%s.pem" % commonname
                new_certfile = "/usr/local/share/ca-certificates/%s.crt" % commonname
                if not os.path.exists(pemfile):
                    return os.system('cp "%s" "%s" && update-ca-certificates' % (certfile, new_certfile))
            elif any(os.path.isfile('%s/certutil' % x) for x in os.environ['PATH'].split(os.pathsep)):
                return os.system('certutil -L -d sql:$HOME/.pki/nssdb | grep "%s" || certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n "%s" -i "%s"' % (commonname, commonname, certfile))
            else:
                logging.warning('please install *libnss3-tools* package to import GoAgent root ca')
        return 0

    @staticmethod
    def remove_ca(name):
        import ctypes
        import ctypes.wintypes
        class CERT_CONTEXT(ctypes.Structure):
            _fields_ = [
                ('dwCertEncodingType', ctypes.wintypes.DWORD),
                ('pbCertEncoded', ctypes.POINTER(ctypes.wintypes.BYTE)),
                ('cbCertEncoded', ctypes.wintypes.DWORD),
                ('pCertInfo', ctypes.c_void_p),
                ('hCertStore', ctypes.c_void_p),]
        crypt32 = ctypes.WinDLL(b'crypt32.dll'.decode())
        store_handle = crypt32.CertOpenStore(10, 0, 0, 0x4000 | 0x20000, b'ROOT'.decode())
        pCertCtx = crypt32.CertEnumCertificatesInStore(store_handle, None)
        while pCertCtx:
            certCtx = CERT_CONTEXT.from_address(pCertCtx)
            certdata = ctypes.string_at(certCtx.pbCertEncoded, certCtx.cbCertEncoded)
            cert =  OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, certdata)
            if hasattr(cert, 'get_subject'):
                cert = cert.get_subject()
            cert_name = next((v for k, v in cert.get_components() if k == 'CN'), '')
            if cert_name and name == cert_name:
                crypt32.CertDeleteCertificateFromStore(crypt32.CertDuplicateCertificateContext(pCertCtx))
            pCertCtx = crypt32.CertEnumCertificatesInStore(store_handle, pCertCtx)
        return 0

    @staticmethod
    def check_ca():
        #Check CA exists
        capath = os.path.join(os.path.dirname(os.path.abspath(__file__)), CertUtil.ca_keyfile)
        certdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), CertUtil.ca_certdir)
        if not os.path.exists(capath):
            if os.path.exists(certdir):
                any(os.remove(x) for x in glob.glob(certdir+'/*.crt')+glob.glob(certdir+'/.*.crt'))
            if os.name == 'nt':
                try:
                    CertUtil.remove_ca('%s CA' % CertUtil.ca_vendor)
                except Exception as e:
                    logging.warning('CertUtil.remove_ca failed: %r', e)
            CertUtil.dump_ca()
        with open(capath, 'rb') as fp:
            CertUtil.ca_thumbprint = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, fp.read()).digest('sha1')
        #Check Certs
        certfiles = glob.glob(certdir+'/*.crt')+glob.glob(certdir+'/.*.crt')
        if certfiles:
            filename = random.choice(certfiles)
            commonname = os.path.splitext(os.path.basename(filename))[0]
            with open(filename, 'rb') as fp:
                serial_number = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, fp.read()).get_serial_number()
            if serial_number != CertUtil.get_cert_serial_number(commonname):
                any(os.remove(x) for x in certfiles)
        #Check CA imported
        if CertUtil.import_ca(capath) != 0:
            logging.warning('install root certificate failed, Please run as administrator/root/sudo')
        #Check Certs Dir
        if not os.path.exists(certdir):
            os.makedirs(certdir)


if __name__ == '__main__':
    capath = os.path.join(os.path.dirname(os.path.abspath(__file__)), CertUtil.ca_keyfile)
    CertUtil.check_ca()
