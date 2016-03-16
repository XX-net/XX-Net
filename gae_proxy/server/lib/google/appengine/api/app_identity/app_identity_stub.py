#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#




"""App identity stub service implementation.

This service behaves the same as the production service, except using
constant values instead of app-specific values:
* Signing key is constant; in production this rotates.
* Public key is constant; in production this varies per app.
* Service account name is constant; in production this varies per app.
"""









import binascii
import logging
import sys
import time

try:
  from Crypto.Hash import SHA256
  from Crypto.PublicKey import RSA
  from Crypto.Util import number
  CRYPTO_LIB_INSTALLED = True
except ImportError, e:
  CRYPTO_LIB_INSTALLED = False

try:
  import rsa
  RSA_LIB_INSTALLED = True
except ImportError, e:
  RSA_LIB_INSTALLED = False

from google.appengine.api import apiproxy_stub

APP_SERVICE_ACCOUNT_NAME = 'test@localhost'
APP_DEFAULT_GCS_BUCKET_NAME = 'app_default_bucket'

SIGNING_KEY_NAME = 'key'


N = 19119371788959611760073322421014045870056498252163411380847152703712917776733759011400972099255719579701566470175077491500050513917658074590935646529525468755348555932670175295728802986097707368373781743941167574738113348515272061138933984990014969297930973127363812200790406743271047572192133912023914306041356562363557723417403707408838823620411045628159183655215061768071407845537324145892973481372872161981015237572556138317222082306397041309823528068650373958169977675424007883635551170458356632131122901683151395297447872184074888239102348331222079943386530179883880518236689216575776729057173406091195993394637
MODULUS_BYTES = 256

E = 65537L

D = 16986504444572720056487621821047100642841595850137583213470349776864799280835251113078612103869013355016302383270733509621770011190160658118800356360958694229960556902751935956316359959542321272425222634888969943798180994410031448370776358545990991384123912313866752051562052322103544805811361355593091450379904792608637886965065110019212136239200637553477192566763015004249754677600683846556806159369233241157779976231822757855748068765507787598014034587835400718727569389998321277712761796543890788269130617890866139616903097422259980026836628018133574943835504630997228592718738382001678104796538128020421537193913
X509_PUBLIC_CERT = """
-----BEGIN CERTIFICATE-----
MIIC/jCCAeagAwIBAgIIQTBFcRw3moMwDQYJKoZIhvcNAQEFBQAwIjEgMB4GA1UE
AxMXcm9ib3RqYXZhLmEuYXBwc3BvdC5jb20wHhcNMTEwMjIzMTUwNzQ5WhcNMTEw
MjI0MTYwNzQ5WjAiMSAwHgYDVQQDExdyb2JvdGphdmEuYS5hcHBzcG90LmNvbTCC
ASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAJd0YJCQWvQMa+7L/orCt3D0
hVtkdAkeGSikuT4U7mNrxBuOaAbxCIGhRbUe2p+uvRF6MZtLvoU1h9qEFo/wAVDO
HN4WHhw3VLl/OVuredRfe8bBTi0KqdgUBrKr8V61n26N3B4Ma9dkTMbcODC/XCfP
IRJnTIf4Z1vnoEfWQEJDfW9QLJFyJF17hpp9l5S1uuMJBxjYMsZ3ExLqSFhM7IbN
1PDBAb6zGtI7b9AVP+gxS1hjXiJoZA32IWINAZiPV+0k925ecsV0BkI0zV4Ta06F
JexNx040y5ivr4C214GRUM3UKihirTcEOBS1a7SRi5wCPh/wT0A8gN6NNbTNjc0C
AwEAAaM4MDYwDAYDVR0TAQH/BAIwADAOBgNVHQ8BAf8EBAMCB4AwFgYDVR0lAQH/
BAwwCgYIKwYBBQUHAwIwDQYJKoZIhvcNAQEFBQADggEBAD+h2D+XGIHWMwPCA2DN
JgMhN1yTTJ8dtwbiQIhfy8xjOJbrzZaSEX8g2gDm50qaEl5TYHHr2zvAI1UMWdR4
nx9TN7I9u3GoOcQsmn9TaOKkBDpMv8sPtFBal3AR5PwR5Sq8/4L/M22LX/TN0eIF
Y4LnkW+X/h442N8a1oXn05UYtFo+p/6emZb1S84WZAnONGtF5D1Z6HuX4ikDI5m+
iZbwm47mLkV8yuTZGKI1gJsWmAsElPkoWVy2X0t69ecBOYyn3wMmQhkLk2+7lLlD
/c4kygP/941fe1Wb/T9yGeBXFwEvJ4jWbX93Q4Xhk9UgHlso9xkCu9QeWFvJqufR
5Cc=
-----END CERTIFICATE-----
"""


PREFIX = '3031300d060960864801650304020105000420'
LEN_OF_PREFIX = 19
HEADER1 = '0001'
HEADER2 = '00'
PADDING = 'ff'


