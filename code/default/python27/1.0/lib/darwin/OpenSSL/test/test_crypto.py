# Copyright (c) Jean-Paul Calderone
# See LICENSE file for details.

"""
Unit tests for L{OpenSSL.crypto}.
"""

from unittest import main

import os, re
from subprocess import PIPE, Popen
from datetime import datetime, timedelta

from OpenSSL.crypto import TYPE_RSA, TYPE_DSA, Error, PKey, PKeyType
from OpenSSL.crypto import X509, X509Type, X509Name, X509NameType
from OpenSSL.crypto import X509Req, X509ReqType
from OpenSSL.crypto import X509Extension, X509ExtensionType
from OpenSSL.crypto import load_certificate, load_privatekey
from OpenSSL.crypto import FILETYPE_PEM, FILETYPE_ASN1, FILETYPE_TEXT
from OpenSSL.crypto import dump_certificate, load_certificate_request
from OpenSSL.crypto import dump_certificate_request, dump_privatekey
from OpenSSL.crypto import PKCS7Type, load_pkcs7_data
from OpenSSL.crypto import PKCS12, PKCS12Type, load_pkcs12
from OpenSSL.crypto import CRL, Revoked, load_crl
from OpenSSL.crypto import NetscapeSPKI, NetscapeSPKIType
from OpenSSL.crypto import sign, verify
from OpenSSL.test.util import TestCase, bytes, b

def normalize_certificate_pem(pem):
    return dump_certificate(FILETYPE_PEM, load_certificate(FILETYPE_PEM, pem))


def normalize_privatekey_pem(pem):
    return dump_privatekey(FILETYPE_PEM, load_privatekey(FILETYPE_PEM, pem))


root_cert_pem = b("""-----BEGIN CERTIFICATE-----
MIIC7TCCAlagAwIBAgIIPQzE4MbeufQwDQYJKoZIhvcNAQEFBQAwWDELMAkGA1UE
BhMCVVMxCzAJBgNVBAgTAklMMRAwDgYDVQQHEwdDaGljYWdvMRAwDgYDVQQKEwdU
ZXN0aW5nMRgwFgYDVQQDEw9UZXN0aW5nIFJvb3QgQ0EwIhgPMjAwOTAzMjUxMjM2
NThaGA8yMDE3MDYxMTEyMzY1OFowWDELMAkGA1UEBhMCVVMxCzAJBgNVBAgTAklM
MRAwDgYDVQQHEwdDaGljYWdvMRAwDgYDVQQKEwdUZXN0aW5nMRgwFgYDVQQDEw9U
ZXN0aW5nIFJvb3QgQ0EwgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAPmaQumL
urpE527uSEHdL1pqcDRmWzu+98Y6YHzT/J7KWEamyMCNZ6fRW1JCR782UQ8a07fy
2xXsKy4WdKaxyG8CcatwmXvpvRQ44dSANMihHELpANTdyVp6DCysED6wkQFurHlF
1dshEaJw8b/ypDhmbVIo6Ci1xvCJqivbLFnbAgMBAAGjgbswgbgwHQYDVR0OBBYE
FINVdy1eIfFJDAkk51QJEo3IfgSuMIGIBgNVHSMEgYAwfoAUg1V3LV4h8UkMCSTn
VAkSjch+BK6hXKRaMFgxCzAJBgNVBAYTAlVTMQswCQYDVQQIEwJJTDEQMA4GA1UE
BxMHQ2hpY2FnbzEQMA4GA1UEChMHVGVzdGluZzEYMBYGA1UEAxMPVGVzdGluZyBS
b290IENBggg9DMTgxt659DAMBgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBBQUAA4GB
AGGCDazMJGoWNBpc03u6+smc95dEead2KlZXBATOdFT1VesY3+nUOqZhEhTGlDMi
hkgaZnzoIq/Uamidegk4hirsCT/R+6vsKAAxNTcBjUeZjlykCJWy5ojShGftXIKY
w/njVbKMXrvc83qmTdGl3TAM0fxQIpqgcglFLveEBgzn
-----END CERTIFICATE-----
""")

root_key_pem = b("""-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQD5mkLpi7q6ROdu7khB3S9aanA0Zls7vvfGOmB80/yeylhGpsjA
jWen0VtSQke/NlEPGtO38tsV7CsuFnSmschvAnGrcJl76b0UOOHUgDTIoRxC6QDU
3claegwsrBA+sJEBbqx5RdXbIRGicPG/8qQ4Zm1SKOgotcbwiaor2yxZ2wIDAQAB
AoGBAPCgMpmLxzwDaUmcFbTJUvlLW1hoxNNYSu2jIZm1k/hRAcE60JYwvBkgz3UB
yMEh0AtLxYe0bFk6EHah11tMUPgscbCq73snJ++8koUw+csk22G65hOs51bVb7Aa
6JBe67oLzdtvgCUFAA2qfrKzWRZzAdhUirQUZgySZk+Xq1pBAkEA/kZG0A6roTSM
BVnx7LnPfsycKUsTumorpXiylZJjTi9XtmzxhrYN6wgZlDOOwOLgSQhszGpxVoMD
u3gByT1b2QJBAPtL3mSKdvwRu/+40zaZLwvSJRxaj0mcE4BJOS6Oqs/hS1xRlrNk
PpQ7WJ4yM6ZOLnXzm2mKyxm50Mv64109FtMCQQDOqS2KkjHaLowTGVxwC0DijMfr
I9Lf8sSQk32J5VWCySWf5gGTfEnpmUa41gKTMJIbqZZLucNuDcOtzUaeWZlZAkA8
ttXigLnCqR486JDPTi9ZscoZkZ+w7y6e/hH8t6d5Vjt48JVyfjPIaJY+km58LcN3
6AWSeGAdtRFHVzR7oHjVAkB4hutvxiOeiIVQNBhM6RSI9aBPMI21DoX2JRoxvNW2
cbvAhow217X9V0dVerEOKxnNYspXRrh36h7k4mQA+sDq
-----END RSA PRIVATE KEY-----
""")

server_cert_pem = b("""-----BEGIN CERTIFICATE-----
MIICKDCCAZGgAwIBAgIJAJn/HpR21r/8MA0GCSqGSIb3DQEBBQUAMFgxCzAJBgNV
BAYTAlVTMQswCQYDVQQIEwJJTDEQMA4GA1UEBxMHQ2hpY2FnbzEQMA4GA1UEChMH
VGVzdGluZzEYMBYGA1UEAxMPVGVzdGluZyBSb290IENBMCIYDzIwMDkwMzI1MTIz
NzUzWhgPMjAxNzA2MTExMjM3NTNaMBgxFjAUBgNVBAMTDWxvdmVseSBzZXJ2ZXIw
gZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAL6m+G653V0tpBC/OKl22VxOi2Cv
lK4TYu9LHSDP9uDVTe7V5D5Tl6qzFoRRx5pfmnkqT5B+W9byp2NU3FC5hLm5zSAr
b45meUhjEJ/ifkZgbNUjHdBIGP9MAQUHZa5WKdkGIJvGAvs8UzUqlr4TBWQIB24+
lJ+Ukk/CRgasrYwdAgMBAAGjNjA0MB0GA1UdDgQWBBS4kC7Ij0W1TZXZqXQFAM2e
gKEG2DATBgNVHSUEDDAKBggrBgEFBQcDATANBgkqhkiG9w0BAQUFAAOBgQBh30Li
dJ+NlxIOx5343WqIBka3UbsOb2kxWrbkVCrvRapCMLCASO4FqiKWM+L0VDBprqIp
2mgpFQ6FHpoIENGvJhdEKpptQ5i7KaGhnDNTfdy3x1+h852G99f1iyj0RmbuFcM8
uzujnS8YXWvM7DM1Ilozk4MzPug8jzFp5uhKCQ==
-----END CERTIFICATE-----
""")

server_key_pem = normalize_privatekey_pem(b("""-----BEGIN RSA PRIVATE KEY-----
MIICWwIBAAKBgQC+pvhuud1dLaQQvzipdtlcTotgr5SuE2LvSx0gz/bg1U3u1eQ+
U5eqsxaEUceaX5p5Kk+QflvW8qdjVNxQuYS5uc0gK2+OZnlIYxCf4n5GYGzVIx3Q
SBj/TAEFB2WuVinZBiCbxgL7PFM1Kpa+EwVkCAduPpSflJJPwkYGrK2MHQIDAQAB
AoGAbwuZ0AR6JveahBaczjfnSpiFHf+mve2UxoQdpyr6ROJ4zg/PLW5K/KXrC48G
j6f3tXMrfKHcpEoZrQWUfYBRCUsGD5DCazEhD8zlxEHahIsqpwA0WWssJA2VOLEN
j6DuV2pCFbw67rfTBkTSo32ahfXxEKev5KswZk0JIzH3ooECQQDgzS9AI89h0gs8
Dt+1m11Rzqo3vZML7ZIyGApUzVan+a7hbc33nbGRkAXjHaUBJO31it/H6dTO+uwX
msWwNG5ZAkEA2RyFKs5xR5USTFaKLWCgpH/ydV96KPOpBND7TKQx62snDenFNNbn
FwwOhpahld+vqhYk+pfuWWUpQciE+Bu7ZQJASjfT4sQv4qbbKK/scePicnDdx9th
4e1EeB9xwb+tXXXUo/6Bor/AcUNwfiQ6Zt9PZOK9sR3lMZSsP7rMi7kzuQJABie6
1sXXjFH7nNJvRG4S39cIxq8YRYTy68II/dlB2QzGpKxV/POCxbJ/zu0CU79tuYK7
NaeNCFfH3aeTrX0LyQJAMBWjWmeKM2G2sCExheeQK0ROnaBC8itCECD4Jsve4nqf
r50+LF74iLXFwqysVCebPKMOpDWp/qQ1BbJQIPs7/A==
-----END RSA PRIVATE KEY-----
"""))

client_cert_pem = b("""-----BEGIN CERTIFICATE-----
MIICJjCCAY+gAwIBAgIJAKxpFI5lODkjMA0GCSqGSIb3DQEBBQUAMFgxCzAJBgNV
BAYTAlVTMQswCQYDVQQIEwJJTDEQMA4GA1UEBxMHQ2hpY2FnbzEQMA4GA1UEChMH
VGVzdGluZzEYMBYGA1UEAxMPVGVzdGluZyBSb290IENBMCIYDzIwMDkwMzI1MTIz
ODA1WhgPMjAxNzA2MTExMjM4MDVaMBYxFDASBgNVBAMTC3VnbHkgY2xpZW50MIGf
MA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDAZh/SRtNm5ntMT4qb6YzEpTroMlq2
rn+GrRHRiZ+xkCw/CGNhbtPir7/QxaUj26BSmQrHw1bGKEbPsWiW7bdXSespl+xK
iku4G/KvnnmWdeJHqsiXeUZtqurMELcPQAw9xPHEuhqqUJvvEoMTsnCEqGM+7Dtb
oCRajYyHfluARQIDAQABozYwNDAdBgNVHQ4EFgQUNQB+qkaOaEVecf1J3TTUtAff
0fAwEwYDVR0lBAwwCgYIKwYBBQUHAwIwDQYJKoZIhvcNAQEFBQADgYEAyv/Jh7gM
Q3OHvmsFEEvRI+hsW8y66zK4K5de239Y44iZrFYkt7Q5nBPMEWDj4F2hLYWL/qtI
9Zdr0U4UDCU9SmmGYh4o7R4TZ5pGFvBYvjhHbkSFYFQXZxKUi+WUxplP6I0wr2KJ
PSTJCjJOn3xo2NTKRgV1gaoTf2EhL+RG8TQ=
-----END CERTIFICATE-----
""")

client_key_pem = normalize_privatekey_pem(b("""-----BEGIN RSA PRIVATE KEY-----
MIICXgIBAAKBgQDAZh/SRtNm5ntMT4qb6YzEpTroMlq2rn+GrRHRiZ+xkCw/CGNh
btPir7/QxaUj26BSmQrHw1bGKEbPsWiW7bdXSespl+xKiku4G/KvnnmWdeJHqsiX
eUZtqurMELcPQAw9xPHEuhqqUJvvEoMTsnCEqGM+7DtboCRajYyHfluARQIDAQAB
AoGATkZ+NceY5Glqyl4mD06SdcKfV65814vg2EL7V9t8+/mi9rYL8KztSXGlQWPX
zuHgtRoMl78yQ4ZJYOBVo+nsx8KZNRCEBlE19bamSbQLCeQMenWnpeYyQUZ908gF
h6L9qsFVJepgA9RDgAjyDoS5CaWCdCCPCH2lDkdcqC54SVUCQQDseuduc4wi8h4t
V8AahUn9fn9gYfhoNuM0gdguTA0nPLVWz4hy1yJiWYQe0H7NLNNTmCKiLQaJpAbb
TC6vE8C7AkEA0Ee8CMJUc20BnGEmxwgWcVuqFWaKCo8jTH1X38FlATUsyR3krjW2
dL3yDD9NwHxsYP7nTKp/U8MV7U9IBn4y/wJBAJl7H0/BcLeRmuJk7IqJ7b635iYB
D/9beFUw3MUXmQXZUfyYz39xf6CDZsu1GEdEC5haykeln3Of4M9d/4Kj+FcCQQCY
si6xwT7GzMDkk/ko684AV3KPc/h6G0yGtFIrMg7J3uExpR/VdH2KgwMkZXisSMvw
JJEQjOMCVsEJlRk54WWjAkEAzoZNH6UhDdBK5F38rVt/y4SEHgbSfJHIAmPS32Kq
f6GGcfNpip0Uk7q7udTKuX7Q/buZi/C4YW7u3VKAquv9NA==
-----END RSA PRIVATE KEY-----
"""))

