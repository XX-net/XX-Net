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



"""Implementation of the Cloud Datastore V1 API.

This implementation forwards directly to the v3 service."""













import collections

from google.appengine.datastore import entity_pb

from google.appengine.api import api_base_pb
from google.appengine.api import apiproxy_rpc
from google.appengine.api import apiproxy_stub
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore_types
from google.appengine.datastore import datastore_pb
from google.appengine.datastore import datastore_pbs
from google.appengine.datastore import datastore_query
from google.appengine.datastore import datastore_stub_util
from google.appengine.datastore import cloud_datastore_validator
from google.appengine.runtime import apiproxy_errors

_CLOUD_DATASTORE_ENABLED = datastore_pbs._CLOUD_DATASTORE_ENABLED
if _CLOUD_DATASTORE_ENABLED:
  from datastore_pbs import googledatastore

SERVICE_NAME = 'cloud_datastore_v1beta3'
V3_SERVICE_NAME = 'datastore_v3'


_NO_VERSION = 0

_MINIMUM_VERSION = 1


class _StubIdResolver(datastore_pbs.IdResolver):
  """A IdResolver that converts all project_ids to dev~project_id.

  Users can provide a list of app_ids to override the conversions.
  """

  def __init__(self, app_ids=None):
    """Create a _StubIdResolver.

    Optionally, can provide a list of application ids.
    """
    super(_StubIdResolver, self).__init__(app_ids)

  def resolve_app_id(self, project_id):
    """Resolve the project id. Defaults to dev~project_id."""
    try:
      return super(_StubIdResolver, self).resolve_app_id(project_id)
    except datastore_pbs.InvalidConversionError:
      return 'dev~%s' % project_id


