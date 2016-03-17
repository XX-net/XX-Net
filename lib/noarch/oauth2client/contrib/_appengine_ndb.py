# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Google App Engine utilities helper.

Classes that directly require App Engine's ndb library. Provided
as a separate module in case of failure to import ndb while
other App Engine libraries are present.
"""

import logging

from google.appengine.ext import ndb

from oauth2client import client


NDB_KEY = ndb.Key
"""Key constant used by :mod:`oauth2client.contrib.appengine`."""

NDB_MODEL = ndb.Model
"""Model constant used by :mod:`oauth2client.contrib.appengine`."""

_LOGGER = logging.getLogger(__name__)


class SiteXsrfSecretKeyNDB(ndb.Model):
    """NDB Model for storage for the sites XSRF secret key.

    Since this model uses the same kind as SiteXsrfSecretKey, it can be
    used interchangeably. This simply provides an NDB model for interacting
    with the same data the DB model interacts with.

    There should only be one instance stored of this model, the one used
    for the site.
    """
    secret = ndb.StringProperty()

    @classmethod
    def _get_kind(cls):
        """Return the kind name for this class."""
        return 'SiteXsrfSecretKey'


class FlowNDBProperty(ndb.PickleProperty):
    """App Engine NDB datastore Property for Flow.

    Serves the same purpose as the DB FlowProperty, but for NDB models.
    Since PickleProperty inherits from BlobProperty, the underlying
    representation of the data in the datastore will be the same as in the
    DB case.

    Utility property that allows easy storage and retrieval of an
    oauth2client.Flow
    """

    def _validate(self, value):
        """Validates a value as a proper Flow object.

        Args:
            value: A value to be set on the property.

        Raises:
            TypeError if the value is not an instance of Flow.
        """
        _LOGGER.info('validate: Got type %s', type(value))
        if value is not None and not isinstance(value, client.Flow):
            raise TypeError('Property %s must be convertible to a flow '
                            'instance; received: %s.' % (self._name,
                                                         value))


class CredentialsNDBProperty(ndb.BlobProperty):
    """App Engine NDB datastore Property for Credentials.

    Serves the same purpose as the DB CredentialsProperty, but for NDB
    models. Since CredentialsProperty stores data as a blob and this
    inherits from BlobProperty, the data in the datastore will be the same
    as in the DB case.

    Utility property that allows easy storage and retrieval of Credentials
    and subclasses.
    """

    def _validate(self, value):
        """Validates a value as a proper credentials object.

        Args:
            value: A value to be set on the property.

        Raises:
            TypeError if the value is not an instance of Credentials.
        """
        _LOGGER.info('validate: Got type %s', type(value))
        if value is not None and not isinstance(value, client.Credentials):
            raise TypeError('Property %s must be convertible to a '
                            'credentials instance; received: %s.' %
                            (self._name, value))

    def _to_base_type(self, value):
        """Converts our validated value to a JSON serialized string.

        Args:
            value: A value to be set in the datastore.

        Returns:
            A JSON serialized version of the credential, else '' if value
            is None.
        """
        if value is None:
            return ''
        else:
            return value.to_json()

    def _from_base_type(self, value):
        """Converts our stored JSON string back to the desired type.

        Args:
            value: A value from the datastore to be converted to the
                   desired type.

        Returns:
            A deserialized Credentials (or subclass) object, else None if
            the value can't be parsed.
        """
        if not value:
            return None
        try:
            # Uses the from_json method of the implied class of value
            credentials = client.Credentials.new_from_json(value)
        except ValueError:
            credentials = None
        return credentials


class CredentialsNDBModel(ndb.Model):
    """NDB Model for storage of OAuth 2.0 Credentials

    Since this model uses the same kind as CredentialsModel and has a
    property which can serialize and deserialize Credentials correctly, it
    can be used interchangeably with a CredentialsModel to access, insert
    and delete the same entities. This simply provides an NDB model for
    interacting with the same data the DB model interacts with.

    Storage of the model is keyed by the user.user_id().
    """
    credentials = CredentialsNDBProperty()

    @classmethod
    def _get_kind(cls):
        """Return the kind name for this class."""
        return 'CredentialsModel'
