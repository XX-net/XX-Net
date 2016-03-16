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
application default credentials.
"""

from __future__ import with_statement







import json
import threading
import time
import urllib

from oauth2client import client
from oauth2client import service_account
from pyasn1.codec.der import decoder
from pyasn1_modules.rfc2459 import Certificate
import rsa

from google.appengine.api import urlfetch
from google.appengine.api.app_identity import app_identity_service_pb
from google.appengine.api.app_identity import app_identity_stub
from google.appengine.runtime import apiproxy_errors


def BitStringToByteString(bs):
  """Convert a pyasn1.type.univ.BitString object to a string of bytes."""
  def BitsToInt(bits):
    return sum(v * (2 ** (7 - j)) for j, v in enumerate(bits))
  return str(bytearray([BitsToInt(bs[i:i + 8]) for i in range(0, len(bs), 8)]))


class DefaultCredentialsBasedAppIdentityServiceStub(
    app_identity_stub.AppIdentityServiceStub):
  """A stub for the AppIdentityService API for offline development.

  Provides stub functions which allow a developer to test integration before
  deployment.
  """

  THREADSAFE = True

  def __init__(self, service_name='app_identity_service'):
    super(DefaultCredentialsBasedAppIdentityServiceStub,
          self).__init__(service_name)

    client.NO_GCE_CHECK = 'True'
    self._credentials = (
        client.GoogleCredentials.get_application_default())
    self._access_token_cache_lock = threading.Lock()
    self._access_token_cache = {}
    self._x509_init_lock = threading.Lock()
    self._default_gcs_bucket_name = (
        app_identity_stub.APP_DEFAULT_GCS_BUCKET_NAME)
    self._x509 = None
    self._signing_key = None
    self._non_service_account_credentials = not isinstance(
        self._credentials, service_account._ServiceAccountCredentials)

  def _PopulateX509(self):
    with self._x509_init_lock:
      if self._x509 is None:

        url = ('https://www.googleapis.com/service_accounts/v1/metadata/x509/%s'
               % urllib.unquote_plus(self._credentials.service_account_email))
        response = urlfetch.fetch(
            url=url,
            validate_certificate=True,
            method=urlfetch.GET)
        if response.status_code != 200:
          raise apiproxy_errors.ApplicationError(
              app_identity_service_pb.AppIdentityServiceError.UNKNOWN_ERROR,
              'Unable to load X509 cert: %s Response code: %i, Content: %s' % (
                  url, response.status_code, response.content))

        message = 'dummy'
        _, signature = self._credentials.sign_blob(message)

        for signing_key, x509 in json.loads(response.content).items():
          der = rsa.pem.load_pem(x509, 'CERTIFICATE')
          asn1_cert, _ = decoder.decode(der, asn1Spec=Certificate())

          key_bitstring = (
              asn1_cert['tbsCertificate']
              ['subjectPublicKeyInfo']
              ['subjectPublicKey'])
          key_bytearray = BitStringToByteString(key_bitstring)

          public_key = rsa.PublicKey.load_pkcs1(key_bytearray, 'DER')
          try:
            if rsa.pkcs1.verify(message, signature, public_key):
              self._x509 = x509
              self._signing_key = signing_key
              return
          except rsa.pkcs1.VerificationError:
            pass

        raise apiproxy_errors.ApplicationError(
            app_identity_service_pb.AppIdentityServiceError.UNKNOWN_ERROR,
            'Unable to find matching X509 cert for private key: %s' % url)

  def _Dynamic_SignForApp(self, request, response):
    """Implementation of AppIdentityService::SignForApp."""
    if self._non_service_account_credentials:




      return super(DefaultCredentialsBasedAppIdentityServiceStub,
                   self)._Dynamic_SignForApp(request, response)
    self._PopulateX509()
    private_key_id, signature = self._credentials.sign_blob(
        request.bytes_to_sign())
    assert private_key_id == self._signing_key
    response.set_signature_bytes(signature)
    response.set_key_name(self._signing_key)

  def _Dynamic_GetPublicCertificatesForApp(self, request, response):
    """Implementation of AppIdentityService::GetPublicCertificatesForApp."""
    if self._non_service_account_credentials:




      return super(DefaultCredentialsBasedAppIdentityServiceStub,
                   self)._Dynamic_GetPublicCertificatesForApp(request, response)
    self._PopulateX509()
    certificate = response.add_public_certificate_list()
    certificate.set_key_name(self._signing_key)
    certificate.set_x509_certificate_pem(self._x509)

  def _Dynamic_GetServiceAccountName(self, request, response):
    """Implementation of AppIdentityService::GetServiceAccountName."""
    if self._non_service_account_credentials:


      response.set_service_account_name('')
    else:
      response.set_service_account_name(self._credentials.service_account_email)

  def _Dynamic_GetDefaultGcsBucketName(self, unused_request, response):
    """Implementation of AppIdentityService::GetDefaultGcsBucketName."""
    response.set_default_gcs_bucket_name(self._default_gcs_bucket_name)

  def SetDefaultGcsBucketName(self, default_gcs_bucket_name):
    if default_gcs_bucket_name:
      self._default_gcs_bucket_name = default_gcs_bucket_name
    else:
      self._default_gcs_bucket_name = (
          app_identity_stub.APP_DEFAULT_GCS_BUCKET_NAME)

  def _Dynamic_GetAccessToken(self, request, response):
    """Implementation of AppIdentityService::GetAccessToken.

    This API requires internet access.

    Raises:
      apiproxy_errors.ApplicationError: If unexpected response from
                                        Google server.
    """
    scope = ' '.join(request.scope_list())
    with self._access_token_cache_lock:
      rv = self._access_token_cache.get(scope, None)
    now = int(time.time())

    if not (rv and rv['expires'] > (now + 60)):
      credentials = self._credentials
      if credentials.create_scoped_required():
        credentials = credentials.create_scoped(request.scope_list())
      token = credentials.get_access_token()
      rv = {
          'access_token': token.access_token,
          'expires': now + token.expires_in,
      }
      with self._access_token_cache_lock:
        self._access_token_cache[scope] = rv

    response.set_access_token(rv['access_token'])
    response.set_expiration_time(rv['expires'])