class CloudDatastoreV1Stub(apiproxy_stub.APIProxyStub):
  """Implementation of the Cloud Datastore V1 API.

  This proxies requests to the v3 service."""


  THREADSAFE = False

  def __init__(self, app_id):
    assert _CLOUD_DATASTORE_ENABLED, (
        'Cannot initialize the Cloud Datastore'
        ' stub without installing the Cloud'
        ' Datastore client libraries.')
    apiproxy_stub.APIProxyStub.__init__(self, SERVICE_NAME)
    self.__app_id = app_id
    self._id_resolver = _StubIdResolver([app_id])
    self.__entity_converter = datastore_pbs.get_entity_converter(
        self._id_resolver)
    self.__service_converter = datastore_stub_util.get_service_converter(
        self._id_resolver)
    self.__service_validator = cloud_datastore_validator.get_service_validator(
        self._id_resolver)

  def _Dynamic_BeginTransaction(self, req, resp):


    try:
      self.__service_validator.validate_begin_transaction_req(req)
      v3_req = self.__service_converter.v1_to_v3_begin_transaction_req(
          self.__app_id, req)
    except datastore_pbs.InvalidConversionError, e:
      raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                             str(e))
    except cloud_datastore_validator.ValidationError, e:
      raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                             str(e))
    v3_resp = datastore_pb.Transaction()
    self.__make_v3_call('BeginTransaction', v3_req, v3_resp)

    try:
      v1_resp = self.__service_converter.v3_to_v1_begin_transaction_resp(
          v3_resp)
    except datastore_pbs.InvalidConversionError, e:
      raise apiproxy_errors.ApplicationError(datastore_pb.Error.INTERNAL_ERROR,
                                             str(e))
    resp.CopyFrom(v1_resp)

  def _Dynamic_Rollback(self, req, unused_resp):


    try:
      self.__service_validator.validate_rollback_req(req)
      v3_req = self.__service_converter.v1_rollback_req_to_v3_txn(req)
    except datastore_pbs.InvalidConversionError, e:
      raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                             str(e))
    except cloud_datastore_validator.ValidationError, e:
      raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                             str(e))

    self.__make_v3_call('Rollback', v3_req, api_base_pb.VoidProto())

  def _Dynamic_Commit(self, req, resp):


    try:
      self.__service_validator.validate_commit_req(req)
    except cloud_datastore_validator.ValidationError, e:
      raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                             str(e))
    single_use_txn = None
    if req.WhichOneof('transaction_selector') == 'single_use_transaction':
      single_use_txn = self.__begin_adhoc_txn(req)

    try:
      try:
        if req.transaction or single_use_txn:
          self.__commit(req.mutations, req.transaction or single_use_txn, resp)
        else:
          v3_txn_req = datastore_pb.BeginTransactionRequest()
          v3_txn_req.set_app(self.__app_id)

          for mutation in req.mutations:
            v3_txn = datastore_pb.Transaction()
            self.__make_v3_call('BeginTransaction', v3_txn_req, v3_txn)
            v1_txn = self.__service_converter._v3_to_v1_txn(v3_txn)

            commit_resp = googledatastore.CommitResponse()
            self.__commit([mutation], v1_txn, commit_resp)

            resp.index_updates += commit_resp.index_updates
            mutation_result = commit_resp.mutation_results[0]
            resp.mutation_results.add().CopyFrom(mutation_result)
      except datastore_pbs.InvalidConversionError, e:


        raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                               str(e))
    except:
      if single_use_txn:
        self.__rollback_adhoc_txn(req, single_use_txn)
      raise

  def _Dynamic_RunQuery(self, req, resp):


    self.__normalize_v1_run_query_request(req)
    snapshot_version = None

    txn = None

    txn_to_cleanup = None

    new_txn = None
    try:
      try:
        self.__service_validator.validate_run_query_req(req)
        if req.read_options.WhichOneof('consistency_type') == 'new_transaction':
          new_txn = self.__begin_adhoc_txn(req)
        v3_req = self.__service_converter.v1_run_query_req_to_v3_query(
            req, new_txn=new_txn)



        if new_txn:
          txn = new_txn
          txn_to_cleanup = new_txn
        elif req.read_options.transaction:
          txn = req.read_options.transaction
        elif (v3_req.has_ancestor() and
              req.read_options.read_consistency
              != googledatastore.ReadOptions.EVENTUAL and
              v3_req.kind != '__property__'):
          txn = self.__begin_adhoc_txn(req)
          txn_to_cleanup = txn
          v3_req.transaction = txn

      except datastore_pbs.InvalidConversionError, e:
        raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                               str(e))
      except cloud_datastore_validator.ValidationError, e:
        raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                               str(e))

      v3_resp = datastore_pb.QueryResult()
      self.__make_v3_call('RunQuery', v3_req, v3_resp)



      if txn:
        lookup = googledatastore.LookupRequest()
        lookup.project_id = req.partition_id.project_id
        lookup.database_id = req.partition_id.database_id
        lookup.read_options.transaction = txn
        key = lookup.keys.add()
        key.partition_id.CopyFrom(req.partition_id)
        key.partition_id.database_id = req.database_id
        path = key.path.add()
        path.kind = '__none__'
        path.id = 1
        lookup_response = googledatastore.LookupResponse()
        self._Dynamic_Lookup(lookup, lookup_response)
        snapshot_version = lookup_response.missing[0].version

      try:
        v1_resp = self.__service_converter.v3_to_v1_run_query_resp(
            v3_resp, new_txn=new_txn)
        if req.query.projection:
          if (len(req.query.projection) == 1 and
              req.query.projection[0].property.name == '__key__'):
            result_type = googledatastore.EntityResult.KEY_ONLY
          else:
            result_type = googledatastore.EntityResult.PROJECTION
          v1_resp.batch.entity_result_type = result_type
        if snapshot_version:
          v1_resp.batch.snapshot_version = snapshot_version
      except datastore_pbs.InvalidConversionError, e:
        raise apiproxy_errors.ApplicationError(
            datastore_pb.Error.INTERNAL_ERROR, str(e))
    except:
      if txn_to_cleanup:
        self.__rollback_adhoc_txn(req, txn_to_cleanup)
      raise
    resp.CopyFrom(v1_resp)

  def _Dynamic_Lookup(self, req, resp):


    new_txn = None
    try:
      try:
        self.__service_validator.validate_lookup_req(req)
        if req.read_options.WhichOneof('consistency_type') == 'new_transaction':
          new_txn = self.__begin_adhoc_txn(req)
        v3_req = self.__service_converter.v1_to_v3_get_req(req, new_txn=new_txn)
      except (cloud_datastore_validator.ValidationError,
              datastore_pbs.InvalidConversionError), e:
        raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                               str(e))

      v3_resp = datastore_pb.GetResponse()
      self.__make_v3_call('Get', v3_req, v3_resp)

      try:
        v1_resp = self.__service_converter.v3_to_v1_lookup_resp(v3_resp,
                                                                new_txn=new_txn)
      except datastore_pbs.InvalidConversionError, e:
        raise apiproxy_errors.ApplicationError(datastore_pb.Error.INTERNAL_ERROR,
                                               str(e))
    except:
      if new_txn:
        self.__rollback_adhoc_txn(req, new_txn)
      raise
    resp.CopyFrom(v1_resp)

  def _Dynamic_AllocateIds(self, req, resp):






    v3_stub = apiproxy_stub_map.apiproxy.GetStub(V3_SERVICE_NAME)
    v3_refs = None
    try:
      self.__service_validator.validate_allocate_ids_req(req)
      if req.keys:
        v3_refs = self.__entity_converter.v1_to_v3_references(req.keys)
    except cloud_datastore_validator.ValidationError, e:
      raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                             str(e))
    except datastore_pbs.InvalidConversionError, e:
      raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                             str(e))
    if v3_refs:
      v3_full_refs = v3_stub._AllocateIds(v3_refs)
      try:
        resp.keys.extend(
            self.__entity_converter.v3_to_v1_keys(v3_full_refs))
      except datastore_pbs.InvalidConversionError, e:
        raise apiproxy_errors.ApplicationError(
            datastore_pb.Error.INTERNAL_ERROR, str(e))

  def __begin_adhoc_txn(self, request):
    """Begins a new transaction as part of another request and returns it.

    Args:
      request: the request that asked for a new transaction to be created.

    Returns:
      a new v1 transaction.
    """
    v1_txn_req = googledatastore.BeginTransactionRequest()
    v1_txn_req.project_id = request.project_id
    v1_txn_resp = googledatastore.BeginTransactionResponse()
    self._Dynamic_BeginTransaction(v1_txn_req, v1_txn_resp)
    return v1_txn_resp.transaction

  def __rollback_adhoc_txn(self, request, v1_transaction):
    """Rolls back a transaction that was created as part of another request.

    This is best effort only, so any error occuring during the rollback will be
    silenced.

    Args:
      request: the request that asked for a new transaction to be created.
      v1_transaction: the transaction that was created and needs to be rolled
          back.
    """
    try:
      v1_rollback_req = googledatastore.RollbackRequest()
      v1_rollback_req.project_id = request.project_id
      v1_rollback_req.transaction = v1_transaction
      self._Dynamic_Rollback(v1_rollback_req,
                             googledatastore.RollbackResponse())
    except apiproxy_errors.ApplicationError, e:
      pass

  def __commit(self, v1_mutations, v1_txn, resp):
    """Commits a list of v1 mutations.

    Args:
      v1_mutations: the list of mutations to apply and commit
      v1_txn: required v1 transaction handle in which to apply the mutations
      resp: a v1 CommitResponse to update with the result of this commit
    """


    mutation_keys = []


    seen_keys = set()


    allocated_keys = {}


    conflict_cache = {}


    version_cache = {}

    for i, mutation in enumerate(v1_mutations):
      v1_key, v1_entity = datastore_pbs.get_v1_mutation_key_and_entity(mutation)
      key = datastore_types.ReferenceToKeyValue(v1_key, self._id_resolver)
      if not datastore_pbs.is_complete_v1_key(v1_key):

        v1_key = self.__put_v1_entity(v1_entity, v1_txn)
        key = datastore_types.ReferenceToKeyValue(v1_key, self._id_resolver)
        allocated_keys[key] = v1_key
      elif key not in conflict_cache:


        base_version = None
        if mutation.HasField('base_version') and key not in seen_keys:
          base_version = mutation.base_version

        conflict_version = self.__apply_v1_mutation(mutation, base_version,
                                                    v1_txn, version_cache)
        if conflict_version is not None:
          conflict_cache[key] = conflict_version

      mutation_keys.append(key)
      seen_keys.add(key)

    v3_txn = datastore_pb.Transaction()
    self.__service_converter.v1_to_v3_txn(v1_txn, v3_txn)
    v3_resp = datastore_pb.CommitResponse()
    self.__make_v3_call('Commit', v3_txn, v3_resp)
    resp.index_updates = v3_resp.cost().index_writes()



    mutation_versions = {}
    for version in v3_resp.version_list():
      key = datastore_types.ReferenceToKeyValue(version.root_entity_key())
      mutation_versions[key] = version.version()

    for key in mutation_keys:
      mutation_result = resp.mutation_results.add()
      if key in allocated_keys:
        mutation_result.key.CopyFrom(allocated_keys[key])
      if key in conflict_cache:
        mutation_result.conflict_detected = True
        mutation_result.version = conflict_cache[key]
      else:
        mutation_result.version = mutation_versions[key]


  def __apply_v1_mutation(self, v1_mutation, base_version, v1_txn,
                          version_cache):
    """Applies a v1 Mutation in a transaction.

    Args:
      v1_mutation: a googledatastore.Mutation, must be for a complete key.
      base_version: optional, the version the entity is expected to be at. If
          the entity has a different version number, the mutation does not
          apply. If None, then this check is skipped.
      v1_txn: a v1 transaction handle
      version_cache: a cache of entity keys to version, for entities that have
          been mutated previously in this transaction.
    """
    v1_key, v1_entity = datastore_pbs.get_v1_mutation_key_and_entity(
        v1_mutation)
    key = datastore_types.ReferenceToKeyValue(v1_key, self._id_resolver)



    if (v1_mutation.HasField('insert') or v1_mutation.HasField('update') or
        base_version is not None) and key not in version_cache:
      version_cache[key] = self.__get_v1_entity_version(v1_key, v1_txn)

    if v1_mutation.HasField('insert'):
      if base_version is not None and base_version != _NO_VERSION:
        raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                               'Cannot insert an entity with a '
                                               'base version greater than zero')
      elif version_cache[key] != _NO_VERSION:
        raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                               'Entity already exists.')
    elif v1_mutation.HasField('update'):
      if base_version is not None and base_version == _NO_VERSION:
        raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                               'Cannot update an entity with a '
                                               'base version set to zero')
      elif version_cache[key] == _NO_VERSION:
        raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                               'Entity does not exist.')


    if base_version is not None:
      persisted_version = version_cache[key]
      if persisted_version != _NO_VERSION and persisted_version < base_version:
        raise apiproxy_errors.ApplicationError(datastore_pb.Error.BAD_REQUEST,
                                               'Invalid base version, it is '
                                               'greater than the stored '
                                               'version')
      if persisted_version != base_version:
        return persisted_version


    if v1_mutation.HasField('delete'):
      self.__delete_v1_key(v1_key, v1_txn)
      version_cache[key] = _NO_VERSION
    else:
      self.__put_v1_entity(v1_entity, v1_txn)
      version_cache[key] = _MINIMUM_VERSION

  def __get_v1_entity_version(self, v1_key, v1_txn):
    """Returns the version of an entity, or _NO_VERSION if it does not exist.

    Args:
      v1_key: the key of the entity to lookup.
      v1_txn: the transaction to use when retrieving the entity.

    Returns:
      the version number of the entity if it was found, or _NO_VERSION
      otherwise.
    """
    v3_key = entity_pb.Reference()
    self.__entity_converter.v1_to_v3_reference(v1_key, v3_key)
    v3_txn = datastore_pb.Transaction()
    self.__service_converter.v1_to_v3_txn(v1_txn, v3_txn)

    v3_get_req = datastore_pb.GetRequest()
    v3_get_req.mutable_transaction().CopyFrom(v3_txn)
    v3_get_req.key_list().append(v3_key)
    v3_get_resp = datastore_pb.GetResponse()
    self.__make_v3_call('Get', v3_get_req, v3_get_resp)
    if v3_get_resp.entity(0).has_entity():
      return v3_get_resp.entity(0).version()
    return _NO_VERSION

  def __put_v1_entity(self, v1_entity, v1_txn):
    """Writes a v1 entity to the datastore in a transaction and return its key.

    Args:
      v1_entity: the entity to write
      v1_txn: the transaction in which to write the entity.

    Returns:
      the key of the entity, which may have been allocated.
    """
    v3_entity = entity_pb.EntityProto()
    self.__entity_converter.v1_to_v3_entity(v1_entity, v3_entity)
    v3_txn = datastore_pb.Transaction()
    self.__service_converter.v1_to_v3_txn(v1_txn, v3_txn)

    v3_put_req = datastore_pb.PutRequest()
    v3_put_req.mutable_transaction().CopyFrom(v3_txn)
    v3_put_req.entity_list().append(v3_entity)
    v3_put_resp = datastore_pb.PutResponse()
    self.__make_v3_call('Put', v3_put_req, v3_put_resp)
    v3_key = v3_put_resp.key(0)

    v1_key = googledatastore.Key()
    self.__entity_converter.v3_to_v1_key(v3_key, v1_key)
    return v1_key

  def __delete_v1_key(self, v1_key, v1_txn):
    """Deletes an entity from a v1 key in a transaction."""
    v3_key = entity_pb.Reference()
    self.__entity_converter.v1_to_v3_reference(v1_key, v3_key)
    v3_txn = datastore_pb.Transaction()
    self.__service_converter.v1_to_v3_txn(v1_txn, v3_txn)

    v3_delete_req = datastore_pb.DeleteRequest()
    v3_delete_req.mutable_transaction().CopyFrom(v3_txn)
    v3_delete_req.add_key().CopyFrom(v3_key)
    v3_delete_resp = datastore_pb.DeleteResponse()
    self.__make_v3_call('Delete', v3_delete_req, v3_delete_resp)

  def __normalize_v1_run_query_request(self, v1_req):

    pass

  def __make_v3_call(self, method, v3_req, v3_resp):
    apiproxy_stub_map.MakeSyncCall(V3_SERVICE_NAME, method, v3_req, v3_resp)
