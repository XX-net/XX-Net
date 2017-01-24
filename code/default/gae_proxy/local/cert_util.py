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
import subprocess

current_path = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data', "gae_proxy"))
if not os.path.isdir(data_path):
    data_path = current_path

if __name__ == "__main__":
    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)

    if sys.platform == "win32":
        win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
        sys.path.append(win32_lib)
    elif sys.platform == "linux" or sys.platform == "linux2":
        linux_lib = os.path.abspath( os.path.join(python_path, 'lib', 'linux'))
        sys.path.append(linux_lib)
    elif sys.platform == "darwin":
        darwin_lib = os.path.abspath( os.path.join(python_path, 'lib', 'darwin'))
        sys.path.append(darwin_lib)

from xlog import getLogger
xlog = getLogger("gae_proxy")

import OpenSSL

import ssl, datetime
from pyasn1.type import univ, constraint, char, namedtype, tag
from pyasn1.codec.der.decoder import decode
from pyasn1.error import PyAsn1Error

from config import config


def get_cmd_out(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = proc.stdout
    lines = out.readlines()
    return lines

class _GeneralName(univ.Choice):
    # We are only interested in dNSNames. We use a default handler to ignore
    # other types.
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('dNSName', char.IA5String().subtype(
                implicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 2)
            )
        ),
    )

class _GeneralNames(univ.SequenceOf):
    componentType = _GeneralName()
    sizeSpec = univ.SequenceOf.sizeSpec + constraint.ValueSizeConstraint(1, 1024)

class SSLCert:
    def __init__(self, cert):
        """
            Returns a (common name, [subject alternative names]) tuple.
        """
        self.x509 = cert

    @classmethod
    def from_pem(klass, txt):
        x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, txt)
        return klass(x509)

    @classmethod
    def from_der(klass, der):
        pem = ssl.DER_cert_to_PEM_cert(der)
        return klass.from_pem(pem)

    def to_pem(self):
        return OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, self.x509)

    def digest(self, name):
        return self.x509.digest(name)

    @property
    def issuer(self):
        return self.x509.get_issuer().get_components()

    @property
    def notbefore(self):
        t = self.x509.get_notBefore()
        return datetime.datetime.strptime(t, "%Y%m%d%H%M%SZ")

    @property
    def notafter(self):
        t = self.x509.get_notAfter()
        return datetime.datetime.strptime(t, "%Y%m%d%H%M%SZ")

    @property
    def has_expired(self):
        return self.x509.has_expired()

    @property
    def subject(self):
        return self.x509.get_subject().get_components()

    @property
    def serial(self):
        return self.x509.get_serial_number()

    @property
    def keyinfo(self):
        pk = self.x509.get_pubkey()
        types = {
            OpenSSL.crypto.TYPE_RSA: "RSA",
            OpenSSL.crypto.TYPE_DSA: "DSA",
        }
        return (
            types.get(pk.type(), "UNKNOWN"),
            pk.bits()
        )

    @property
    def cn(self):
        c = None
        for i in self.subject:
            if i[0] == "CN":
                c = i[1]
        return c

    @property
    def altnames(self):
        altnames = []
        for i in range(self.x509.get_extension_count()):
            ext = self.x509.get_extension(i)
            if ext.get_short_name() == "subjectAltName":
                try:
                    dec = decode(ext.get_data(), asn1Spec=_GeneralNames())
                except PyAsn1Error:
                    continue
                for i in dec[0]:
                    altnames.append(i[0].asOctets())
        return altnames