LENGTH_OF_SHA256_HASH = 32


class AppIdentityServiceStub(apiproxy_stub.APIProxyStub):
  """A stub for the AppIdentityService API for offline development.

  Provides stub functions which allow a developer to test integration before
  deployment.
  """
  THREADSAFE = True

  def __init__(self, service_name='app_identity_service'):
    """Constructor."""
    super(AppIdentityServiceStub, self).__init__(service_name)
    self.__default_gcs_bucket_name = APP_DEFAULT_GCS_BUCKET_NAME

  def _Dynamic_SignForApp(self, request, response):
    """Implementation of AppIdentityService::SignForApp."""
    bytes_to_sign = request.bytes_to_sign()
    if RSA_LIB_INSTALLED:




      signature_bytes = rsa.pkcs1.sign(
          bytes_to_sign,
          rsa.key.PrivateKey(N, E, D, 3, 5),
          'SHA-256')
    elif CRYPTO_LIB_INSTALLED:


      rsa_obj = RSA.construct((N, E, D))
      hash_obj = SHA256.new()
      hash_obj.update(bytes_to_sign)
      padding_length = MODULUS_BYTES - LEN_OF_PREFIX - LENGTH_OF_SHA256_HASH - 3
      emsa = (HEADER1 + (PADDING * padding_length) + HEADER2 +
              PREFIX + hash_obj.hexdigest())
      sig = rsa_obj.sign(binascii.a2b_hex(emsa), '')
      signature_bytes = number.long_to_bytes(sig[0])
    else:
      raise NotImplementedError("""Unable to import the pycrypto module,
                                SignForApp is disabled.""")
    response.set_signature_bytes(signature_bytes)
    response.set_key_name(SIGNING_KEY_NAME)

  def _Dynamic_GetPublicCertificatesForApp(self, request, response):
    """Implementation of AppIdentityService::GetPublicCertificatesForApp"""
    cert = response.add_public_certificate_list()
    cert.set_key_name(SIGNING_KEY_NAME)
    cert.set_x509_certificate_pem(X509_PUBLIC_CERT)

  def _Dynamic_GetServiceAccountName(self, request, response):
    """Implementation of AppIdentityService::GetServiceAccountName"""
    response.set_service_account_name(APP_SERVICE_ACCOUNT_NAME)

  def _Dynamic_GetDefaultGcsBucketName(self, unused_request, response):
    """Implementation of AppIdentityService::GetDefaultGcsBucketName."""
    response.set_default_gcs_bucket_name(self.__default_gcs_bucket_name)

  def SetDefaultGcsBucketName(self, default_gcs_bucket_name):
    if default_gcs_bucket_name:
      self.__default_gcs_bucket_name = default_gcs_bucket_name
    else:
      self.__default_gcs_bucket_name = APP_DEFAULT_GCS_BUCKET_NAME

  def _Dynamic_GetAccessToken(self, request, response):
    """Implementation of AppIdentityService::GetAccessToken.

    This API returns an invalid token, as the dev_appserver does not have
    access to an actual service account.
    """
    token = ':'.join(request.scope_list())
    service_account_id = request.service_account_id()
    if service_account_id:
      token += '.%d' % service_account_id
    if request.service_account_name():
      token += '.%s' % request.service_account_name()
    response.set_access_token('InvalidToken:%s:%s' % (token, time.time() % 100))

    response.set_expiration_time(int(time.time()) + 1800)

  @staticmethod
  def Create(email_address=None, private_key_path=None, oauth_url=None):
    if email_address:
      from google.appengine.api.app_identity import app_identity_keybased_stub

      logging.debug('Using the KeyBasedAppIdentityServiceStub.')
      return app_identity_keybased_stub.KeyBasedAppIdentityServiceStub(
          email_address=email_address,
          private_key_path=private_key_path,
          oauth_url=oauth_url)
    elif sys.version_info >= (2, 6):





      import six
      if six._importer not in sys.meta_path:
        sys.meta_path.append(six._importer)
      from oauth2client import client
      from google.appengine.api.app_identity import app_identity_defaultcredentialsbased_stub as ai_stub
      try:
        dc = ai_stub.DefaultCredentialsBasedAppIdentityServiceStub()
        logging.debug('Successfully loaded Application Default Credentials.')
        return dc
      except client.ApplicationDefaultCredentialsError, error:
        if not str(error).startswith('The Application Default Credentials '
                                     'are not available.'):
          logging.warning('An exception has been encountered when attempting '
                          'to use Application Default Credentials: %s'
                          '. Falling back on dummy AppIdentityServiceStub.',
                          str(error))
        return AppIdentityServiceStub()
    else:
      logging.debug('Running under Python 2.5 uses dummy '
                    'AppIdentityServiceStub.')
      return AppIdentityServiceStub()