cleartextCertificatePEM = b("""-----BEGIN CERTIFICATE-----
MIIC7TCCAlagAwIBAgIIPQzE4MbeufQwDQYJKoZIhvcNAQEFBQAwWDELMAkGA1UE
BhMCVVMxCzAJBgNVBAgTAklMMRAwDgYDVQQHEwdDaGljYWdvMRAwDgYDVQQKEwdU
ZXN0aW5nMRgwFgYDVQQDEw9UZXN0aW5nIFJvb3QgQ0EwIhgPMjAwOTAzMjUxMjM2
NThaGA8yMDE3MDYxMTEyMzY1OFowWDELMAkGA1UEBhMCVVMxCzAJBgNVBAgTAklM
MRAwDgYDVQQHEwdDaGljYWdvMRAwDgYDVQQKEwdUZXN0aW5nMRgwFgYDVQQDEw9U
ZXN0aW5nIFJvb3QgQ0EwgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAPmaQumL
urpE527uSEHdL1pqcDRmWzu+98Y6YHzT/J7KWEamyMCNZ6fRW1JCR782UQ8a07fy
2xXsKy4WdKaxyG8CcatwmXvpvRQ44dSANMihHELpANTdyVp6DCysED6wkQFurHlF
1dshEaJw8b/ypDhmbVIo6Ci1xvCJqivbLFnbAgMBAAGjgbswgbgwHQYDVR0OBBYE
FINVdy1eIfFJDAkk51QJEo3IfgSuMIGIBgNVHSMEgYAwfoAUg1V3LV4h8UkMCSTn
VAkSjch+BK6hXKRaMFgxCzAJBgNVBAYTAlVTMQswCQYDVQQIEwJJTDEQMA4GA1UE
BxMHQ2hpY2FnbzEQMA4GA1UEChMHVGVzdGluZzEYMBYGA1UEAxMPVGVzdGluZyBS
b290IENBggg9DMTgxt659DAMBgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBBQUAA4GB
AGGCDazMJGoWNBpc03u6+smc95dEead2KlZXBATOdFT1VesY3+nUOqZhEhTGlDMi
hkgaZnzoIq/Uamidegk4hirsCT/R+6vsKAAxNTcBjUeZjlykCJWy5ojShGftXIKY
w/njVbKMXrvc83qmTdGl3TAM0fxQIpqgcglFLveEBgzn
-----END CERTIFICATE-----
""")

cleartextPrivateKeyPEM = normalize_privatekey_pem(b("""\
-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQD5mkLpi7q6ROdu7khB3S9aanA0Zls7vvfGOmB80/yeylhGpsjA
jWen0VtSQke/NlEPGtO38tsV7CsuFnSmschvAnGrcJl76b0UOOHUgDTIoRxC6QDU
3claegwsrBA+sJEBbqx5RdXbIRGicPG/8qQ4Zm1SKOgotcbwiaor2yxZ2wIDAQAB
AoGBAPCgMpmLxzwDaUmcFbTJUvlLW1hoxNNYSu2jIZm1k/hRAcE60JYwvBkgz3UB
yMEh0AtLxYe0bFk6EHah11tMUPgscbCq73snJ++8koUw+csk22G65hOs51bVb7Aa
6JBe67oLzdtvgCUFAA2qfrKzWRZzAdhUirQUZgySZk+Xq1pBAkEA/kZG0A6roTSM
BVnx7LnPfsycKUsTumorpXiylZJjTi9XtmzxhrYN6wgZlDOOwOLgSQhszGpxVoMD
u3gByT1b2QJBAPtL3mSKdvwRu/+40zaZLwvSJRxaj0mcE4BJOS6Oqs/hS1xRlrNk
PpQ7WJ4yM6ZOLnXzm2mKyxm50Mv64109FtMCQQDOqS2KkjHaLowTGVxwC0DijMfr
I9Lf8sSQk32J5VWCySWf5gGTfEnpmUa41gKTMJIbqZZLucNuDcOtzUaeWZlZAkA8
ttXigLnCqR486JDPTi9ZscoZkZ+w7y6e/hH8t6d5Vjt48JVyfjPIaJY+km58LcN3
6AWSeGAdtRFHVzR7oHjVAkB4hutvxiOeiIVQNBhM6RSI9aBPMI21DoX2JRoxvNW2
cbvAhow217X9V0dVerEOKxnNYspXRrh36h7k4mQA+sDq
-----END RSA PRIVATE KEY-----
"""))

cleartextCertificateRequestPEM = b("""-----BEGIN CERTIFICATE REQUEST-----
MIIBnjCCAQcCAQAwXjELMAkGA1UEBhMCVVMxCzAJBgNVBAgTAklMMRAwDgYDVQQH
EwdDaGljYWdvMRcwFQYDVQQKEw5NeSBDb21wYW55IEx0ZDEXMBUGA1UEAxMORnJl
ZGVyaWNrIERlYW4wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBANp6Y17WzKSw
BsUWkXdqg6tnXy8H8hA1msCMWpc+/2KJ4mbv5NyD6UD+/SqagQqulPbF/DFea9nA
E0zhmHJELcM8gUTIlXv/cgDWnmK4xj8YkjVUiCdqKRAKeuzLG1pGmwwF5lGeJpXN
xQn5ecR0UYSOWj6TTGXB9VyUMQzCClcBAgMBAAGgADANBgkqhkiG9w0BAQUFAAOB
gQAAJGuF/R/GGbeC7FbFW+aJgr9ee0Xbl6nlhu7pTe67k+iiKT2dsl2ti68MVTnu
Vrb3HUNqOkiwsJf6kCtq5oPn3QVYzTa76Dt2y3Rtzv6boRSlmlfrgS92GNma8JfR
oICQk3nAudi6zl1Dix3BCv1pUp5KMtGn3MeDEi6QFGy2rA==
-----END CERTIFICATE REQUEST-----
""")

encryptedPrivateKeyPEM = b("""-----BEGIN RSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: DES-EDE3-CBC,9573604A18579E9E

SHOho56WxDkT0ht10UTeKc0F5u8cqIa01kzFAmETw0MAs8ezYtK15NPdCXUm3X/2
a17G7LSF5bkxOgZ7vpXyMzun/owrj7CzvLxyncyEFZWvtvzaAhPhvTJtTIB3kf8B
8+qRcpTGK7NgXEgYBW5bj1y4qZkD4zCL9o9NQzsKI3Ie8i0239jsDOWR38AxjXBH
mGwAQ4Z6ZN5dnmM4fhMIWsmFf19sNyAML4gHenQCHhmXbjXeVq47aC2ProInJbrm
+00TcisbAQ40V9aehVbcDKtS4ZbMVDwncAjpXpcncC54G76N6j7F7wL7L/FuXa3A
fvSVy9n2VfF/pJ3kYSflLHH2G/DFxjF7dl0GxhKPxJjp3IJi9VtuvmN9R2jZWLQF
tfC8dXgy/P9CfFQhlinqBTEwgH0oZ/d4k4NVFDSdEMaSdmBAjlHpc+Vfdty3HVnV
rKXj//wslsFNm9kIwJGIgKUa/n2jsOiydrsk1mgH7SmNCb3YHgZhbbnq0qLat/HC
gHDt3FHpNQ31QzzL3yrenFB2L9osIsnRsDTPFNi4RX4SpDgNroxOQmyzCCV6H+d4
o1mcnNiZSdxLZxVKccq0AfRpHqpPAFnJcQHP6xyT9MZp6fBa0XkxDnt9kNU8H3Qw
7SJWZ69VXjBUzMlQViLuaWMgTnL+ZVyFZf9hTF7U/ef4HMLMAVNdiaGG+G+AjCV/
MbzjS007Oe4qqBnCWaFPSnJX6uLApeTbqAxAeyCql56ULW5x6vDMNC3dwjvS/CEh
11n8RkgFIQA0AhuKSIg3CbuartRsJnWOLwgLTzsrKYL4yRog1RJrtw==
-----END RSA PRIVATE KEY-----
""")

encryptedPrivateKeyPEMPassphrase = b("foobar")

# Some PKCS#7 stuff.  Generated with the openssl command line:
#
#    openssl crl2pkcs7 -inform pem -outform pem -certfile s.pem -nocrl
#
# with a certificate and key (but the key should be irrelevant) in s.pem
pkcs7Data = b("""\
-----BEGIN PKCS7-----
MIIDNwYJKoZIhvcNAQcCoIIDKDCCAyQCAQExADALBgkqhkiG9w0BBwGgggMKMIID
BjCCAm+gAwIBAgIBATANBgkqhkiG9w0BAQQFADB7MQswCQYDVQQGEwJTRzERMA8G
A1UEChMITTJDcnlwdG8xFDASBgNVBAsTC00yQ3J5cHRvIENBMSQwIgYDVQQDExtN
MkNyeXB0byBDZXJ0aWZpY2F0ZSBNYXN0ZXIxHTAbBgkqhkiG9w0BCQEWDm5ncHNA
cG9zdDEuY29tMB4XDTAwMDkxMDA5NTEzMFoXDTAyMDkxMDA5NTEzMFowUzELMAkG
A1UEBhMCU0cxETAPBgNVBAoTCE0yQ3J5cHRvMRIwEAYDVQQDEwlsb2NhbGhvc3Qx
HTAbBgkqhkiG9w0BCQEWDm5ncHNAcG9zdDEuY29tMFwwDQYJKoZIhvcNAQEBBQAD
SwAwSAJBAKy+e3dulvXzV7zoTZWc5TzgApr8DmeQHTYC8ydfzH7EECe4R1Xh5kwI
zOuuFfn178FBiS84gngaNcrFi0Z5fAkCAwEAAaOCAQQwggEAMAkGA1UdEwQCMAAw
LAYJYIZIAYb4QgENBB8WHU9wZW5TU0wgR2VuZXJhdGVkIENlcnRpZmljYXRlMB0G
A1UdDgQWBBTPhIKSvnsmYsBVNWjj0m3M2z0qVTCBpQYDVR0jBIGdMIGagBT7hyNp
65w6kxXlxb8pUU/+7Sg4AaF/pH0wezELMAkGA1UEBhMCU0cxETAPBgNVBAoTCE0y
Q3J5cHRvMRQwEgYDVQQLEwtNMkNyeXB0byBDQTEkMCIGA1UEAxMbTTJDcnlwdG8g
Q2VydGlmaWNhdGUgTWFzdGVyMR0wGwYJKoZIhvcNAQkBFg5uZ3BzQHBvc3QxLmNv
bYIBADANBgkqhkiG9w0BAQQFAAOBgQA7/CqT6PoHycTdhEStWNZde7M/2Yc6BoJu
VwnW8YxGO8Sn6UJ4FeffZNcYZddSDKosw8LtPOeWoK3JINjAk5jiPQ2cww++7QGG
/g5NDjxFZNDJP1dGiLAxPW6JXwov4v0FmdzfLOZ01jDcgQQZqEpYlgpuI5JEWUQ9
Ho4EzbYCOaEAMQA=
-----END PKCS7-----
""")

crlData = b("""\
-----BEGIN X509 CRL-----
MIIBWzCBxTANBgkqhkiG9w0BAQQFADBYMQswCQYDVQQGEwJVUzELMAkGA1UECBMC
SUwxEDAOBgNVBAcTB0NoaWNhZ28xEDAOBgNVBAoTB1Rlc3RpbmcxGDAWBgNVBAMT
D1Rlc3RpbmcgUm9vdCBDQRcNMDkwNzI2MDQzNDU2WhcNMTIwOTI3MDI0MTUyWjA8
MBUCAgOrGA8yMDA5MDcyNTIzMzQ1NlowIwICAQAYDzIwMDkwNzI1MjMzNDU2WjAM
MAoGA1UdFQQDCgEEMA0GCSqGSIb3DQEBBAUAA4GBAEBt7xTs2htdD3d4ErrcGAw1
4dKcVnIWTutoI7xxen26Wwvh8VCsT7i/UeP+rBl9rC/kfjWjzQk3/zleaarGTpBT
0yp4HXRFFoRhhSE/hP+eteaPXRgrsNRLHe9ZDd69wmh7J1wMDb0m81RG7kqcbsid
vrzEeLDRiiPl92dyyWmu
-----END X509 CRL-----
""")


# A broken RSA private key which can be used to test the error path through
# PKey.check.
inconsistentPrivateKeyPEM = b("""-----BEGIN RSA PRIVATE KEY-----
MIIBPAIBAAJBAKy+e3dulvXzV7zoTZWc5TzgApr8DmeQHTYC8ydfzH7EECe4R1Xh
5kwIzOuuFfn178FBiS84gngaNcrFi0Z5fAkCAwEaAQJBAIqm/bz4NA1H++Vx5Ewx
OcKp3w19QSaZAwlGRtsUxrP7436QjnREM3Bm8ygU11BjkPVmtrKm6AayQfCHqJoT
zIECIQDW0BoMoL0HOYM/mrTLhaykYAVqgIeJsPjvkEhTFXWBuQIhAM3deFAvWNu4
nklUQ37XsCT2c9tmNt1LAT+slG2JOTTRAiAuXDtC/m3NYVwyHfFm+zKHRzHkClk2
HjubeEgjpj32AQIhAJqMGTaZVOwevTXvvHwNeH+vRWsAYU/gbx+OQB+7VOcBAiEA
oolb6NMg/R3enNPvS1O4UU1H8wpaF77L4yiSWlE0p4w=
-----END RSA PRIVATE KEY-----
""")