class CertUtil(object):
    """CertUtil module, based on mitmproxy"""

    ca_vendor = 'GoAgent' #TODO: here should be XX-Net
    ca_keyfile = os.path.join(data_path, 'CA.crt')
    ca_thumbprint = ''
    ca_certdir = os.path.join(data_path, 'certs')
    ca_digest = 'sha256'
    ca_lock = threading.Lock()
    ca_validity_years = 10
    ca_validity = 24 * 60 * 60 * 365 * ca_validity_years

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
        subj.commonName = '%s XX-Net' % CertUtil.ca_vendor #TODO: here should be GoAgent
        req.set_pubkey(key)
        req.sign(key, CertUtil.ca_digest)
        ca = OpenSSL.crypto.X509()
        ca.set_version(2)
        ca.set_serial_number(0)
        ca.gmtime_adj_notBefore(0)
        ca.gmtime_adj_notAfter(CertUtil.ca_validity)
        ca.set_issuer(req.get_subject())
        ca.set_subject(req.get_subject())
        ca.set_pubkey(req.get_pubkey())
        ca.add_extensions([
            OpenSSL.crypto.X509Extension(
                'basicConstraints', False, 'CA:TRUE', subject=ca, issuer=ca)
            ])
        ca.sign(key, CertUtil.ca_digest)
        #xlog.debug("CA key:%s", key)
        xlog.info("create CA")
        return key, ca

    @staticmethod
    def generate_ca_file():
        xlog.info("generate CA file:%s", CertUtil.ca_keyfile)
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
        req.sign(pkey, CertUtil.ca_digest)

        cert = OpenSSL.crypto.X509()
        cert.set_version(2)
        try:
            cert.set_serial_number(CertUtil.get_cert_serial_number(commonname))
        except OpenSSL.SSL.Error:
            cert.set_serial_number(int(time.time()*1000))
        cert.gmtime_adj_notBefore(-600) #avoid crt time error warning
        cert.gmtime_adj_notAfter(CertUtil.ca_validity)
        cert.set_issuer(ca.get_subject())
        cert.set_subject(req.get_subject())
        cert.set_pubkey(req.get_pubkey())
        if commonname[0] == '.':
            sans = ['*'+commonname] + [s for s in sans if s != '*'+commonname]
        else:
            sans = [commonname] + [s for s in sans if s != commonname]
        #cert.add_extensions([OpenSSL.crypto.X509Extension(b'subjectAltName', True, ', '.join('DNS: %s' % x for x in sans))])
        cert.sign(key, CertUtil.ca_digest)

        certfile = os.path.join(CertUtil.ca_certdir, commonname + '.crt')
        with open(certfile, 'wb') as fp:
            fp.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert))
            fp.write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, pkey))
        return certfile

    @staticmethod
    def get_cert(commonname, sans=(), full_name=False):
        certfile = os.path.join(CertUtil.ca_certdir, commonname + '.crt')
        if os.path.exists(certfile):
            return certfile

        # some site need full name cert
        # like https://about.twitter.com in Google Chrome
        if commonname.count('.') >= 2 and [len(x) for x in reversed(commonname.split('.'))] > [2, 4] and not full_name:
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
    def import_windows_ca(common_name, certfile):
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
                return False
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
                return True

            ret = crypt32.CertAddEncodedCertificateToStore(store_handle, 0x1, certdata, len(certdata), 4, None)
            crypt32.CertCloseStore(store_handle, 0)
            del crypt32


            if not ret and __name__ != "__main__":
                #res = CertUtil.win32_notify(msg=u'Import GoAgent Ca?', title=u'Authority need')
                #if res == 2:
                #    return -1

                import win32elevate
                try:
                    win32elevate.elevateAdminRun(os.path.abspath(__file__))
                except Exception as e:
                    xlog.warning('CertUtil.import_windows_ca failed: %r', e)
                return True
            else:
                CertUtil.win32_notify(msg=u'已经导入GoAgent证书，请重启浏览器.', title=u'Restart browser need.')

            return True if ret else False

    @staticmethod
    def remove_windows_ca(name):
        import ctypes
        import ctypes.wintypes
        class CERT_CONTEXT(ctypes.Structure):
            _fields_ = [
                ('dwCertEncodingType', ctypes.wintypes.DWORD),
                ('pbCertEncoded', ctypes.POINTER(ctypes.wintypes.BYTE)),
                ('cbCertEncoded', ctypes.wintypes.DWORD),
                ('pCertInfo', ctypes.c_void_p),
                ('hCertStore', ctypes.c_void_p),]
        try:
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
        except Exception as e:
            xlog.warning('CertUtil.remove_windows_ca failed: %r', e)


    @staticmethod
    def get_linux_firefox_path():
        home_path = os.path.expanduser("~")
        firefox_path = os.path.join(home_path, ".mozilla/firefox")
        if not os.path.isdir(firefox_path):
            return

        for filename in os.listdir(firefox_path):
            if filename.endswith(".default") and os.path.isdir(os.path.join(firefox_path, filename)):
                config_path = os.path.join(firefox_path, filename)
                return config_path

    @staticmethod
    def import_linux_firefox_ca(common_name, ca_file):
        firefox_config_path = CertUtil.get_linux_firefox_path()
        if not firefox_config_path:
            return False

        if not any(os.path.isfile('%s/certutil' % x) for x in os.environ['PATH'].split(os.pathsep)):
            xlog.warning('please install *libnss3-tools* package to import GoAgent root ca')
            return False

        cmd_line = 'certutil -L -d %s |grep "GoAgent" &&certutil -d %s -D -n "%s" ' % (firefox_config_path, firefox_config_path, common_name)
        os.system(cmd_line) # remove old cert first

        cmd_line = 'certutil -d %s -A -t "C,," -n "%s" -i "%s"' % (firefox_config_path, common_name, ca_file)
        os.system(cmd_line) # install new cert
        return True

    @staticmethod
    def import_debian_ca(common_name, ca_file):

        def get_debian_ca_sha1(nss_path):
            commonname = "GoAgent XX-Net - GoAgent" #TODO: here should be GoAgent - XX-Net

            cmd = ['certutil', '-L','-d', 'sql:%s' % nss_path, '-n', commonname]
            lines = get_cmd_out(cmd)

            get_sha1_title = False
            sha1 = ""
            for line in lines:
                if line.endswith("Fingerprint (SHA1):\n"):
                    get_sha1_title = True
                    continue
                if get_sha1_title:
                    sha1 = line
                    break

            sha1 = sha1.replace(' ', '').replace(':', '').replace('\n', '')
            if len(sha1) != 40:
                return False
            else:
                return sha1

        home_path = os.path.expanduser("~")
        nss_path = os.path.join(home_path, ".pki/nssdb")
        if not os.path.isdir(nss_path):
            return False

        if not any(os.path.isfile('%s/certutil' % x) for x in os.environ['PATH'].split(os.pathsep)):
            xlog.warning('please install *libnss3-tools* package to import GoAgent root ca')
            return False

        sha1 = get_debian_ca_sha1(nss_path)
        ca_hash = CertUtil.ca_thumbprint.replace(':', '')
        if sha1 == ca_hash:
            xlog.info("system cert exist")
            return


        # shell command to list all cert
        # certutil -L -d sql:$HOME/.pki/nssdb

        # remove old cert first
        cmd_line = 'certutil -L -d sql:$HOME/.pki/nssdb |grep "GoAgent" && certutil -d sql:$HOME/.pki/nssdb -D -n "%s" ' % ( common_name)
        os.system(cmd_line)

        # install new cert
        cmd_line = 'certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n "%s" -i "%s"' % (common_name, ca_file)
        os.system(cmd_line)
        return True


    @staticmethod
    def import_ubuntu_system_ca(common_name, certfile):
        import platform
        platform_distname = platform.dist()[0]
        if platform_distname != 'Ubuntu':
            return

        pemfile = "/etc/ssl/certs/CA.pem"
        new_certfile = "/usr/local/share/ca-certificates/CA.crt"
        if not os.path.exists(pemfile) or not CertUtil.file_is_same(certfile, new_certfile):
            if os.system('cp "%s" "%s" && update-ca-certificates' % (certfile, new_certfile)) != 0:
                xlog.warning('install root certificate failed, Please run as administrator/root/sudo')

    @staticmethod
    def file_is_same(file1, file2):
        BLOCKSIZE = 65536

        try:
            with open(file1, 'rb') as f1:
                buf1 = f1.read(BLOCKSIZE)
        except:
            return False

        try:
            with open(file2, 'rb') as f2:
                buf2 = f2.read(BLOCKSIZE)
        except:
            return False

        if buf1 != buf2:
            return False
        else:
            return True



    @staticmethod
    def import_mac_ca(common_name, certfile):
        commonname = "GoAgent XX-Net" #TODO: need check again
        ca_hash = CertUtil.ca_thumbprint.replace(':', '')

        def get_exist_ca_sha1():
            args = ['security', 'find-certificate', '-Z', '-a', '-c', commonname]
            output = subprocess.check_output(args)
            for line in output.splitlines(True):
                if len(line) == 53 and line.startswith("SHA-1 hash:"):
                    sha1_hash = line[12:52]
                    return sha1_hash

        exist_ca_sha1 = get_exist_ca_sha1()
        if exist_ca_sha1 == ca_hash:
            xlog.info("GoAgent CA exist")
            return

        import_command = 'security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ../../../../data/gae_proxy/CA.crt'# % certfile.decode('utf-8')
        if exist_ca_sha1:
            delete_ca_command = 'security delete-certificate -Z %s' % exist_ca_sha1
            exec_command = "%s;%s" % (delete_ca_command, import_command)
        else:
            exec_command = import_command

        admin_command = """osascript -e 'do shell script "%s" with administrator privileges' """ % exec_command
        cmd = admin_command.encode('utf-8')
        xlog.info("try auto import CA command:%s", cmd)
        os.system(cmd)

    @staticmethod
    def import_ca(certfile):
        commonname = "GoAgent XX-Net - GoAgent" #TODO: here should be GoAgent - XX-Net
        if sys.platform.startswith('win'):
            CertUtil.import_windows_ca(commonname, certfile)
        elif sys.platform == 'darwin':
            CertUtil.import_mac_ca(commonname, certfile)
        elif sys.platform.startswith('linux'):
            CertUtil.import_debian_ca(commonname, certfile)
            CertUtil.import_linux_firefox_ca(commonname, certfile)
            #CertUtil.import_ubuntu_system_ca(commonname, certfile) # we don't need install CA to system root, special user is enough


    @staticmethod
    def init_ca():
        #Check Certs Dir
        if not os.path.exists(CertUtil.ca_certdir):
            os.makedirs(CertUtil.ca_certdir)

        # Confirmed GoAgent CA exist
        if not os.path.exists(CertUtil.ca_keyfile):
            xlog.info("no CA file exist")

            xlog.info("clean old site certs")
            any(os.remove(x) for x in glob.glob(CertUtil.ca_certdir+'/*.crt')+glob.glob(CertUtil.ca_certdir+'/.*.crt'))

            if os.name == 'nt':
                CertUtil.remove_windows_ca('%s CA' % CertUtil.ca_vendor)

            CertUtil.generate_ca_file()

        # Load GoAgent CA
        with open(CertUtil.ca_keyfile, 'rb') as fp:
            CertUtil.ca_thumbprint = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, fp.read()).digest('sha1')

        #Check exist site cert buffer with CA
        certfiles = glob.glob(CertUtil.ca_certdir+'/*.crt')+glob.glob(CertUtil.ca_certdir+'/.*.crt')
        if certfiles:
            filename = random.choice(certfiles)
            commonname = os.path.splitext(os.path.basename(filename))[0]
            with open(filename, 'rb') as fp:
                serial_number = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, fp.read()).get_serial_number()
            if serial_number != CertUtil.get_cert_serial_number(commonname):
                any(os.remove(x) for x in certfiles)

        CertUtil.import_ca(CertUtil.ca_keyfile)

        # change the status,
        # web_control /cert_import_status will return True, else return False
        # launcher will wait ready to open browser and check update
        config.cert_import_ready = True




if __name__ == '__main__':
    CertUtil.init_ca()


#TODO:
# CA commaon should be GoAgent, vander should be XX-Net
# need change and test on all support platform: Windows/Mac/Ubuntu/Debian
