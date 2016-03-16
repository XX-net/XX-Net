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




"""Implementation of the datastore_v4 API that forwards to the v3 service."""













from google.appengine.datastore import entity_pb

from google.appengine.api import api_base_pb
from google.appengine.api import apiproxy_stub
from google.appengine.api import apiproxy_stub_map
from google.appengine.datastore import datastore_pb
from google.appengine.datastore import datastore_pbs
from google.appengine.datastore import datastore_query
from google.appengine.datastore import datastore_stub_util
from google.appengine.datastore import datastore_v4_pb
from google.appengine.datastore import datastore_v4_validator
from google.appengine.runtime import apiproxy_errors


SERVICE_NAME = 'datastore_v4'
V3_SERVICE_NAME = 'datastore_v3'


class DatastoreV4Stub(apiproxy_stub.APIProxyStub):
  """Implementation of the datastore_v4 API that forwards to the v3 service."""


  THREADSAFE = False

  def __init__(self, app_id):
    apiproxy_stub.APIProxyStub.__init__(self, SERVICE_NAME)
    self.__app_id = app_id
    self.__entity_converter = datastore_pbs.get_entity_converter()
    self.__service_converter = datastore_stub_util.get_service_converter()
    self.__service_validator = datastore_v4_validator.get_service_validator()

  def _Dynamic_BeginTransaction(self, req, resp):
    try:
      self.__service_validator.validate_begin_transaction_req(req)
      v3_req = self.__service_converter.v4_to_v3_begin_transaction_req(
          self.__app_id, req)
      v3_resp = datastore_pb.Transaction()
      self.__make_v3_call('BeginTransaction', v3_req, v3_resp)
    except datastore_pbs.InvalidConversionError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.BAD_REQUEST, str(e))
    except datastore_v4_validator.ValidationError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.BAD_REQUEST, str(e))
    try:
      v4_resp = self.__service_converter.v3_to_v4_begin_transaction_resp(
          v3_resp)
    except datastore_pbs.InvalidConversionError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.INTERNAL_ERROR, str(e))
    resp.CopyFrom(v4_resp)

  def _Dynamic_Rollback(self, req, unused_resp):
    try:
      self.__service_validator.validate_rollback_req(req)
      v3_req = self.__service_converter.v4_rollback_req_to_v3_txn(req)
      self.__make_v3_call('Rollback', v3_req, api_base_pb.VoidProto())
    except datastore_pbs.InvalidConversionError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.BAD_REQUEST, str(e))
    except datastore_v4_validator.ValidationError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.BAD_REQUEST, str(e))

  def _Dynamic_Commit(self, req, resp):
    try:
      self.__service_validator.validate_commit_req(req)
      if req.has_transaction():
        resp.mutable_deprecated_mutation_result()
        resp.mutable_deprecated_mutation_result().CopyFrom(
            self.__apply_v4_deprecated_mutation(req.deprecated_mutation(),
                                                req.transaction()))
        v3_req = self.__service_converter.v4_commit_req_to_v3_txn(req)
        v3_resp = datastore_pb.CommitResponse()
        self.__make_v3_call('Commit', v3_req, v3_resp)
        total_index_updates = (
            resp.mutable_deprecated_mutation_result().index_updates()
            + v3_resp.cost().index_writes())
        resp.mutable_deprecated_mutation_result().set_index_updates(
            total_index_updates)
      else:
        resp.mutable_deprecated_mutation_result().CopyFrom(
            self.__apply_v4_deprecated_mutation(req.deprecated_mutation(),
                                                None))
    except datastore_pbs.InvalidConversionError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.BAD_REQUEST, str(e))
    except datastore_v4_validator.ValidationError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.BAD_REQUEST, str(e))

  def _Dynamic_RunQuery(self, req, resp):
    try:
      self.__normalize_v4_run_query_request(req)
      self.__service_validator.validate_run_query_req(req)
      v3_req = self.__service_converter.v4_run_query_req_to_v3_query(req)
      v3_resp = datastore_pb.QueryResult()
      self.__make_v3_call('RunQuery', v3_req, v3_resp)
    except datastore_pbs.InvalidConversionError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.BAD_REQUEST, str(e))
    except datastore_v4_validator.ValidationError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.BAD_REQUEST, str(e))
    try:
      v4_resp = self.__service_converter.v3_to_v4_run_query_resp(v3_resp)
      if req.query().projection_list():
        if req.query().projection_list() == ['__key__']:
          result_type = datastore_v4_pb.EntityResult.KEY_ONLY
        else:
          result_type = datastore_v4_pb.EntityResult.PROJECTION
        v4_resp.mutable_batch().set_entity_result_type(result_type)
    except datastore_pbs.InvalidConversionError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.INTERNAL_ERROR, str(e))
    resp.CopyFrom(v4_resp)

  def _Dynamic_ContinueQuery(self, req, resp):
    try:
      self.__service_validator.validate_continue_query_req(req)
      v3_req = self.__service_converter.v4_to_v3_next_req(req)
      v3_resp = datastore_pb.QueryResult()
      self.__make_v3_call('Next', v3_req, v3_resp)
    except datastore_pbs.InvalidConversionError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.BAD_REQUEST, str(e))
    except datastore_v4_validator.ValidationError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.BAD_REQUEST, str(e))
    try:
      v4_resp = self.__service_converter.v3_to_v4_continue_query_resp(v3_resp)
    except datastore_pbs.InvalidConversionError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.INTERNAL_ERROR, str(e))
    resp.CopyFrom(v4_resp)

  def _Dynamic_Lookup(self, req, resp):
    try:
      self.__service_validator.validate_lookup_req(req)
      v3_req = self.__service_converter.v4_to_v3_get_req(req)
      v3_resp = datastore_pb.GetResponse()
      self.__make_v3_call('Get', v3_req, v3_resp)
    except datastore_pbs.InvalidConversionError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.BAD_REQUEST, str(e))
    except datastore_v4_validator.ValidationError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.BAD_REQUEST, str(e))
    try:
      v4_resp = self.__service_converter.v3_to_v4_lookup_resp(v3_resp)
    except datastore_pbs.InvalidConversionError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.INTERNAL_ERROR, str(e))
    resp.CopyFrom(v4_resp)

  def _Dynamic_AllocateIds(self, req, resp):



    v3_stub = apiproxy_stub_map.apiproxy.GetStub(V3_SERVICE_NAME)
    try:
      self.__service_validator.validate_allocate_ids_req(req)

      if req.allocate_list():
        v3_refs = self.__entity_converter.v4_to_v3_references(
            req.allocate_list())

        v3_full_refs = v3_stub._AllocateIds(v3_refs)
        resp.allocated_list().extend(
            self.__entity_converter.v3_to_v4_keys(v3_full_refs))
      elif req.reserve_list():
        v3_refs = self.__entity_converter.v4_to_v3_references(
            req.reserve_list())

        v3_stub._AllocateIds(v3_refs)
    except datastore_pbs.InvalidConversionError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.BAD_REQUEST, str(e))
    except datastore_v4_validator.ValidationError, e:
      raise apiproxy_errors.ApplicationError(
          datastore_v4_pb.Error.BAD_REQUEST, str(e))

  def __insert_v3_entity(self, v3_entity, v3_txn):
    """Inserts a v3 entity.

    Args:
      v3_entity: a datastore_v4_pb.Entity
      v3_txn: a datastore_pb.Transaction or None

    Returns:
      the number of index writes that occurred

    Raises:
      ApplicationError: if the entity already exists
    """
    if not v3_txn:

      v3_txn = datastore_pb.Transaction()
      v3_begin_txn_req = datastore_pb.BeginTransactionRequest()
      v3_begin_txn_req.set_app(v3_entity.key().app())
      self.__make_v3_call('BeginTransaction', v3_begin_txn_req, v3_txn)
      self.__insert_v3_entity(v3_entity, v3_txn)
      v3_resp = datastore_pb.CommitResponse()
      self.__make_v3_call('Commit', v3_txn, v3_resp)
      return v3_resp.cost().index_writes()

    v3_get_req = datastore_pb.GetRequest()
    v3_get_req.mutable_transaction().CopyFrom(v3_txn)
    v3_get_req.key_list().append(v3_entity.key())
    v3_get_resp = datastore_pb.GetResponse()
    self.__make_v3_call('Get', v3_get_req, v3_get_resp)
    if v3_get_resp.entity(0).has_entity():
      raise apiproxy_errors.ApplicationError(datastore_v4_pb.Error.BAD_REQUEST,
                                             'Entity already exists.')
    v3_put_req = datastore_pb.PutRequest()
    v3_put_req.mutable_transaction().CopyFrom(v3_txn)
    v3_put_req.entity_list().append(v3_entity)
    v3_put_resp = datastore_pb.PutResponse()
    self.__make_v3_call('Put', v3_put_req, v3_put_resp)
    return v3_put_resp.cost().index_writes()

  def __update_v3_entity(self, v3_entity, v3_txn):
    """Updates a v3 entity.

    Args:
      v3_entity: a datastore_v4_pb.Entity
      v3_txn: a datastore_pb.Transaction or None

    Returns:
      the number of index writes that occurred

    Raises:
      ApplicationError: if the entity does not exist
    """
    if not v3_txn:

      v3_txn = datastore_pb.Transaction()
      v3_begin_txn_req = datastore_pb.BeginTransactionRequest()
      v3_begin_txn_req.set_app(v3_entity.key().app())
      self.__make_v3_call('BeginTransaction', v3_begin_txn_req, v3_txn)
      self.__update_v3_entity(v3_entity, v3_txn)
      v3_resp = datastore_pb.CommitResponse()
      self.__make_v3_call('Commit', v3_txn, v3_resp)
      return v3_resp.cost().index_writes()

    v3_get_req = datastore_pb.GetRequest()
    v3_get_req.mutable_transaction().CopyFrom(v3_txn)
    v3_get_req.key_list().append(v3_entity.key())
    v3_get_resp = datastore_pb.GetResponse()
    self.__make_v3_call('Get', v3_get_req, v3_get_resp)
    if not v3_get_resp.entity(0).has_entity():
      raise apiproxy_errors.ApplicationError(datastore_v4_pb.Error.BAD_REQUEST,
                                             'Entity does not exist.')
    v3_put_req = datastore_pb.PutRequest()
    v3_put_req.mutable_transaction().CopyFrom(v3_txn)
    v3_put_req.entity_list().append(v3_entity)
    v3_put_resp = datastore_pb.PutResponse()
    self.__make_v3_call('Put', v3_put_req, v3_put_resp)
    return v3_put_resp.cost().index_writes()

  def __apply_v4_deprecated_mutation(self, v4_deprecated_mutation, v4_txn):
    """Applies a v4 DeprecatedMutation.

    Args:
      v4_deprecated_mutation: a datastore_v4_pb.DeprecatedMutation
      v4_txn: an optional v4 transaction handle or None

    Returns:
      a datastore_v4_pb.DeprecatedMutationResult
    """
    index_writes = 0
    v3_txn = None
    if v4_txn:
      v3_txn = datastore_pb.Transaction()
      self.__service_converter.v4_to_v3_txn(v4_txn, v3_txn)


    for v4_entity in v4_deprecated_mutation.insert_list():
      v3_entity = entity_pb.EntityProto()
      self.__entity_converter.v4_to_v3_entity(v4_entity, v3_entity)
      index_writes += self.__insert_v3_entity(v3_entity, v3_txn)


    for v4_entity in v4_deprecated_mutation.update_list():
      v3_entity = entity_pb.EntityProto()
      self.__entity_converter.v4_to_v3_entity(v4_entity, v3_entity)
      index_writes += self.__update_v3_entity(v3_entity, v3_txn)


    v3_insert_auto_req = datastore_pb.PutRequest()
    if v3_txn:
      v3_insert_auto_req.mutable_transaction().CopyFrom(v3_txn)
    for v4_entity in v4_deprecated_mutation.insert_auto_id_list():
      v3_entity = entity_pb.EntityProto()
      self.__entity_converter.v4_to_v3_entity(v4_entity, v3_entity)
      v3_insert_auto_req.entity_list().append(v3_entity)
    v3_insert_auto_id_resp = datastore_pb.PutResponse()
    self.__make_v3_call('Put', v3_insert_auto_req, v3_insert_auto_id_resp)
    index_writes += v3_insert_auto_id_resp.cost().index_writes()


    v3_upsert_req = datastore_pb.PutRequest()
    if v3_txn:
      v3_upsert_req.mutable_transaction().CopyFrom(v3_txn)
    for v4_entity in v4_deprecated_mutation.upsert_list():
      v3_entity = entity_pb.EntityProto()
      self.__entity_converter.v4_to_v3_entity(v4_entity, v3_entity)
      v3_upsert_req.entity_list().append(v3_entity)
    v3_upsert_resp = datastore_pb.PutResponse()
    self.__make_v3_call('Put', v3_upsert_req, v3_upsert_resp)
    index_writes += v3_upsert_resp.cost().index_writes()


    v3_delete_req = datastore_pb.DeleteRequest()
    if v3_txn:
      v3_delete_req.mutable_transaction().CopyFrom(v3_txn)
    for v4_key in v4_deprecated_mutation.delete_list():
      self.__entity_converter.v4_to_v3_reference(v4_key,
                                                 v3_delete_req.add_key())
    v3_delete_resp = datastore_pb.DeleteResponse()
    self.__make_v3_call('Delete', v3_delete_req, v3_delete_resp)
    index_writes += v3_delete_resp.cost().index_writes()

    v4_deprecated_mutation_result = datastore_v4_pb.DeprecatedMutationResult()
    for v3_ref in v3_insert_auto_id_resp.key_list():
      self.__entity_converter.v3_to_v4_key(
          v3_ref, v4_deprecated_mutation_result.add_insert_auto_id_key())
    v4_deprecated_mutation_result.set_index_updates(index_writes)

    return v4_deprecated_mutation_result

  def __normalize_v4_run_query_request(self, v4_req):

    pass

  def __make_v3_call(self, method, v3_req, v3_resp):
    apiproxy_stub_map.MakeSyncCall(V3_SERVICE_NAME, method, v3_req, v3_resp)