class X509ExtTests(TestCase):
    """
    Tests for L{OpenSSL.crypto.X509Extension}.
    """

    def setUp(self):
        """
        Create a new private key and start a certificate request (for a test
        method to finish in one way or another).
        """
        # Basic setup stuff to generate a certificate
        self.pkey = PKey()
        self.pkey.generate_key(TYPE_RSA, 384)
        self.req = X509Req()
        self.req.set_pubkey(self.pkey)
        # Authority good you have.
        self.req.get_subject().commonName = "Yoda root CA"
        self.x509 = X509()
        self.subject = self.x509.get_subject()
        self.subject.commonName = self.req.get_subject().commonName
        self.x509.set_issuer(self.subject)
        self.x509.set_pubkey(self.pkey)
        now = b(datetime.now().strftime("%Y%m%d%H%M%SZ"))
        expire  = b((datetime.now() + timedelta(days=100)).strftime("%Y%m%d%H%M%SZ"))
        self.x509.set_notBefore(now)
        self.x509.set_notAfter(expire)


    def test_str(self):
        """
        The string representation of L{X509Extension} instances as returned by
        C{str} includes stuff.
        """
        # This isn't necessarily the best string representation.  Perhaps it
        # will be changed/improved in the future.
        self.assertEquals(
            str(X509Extension(b('basicConstraints'), True, b('CA:false'))),
            'CA:FALSE')


    def test_type(self):
        """
        L{X509Extension} and L{X509ExtensionType} refer to the same type object
        and can be used to create instances of that type.
        """
        self.assertIdentical(X509Extension, X509ExtensionType)
        self.assertConsistentType(
            X509Extension,
            'X509Extension', b('basicConstraints'), True, b('CA:true'))


    def test_construction(self):
        """
        L{X509Extension} accepts an extension type name, a critical flag,
        and an extension value and returns an L{X509ExtensionType} instance.
        """
        basic = X509Extension(b('basicConstraints'), True, b('CA:true'))
        self.assertTrue(
            isinstance(basic, X509ExtensionType),
            "%r is of type %r, should be %r" % (
                basic, type(basic), X509ExtensionType))

        comment = X509Extension(
            b('nsComment'), False, b('pyOpenSSL unit test'))
        self.assertTrue(
            isinstance(comment, X509ExtensionType),
            "%r is of type %r, should be %r" % (
                comment, type(comment), X509ExtensionType))


    def test_invalid_extension(self):
        """
        L{X509Extension} raises something if it is passed a bad extension
        name or value.
        """
        self.assertRaises(
            Error, X509Extension, b('thisIsMadeUp'), False, b('hi'))
        self.assertRaises(
            Error, X509Extension, b('basicConstraints'), False, b('blah blah'))

        # Exercise a weird one (an extension which uses the r2i method).  This
        # exercises the codepath that requires a non-NULL ctx to be passed to
        # X509V3_EXT_nconf.  It can't work now because we provide no
        # configuration database.  It might be made to work in the future.
        self.assertRaises(
            Error, X509Extension, b('proxyCertInfo'), True,
            b('language:id-ppl-anyLanguage,pathlen:1,policy:text:AB'))


    def test_get_critical(self):
        """
        L{X509ExtensionType.get_critical} returns the value of the
        extension's critical flag.
        """
        ext = X509Extension(b('basicConstraints'), True, b('CA:true'))
        self.assertTrue(ext.get_critical())
        ext = X509Extension(b('basicConstraints'), False, b('CA:true'))
        self.assertFalse(ext.get_critical())


    def test_get_short_name(self):
        """
        L{X509ExtensionType.get_short_name} returns a string giving the short
        type name of the extension.
        """
        ext = X509Extension(b('basicConstraints'), True, b('CA:true'))
        self.assertEqual(ext.get_short_name(), b('basicConstraints'))
        ext = X509Extension(b('nsComment'), True, b('foo bar'))
        self.assertEqual(ext.get_short_name(), b('nsComment'))


    def test_get_data(self):
        """
        L{X509Extension.get_data} returns a string giving the data of the
        extension.
        """
        ext = X509Extension(b('basicConstraints'), True, b('CA:true'))
        # Expect to get back the DER encoded form of CA:true.
        self.assertEqual(ext.get_data(), b('0\x03\x01\x01\xff'))


    def test_get_data_wrong_args(self):
        """
        L{X509Extension.get_data} raises L{TypeError} if passed any arguments.
        """
        ext = X509Extension(b('basicConstraints'), True, b('CA:true'))
        self.assertRaises(TypeError, ext.get_data, None)
        self.assertRaises(TypeError, ext.get_data, "foo")
        self.assertRaises(TypeError, ext.get_data, 7)


    def test_unused_subject(self):
        """
        The C{subject} parameter to L{X509Extension} may be provided for an
        extension which does not use it and is ignored in this case.
        """
        ext1 = X509Extension(
            b('basicConstraints'), False, b('CA:TRUE'), subject=self.x509)
        self.x509.add_extensions([ext1])
        self.x509.sign(self.pkey, 'sha1')
        # This is a little lame.  Can we think of a better way?
        text = dump_certificate(FILETYPE_TEXT, self.x509)
        self.assertTrue(b('X509v3 Basic Constraints:') in text)
        self.assertTrue(b('CA:TRUE') in text)


    def test_subject(self):
        """
        If an extension requires a subject, the C{subject} parameter to
        L{X509Extension} provides its value.
        """
        ext3 = X509Extension(
            b('subjectKeyIdentifier'), False, b('hash'), subject=self.x509)
        self.x509.add_extensions([ext3])
        self.x509.sign(self.pkey, 'sha1')
        text = dump_certificate(FILETYPE_TEXT, self.x509)
        self.assertTrue(b('X509v3 Subject Key Identifier:') in text)


    def test_missing_subject(self):
        """
        If an extension requires a subject and the C{subject} parameter is
        given no value, something happens.
        """
        self.assertRaises(
            Error, X509Extension, b('subjectKeyIdentifier'), False, b('hash'))


    def test_invalid_subject(self):
        """
        If the C{subject} parameter is given a value which is not an L{X509}
        instance, L{TypeError} is raised.
        """
        for badObj in [True, object(), "hello", [], self]:
            self.assertRaises(
                TypeError,
                X509Extension,
                'basicConstraints', False, 'CA:TRUE', subject=badObj)


    def test_unused_issuer(self):
        """
        The C{issuer} parameter to L{X509Extension} may be provided for an
        extension which does not use it and is ignored in this case.
        """
        ext1 = X509Extension(
            b('basicConstraints'), False, b('CA:TRUE'), issuer=self.x509)
        self.x509.add_extensions([ext1])
        self.x509.sign(self.pkey, 'sha1')
        text = dump_certificate(FILETYPE_TEXT, self.x509)
        self.assertTrue(b('X509v3 Basic Constraints:') in text)
        self.assertTrue(b('CA:TRUE') in text)


    def test_issuer(self):
        """
        If an extension requires a issuer, the C{issuer} parameter to
        L{X509Extension} provides its value.
        """
        ext2 = X509Extension(
            b('authorityKeyIdentifier'), False, b('issuer:always'),
            issuer=self.x509)
        self.x509.add_extensions([ext2])
        self.x509.sign(self.pkey, 'sha1')
        text = dump_certificate(FILETYPE_TEXT, self.x509)
        self.assertTrue(b('X509v3 Authority Key Identifier:') in text)
        self.assertTrue(b('DirName:/CN=Yoda root CA') in text)


    def test_missing_issuer(self):
        """
        If an extension requires an issue and the C{issuer} parameter is given
        no value, something happens.
        """
        self.assertRaises(
            Error,
            X509Extension,
            b('authorityKeyIdentifier'), False,
            b('keyid:always,issuer:always'))


    def test_invalid_issuer(self):
        """
        If the C{issuer} parameter is given a value which is not an L{X509}
        instance, L{TypeError} is raised.
        """
        for badObj in [True, object(), "hello", [], self]:
            self.assertRaises(
                TypeError,
                X509Extension,
                'authorityKeyIdentifier', False, 'keyid:always,issuer:always',
                issuer=badObj)



class PKeyTests(TestCase):
    """
    Unit tests for L{OpenSSL.crypto.PKey}.
    """
    def test_type(self):
        """
        L{PKey} and L{PKeyType} refer to the same type object and can be used
        to create instances of that type.
        """
        self.assertIdentical(PKey, PKeyType)
        self.assertConsistentType(PKey, 'PKey')


    def test_construction(self):
        """
        L{PKey} takes no arguments and returns a new L{PKey} instance.
        """
        self.assertRaises(TypeError, PKey, None)
        key = PKey()
        self.assertTrue(
            isinstance(key, PKeyType),
            "%r is of type %r, should be %r" % (key, type(key), PKeyType))


    def test_pregeneration(self):
        """
        L{PKeyType.bits} and L{PKeyType.type} return C{0} before the key is
        generated.  L{PKeyType.check} raises L{TypeError} before the key is
        generated.
        """
        key = PKey()
        self.assertEqual(key.type(), 0)
        self.assertEqual(key.bits(), 0)
        self.assertRaises(TypeError, key.check)


    def test_failedGeneration(self):
        """
        L{PKeyType.generate_key} takes two arguments, the first giving the key
        type as one of L{TYPE_RSA} or L{TYPE_DSA} and the second giving the
        number of bits to generate.  If an invalid type is specified or
        generation fails, L{Error} is raised.  If an invalid number of bits is
        specified, L{ValueError} or L{Error} is raised.
        """
        key = PKey()
        self.assertRaises(TypeError, key.generate_key)
        self.assertRaises(TypeError, key.generate_key, 1, 2, 3)
        self.assertRaises(TypeError, key.generate_key, "foo", "bar")
        self.assertRaises(Error, key.generate_key, -1, 0)

        self.assertRaises(ValueError, key.generate_key, TYPE_RSA, -1)
        self.assertRaises(ValueError, key.generate_key, TYPE_RSA, 0)

        # XXX RSA generation for small values of bits is fairly buggy in a wide
        # range of OpenSSL versions.  I need to figure out what the safe lower
        # bound for a reasonable number of OpenSSL versions is and explicitly
        # check for that in the wrapper.  The failure behavior is typically an
        # infinite loop inside OpenSSL.

        # self.assertRaises(Error, key.generate_key, TYPE_RSA, 2)

        # XXX DSA generation seems happy with any number of bits.  The DSS
        # says bits must be between 512 and 1024 inclusive.  OpenSSL's DSA
        # generator doesn't seem to care about the upper limit at all.  For
        # the lower limit, it uses 512 if anything smaller is specified.
        # So, it doesn't seem possible to make generate_key fail for
        # TYPE_DSA with a bits argument which is at least an int.

        # self.assertRaises(Error, key.generate_key, TYPE_DSA, -7)


    def test_rsaGeneration(self):
        """
        L{PKeyType.generate_key} generates an RSA key when passed
        L{TYPE_RSA} as a type and a reasonable number of bits.
        """
        bits = 128
        key = PKey()
        key.generate_key(TYPE_RSA, bits)
        self.assertEqual(key.type(), TYPE_RSA)
        self.assertEqual(key.bits(), bits)
        self.assertTrue(key.check())


    def test_dsaGeneration(self):
        """
        L{PKeyType.generate_key} generates a DSA key when passed
        L{TYPE_DSA} as a type and a reasonable number of bits.
        """
        # 512 is a magic number.  The DSS (Digital Signature Standard)
        # allows a minimum of 512 bits for DSA.  DSA_generate_parameters
        # will silently promote any value below 512 to 512.
        bits = 512
        key = PKey()
        key.generate_key(TYPE_DSA, bits)
        self.assertEqual(key.type(), TYPE_DSA)
        self.assertEqual(key.bits(), bits)
        self.assertRaises(TypeError, key.check)


    def test_regeneration(self):
        """
        L{PKeyType.generate_key} can be called multiple times on the same
        key to generate new keys.
        """
        key = PKey()
        for type, bits in [(TYPE_RSA, 512), (TYPE_DSA, 576)]:
             key.generate_key(type, bits)
             self.assertEqual(key.type(), type)
             self.assertEqual(key.bits(), bits)


    def test_inconsistentKey(self):
        """
        L{PKeyType.check} returns C{False} if the key is not consistent.
        """
        key = load_privatekey(FILETYPE_PEM, inconsistentPrivateKeyPEM)
        self.assertRaises(Error, key.check)


    def test_check_wrong_args(self):
        """
        L{PKeyType.check} raises L{TypeError} if called with any arguments.
        """
        self.assertRaises(TypeError, PKey().check, None)
        self.assertRaises(TypeError, PKey().check, object())
        self.assertRaises(TypeError, PKey().check, 1)



class X509NameTests(TestCase):
    """
    Unit tests for L{OpenSSL.crypto.X509Name}.
    """
    def _x509name(self, **attrs):
        # XXX There's no other way to get a new X509Name yet.
        name = X509().get_subject()
        attrs = list(attrs.items())
        # Make the order stable - order matters!
        def key(attr):
            return attr[1]
        attrs.sort(key=key)
        for k, v in attrs:
            setattr(name, k, v)
        return name


    def test_type(self):
        """
        The type of X509Name objects is L{X509NameType}.
        """
        self.assertIdentical(X509Name, X509NameType)
        self.assertEqual(X509NameType.__name__, 'X509Name')
        self.assertTrue(isinstance(X509NameType, type))

        name = self._x509name()
        self.assertTrue(
            isinstance(name, X509NameType),
            "%r is of type %r, should be %r" % (
                name, type(name), X509NameType))


    def test_onlyStringAttributes(self):
        """
        Attempting to set a non-L{str} attribute name on an L{X509NameType}
        instance causes L{TypeError} to be raised.
        """
        name = self._x509name()
        # Beyond these cases, you may also think that unicode should be
        # rejected.  Sorry, you're wrong.  unicode is automatically converted to
        # str outside of the control of X509Name, so there's no way to reject
        # it.
        self.assertRaises(TypeError, setattr, name, None, "hello")
        self.assertRaises(TypeError, setattr, name, 30, "hello")
        class evil(str):
            pass
        self.assertRaises(TypeError, setattr, name, evil(), "hello")


    def test_setInvalidAttribute(self):
        """
        Attempting to set any attribute name on an L{X509NameType} instance for
        which no corresponding NID is defined causes L{AttributeError} to be
        raised.
        """
        name = self._x509name()
        self.assertRaises(AttributeError, setattr, name, "no such thing", None)


    def test_attributes(self):
        """
        L{X509NameType} instances have attributes for each standard (?)
        X509Name field.
        """
        name = self._x509name()
        name.commonName = "foo"
        self.assertEqual(name.commonName, "foo")
        self.assertEqual(name.CN, "foo")
        name.CN = "baz"
        self.assertEqual(name.commonName, "baz")
        self.assertEqual(name.CN, "baz")
        name.commonName = "bar"
        self.assertEqual(name.commonName, "bar")
        self.assertEqual(name.CN, "bar")
        name.CN = "quux"
        self.assertEqual(name.commonName, "quux")
        self.assertEqual(name.CN, "quux")


    def test_copy(self):
        """
        L{X509Name} creates a new L{X509NameType} instance with all the same
        attributes as an existing L{X509NameType} instance when called with
        one.
        """
        name = self._x509name(commonName="foo", emailAddress="bar@example.com")

        copy = X509Name(name)
        self.assertEqual(copy.commonName, "foo")
        self.assertEqual(copy.emailAddress, "bar@example.com")

        # Mutate the copy and ensure the original is unmodified.
        copy.commonName = "baz"
        self.assertEqual(name.commonName, "foo")

        # Mutate the original and ensure the copy is unmodified.
        name.emailAddress = "quux@example.com"
        self.assertEqual(copy.emailAddress, "bar@example.com")


    def test_repr(self):
        """
        L{repr} passed an L{X509NameType} instance should return a string
        containing a description of the type and the NIDs which have been set
        on it.
        """
        name = self._x509name(commonName="foo", emailAddress="bar")
        self.assertEqual(
            repr(name),
            "<X509Name object '/emailAddress=bar/CN=foo'>")


    def test_comparison(self):
        """
        L{X509NameType} instances should compare based on their NIDs.
        """
        def _equality(a, b, assertTrue, assertFalse):
            assertTrue(a == b, "(%r == %r) --> False" % (a, b))
            assertFalse(a != b)
            assertTrue(b == a)
            assertFalse(b != a)

        def assertEqual(a, b):
            _equality(a, b, self.assertTrue, self.assertFalse)

        # Instances compare equal to themselves.
        name = self._x509name()
        assertEqual(name, name)

        # Empty instances should compare equal to each other.
        assertEqual(self._x509name(), self._x509name())

        # Instances with equal NIDs should compare equal to each other.
        assertEqual(self._x509name(commonName="foo"),
                    self._x509name(commonName="foo"))

        # Instance with equal NIDs set using different aliases should compare
        # equal to each other.
        assertEqual(self._x509name(commonName="foo"),
                    self._x509name(CN="foo"))

        # Instances with more than one NID with the same values should compare
        # equal to each other.
        assertEqual(self._x509name(CN="foo", organizationalUnitName="bar"),
                    self._x509name(commonName="foo", OU="bar"))

        def assertNotEqual(a, b):
            _equality(a, b, self.assertFalse, self.assertTrue)

        # Instances with different values for the same NID should not compare
        # equal to each other.
        assertNotEqual(self._x509name(CN="foo"),
                       self._x509name(CN="bar"))

        # Instances with different NIDs should not compare equal to each other.
        assertNotEqual(self._x509name(CN="foo"),
                       self._x509name(OU="foo"))

        def _inequality(a, b, assertTrue, assertFalse):
            assertTrue(a < b)
            assertTrue(a <= b)
            assertTrue(b > a)
            assertTrue(b >= a)
            assertFalse(a > b)
            assertFalse(a >= b)
            assertFalse(b < a)
            assertFalse(b <= a)

        def assertLessThan(a, b):
            _inequality(a, b, self.assertTrue, self.assertFalse)

        # An X509Name with a NID with a value which sorts less than the value
        # of the same NID on another X509Name compares less than the other
        # X509Name.
        assertLessThan(self._x509name(CN="abc"),
                       self._x509name(CN="def"))

        def assertGreaterThan(a, b):
            _inequality(a, b, self.assertFalse, self.assertTrue)

        # An X509Name with a NID with a value which sorts greater than the
        # value of the same NID on another X509Name compares greater than the
        # other X509Name.
        assertGreaterThan(self._x509name(CN="def"),
                          self._x509name(CN="abc"))


    def test_hash(self):
        """
        L{X509Name.hash} returns an integer hash based on the value of the
        name.
        """
        a = self._x509name(CN="foo")
        b = self._x509name(CN="foo")
        self.assertEqual(a.hash(), b.hash())
        a.CN = "bar"
        self.assertNotEqual(a.hash(), b.hash())


    def test_der(self):
        """
        L{X509Name.der} returns the DER encoded form of the name.
        """
        a = self._x509name(CN="foo", C="US")
        self.assertEqual(
            a.der(),
            b('0\x1b1\x0b0\t\x06\x03U\x04\x06\x13\x02US'
              '1\x0c0\n\x06\x03U\x04\x03\x13\x03foo'))


    def test_get_components(self):
        """
        L{X509Name.get_components} returns a C{list} of two-tuples of C{str}
        giving the NIDs and associated values which make up the name.
        """
        a = self._x509name()
        self.assertEqual(a.get_components(), [])
        a.CN = "foo"
        self.assertEqual(a.get_components(), [(b("CN"), b("foo"))])
        a.organizationalUnitName = "bar"
        self.assertEqual(
            a.get_components(),
            [(b("CN"), b("foo")), (b("OU"), b("bar"))])


class _PKeyInteractionTestsMixin:
    """
    Tests which involve another thing and a PKey.
    """
    def signable(self):
        """
        Return something with a C{set_pubkey}, C{set_pubkey}, and C{sign} method.
        """
        raise NotImplementedError()


    def test_signWithUngenerated(self):
        """
        L{X509Req.sign} raises L{ValueError} when pass a L{PKey} with no parts.
        """
        request = self.signable()
        key = PKey()
        self.assertRaises(ValueError, request.sign, key, 'MD5')


    def test_signWithPublicKey(self):
        """
        L{X509Req.sign} raises L{ValueError} when pass a L{PKey} with no
        private part as the signing key.
        """
        request = self.signable()
        key = PKey()
        key.generate_key(TYPE_RSA, 512)
        request.set_pubkey(key)
        pub = request.get_pubkey()
        self.assertRaises(ValueError, request.sign, pub, 'MD5')


    def test_signWithUnknownDigest(self):
        """
        L{X509Req.sign} raises L{ValueError} when passed a digest name which is
        not known.
        """
        request = self.signable()
        key = PKey()
        key.generate_key(TYPE_RSA, 512)
        self.assertRaises(ValueError, request.sign, key, "monkeys")


    def test_sign(self):
        """
        L{X509Req.sign} succeeds when passed a private key object and a valid
        digest function.  C{X509Req.verify} can be used to check the signature.
        """
        request = self.signable()
        key = PKey()
        key.generate_key(TYPE_RSA, 512)
        request.set_pubkey(key)
        request.sign(key, 'MD5')
        # If the type has a verify method, cover that too.
        if getattr(request, 'verify', None) is not None:
            pub = request.get_pubkey()
            self.assertTrue(request.verify(pub))
            # Make another key that won't verify.
            key = PKey()
            key.generate_key(TYPE_RSA, 512)
            self.assertRaises(Error, request.verify, key)




class X509ReqTests(TestCase, _PKeyInteractionTestsMixin):
    """
    Tests for L{OpenSSL.crypto.X509Req}.
    """
    def signable(self):
        """
        Create and return a new L{X509Req}.
        """
        return X509Req()


    def test_type(self):
        """
        L{X509Req} and L{X509ReqType} refer to the same type object and can be
        used to create instances of that type.
        """
        self.assertIdentical(X509Req, X509ReqType)
        self.assertConsistentType(X509Req, 'X509Req')


    def test_construction(self):
        """
        L{X509Req} takes no arguments and returns an L{X509ReqType} instance.
        """
        request = X509Req()
        self.assertTrue(
            isinstance(request, X509ReqType),
            "%r is of type %r, should be %r" % (request, type(request), X509ReqType))


    def test_version(self):
        """
        L{X509ReqType.set_version} sets the X.509 version of the certificate
        request.  L{X509ReqType.get_version} returns the X.509 version of
        the certificate request.  The initial value of the version is 0.
        """
        request = X509Req()
        self.assertEqual(request.get_version(), 0)
        request.set_version(1)
        self.assertEqual(request.get_version(), 1)
        request.set_version(3)
        self.assertEqual(request.get_version(), 3)


    def test_version_wrong_args(self):
        """
        L{X509ReqType.set_version} raises L{TypeError} if called with the wrong
        number of arguments or with a non-C{int} argument.
        L{X509ReqType.get_version} raises L{TypeError} if called with any
        arguments.
        """
        request = X509Req()
        self.assertRaises(TypeError, request.set_version)
        self.assertRaises(TypeError, request.set_version, "foo")
        self.assertRaises(TypeError, request.set_version, 1, 2)
        self.assertRaises(TypeError, request.get_version, None)


    def test_get_subject(self):
        """
        L{X509ReqType.get_subject} returns an L{X509Name} for the subject of
        the request and which is valid even after the request object is
        otherwise dead.
        """
        request = X509Req()
        subject = request.get_subject()
        self.assertTrue(
            isinstance(subject, X509NameType),
            "%r is of type %r, should be %r" % (subject, type(subject), X509NameType))
        subject.commonName = "foo"
        self.assertEqual(request.get_subject().commonName, "foo")
        del request
        subject.commonName = "bar"
        self.assertEqual(subject.commonName, "bar")


    def test_get_subject_wrong_args(self):
        """
        L{X509ReqType.get_subject} raises L{TypeError} if called with any
        arguments.
        """
        request = X509Req()
        self.assertRaises(TypeError, request.get_subject, None)


    def test_add_extensions(self):
        """
        L{X509Req.add_extensions} accepts a C{list} of L{X509Extension}
        instances and adds them to the X509 request.
        """
        request = X509Req()
        request.add_extensions([
                X509Extension(b('basicConstraints'), True, b('CA:false'))])
        # XXX Add get_extensions so the rest of this unit test can be written.


    def test_add_extensions_wrong_args(self):
        """
        L{X509Req.add_extensions} raises L{TypeError} if called with the wrong
        number of arguments or with a non-C{list}.  Or it raises L{ValueError}
        if called with a C{list} containing objects other than L{X509Extension}
        instances.
        """
        request = X509Req()
        self.assertRaises(TypeError, request.add_extensions)
        self.assertRaises(TypeError, request.add_extensions, object())
        self.assertRaises(ValueError, request.add_extensions, [object()])
        self.assertRaises(TypeError, request.add_extensions, [], None)



class X509Tests(TestCase, _PKeyInteractionTestsMixin):
    """
    Tests for L{OpenSSL.crypto.X509}.
    """
    pemData = cleartextCertificatePEM + cleartextPrivateKeyPEM

    extpem = """
-----BEGIN CERTIFICATE-----
MIIC3jCCAkegAwIBAgIJAJHFjlcCgnQzMA0GCSqGSIb3DQEBBQUAMEcxCzAJBgNV
BAYTAlNFMRUwEwYDVQQIEwxXZXN0ZXJib3R0b20xEjAQBgNVBAoTCUNhdGFsb2dp
eDENMAsGA1UEAxMEUm9vdDAeFw0wODA0MjIxNDQ1MzhaFw0wOTA0MjIxNDQ1Mzha
MFQxCzAJBgNVBAYTAlNFMQswCQYDVQQIEwJXQjEUMBIGA1UEChMLT3Blbk1ldGFk
aXIxIjAgBgNVBAMTGW5vZGUxLm9tMi5vcGVubWV0YWRpci5vcmcwgZ8wDQYJKoZI
hvcNAQEBBQADgY0AMIGJAoGBAPIcQMrwbk2nESF/0JKibj9i1x95XYAOwP+LarwT
Op4EQbdlI9SY+uqYqlERhF19w7CS+S6oyqx0DRZSk4Y9dZ9j9/xgm2u/f136YS1u
zgYFPvfUs6PqYLPSM8Bw+SjJ+7+2+TN+Tkiof9WP1cMjodQwOmdsiRbR0/J7+b1B
hec1AgMBAAGjgcQwgcEwCQYDVR0TBAIwADAsBglghkgBhvhCAQ0EHxYdT3BlblNT
TCBHZW5lcmF0ZWQgQ2VydGlmaWNhdGUwHQYDVR0OBBYEFIdHsBcMVVMbAO7j6NCj
03HgLnHaMB8GA1UdIwQYMBaAFL2h9Bf9Mre4vTdOiHTGAt7BRY/8MEYGA1UdEQQ/
MD2CDSouZXhhbXBsZS5vcmeCESoub20yLmV4bWFwbGUuY29thwSC7wgKgRNvbTJA
b3Blbm1ldGFkaXIub3JnMA0GCSqGSIb3DQEBBQUAA4GBALd7WdXkp2KvZ7/PuWZA
MPlIxyjS+Ly11+BNE0xGQRp9Wz+2lABtpgNqssvU156+HkKd02rGheb2tj7MX9hG
uZzbwDAZzJPjzDQDD7d3cWsrVcfIdqVU7epHqIadnOF+X0ghJ39pAm6VVadnSXCt
WpOdIpB8KksUTCzV591Nr1wd
-----END CERTIFICATE-----
    """
    def signable(self):
        """
        Create and return a new L{X509}.
        """
        return X509()


    def test_type(self):
        """
        L{X509} and L{X509Type} refer to the same type object and can be used
        to create instances of that type.
        """
        self.assertIdentical(X509, X509Type)
        self.assertConsistentType(X509, 'X509')


    def test_construction(self):
        """
        L{X509} takes no arguments and returns an instance of L{X509Type}.
        """
        certificate = X509()
        self.assertTrue(
            isinstance(certificate, X509Type),
            "%r is of type %r, should be %r" % (certificate,
                                                type(certificate),
                                                X509Type))
        self.assertEqual(type(X509Type).__name__, 'type')
        self.assertEqual(type(certificate).__name__, 'X509')
        self.assertEqual(type(certificate), X509Type)
        self.assertEqual(type(certificate), X509)


    def test_get_version_wrong_args(self):
        """
        L{X509.get_version} raises L{TypeError} if invoked with any arguments.
        """
        cert = X509()
        self.assertRaises(TypeError, cert.get_version, None)


    def test_set_version_wrong_args(self):
        """
        L{X509.set_version} raises L{TypeError} if invoked with the wrong number
        of arguments or an argument not of type C{int}.
        """
        cert = X509()
        self.assertRaises(TypeError, cert.set_version)
        self.assertRaises(TypeError, cert.set_version, None)
        self.assertRaises(TypeError, cert.set_version, 1, None)


    def test_version(self):
        """
        L{X509.set_version} sets the certificate version number.
        L{X509.get_version} retrieves it.
        """
        cert = X509()
        cert.set_version(1234)
        self.assertEquals(cert.get_version(), 1234)


    def test_get_serial_number_wrong_args(self):
        """
        L{X509.get_serial_number} raises L{TypeError} if invoked with any
        arguments.
        """
        cert = X509()
        self.assertRaises(TypeError, cert.get_serial_number, None)


    def test_serial_number(self):
        """
        The serial number of an L{X509Type} can be retrieved and modified with
        L{X509Type.get_serial_number} and L{X509Type.set_serial_number}.
        """
        certificate = X509()
        self.assertRaises(TypeError, certificate.set_serial_number)
        self.assertRaises(TypeError, certificate.set_serial_number, 1, 2)
        self.assertRaises(TypeError, certificate.set_serial_number, "1")
        self.assertRaises(TypeError, certificate.set_serial_number, 5.5)
        self.assertEqual(certificate.get_serial_number(), 0)
        certificate.set_serial_number(1)
        self.assertEqual(certificate.get_serial_number(), 1)
        certificate.set_serial_number(2 ** 32 + 1)
        self.assertEqual(certificate.get_serial_number(), 2 ** 32 + 1)
        certificate.set_serial_number(2 ** 64 + 1)
        self.assertEqual(certificate.get_serial_number(), 2 ** 64 + 1)
        certificate.set_serial_number(2 ** 128 + 1)
        self.assertEqual(certificate.get_serial_number(), 2 ** 128 + 1)


    def _setBoundTest(self, which):
        """
        L{X509Type.set_notBefore} takes a string in the format of an ASN1
        GENERALIZEDTIME and sets the beginning of the certificate's validity
        period to it.
        """
        certificate = X509()
        set = getattr(certificate, 'set_not' + which)
        get = getattr(certificate, 'get_not' + which)

        # Starts with no value.
        self.assertEqual(get(), None)

        # GMT (Or is it UTC?) -exarkun
        when = b("20040203040506Z")
        set(when)
        self.assertEqual(get(), when)

        # A plus two hours and thirty minutes offset
        when = b("20040203040506+0530")
        set(when)
        self.assertEqual(get(), when)

        # A minus one hour fifteen minutes offset
        when = b("20040203040506-0115")
        set(when)
        self.assertEqual(get(), when)

        # An invalid string results in a ValueError
        self.assertRaises(ValueError, set, b("foo bar"))

        # The wrong number of arguments results in a TypeError.
        self.assertRaises(TypeError, set)
        self.assertRaises(TypeError, set, b("20040203040506Z"), b("20040203040506Z"))
        self.assertRaises(TypeError, get, b("foo bar"))


    # XXX ASN1_TIME (not GENERALIZEDTIME)

    def test_set_notBefore(self):
        """
        L{X509Type.set_notBefore} takes a string in the format of an ASN1
        GENERALIZEDTIME and sets the beginning of the certificate's validity
        period to it.
        """
        self._setBoundTest("Before")


    def test_set_notAfter(self):
        """
        L{X509Type.set_notAfter} takes a string in the format of an ASN1
        GENERALIZEDTIME and sets the end of the certificate's validity period
        to it.
        """
        self._setBoundTest("After")


    def test_get_notBefore(self):
        """
        L{X509Type.get_notBefore} returns a string in the format of an ASN1
        GENERALIZEDTIME even for certificates which store it as UTCTIME
        internally.
        """
        cert = load_certificate(FILETYPE_PEM, self.pemData)
        self.assertEqual(cert.get_notBefore(), b("20090325123658Z"))


    def test_get_notAfter(self):
        """
        L{X509Type.get_notAfter} returns a string in the format of an ASN1
        GENERALIZEDTIME even for certificates which store it as UTCTIME
        internally.
        """
        cert = load_certificate(FILETYPE_PEM, self.pemData)
        self.assertEqual(cert.get_notAfter(), b("20170611123658Z"))


    def test_gmtime_adj_notBefore_wrong_args(self):
        """
        L{X509Type.gmtime_adj_notBefore} raises L{TypeError} if called with the
        wrong number of arguments or a non-C{int} argument.
        """
        cert = X509()
        self.assertRaises(TypeError, cert.gmtime_adj_notBefore)
        self.assertRaises(TypeError, cert.gmtime_adj_notBefore, None)
        self.assertRaises(TypeError, cert.gmtime_adj_notBefore, 123, None)


    def test_gmtime_adj_notBefore(self):
        """
        L{X509Type.gmtime_adj_notBefore} changes the not-before timestamp to be
        the current time plus the number of seconds passed in.
        """
        cert = load_certificate(FILETYPE_PEM, self.pemData)
        now = datetime.utcnow() + timedelta(seconds=100)
        cert.gmtime_adj_notBefore(100)
        self.assertEqual(cert.get_notBefore(), b(now.strftime("%Y%m%d%H%M%SZ")))


    def test_gmtime_adj_notAfter_wrong_args(self):
        """
        L{X509Type.gmtime_adj_notAfter} raises L{TypeError} if called with the
        wrong number of arguments or a non-C{int} argument.
        """
        cert = X509()
        self.assertRaises(TypeError, cert.gmtime_adj_notAfter)
        self.assertRaises(TypeError, cert.gmtime_adj_notAfter, None)
        self.assertRaises(TypeError, cert.gmtime_adj_notAfter, 123, None)


    def test_gmtime_adj_notAfter(self):
        """
        L{X509Type.gmtime_adj_notAfter} changes the not-after timestamp to be
        the current time plus the number of seconds passed in.
        """
        cert = load_certificate(FILETYPE_PEM, self.pemData)
        now = datetime.utcnow() + timedelta(seconds=100)
        cert.gmtime_adj_notAfter(100)
        self.assertEqual(cert.get_notAfter(), b(now.strftime("%Y%m%d%H%M%SZ")))


    def test_has_expired_wrong_args(self):
        """
        L{X509Type.has_expired} raises L{TypeError} if called with any
        arguments.
        """
        cert = X509()
        self.assertRaises(TypeError, cert.has_expired, None)


    def test_has_expired(self):
        """
        L{X509Type.has_expired} returns C{True} if the certificate's not-after
        time is in the past.
        """
        cert = X509()
        cert.gmtime_adj_notAfter(-1)
        self.assertTrue(cert.has_expired())


    def test_has_not_expired(self):
        """
        L{X509Type.has_expired} returns C{False} if the certificate's not-after
        time is in the future.
        """
        cert = X509()
        cert.gmtime_adj_notAfter(2)
        self.assertFalse(cert.has_expired())


    def test_digest(self):
        """
        L{X509.digest} returns a string giving ":"-separated hex-encoded words
        of the digest of the certificate.
        """
        cert = X509()
        self.assertEqual(
            cert.digest("md5"),
            b("A8:EB:07:F8:53:25:0A:F2:56:05:C5:A5:C4:C4:C7:15"))


    def _extcert(self, pkey, extensions):
        cert = X509()
        cert.set_pubkey(pkey)
        cert.get_subject().commonName = "Unit Tests"
        cert.get_issuer().commonName = "Unit Tests"
        when = b(datetime.now().strftime("%Y%m%d%H%M%SZ"))
        cert.set_notBefore(when)
        cert.set_notAfter(when)

        cert.add_extensions(extensions)
        return load_certificate(
            FILETYPE_PEM, dump_certificate(FILETYPE_PEM, cert))


    def test_extension_count(self):
        """
        L{X509.get_extension_count} returns the number of extensions that are
        present in the certificate.
        """
        pkey = load_privatekey(FILETYPE_PEM, client_key_pem)
        ca = X509Extension(b('basicConstraints'), True, b('CA:FALSE'))
        key = X509Extension(b('keyUsage'), True, b('digitalSignature'))
        subjectAltName = X509Extension(
            b('subjectAltName'), True, b('DNS:example.com'))

        # Try a certificate with no extensions at all.
        c = self._extcert(pkey, [])
        self.assertEqual(c.get_extension_count(), 0)

        # And a certificate with one
        c = self._extcert(pkey, [ca])
        self.assertEqual(c.get_extension_count(), 1)

        # And a certificate with several
        c = self._extcert(pkey, [ca, key, subjectAltName])
        self.assertEqual(c.get_extension_count(), 3)


    def test_get_extension(self):
        """
        L{X509.get_extension} takes an integer and returns an L{X509Extension}
        corresponding to the extension at that index.
        """
        pkey = load_privatekey(FILETYPE_PEM, client_key_pem)
        ca = X509Extension(b('basicConstraints'), True, b('CA:FALSE'))
        key = X509Extension(b('keyUsage'), True, b('digitalSignature'))
        subjectAltName = X509Extension(
            b('subjectAltName'), False, b('DNS:example.com'))

        cert = self._extcert(pkey, [ca, key, subjectAltName])

        ext = cert.get_extension(0)
        self.assertTrue(isinstance(ext, X509Extension))
        self.assertTrue(ext.get_critical())
        self.assertEqual(ext.get_short_name(), b('basicConstraints'))

        ext = cert.get_extension(1)
        self.assertTrue(isinstance(ext, X509Extension))
        self.assertTrue(ext.get_critical())
        self.assertEqual(ext.get_short_name(), b('keyUsage'))

        ext = cert.get_extension(2)
        self.assertTrue(isinstance(ext, X509Extension))
        self.assertFalse(ext.get_critical())
        self.assertEqual(ext.get_short_name(), b('subjectAltName'))

        self.assertRaises(IndexError, cert.get_extension, -1)
        self.assertRaises(IndexError, cert.get_extension, 4)
        self.assertRaises(TypeError, cert.get_extension, "hello")


    def test_invalid_digest_algorithm(self):
        """
        L{X509.digest} raises L{ValueError} if called with an unrecognized hash
        algorithm.
        """
        cert = X509()
        self.assertRaises(ValueError, cert.digest, "monkeys")


    def test_get_subject_wrong_args(self):
        """
        L{X509.get_subject} raises L{TypeError} if called with any arguments.
        """
        cert = X509()
        self.assertRaises(TypeError, cert.get_subject, None)


    def test_get_subject(self):
        """
        L{X509.get_subject} returns an L{X509Name} instance.
        """
        cert = load_certificate(FILETYPE_PEM, self.pemData)
        subj = cert.get_subject()
        self.assertTrue(isinstance(subj, X509Name))
        self.assertEquals(
            subj.get_components(),
            [(b('C'), b('US')), (b('ST'), b('IL')), (b('L'), b('Chicago')),
             (b('O'), b('Testing')), (b('CN'), b('Testing Root CA'))])


    def test_set_subject_wrong_args(self):
        """
        L{X509.set_subject} raises a L{TypeError} if called with the wrong
        number of arguments or an argument not of type L{X509Name}.
        """
        cert = X509()
        self.assertRaises(TypeError, cert.set_subject)
        self.assertRaises(TypeError, cert.set_subject, None)
        self.assertRaises(TypeError, cert.set_subject, cert.get_subject(), None)


    def test_set_subject(self):
        """
        L{X509.set_subject} changes the subject of the certificate to the one
        passed in.
        """
        cert = X509()
        name = cert.get_subject()
        name.C = 'AU'
        name.O = 'Unit Tests'
        cert.set_subject(name)
        self.assertEquals(
            cert.get_subject().get_components(),
            [(b('C'), b('AU')), (b('O'), b('Unit Tests'))])


    def test_get_issuer_wrong_args(self):
        """
        L{X509.get_issuer} raises L{TypeError} if called with any arguments.
        """
        cert = X509()
        self.assertRaises(TypeError, cert.get_issuer, None)


    def test_get_issuer(self):
        """
        L{X509.get_issuer} returns an L{X509Name} instance.
        """
        cert = load_certificate(FILETYPE_PEM, self.pemData)
        subj = cert.get_issuer()
        self.assertTrue(isinstance(subj, X509Name))
        comp = subj.get_components()
        self.assertEquals(
            comp,
            [(b('C'), b('US')), (b('ST'), b('IL')), (b('L'), b('Chicago')),
             (b('O'), b('Testing')), (b('CN'), b('Testing Root CA'))])


    def test_set_issuer_wrong_args(self):
        """
        L{X509.set_issuer} raises a L{TypeError} if called with the wrong
        number of arguments or an argument not of type L{X509Name}.
        """
        cert = X509()
        self.assertRaises(TypeError, cert.set_issuer)
        self.assertRaises(TypeError, cert.set_issuer, None)
        self.assertRaises(TypeError, cert.set_issuer, cert.get_issuer(), None)


    def test_set_issuer(self):
        """
        L{X509.set_issuer} changes the issuer of the certificate to the one
        passed in.
        """
        cert = X509()
        name = cert.get_issuer()
        name.C = 'AU'
        name.O = 'Unit Tests'
        cert.set_issuer(name)
        self.assertEquals(
            cert.get_issuer().get_components(),
            [(b('C'), b('AU')), (b('O'), b('Unit Tests'))])


    def test_get_pubkey_uninitialized(self):
        """
        When called on a certificate with no public key, L{X509.get_pubkey}
        raises L{OpenSSL.crypto.Error}.
        """
        cert = X509()
        self.assertRaises(Error, cert.get_pubkey)


    def test_subject_name_hash_wrong_args(self):
        """
        L{X509.subject_name_hash} raises L{TypeError} if called with any
        arguments.
        """
        cert = X509()
        self.assertRaises(TypeError, cert.subject_name_hash, None)


    def test_subject_name_hash(self):
        """
        L{X509.subject_name_hash} returns the hash of the certificate's subject
        name.
        """
        cert = load_certificate(FILETYPE_PEM, self.pemData)
        self.assertIn(
            cert.subject_name_hash(),
            [3350047874, # OpenSSL 0.9.8, MD5
             3278919224, # OpenSSL 1.0.0, SHA1
             ])


    def test_get_signature_algorithm(self):
        """
        L{X509Type.get_signature_algorithm} returns a string which means
        the algorithm used to sign the certificate.
        """
        cert = load_certificate(FILETYPE_PEM, self.pemData)
        self.assertEqual(
            b("sha1WithRSAEncryption"), cert.get_signature_algorithm())


    def test_get_undefined_signature_algorithm(self):
        """
        L{X509Type.get_signature_algorithm} raises L{ValueError} if the
        signature algorithm is undefined or unknown.
        """
        # This certificate has been modified to indicate a bogus OID in the
        # signature algorithm field so that OpenSSL does not recognize it.
        certPEM = """\
-----BEGIN CERTIFICATE-----
MIIC/zCCAmigAwIBAgIBATAGBgJ8BQUAMHsxCzAJBgNVBAYTAlNHMREwDwYDVQQK
EwhNMkNyeXB0bzEUMBIGA1UECxMLTTJDcnlwdG8gQ0ExJDAiBgNVBAMTG00yQ3J5
cHRvIENlcnRpZmljYXRlIE1hc3RlcjEdMBsGCSqGSIb3DQEJARYObmdwc0Bwb3N0
MS5jb20wHhcNMDAwOTEwMDk1MTMwWhcNMDIwOTEwMDk1MTMwWjBTMQswCQYDVQQG
EwJTRzERMA8GA1UEChMITTJDcnlwdG8xEjAQBgNVBAMTCWxvY2FsaG9zdDEdMBsG
CSqGSIb3DQEJARYObmdwc0Bwb3N0MS5jb20wXDANBgkqhkiG9w0BAQEFAANLADBI
AkEArL57d26W9fNXvOhNlZzlPOACmvwOZ5AdNgLzJ1/MfsQQJ7hHVeHmTAjM664V
+fXvwUGJLziCeBo1ysWLRnl8CQIDAQABo4IBBDCCAQAwCQYDVR0TBAIwADAsBglg
hkgBhvhCAQ0EHxYdT3BlblNTTCBHZW5lcmF0ZWQgQ2VydGlmaWNhdGUwHQYDVR0O
BBYEFM+EgpK+eyZiwFU1aOPSbczbPSpVMIGlBgNVHSMEgZ0wgZqAFPuHI2nrnDqT
FeXFvylRT/7tKDgBoX+kfTB7MQswCQYDVQQGEwJTRzERMA8GA1UEChMITTJDcnlw
dG8xFDASBgNVBAsTC00yQ3J5cHRvIENBMSQwIgYDVQQDExtNMkNyeXB0byBDZXJ0
aWZpY2F0ZSBNYXN0ZXIxHTAbBgkqhkiG9w0BCQEWDm5ncHNAcG9zdDEuY29tggEA
MA0GCSqGSIb3DQEBBAUAA4GBADv8KpPo+gfJxN2ERK1Y1l17sz/ZhzoGgm5XCdbx
jEY7xKfpQngV599k1xhl11IMqizDwu0855agrckg2MCTmOI9DZzDD77tAYb+Dk0O
PEVk0Mk/V0aIsDE9bolfCi/i/QWZ3N8s5nTWMNyBBBmoSliWCm4jkkRZRD0ejgTN
tgI5
-----END CERTIFICATE-----
"""
        cert = load_certificate(FILETYPE_PEM, certPEM)
        self.assertRaises(ValueError, cert.get_signature_algorithm)



class PKCS12Tests(TestCase):
    """
    Test for L{OpenSSL.crypto.PKCS12} and L{OpenSSL.crypto.load_pkcs12}.
    """
    pemData = cleartextCertificatePEM + cleartextPrivateKeyPEM

    def test_type(self):
        """
        L{PKCS12Type} is a type object.
        """
        self.assertIdentical(PKCS12, PKCS12Type)
        self.assertConsistentType(PKCS12, 'PKCS12')


    def test_empty_construction(self):
        """
        L{PKCS12} returns a new instance of L{PKCS12} with no certificate,
        private key, CA certificates, or friendly name.
        """
        p12 = PKCS12()
        self.assertEqual(None, p12.get_certificate())
        self.assertEqual(None, p12.get_privatekey())
        self.assertEqual(None, p12.get_ca_certificates())
        self.assertEqual(None, p12.get_friendlyname())


    def test_type_errors(self):
        """
        The L{PKCS12} setter functions (C{set_certificate}, C{set_privatekey},
        C{set_ca_certificates}, and C{set_friendlyname}) raise L{TypeError}
        when passed objects of types other than those expected.
        """
        p12 = PKCS12()
        self.assertRaises(TypeError, p12.set_certificate, 3)
        self.assertRaises(TypeError, p12.set_certificate, PKey())
        self.assertRaises(TypeError, p12.set_certificate, X509)
        self.assertRaises(TypeError, p12.set_privatekey, 3)
        self.assertRaises(TypeError, p12.set_privatekey, 'legbone')
        self.assertRaises(TypeError, p12.set_privatekey, X509())
        self.assertRaises(TypeError, p12.set_ca_certificates, 3)
        self.assertRaises(TypeError, p12.set_ca_certificates, X509())
        self.assertRaises(TypeError, p12.set_ca_certificates, (3, 4))
        self.assertRaises(TypeError, p12.set_ca_certificates, ( PKey(), ))
        self.assertRaises(TypeError, p12.set_friendlyname, 6)
        self.assertRaises(TypeError, p12.set_friendlyname, ('foo', 'bar'))


    def test_key_only(self):
        """
        A L{PKCS12} with only a private key can be exported using
        L{PKCS12.export} and loaded again using L{load_pkcs12}.
        """
        passwd = 'blah'
        p12 = PKCS12()
        pkey = load_privatekey(FILETYPE_PEM, cleartextPrivateKeyPEM)
        p12.set_privatekey(pkey)
        self.assertEqual(None, p12.get_certificate())
        self.assertEqual(pkey, p12.get_privatekey())
        try:
            dumped_p12 = p12.export(passphrase=passwd, iter=2, maciter=3)
        except Error:
            # Some versions of OpenSSL will throw an exception
            # for this nearly useless PKCS12 we tried to generate:
            # [('PKCS12 routines', 'PKCS12_create', 'invalid null argument')]
            return
        p12 = load_pkcs12(dumped_p12, passwd)
        self.assertEqual(None, p12.get_ca_certificates())
        self.assertEqual(None, p12.get_certificate())

        # OpenSSL fails to bring the key back to us.  So sad.  Perhaps in the
        # future this will be improved.
        self.assertTrue(isinstance(p12.get_privatekey(), (PKey, type(None))))


    def test_cert_only(self):
        """
        A L{PKCS12} with only a certificate can be exported using
        L{PKCS12.export} and loaded again using L{load_pkcs12}.
        """
        passwd = 'blah'
        p12 = PKCS12()
        cert = load_certificate(FILETYPE_PEM, cleartextCertificatePEM)
        p12.set_certificate(cert)
        self.assertEqual(cert, p12.get_certificate())
        self.assertEqual(None, p12.get_privatekey())
        try:
            dumped_p12 = p12.export(passphrase=passwd, iter=2, maciter=3)
        except Error:
            # Some versions of OpenSSL will throw an exception
            # for this nearly useless PKCS12 we tried to generate:
            # [('PKCS12 routines', 'PKCS12_create', 'invalid null argument')]
            return
        p12 = load_pkcs12(dumped_p12, passwd)
        self.assertEqual(None, p12.get_privatekey())

        # OpenSSL fails to bring the cert back to us.  Groany mcgroan.
        self.assertTrue(isinstance(p12.get_certificate(), (X509, type(None))))

        # Oh ho.  It puts the certificate into the ca certificates list, in
        # fact.  Totally bogus, I would think.  Nevertheless, let's exploit
        # that to check to see if it reconstructed the certificate we expected
        # it to.  At some point, hopefully this will change so that
        # p12.get_certificate() is actually what returns the loaded
        # certificate.
        self.assertEqual(
            cleartextCertificatePEM,
            dump_certificate(FILETYPE_PEM, p12.get_ca_certificates()[0]))


    def gen_pkcs12(self, cert_pem=None, key_pem=None, ca_pem=None, friendly_name=None):
        """
        Generate a PKCS12 object with components from PEM.  Verify that the set
        functions return None.
        """
        p12 = PKCS12()
        if cert_pem:
            ret = p12.set_certificate(load_certificate(FILETYPE_PEM, cert_pem))
            self.assertEqual(ret, None)
        if key_pem:
            ret = p12.set_privatekey(load_privatekey(FILETYPE_PEM, key_pem))
            self.assertEqual(ret, None)
        if ca_pem:
            ret = p12.set_ca_certificates((load_certificate(FILETYPE_PEM, ca_pem),))
            self.assertEqual(ret, None)
        if friendly_name:
            ret = p12.set_friendlyname(friendly_name)
            self.assertEqual(ret, None)
        return p12


    def check_recovery(self, p12_str, key=None, cert=None, ca=None, passwd='',
                       extra=()):
        """
        Use openssl program to confirm three components are recoverable from a
        PKCS12 string.
        """
        if key:
            recovered_key = _runopenssl(
                p12_str, "pkcs12", '-nocerts', '-nodes', '-passin',
                'pass:' + passwd, *extra)
            self.assertEqual(recovered_key[-len(key):], key)
        if cert:
            recovered_cert = _runopenssl(
                p12_str, "pkcs12", '-clcerts', '-nodes', '-passin',
                'pass:' + passwd, '-nokeys', *extra)
            self.assertEqual(recovered_cert[-len(cert):], cert)
        if ca:
            recovered_cert = _runopenssl(
                p12_str, "pkcs12", '-cacerts', '-nodes', '-passin',
                'pass:' + passwd, '-nokeys', *extra)
            self.assertEqual(recovered_cert[-len(ca):], ca)


    def test_load_pkcs12(self):
        """
        A PKCS12 string generated using the openssl command line can be loaded
        with L{load_pkcs12} and its components extracted and examined.
        """
        passwd = 'whatever'
        pem = client_key_pem + client_cert_pem
        p12_str = _runopenssl(
            pem, "pkcs12", '-export', '-clcerts', '-passout', 'pass:' + passwd)
        p12 = load_pkcs12(p12_str, passwd)
        # verify
        self.assertTrue(isinstance(p12, PKCS12))
        cert_pem = dump_certificate(FILETYPE_PEM, p12.get_certificate())
        self.assertEqual(cert_pem, client_cert_pem)
        key_pem = dump_privatekey(FILETYPE_PEM, p12.get_privatekey())
        self.assertEqual(key_pem, client_key_pem)
        self.assertEqual(None, p12.get_ca_certificates())


    def test_load_pkcs12_garbage(self):
        """
        L{load_pkcs12} raises L{OpenSSL.crypto.Error} when passed a string
        which is not a PKCS12 dump.
        """
        passwd = 'whatever'
        e = self.assertRaises(Error, load_pkcs12, 'fruit loops', passwd)
        self.assertEqual( e.args[0][0][0], 'asn1 encoding routines')
        self.assertEqual( len(e.args[0][0]), 3)


    def test_replace(self):
        """
        L{PKCS12.set_certificate} replaces the certificate in a PKCS12 cluster.
        L{PKCS12.set_privatekey} replaces the private key.
        L{PKCS12.set_ca_certificates} replaces the CA certificates.
        """
        p12 = self.gen_pkcs12(client_cert_pem, client_key_pem, root_cert_pem)
        p12.set_certificate(load_certificate(FILETYPE_PEM, server_cert_pem))
        p12.set_privatekey(load_privatekey(FILETYPE_PEM, server_key_pem))
        root_cert = load_certificate(FILETYPE_PEM, root_cert_pem)
        client_cert = load_certificate(FILETYPE_PEM, client_cert_pem)
        p12.set_ca_certificates([root_cert]) # not a tuple
        self.assertEqual(1, len(p12.get_ca_certificates()))
        self.assertEqual(root_cert, p12.get_ca_certificates()[0])
        p12.set_ca_certificates([client_cert, root_cert])
        self.assertEqual(2, len(p12.get_ca_certificates()))
        self.assertEqual(client_cert, p12.get_ca_certificates()[0])
        self.assertEqual(root_cert, p12.get_ca_certificates()[1])


    def test_friendly_name(self):
        """
        The I{friendlyName} of a PKCS12 can be set and retrieved via
        L{PKCS12.get_friendlyname} and L{PKCS12_set_friendlyname}, and a
        L{PKCS12} with a friendly name set can be dumped with L{PKCS12.export}.
        """
        passwd = 'Dogmeat[]{}!@#$%^&*()~`?/.,<>-_+=";:'
        p12 = self.gen_pkcs12(server_cert_pem, server_key_pem, root_cert_pem)
        for friendly_name in [b('Serverlicious'), None, b('###')]:
            p12.set_friendlyname(friendly_name)
            self.assertEqual(p12.get_friendlyname(), friendly_name)
            dumped_p12 = p12.export(passphrase=passwd, iter=2, maciter=3)
            reloaded_p12 = load_pkcs12(dumped_p12, passwd)
            self.assertEqual(
                p12.get_friendlyname(), reloaded_p12.get_friendlyname())
            # We would use the openssl program to confirm the friendly
            # name, but it is not possible.  The pkcs12 command
            # does not store the friendly name in the cert's
            # alias, which we could then extract.
            self.check_recovery(
                dumped_p12, key=server_key_pem, cert=server_cert_pem,
                ca=root_cert_pem, passwd=passwd)


    def test_various_empty_passphrases(self):
        """
        Test that missing, None, and '' passphrases are identical for PKCS12
        export.
        """
        p12 = self.gen_pkcs12(client_cert_pem, client_key_pem, root_cert_pem)
        passwd = ''
        dumped_p12_empty = p12.export(iter=2, maciter=0, passphrase=passwd)
        dumped_p12_none = p12.export(iter=3, maciter=2, passphrase=None)
        dumped_p12_nopw = p12.export(iter=9, maciter=4)
        for dumped_p12 in [dumped_p12_empty, dumped_p12_none, dumped_p12_nopw]:
            self.check_recovery(
                dumped_p12, key=client_key_pem, cert=client_cert_pem,
                ca=root_cert_pem, passwd=passwd)


    def test_removing_ca_cert(self):
        """
        Passing C{None} to L{PKCS12.set_ca_certificates} removes all CA
        certificates.
        """
        p12 = self.gen_pkcs12(server_cert_pem, server_key_pem, root_cert_pem)
        p12.set_ca_certificates(None)
        self.assertEqual(None, p12.get_ca_certificates())


    def test_export_without_mac(self):
        """
        Exporting a PKCS12 with a C{maciter} of C{-1} excludes the MAC
        entirely.
        """
        passwd = 'Lake Michigan'
        p12 = self.gen_pkcs12(server_cert_pem, server_key_pem, root_cert_pem)
        dumped_p12 = p12.export(maciter=-1, passphrase=passwd, iter=2)
        self.check_recovery(
            dumped_p12, key=server_key_pem, cert=server_cert_pem,
            passwd=passwd, extra=('-nomacver',))


    def test_load_without_mac(self):
        """
        Loading a PKCS12 without a MAC does something other than crash.
        """
        passwd = 'Lake Michigan'
        p12 = self.gen_pkcs12(server_cert_pem, server_key_pem, root_cert_pem)
        dumped_p12 = p12.export(maciter=-1, passphrase=passwd, iter=2)
        try:
            recovered_p12 = load_pkcs12(dumped_p12, passwd)
            # The person who generated this PCKS12 should be flogged,
            # or better yet we should have a means to determine
            # whether a PCKS12 had a MAC that was verified.
            # Anyway, libopenssl chooses to allow it, so the
            # pyopenssl binding does as well.
            self.assertTrue(isinstance(recovered_p12, PKCS12))
        except Error:
            # Failing here with an exception is preferred as some openssl
            # versions do.
            pass


    def test_zero_len_list_for_ca(self):
        """
        A PKCS12 with an empty CA certificates list can be exported.
        """
        passwd = 'Hobie 18'
        p12 = self.gen_pkcs12(server_cert_pem, server_key_pem)
        p12.set_ca_certificates([])
        self.assertEqual((), p12.get_ca_certificates())
        dumped_p12 = p12.export(passphrase=passwd, iter=3)
        self.check_recovery(
            dumped_p12, key=server_key_pem, cert=server_cert_pem,
            passwd=passwd)


    def test_export_without_args(self):
        """
        All the arguments to L{PKCS12.export} are optional.
        """
        p12 = self.gen_pkcs12(server_cert_pem, server_key_pem, root_cert_pem)
        dumped_p12 = p12.export()  # no args
        self.check_recovery(
            dumped_p12, key=server_key_pem, cert=server_cert_pem, passwd='')


    def test_key_cert_mismatch(self):
        """
        L{PKCS12.export} raises an exception when a key and certificate
        mismatch.
        """
        p12 = self.gen_pkcs12(server_cert_pem, client_key_pem, root_cert_pem)
        self.assertRaises(Error, p12.export)



# These quoting functions taken directly from Twisted's twisted.python.win32.
_cmdLineQuoteRe = re.compile(r'(\\*)"')
_cmdLineQuoteRe2 = re.compile(r'(\\+)\Z')
def cmdLineQuote(s):
    """
    Internal method for quoting a single command-line argument.

    @type: C{str}
    @param s: A single unquoted string to quote for something that is expecting
        cmd.exe-style quoting

    @rtype: C{str}
    @return: A cmd.exe-style quoted string

    @see: U{http://www.perlmonks.org/?node_id=764004}
    """
    s = _cmdLineQuoteRe2.sub(r"\1\1", _cmdLineQuoteRe.sub(r'\1\1\\"', s))
    return '"%s"' % s



def quoteArguments(arguments):
    """
    Quote an iterable of command-line arguments for passing to CreateProcess or
    a similar API.  This allows the list passed to C{reactor.spawnProcess} to
    match the child process's C{sys.argv} properly.

    @type arguments: C{iterable} of C{str}
    @param arguments: An iterable of unquoted arguments to quote

    @rtype: C{str}
    @return: A space-delimited string containing quoted versions of L{arguments}
    """
    return ' '.join(map(cmdLineQuote, arguments))



def _runopenssl(pem, *args):
    """
    Run the command line openssl tool with the given arguments and write
    the given PEM to its stdin.  Not safe for quotes.
    """
    if os.name == 'posix':
        command = "openssl " + " ".join([
                "'%s'" % (arg.replace("'", "'\\''"),) for arg in args])
    else:
        command = "openssl " + quoteArguments(args)
    proc = Popen(command, shell=True, stdin=PIPE, stdout=PIPE)
    proc.stdin.write(pem)
    proc.stdin.close()
    return proc.stdout.read()



class FunctionTests(TestCase):
    """
    Tests for free-functions in the L{OpenSSL.crypto} module.
    """

    def test_load_privatekey_invalid_format(self):
        """
        L{load_privatekey} raises L{ValueError} if passed an unknown filetype.
        """
        self.assertRaises(ValueError, load_privatekey, 100, root_key_pem)


    def test_load_privatekey_invalid_passphrase_type(self):
        """
        L{load_privatekey} raises L{TypeError} if passed a passphrase that is
        neither a c{str} nor a callable.
        """
        self.assertRaises(
            TypeError,
            load_privatekey,
            FILETYPE_PEM, encryptedPrivateKeyPEMPassphrase, object())


    def test_load_privatekey_wrong_args(self):
        """
        L{load_privatekey} raises L{TypeError} if called with the wrong number
        of arguments.
        """
        self.assertRaises(TypeError, load_privatekey)


    def test_load_privatekey_wrongPassphrase(self):
        """
        L{load_privatekey} raises L{OpenSSL.crypto.Error} when it is passed an
        encrypted PEM and an incorrect passphrase.
        """
        self.assertRaises(
            Error,
            load_privatekey, FILETYPE_PEM, encryptedPrivateKeyPEM, b("quack"))


    def test_load_privatekey_passphrase(self):
        """
        L{load_privatekey} can create a L{PKey} object from an encrypted PEM
        string if given the passphrase.
        """
        key = load_privatekey(
            FILETYPE_PEM, encryptedPrivateKeyPEM,
            encryptedPrivateKeyPEMPassphrase)
        self.assertTrue(isinstance(key, PKeyType))


    def test_load_privatekey_wrongPassphraseCallback(self):
        """
        L{load_privatekey} raises L{OpenSSL.crypto.Error} when it is passed an
        encrypted PEM and a passphrase callback which returns an incorrect
        passphrase.
        """
        called = []
        def cb(*a):
            called.append(None)
            return "quack"
        self.assertRaises(
            Error,
            load_privatekey, FILETYPE_PEM, encryptedPrivateKeyPEM, cb)
        self.assertTrue(called)


    def test_load_privatekey_passphraseCallback(self):
        """
        L{load_privatekey} can create a L{PKey} object from an encrypted PEM
        string if given a passphrase callback which returns the correct
        password.
        """
        called = []
        def cb(writing):
            called.append(writing)
            return encryptedPrivateKeyPEMPassphrase
        key = load_privatekey(FILETYPE_PEM, encryptedPrivateKeyPEM, cb)
        self.assertTrue(isinstance(key, PKeyType))
        self.assertEqual(called, [False])


    def test_load_privatekey_passphrase_exception(self):
        """
        An exception raised by the passphrase callback passed to
        L{load_privatekey} causes L{OpenSSL.crypto.Error} to be raised.

        This isn't as nice as just letting the exception pass through.  The
        behavior might be changed to that eventually.
        """
        def broken(ignored):
            raise RuntimeError("This is not working.")
        self.assertRaises(
            Error,
            load_privatekey,
            FILETYPE_PEM, encryptedPrivateKeyPEM, broken)


    def test_dump_privatekey_wrong_args(self):
        """
        L{dump_privatekey} raises L{TypeError} if called with the wrong number
        of arguments.
        """
        self.assertRaises(TypeError, dump_privatekey)


    def test_dump_privatekey_unknown_cipher(self):
        """
        L{dump_privatekey} raises L{ValueError} if called with an unrecognized
        cipher name.
        """
        key = PKey()
        key.generate_key(TYPE_RSA, 512)
        self.assertRaises(
            ValueError, dump_privatekey,
            FILETYPE_PEM, key, "zippers", "passphrase")


    def test_dump_privatekey_invalid_passphrase_type(self):
        """
        L{dump_privatekey} raises L{TypeError} if called with a passphrase which
        is neither a C{str} nor a callable.
        """
        key = PKey()
        key.generate_key(TYPE_RSA, 512)
        self.assertRaises(
            TypeError,
            dump_privatekey, FILETYPE_PEM, key, "blowfish", object())


    def test_dump_privatekey_invalid_filetype(self):
        """
        L{dump_privatekey} raises L{ValueError} if called with an unrecognized
        filetype.
        """
        key = PKey()
        key.generate_key(TYPE_RSA, 512)
        self.assertRaises(ValueError, dump_privatekey, 100, key)


    def test_dump_privatekey_passphrase(self):
        """
        L{dump_privatekey} writes an encrypted PEM when given a passphrase.
        """
        passphrase = b("foo")
        key = load_privatekey(FILETYPE_PEM, cleartextPrivateKeyPEM)
        pem = dump_privatekey(FILETYPE_PEM, key, "blowfish", passphrase)
        self.assertTrue(isinstance(pem, bytes))
        loadedKey = load_privatekey(FILETYPE_PEM, pem, passphrase)
        self.assertTrue(isinstance(loadedKey, PKeyType))
        self.assertEqual(loadedKey.type(), key.type())
        self.assertEqual(loadedKey.bits(), key.bits())


    def test_dump_certificate(self):
        """
        L{dump_certificate} writes PEM, DER, and text.
        """
        pemData = cleartextCertificatePEM + cleartextPrivateKeyPEM
        cert = load_certificate(FILETYPE_PEM, pemData)
        dumped_pem = dump_certificate(FILETYPE_PEM, cert)
        self.assertEqual(dumped_pem, cleartextCertificatePEM)
        dumped_der = dump_certificate(FILETYPE_ASN1, cert)
        good_der = _runopenssl(dumped_pem, "x509", "-outform", "DER")
        self.assertEqual(dumped_der, good_der)
        cert2 = load_certificate(FILETYPE_ASN1, dumped_der)
        dumped_pem2 = dump_certificate(FILETYPE_PEM, cert2)
        self.assertEqual(dumped_pem2, cleartextCertificatePEM)
        dumped_text = dump_certificate(FILETYPE_TEXT, cert)
        good_text = _runopenssl(dumped_pem, "x509", "-noout", "-text")
        self.assertEqual(dumped_text, good_text)


    def test_dump_privatekey(self):
        """
        L{dump_privatekey} writes a PEM, DER, and text.
        """
        key = load_privatekey(FILETYPE_PEM, cleartextPrivateKeyPEM)
        self.assertTrue(key.check())
        dumped_pem = dump_privatekey(FILETYPE_PEM, key)
        self.assertEqual(dumped_pem, cleartextPrivateKeyPEM)
        dumped_der = dump_privatekey(FILETYPE_ASN1, key)
        # XXX This OpenSSL call writes "writing RSA key" to standard out.  Sad.
        good_der = _runopenssl(dumped_pem, "rsa", "-outform", "DER")
        self.assertEqual(dumped_der, good_der)
        key2 = load_privatekey(FILETYPE_ASN1, dumped_der)
        dumped_pem2 = dump_privatekey(FILETYPE_PEM, key2)
        self.assertEqual(dumped_pem2, cleartextPrivateKeyPEM)
        dumped_text = dump_privatekey(FILETYPE_TEXT, key)
        good_text = _runopenssl(dumped_pem, "rsa", "-noout", "-text")
        self.assertEqual(dumped_text, good_text)


    def test_dump_certificate_request(self):
        """
        L{dump_certificate_request} writes a PEM, DER, and text.
        """
        req = load_certificate_request(FILETYPE_PEM, cleartextCertificateRequestPEM)
        dumped_pem = dump_certificate_request(FILETYPE_PEM, req)
        self.assertEqual(dumped_pem, cleartextCertificateRequestPEM)
        dumped_der = dump_certificate_request(FILETYPE_ASN1, req)
        good_der = _runopenssl(dumped_pem, "req", "-outform", "DER")
        self.assertEqual(dumped_der, good_der)
        req2 = load_certificate_request(FILETYPE_ASN1, dumped_der)
        dumped_pem2 = dump_certificate_request(FILETYPE_PEM, req2)
        self.assertEqual(dumped_pem2, cleartextCertificateRequestPEM)
        dumped_text = dump_certificate_request(FILETYPE_TEXT, req)
        good_text = _runopenssl(dumped_pem, "req", "-noout", "-text")
        self.assertEqual(dumped_text, good_text)
        self.assertRaises(ValueError, dump_certificate_request, 100, req)


    def test_dump_privatekey_passphraseCallback(self):
        """
        L{dump_privatekey} writes an encrypted PEM when given a callback which
        returns the correct passphrase.
        """
        passphrase = b("foo")
        called = []
        def cb(writing):
            called.append(writing)
            return passphrase
        key = load_privatekey(FILETYPE_PEM, cleartextPrivateKeyPEM)
        pem = dump_privatekey(FILETYPE_PEM, key, "blowfish", cb)
        self.assertTrue(isinstance(pem, bytes))
        self.assertEqual(called, [True])
        loadedKey = load_privatekey(FILETYPE_PEM, pem, passphrase)
        self.assertTrue(isinstance(loadedKey, PKeyType))
        self.assertEqual(loadedKey.type(), key.type())
        self.assertEqual(loadedKey.bits(), key.bits())


    def test_load_pkcs7_data(self):
        """
        L{load_pkcs7_data} accepts a PKCS#7 string and returns an instance of
        L{PKCS7Type}.
        """
        pkcs7 = load_pkcs7_data(FILETYPE_PEM, pkcs7Data)
        self.assertTrue(isinstance(pkcs7, PKCS7Type))



class PKCS7Tests(TestCase):
    """
    Tests for L{PKCS7Type}.
    """
    def test_type(self):
        """
        L{PKCS7Type} is a type object.
        """
        self.assertTrue(isinstance(PKCS7Type, type))
        self.assertEqual(PKCS7Type.__name__, 'PKCS7')

        # XXX This doesn't currently work.
        # self.assertIdentical(PKCS7, PKCS7Type)


    # XXX Opposite results for all these following methods

    def test_type_is_signed_wrong_args(self):
        """
        L{PKCS7Type.type_is_signed} raises L{TypeError} if called with any
        arguments.
        """
        pkcs7 = load_pkcs7_data(FILETYPE_PEM, pkcs7Data)
        self.assertRaises(TypeError, pkcs7.type_is_signed, None)


    def test_type_is_signed(self):
        """
        L{PKCS7Type.type_is_signed} returns C{True} if the PKCS7 object is of
        the type I{signed}.
        """
        pkcs7 = load_pkcs7_data(FILETYPE_PEM, pkcs7Data)
        self.assertTrue(pkcs7.type_is_signed())


    def test_type_is_enveloped_wrong_args(self):
        """
        L{PKCS7Type.type_is_enveloped} raises L{TypeError} if called with any
        arguments.
        """
        pkcs7 = load_pkcs7_data(FILETYPE_PEM, pkcs7Data)
        self.assertRaises(TypeError, pkcs7.type_is_enveloped, None)


    def test_type_is_enveloped(self):
        """
        L{PKCS7Type.type_is_enveloped} returns C{False} if the PKCS7 object is
        not of the type I{enveloped}.
        """
        pkcs7 = load_pkcs7_data(FILETYPE_PEM, pkcs7Data)
        self.assertFalse(pkcs7.type_is_enveloped())


    def test_type_is_signedAndEnveloped_wrong_args(self):
        """
        L{PKCS7Type.type_is_signedAndEnveloped} raises L{TypeError} if called
        with any arguments.
        """
        pkcs7 = load_pkcs7_data(FILETYPE_PEM, pkcs7Data)
        self.assertRaises(TypeError, pkcs7.type_is_signedAndEnveloped, None)


    def test_type_is_signedAndEnveloped(self):
        """
        L{PKCS7Type.type_is_signedAndEnveloped} returns C{False} if the PKCS7
        object is not of the type I{signed and enveloped}.
        """
        pkcs7 = load_pkcs7_data(FILETYPE_PEM, pkcs7Data)
        self.assertFalse(pkcs7.type_is_signedAndEnveloped())


    def test_type_is_data(self):
        """
        L{PKCS7Type.type_is_data} returns C{False} if the PKCS7 object is not of
        the type data.
        """
        pkcs7 = load_pkcs7_data(FILETYPE_PEM, pkcs7Data)
        self.assertFalse(pkcs7.type_is_data())


    def test_type_is_data_wrong_args(self):
        """
        L{PKCS7Type.type_is_data} raises L{TypeError} if called with any
        arguments.
        """
        pkcs7 = load_pkcs7_data(FILETYPE_PEM, pkcs7Data)
        self.assertRaises(TypeError, pkcs7.type_is_data, None)


    def test_get_type_name_wrong_args(self):
        """
        L{PKCS7Type.get_type_name} raises L{TypeError} if called with any
        arguments.
        """
        pkcs7 = load_pkcs7_data(FILETYPE_PEM, pkcs7Data)
        self.assertRaises(TypeError, pkcs7.get_type_name, None)


    def test_get_type_name(self):
        """
        L{PKCS7Type.get_type_name} returns a C{str} giving the type name.
        """
        pkcs7 = load_pkcs7_data(FILETYPE_PEM, pkcs7Data)
        self.assertEquals(pkcs7.get_type_name(), b('pkcs7-signedData'))


    def test_attribute(self):
        """
        If an attribute other than one of the methods tested here is accessed on
        an instance of L{PKCS7Type}, L{AttributeError} is raised.
        """
        pkcs7 = load_pkcs7_data(FILETYPE_PEM, pkcs7Data)
        self.assertRaises(AttributeError, getattr, pkcs7, "foo")



class NetscapeSPKITests(TestCase, _PKeyInteractionTestsMixin):
    """
    Tests for L{OpenSSL.crypto.NetscapeSPKI}.
    """
    def signable(self):
        """
        Return a new L{NetscapeSPKI} for use with signing tests.
        """
        return NetscapeSPKI()


    def test_type(self):
        """
        L{NetscapeSPKI} and L{NetscapeSPKIType} refer to the same type object
        and can be used to create instances of that type.
        """
        self.assertIdentical(NetscapeSPKI, NetscapeSPKIType)
        self.assertConsistentType(NetscapeSPKI, 'NetscapeSPKI')


    def test_construction(self):
        """
        L{NetscapeSPKI} returns an instance of L{NetscapeSPKIType}.
        """
        nspki = NetscapeSPKI()
        self.assertTrue(isinstance(nspki, NetscapeSPKIType))


    def test_invalid_attribute(self):
        """
        Accessing a non-existent attribute of a L{NetscapeSPKI} instance causes
        an L{AttributeError} to be raised.
        """
        nspki = NetscapeSPKI()
        self.assertRaises(AttributeError, lambda: nspki.foo)


    def test_b64_encode(self):
        """
        L{NetscapeSPKI.b64_encode} encodes the certificate to a base64 blob.
        """
        nspki = NetscapeSPKI()
        blob = nspki.b64_encode()
        self.assertTrue(isinstance(blob, bytes))



class RevokedTests(TestCase):
    """
    Tests for L{OpenSSL.crypto.Revoked}
    """
    def test_construction(self):
        """
        Confirm we can create L{OpenSSL.crypto.Revoked}.  Check
        that it is empty.
        """
        revoked = Revoked()
        self.assertTrue(isinstance(revoked, Revoked))
        self.assertEquals(type(revoked), Revoked)
        self.assertEquals(revoked.get_serial(), b('00'))
        self.assertEquals(revoked.get_rev_date(), None)
        self.assertEquals(revoked.get_reason(), None)


    def test_construction_wrong_args(self):
        """
        Calling L{OpenSSL.crypto.Revoked} with any arguments results
        in a L{TypeError} being raised.
        """
        self.assertRaises(TypeError, Revoked, None)
        self.assertRaises(TypeError, Revoked, 1)
        self.assertRaises(TypeError, Revoked, "foo")


    def test_serial(self):
        """
        Confirm we can set and get serial numbers from
        L{OpenSSL.crypto.Revoked}.  Confirm errors are handled
        with grace.
        """
        revoked = Revoked()
        ret = revoked.set_serial(b('10b'))
        self.assertEquals(ret, None)
        ser = revoked.get_serial()
        self.assertEquals(ser, b('010B'))

        revoked.set_serial(b('31ppp'))  # a type error would be nice
        ser = revoked.get_serial()
        self.assertEquals(ser, b('31'))

        self.assertRaises(ValueError, revoked.set_serial, b('pqrst'))
        self.assertRaises(TypeError, revoked.set_serial, 100)
        self.assertRaises(TypeError, revoked.get_serial, 1)
        self.assertRaises(TypeError, revoked.get_serial, None)
        self.assertRaises(TypeError, revoked.get_serial, "")


    def test_date(self):
        """
        Confirm we can set and get revocation dates from
        L{OpenSSL.crypto.Revoked}.  Confirm errors are handled
        with grace.
        """
        revoked = Revoked()
        date = revoked.get_rev_date()
        self.assertEquals(date, None)

        now = b(datetime.now().strftime("%Y%m%d%H%M%SZ"))
        ret = revoked.set_rev_date(now)
        self.assertEqual(ret, None)
        date = revoked.get_rev_date()
        self.assertEqual(date, now)


    def test_reason(self):
        """
        Confirm we can set and get revocation reasons from
        L{OpenSSL.crypto.Revoked}.  The "get" need to work
        as "set".  Likewise, each reason of all_reasons() must work.
        """
        revoked = Revoked()
        for r in revoked.all_reasons():
            for x in range(2):
                ret = revoked.set_reason(r)
                self.assertEquals(ret, None)
                reason = revoked.get_reason()
                self.assertEquals(
                    reason.lower().replace(b(' '), b('')),
                    r.lower().replace(b(' '), b('')))
                r = reason # again with the resp of get

        revoked.set_reason(None)
        self.assertEqual(revoked.get_reason(), None)


    def test_set_reason_wrong_arguments(self):
        """
        Calling L{OpenSSL.crypto.Revoked.set_reason} with other than
        one argument, or an argument which isn't a valid reason,
        results in L{TypeError} or L{ValueError} being raised.
        """
        revoked = Revoked()
        self.assertRaises(TypeError, revoked.set_reason, 100)
        self.assertRaises(ValueError, revoked.set_reason, b('blue'))


    def test_get_reason_wrong_arguments(self):
        """
        Calling L{OpenSSL.crypto.Revoked.get_reason} with any
        arguments results in L{TypeError} being raised.
        """
        revoked = Revoked()
        self.assertRaises(TypeError, revoked.get_reason, None)
        self.assertRaises(TypeError, revoked.get_reason, 1)
        self.assertRaises(TypeError, revoked.get_reason, "foo")



class CRLTests(TestCase):
    """
    Tests for L{OpenSSL.crypto.CRL}
    """
    cert = load_certificate(FILETYPE_PEM, cleartextCertificatePEM)
    pkey = load_privatekey(FILETYPE_PEM, cleartextPrivateKeyPEM)

    def test_construction(self):
        """
        Confirm we can create L{OpenSSL.crypto.CRL}.  Check
        that it is empty
        """
        crl = CRL()
        self.assertTrue( isinstance(crl, CRL) )
        self.assertEqual(crl.get_revoked(), None)


    def test_construction_wrong_args(self):
        """
        Calling L{OpenSSL.crypto.CRL} with any number of arguments
        results in a L{TypeError} being raised.
        """
        self.assertRaises(TypeError, CRL, 1)
        self.assertRaises(TypeError, CRL, "")
        self.assertRaises(TypeError, CRL, None)


    def test_export(self):
        """
        Use python to create a simple CRL with a revocation, and export
        the CRL in formats of PEM, DER and text.  Those outputs are verified
        with the openssl program.
        """
        crl = CRL()
        revoked = Revoked()
        now = b(datetime.now().strftime("%Y%m%d%H%M%SZ"))
        revoked.set_rev_date(now)
        revoked.set_serial(b('3ab'))
        revoked.set_reason(b('sUpErSeDEd'))
        crl.add_revoked(revoked)

        # PEM format
        dumped_crl = crl.export(self.cert, self.pkey, days=20)
        text = _runopenssl(dumped_crl, "crl", "-noout", "-text")
        text.index(b('Serial Number: 03AB'))
        text.index(b('Superseded'))
        text.index(b('Issuer: /C=US/ST=IL/L=Chicago/O=Testing/CN=Testing Root CA'))

        # DER format
        dumped_crl = crl.export(self.cert, self.pkey, FILETYPE_ASN1)
        text = _runopenssl(dumped_crl, "crl", "-noout", "-text", "-inform", "DER")
        text.index(b('Serial Number: 03AB'))
        text.index(b('Superseded'))
        text.index(b('Issuer: /C=US/ST=IL/L=Chicago/O=Testing/CN=Testing Root CA'))

        # text format
        dumped_text = crl.export(self.cert, self.pkey, type=FILETYPE_TEXT)
        self.assertEqual(text, dumped_text)


    def test_add_revoked_keyword(self):
        """
        L{OpenSSL.CRL.add_revoked} accepts its single argument as the
        I{revoked} keyword argument.
        """
        crl = CRL()
        revoked = Revoked()
        crl.add_revoked(revoked=revoked)
        self.assertTrue(isinstance(crl.get_revoked()[0], Revoked))


    def test_export_wrong_args(self):
        """
        Calling L{OpenSSL.CRL.export} with fewer than two or more than
        four arguments, or with arguments other than the certificate,
        private key, integer file type, and integer number of days it
        expects, results in a L{TypeError} being raised.
        """
        crl = CRL()
        self.assertRaises(TypeError, crl.export)
        self.assertRaises(TypeError, crl.export, self.cert)
        self.assertRaises(TypeError, crl.export, self.cert, self.pkey, FILETYPE_PEM, 10, "foo")

        self.assertRaises(TypeError, crl.export, None, self.pkey, FILETYPE_PEM, 10)
        self.assertRaises(TypeError, crl.export, self.cert, None, FILETYPE_PEM, 10)
        self.assertRaises(TypeError, crl.export, self.cert, self.pkey, None, 10)
        self.assertRaises(TypeError, crl.export, self.cert, FILETYPE_PEM, None)


    def test_export_unknown_filetype(self):
        """
        Calling L{OpenSSL.CRL.export} with a file type other than
        L{FILETYPE_PEM}, L{FILETYPE_ASN1}, or L{FILETYPE_TEXT} results
        in a L{ValueError} being raised.
        """
        crl = CRL()
        self.assertRaises(ValueError, crl.export, self.cert, self.pkey, 100, 10)


    def test_get_revoked(self):
        """
        Use python to create a simple CRL with two revocations.
        Get back the L{Revoked} using L{OpenSSL.CRL.get_revoked} and
        verify them.
        """
        crl = CRL()

        revoked = Revoked()
        now = b(datetime.now().strftime("%Y%m%d%H%M%SZ"))
        revoked.set_rev_date(now)
        revoked.set_serial(b('3ab'))
        crl.add_revoked(revoked)
        revoked.set_serial(b('100'))
        revoked.set_reason(b('sUpErSeDEd'))
        crl.add_revoked(revoked)

        revs = crl.get_revoked()
        self.assertEqual(len(revs), 2)
        self.assertEqual(type(revs[0]), Revoked)
        self.assertEqual(type(revs[1]), Revoked)
        self.assertEqual(revs[0].get_serial(), b('03AB'))
        self.assertEqual(revs[1].get_serial(), b('0100'))
        self.assertEqual(revs[0].get_rev_date(), now)
        self.assertEqual(revs[1].get_rev_date(), now)


    def test_get_revoked_wrong_args(self):
        """
        Calling L{OpenSSL.CRL.get_revoked} with any arguments results
        in a L{TypeError} being raised.
        """
        crl = CRL()
        self.assertRaises(TypeError, crl.get_revoked, None)
        self.assertRaises(TypeError, crl.get_revoked, 1)
        self.assertRaises(TypeError, crl.get_revoked, "")
        self.assertRaises(TypeError, crl.get_revoked, "", 1, None)


    def test_add_revoked_wrong_args(self):
        """
        Calling L{OpenSSL.CRL.add_revoked} with other than one
        argument results in a L{TypeError} being raised.
        """
        crl = CRL()
        self.assertRaises(TypeError, crl.add_revoked)
        self.assertRaises(TypeError, crl.add_revoked, 1, 2)
        self.assertRaises(TypeError, crl.add_revoked, "foo", "bar")


    def test_load_crl(self):
        """
        Load a known CRL and inspect its revocations.  Both
        PEM and DER formats are loaded.
        """
        crl = load_crl(FILETYPE_PEM, crlData)
        revs = crl.get_revoked()
        self.assertEqual(len(revs), 2)
        self.assertEqual(revs[0].get_serial(), b('03AB'))
        self.assertEqual(revs[0].get_reason(), None)
        self.assertEqual(revs[1].get_serial(), b('0100'))
        self.assertEqual(revs[1].get_reason(), b('Superseded'))

        der = _runopenssl(crlData, "crl", "-outform", "DER")
        crl = load_crl(FILETYPE_ASN1, der)
        revs = crl.get_revoked()
        self.assertEqual(len(revs), 2)
        self.assertEqual(revs[0].get_serial(), b('03AB'))
        self.assertEqual(revs[0].get_reason(), None)
        self.assertEqual(revs[1].get_serial(), b('0100'))
        self.assertEqual(revs[1].get_reason(), b('Superseded'))


    def test_load_crl_wrong_args(self):
        """
        Calling L{OpenSSL.crypto.load_crl} with other than two
        arguments results in a L{TypeError} being raised.
        """
        self.assertRaises(TypeError, load_crl)
        self.assertRaises(TypeError, load_crl, FILETYPE_PEM)
        self.assertRaises(TypeError, load_crl, FILETYPE_PEM, crlData, None)


    def test_load_crl_bad_filetype(self):
        """
        Calling L{OpenSSL.crypto.load_crl} with an unknown file type
        raises a L{ValueError}.
        """
        self.assertRaises(ValueError, load_crl, 100, crlData)


    def test_load_crl_bad_data(self):
        """
        Calling L{OpenSSL.crypto.load_crl} with file data which can't
        be loaded raises a L{OpenSSL.crypto.Error}.
        """
        self.assertRaises(Error, load_crl, FILETYPE_PEM, "hello, world")


class SignVerifyTests(TestCase):
    """
    Tests for L{OpenSSL.crypto.sign} and L{OpenSSL.crypto.verify}.
    """
    def test_sign_verify(self):
        """
        L{sign} generates a cryptographic signature which L{verify} can check.
        """
        content = b(
            "It was a bright cold day in April, and the clocks were striking "
            "thirteen. Winston Smith, his chin nuzzled into his breast in an "
            "effort to escape the vile wind, slipped quickly through the "
            "glass doors of Victory Mansions, though not quickly enough to "
            "prevent a swirl of gritty dust from entering along with him.")

        # sign the content with this private key
        priv_key = load_privatekey(FILETYPE_PEM, root_key_pem)
        # verify the content with this cert
        good_cert = load_certificate(FILETYPE_PEM, root_cert_pem)
        # certificate unrelated to priv_key, used to trigger an error
        bad_cert = load_certificate(FILETYPE_PEM, server_cert_pem)

        for digest in ['md5', 'sha1']:
            sig = sign(priv_key, content, digest)

            # Verify the signature of content, will throw an exception if error.
            verify(good_cert, sig, content, digest)

            # This should fail because the certificate doesn't match the
            # private key that was used to sign the content.
            self.assertRaises(Error, verify, bad_cert, sig, content, digest)

            # This should fail because we've "tainted" the content after
            # signing it.
            self.assertRaises(
                Error, verify,
                good_cert, sig, content + b("tainted"), digest)

        # test that unknown digest types fail
        self.assertRaises(
            ValueError, sign, priv_key, content, "strange-digest")
        self.assertRaises(
            ValueError, verify, good_cert, sig, content, "strange-digest")


    def test_sign_nulls(self):
        """
        L{sign} produces a signature for a string with embedded nulls.
        """
        content = b("Watch out!  \0  Did you see it?")
        priv_key = load_privatekey(FILETYPE_PEM, root_key_pem)
        good_cert = load_certificate(FILETYPE_PEM, root_cert_pem)
        sig = sign(priv_key, content, "sha1")
        verify(good_cert, sig, content, "sha1")


if __name__ == '__main__':
    main()
