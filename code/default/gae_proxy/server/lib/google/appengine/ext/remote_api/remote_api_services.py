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




"""Service configuration for remote API.

This module is shared by both the remote_api_stub and the handler.
"""

import sys

from google.appengine.api import api_base_pb
from google.appengine.api import mail_service_pb
from google.appengine.api import urlfetch_service_pb
from google.appengine.api import user_service_pb
from google.appengine.api.app_identity import app_identity_service_pb
from google.appengine.api.blobstore import blobstore_service_pb
from google.appengine.api.capabilities import capability_service_pb
from google.appengine.api.channel import channel_service_pb
from google.appengine.api.files import file_service_pb
from google.appengine.api.images import images_service_pb
from google.appengine.api.logservice import log_service_pb
from google.appengine.api.memcache import memcache_service_pb
from google.appengine.api.modules import modules_service_pb
from google.appengine.api.prospective_search import prospective_search_pb
from google.appengine.api.remote_socket import remote_socket_service_pb
from google.appengine.api.search import search_service_pb
from google.appengine.api.system import system_service_pb
from google.appengine.api.taskqueue import taskqueue_service_pb
from google.appengine.api.xmpp import xmpp_service_pb
from google.appengine.datastore import datastore_pb
from google.appengine.datastore import datastore_v4_pb
from google.appengine.ext.remote_api import remote_api_pb


SERVICE_PB_MAP = {
    'app_identity_service': {
        'SignForApp': (app_identity_service_pb.SignForAppRequest,
                       app_identity_service_pb.SignForAppResponse),
        'GetPublicCertificatesForApp': (
            app_identity_service_pb.GetPublicCertificateForAppRequest,
            app_identity_service_pb.GetPublicCertificateForAppResponse),
        'GetServiceAccountName': (
            app_identity_service_pb.GetServiceAccountNameRequest,
            app_identity_service_pb.GetServiceAccountNameResponse),
        'GetDefaultGcsBucketName': (
            app_identity_service_pb.GetDefaultGcsBucketNameRequest,
            app_identity_service_pb.GetDefaultGcsBucketNameResponse),
        'GetAccessToken': (app_identity_service_pb.GetAccessTokenRequest,
                           app_identity_service_pb.GetAccessTokenResponse),
    },
    'blobstore': {
        'CreateUploadURL': (blobstore_service_pb.CreateUploadURLRequest,
                            blobstore_service_pb.CreateUploadURLResponse),
        'DeleteBlob': (blobstore_service_pb.DeleteBlobRequest,
                       api_base_pb.VoidProto),
        'FetchData': (blobstore_service_pb.FetchDataRequest,
                      blobstore_service_pb.FetchDataResponse),
        'DecodeBlobKey': (blobstore_service_pb.DecodeBlobKeyRequest,
                          blobstore_service_pb.DecodeBlobKeyResponse),
        'CreateEncodedGoogleStorageKey': (
            blobstore_service_pb.CreateEncodedGoogleStorageKeyRequest,
            blobstore_service_pb.CreateEncodedGoogleStorageKeyResponse),
    },
    'capability_service': {
        'IsEnabled': (capability_service_pb.IsEnabledRequest,
                      capability_service_pb.IsEnabledResponse),
    },
    'channel': {
        'CreateChannel': (channel_service_pb.CreateChannelRequest,
                          channel_service_pb.CreateChannelResponse),
        'SendChannelMessage': (channel_service_pb.SendMessageRequest,
                               api_base_pb.VoidProto),
    },
    'datastore_v3': {
        'Get': (datastore_pb.GetRequest, datastore_pb.GetResponse),
        'Put': (datastore_pb.PutRequest, datastore_pb.PutResponse),
        'Delete': (datastore_pb.DeleteRequest, datastore_pb.DeleteResponse),
        'AllocateIds': (datastore_pb.AllocateIdsRequest,
                        datastore_pb.AllocateIdsResponse),
        'RunQuery': (datastore_pb.Query, datastore_pb.QueryResult),
        'Next': (datastore_pb.NextRequest, datastore_pb.QueryResult),
        'BeginTransaction': (datastore_pb.BeginTransactionRequest,
                             datastore_pb.Transaction),
        'Commit': (datastore_pb.Transaction, datastore_pb.CommitResponse),
        'Rollback': (datastore_pb.Transaction, api_base_pb.VoidProto),
        'GetIndices': (datastore_pb.GetIndicesRequest,
                       datastore_pb.CompositeIndices),
    },
    'datastore_v4': {
        'AllocateIds': (datastore_v4_pb.AllocateIdsRequest,
                        datastore_v4_pb.AllocateIdsResponse),
    },
    'file': {
        'Create': (file_service_pb.CreateRequest,
                   file_service_pb.CreateResponse),
        'Open': (file_service_pb.OpenRequest, file_service_pb.OpenResponse),
        'Close': (file_service_pb.CloseRequest, file_service_pb.CloseResponse),
        'Append': (file_service_pb.AppendRequest,
                   file_service_pb.AppendResponse),
        'Stat': (file_service_pb.StatRequest, file_service_pb.StatResponse),
        'Delete': (file_service_pb.DeleteRequest,
                   file_service_pb.DeleteResponse),
        'Read': (file_service_pb.ReadRequest, file_service_pb.ReadResponse),
        'ReadKeyValue': (file_service_pb.ReadKeyValueRequest,
                         file_service_pb.ReadKeyValueResponse),
        'Shuffle': (file_service_pb.ShuffleRequest,
                    file_service_pb.ShuffleResponse),
        'GetShuffleStatus': (file_service_pb.GetShuffleStatusRequest,
                             file_service_pb.GetShuffleStatusResponse),
        'GetCapabilities': (file_service_pb.GetCapabilitiesRequest,
                            file_service_pb.GetCapabilitiesResponse),
        'GetDefaultGsBucketName': (
            file_service_pb.GetDefaultGsBucketNameRequest,
            file_service_pb.GetDefaultGsBucketNameResponse),
        'ListDir': (file_service_pb.ListDirRequest,
                    file_service_pb.ListDirResponse),
    },
    'images': {
        'Transform': (images_service_pb.ImagesTransformRequest,
                      images_service_pb.ImagesTransformResponse),
        'Composite': (images_service_pb.ImagesCompositeRequest,
                      images_service_pb.ImagesCompositeResponse),
        'Histogram': (images_service_pb.ImagesHistogramRequest,
                      images_service_pb.ImagesHistogramResponse),
        'GetUrlBase': (images_service_pb.ImagesGetUrlBaseRequest,
                       images_service_pb.ImagesGetUrlBaseResponse),
        'DeleteUrlBase': (images_service_pb.ImagesDeleteUrlBaseRequest,
                          images_service_pb.ImagesDeleteUrlBaseResponse),
    },
    'logservice': {
        'Flush': (log_service_pb.FlushRequest, api_base_pb.VoidProto),
        'SetStatus': (log_service_pb.SetStatusRequest, api_base_pb.VoidProto),
        'Read':
            (log_service_pb.LogReadRequest, log_service_pb.LogReadResponse),
    },
    'mail': {
        'Send': (mail_service_pb.MailMessage, api_base_pb.VoidProto),
        'SendToAdmins': (mail_service_pb.MailMessage, api_base_pb.VoidProto),
    },
    'matcher': {
        'Subscribe': (prospective_search_pb.SubscribeRequest,
                      prospective_search_pb.SubscribeResponse),
        'Unsubscribe': (prospective_search_pb.UnsubscribeRequest,
                        prospective_search_pb.UnsubscribeResponse),
        'ListSubscriptions': (prospective_search_pb.ListSubscriptionsRequest,
                              prospective_search_pb.ListSubscriptionsResponse),
        'ListTopics': (prospective_search_pb.ListTopicsRequest,
                       prospective_search_pb.ListTopicsResponse),
        'Match': (prospective_search_pb.MatchRequest,
                  prospective_search_pb.MatchResponse),
    },
    'memcache': {
        'Get': (memcache_service_pb.MemcacheGetRequest,
                memcache_service_pb.MemcacheGetResponse),
        'Set': (memcache_service_pb.MemcacheSetRequest,
                memcache_service_pb.MemcacheSetResponse),
        'Delete': (memcache_service_pb.MemcacheDeleteRequest,
                   memcache_service_pb.MemcacheDeleteResponse),
        'Increment': (memcache_service_pb.MemcacheIncrementRequest,
                      memcache_service_pb.MemcacheIncrementResponse),
        'BatchIncrement': (memcache_service_pb.MemcacheBatchIncrementRequest,
                           memcache_service_pb.MemcacheBatchIncrementResponse),
        'FlushAll': (memcache_service_pb.MemcacheFlushRequest,
                     memcache_service_pb.MemcacheFlushResponse),
        'Stats': (memcache_service_pb.MemcacheStatsRequest,
                  memcache_service_pb.MemcacheStatsResponse),
    },
    'remote_datastore': {
        'RunQuery': (datastore_pb.Query, datastore_pb.QueryResult),
        'TransactionQuery': (datastore_pb.Query,
                             remote_api_pb.TransactionQueryResult),
        'Transaction': (remote_api_pb.TransactionRequest,
                        datastore_pb.PutResponse),
        'GetIDs': (datastore_pb.PutRequest, datastore_pb.PutResponse),
        'GetIDsXG': (datastore_pb.PutRequest, datastore_pb.PutResponse),
    },
    'remote_socket': {
        'CreateSocket': (remote_socket_service_pb.CreateSocketRequest,
                         remote_socket_service_pb.CreateSocketReply),
        'Bind': (remote_socket_service_pb.BindRequest,
                 remote_socket_service_pb.BindReply),
        'GetSocketName': (remote_socket_service_pb.GetSocketNameRequest,
                          remote_socket_service_pb.GetSocketNameReply),
        'GetPeerName': (remote_socket_service_pb.GetPeerNameRequest,
                        remote_socket_service_pb.GetPeerNameReply),
        'SetSocketOptions': (remote_socket_service_pb.SetSocketOptionsRequest,
                             remote_socket_service_pb.SetSocketOptionsReply),
        'GetSocketOptions': (remote_socket_service_pb.GetSocketOptionsRequest,
                             remote_socket_service_pb.GetSocketOptionsReply),
        'Connect': (remote_socket_service_pb.ConnectRequest,
                    remote_socket_service_pb.ConnectReply),
        'Listen': (remote_socket_service_pb.ListenRequest,
                   remote_socket_service_pb.ListenReply),
        'Accept': (remote_socket_service_pb.AcceptRequest,
                   remote_socket_service_pb.AcceptReply),
        'ShutDown': (remote_socket_service_pb.ShutDownRequest,
                     remote_socket_service_pb.ShutDownReply),
        'Close': (remote_socket_service_pb.CloseRequest,
                  remote_socket_service_pb.CloseReply),
        'Send': (remote_socket_service_pb.SendRequest,
                 remote_socket_service_pb.SendReply),
        'Receive': (remote_socket_service_pb.ReceiveRequest,
                    remote_socket_service_pb.ReceiveReply),
        'Poll': (remote_socket_service_pb.PollRequest,
                 remote_socket_service_pb.PollReply),
        'Resolve': (remote_socket_service_pb.ResolveRequest,
                    remote_socket_service_pb.ResolveReply),
    },
    'search': {
        'IndexDocument': (search_service_pb.IndexDocumentRequest,
                          search_service_pb.IndexDocumentResponse),
        'DeleteDocument': (search_service_pb.DeleteDocumentRequest,
                           search_service_pb.DeleteDocumentResponse),
        'ListDocuments': (search_service_pb.ListDocumentsRequest,
                          search_service_pb.ListDocumentsResponse),
        'ListIndexes': (search_service_pb.ListIndexesRequest,
                        search_service_pb.ListIndexesResponse),
        'Search': (search_service_pb.SearchRequest,
                   search_service_pb.SearchResponse),
        'DeleteSchema': (search_service_pb.DeleteSchemaRequest,
                         search_service_pb.DeleteSchemaResponse),
    },
    'modules': {
        'GetModules': (modules_service_pb.GetModulesRequest,
                       modules_service_pb.GetModulesResponse),
        'GetVersions': (modules_service_pb.GetVersionsRequest,
                        modules_service_pb.GetVersionsResponse),
        'GetDefaultVersion': (modules_service_pb.GetDefaultVersionRequest,
                              modules_service_pb.GetDefaultVersionResponse),
        'GetNumInstances': (modules_service_pb.GetNumInstancesRequest,
                            modules_service_pb.GetNumInstancesResponse),
        'SetNumInstances': (modules_service_pb.SetNumInstancesRequest,
                            modules_service_pb.SetNumInstancesResponse),
        'StartModule': (modules_service_pb.StartModuleRequest,
                        modules_service_pb.StartModuleResponse),
        'StopModule': (modules_service_pb.StopModuleRequest,
                       modules_service_pb.StopModuleResponse),
        'GetHostname': (modules_service_pb.GetHostnameRequest,
                        modules_service_pb.GetHostnameResponse),
    },
    'system': {
        'GetSystemStats': (system_service_pb.GetSystemStatsRequest,
                           system_service_pb.GetSystemStatsResponse),
        'StartBackgroundRequest': (
            system_service_pb.StartBackgroundRequestRequest,
            system_service_pb.StartBackgroundRequestResponse),
    },
    'taskqueue': {
        'Add': (taskqueue_service_pb.TaskQueueAddRequest,
                taskqueue_service_pb.TaskQueueAddResponse),
        'BulkAdd': (taskqueue_service_pb.TaskQueueBulkAddRequest,
                    taskqueue_service_pb.TaskQueueBulkAddResponse),
        'FetchQueues': (taskqueue_service_pb.TaskQueueFetchQueuesRequest,
                        taskqueue_service_pb.TaskQueueFetchQueuesResponse),
        'FetchQueueStats': (
            taskqueue_service_pb.TaskQueueFetchQueueStatsRequest,
            taskqueue_service_pb.TaskQueueFetchQueueStatsResponse),
        'Delete': (taskqueue_service_pb.TaskQueueDeleteRequest,
                   taskqueue_service_pb.TaskQueueDeleteResponse),
        'ForceRun': (taskqueue_service_pb.TaskQueueForceRunRequest,
                     taskqueue_service_pb.TaskQueueForceRunResponse),
        'UpdateQueue': (taskqueue_service_pb.TaskQueueUpdateQueueRequest,
                        taskqueue_service_pb.TaskQueueUpdateQueueResponse),
        'PauseQueue': (taskqueue_service_pb.TaskQueuePauseQueueRequest,
                       taskqueue_service_pb.TaskQueuePauseQueueResponse),
        'PurgeQueue': (taskqueue_service_pb.TaskQueuePurgeQueueRequest,
                       taskqueue_service_pb.TaskQueuePurgeQueueResponse),
        'DeleteQueue': (taskqueue_service_pb.TaskQueueDeleteQueueRequest,
                        taskqueue_service_pb.TaskQueueDeleteQueueResponse),
        'DeleteGroup': (taskqueue_service_pb.TaskQueueDeleteGroupRequest,
                        taskqueue_service_pb.TaskQueueDeleteGroupResponse),
        'QueryTasks': (taskqueue_service_pb.TaskQueueQueryTasksRequest,
                       taskqueue_service_pb.TaskQueueQueryTasksResponse),
        'FetchTask': (taskqueue_service_pb.TaskQueueFetchTaskRequest,
                      taskqueue_service_pb.TaskQueueFetchTaskResponse),
        'QueryAndOwnTasks': (
            taskqueue_service_pb.TaskQueueQueryAndOwnTasksRequest,
            taskqueue_service_pb.TaskQueueQueryAndOwnTasksResponse),
        'ModifyTaskLease': (
            taskqueue_service_pb.TaskQueueModifyTaskLeaseRequest,
            taskqueue_service_pb.TaskQueueModifyTaskLeaseResponse),
        'UpdateStorageLimit': (
            taskqueue_service_pb.TaskQueueUpdateStorageLimitRequest,
            taskqueue_service_pb.TaskQueueUpdateStorageLimitResponse),
    },
    'urlfetch': {
        'Fetch': (urlfetch_service_pb.URLFetchRequest,
                  urlfetch_service_pb.URLFetchResponse),
    },
    'user': {
        'CreateLoginURL': (user_service_pb.CreateLoginURLRequest,
                           user_service_pb.CreateLoginURLResponse),
        'CreateLogoutURL': (user_service_pb.CreateLogoutURLRequest,
                            user_service_pb.CreateLogoutURLResponse),
        'GetOAuthUser': (user_service_pb.GetOAuthUserRequest,
                         user_service_pb.GetOAuthUserResponse),
        'CheckOAuthSignature': (user_service_pb.CheckOAuthSignatureRequest,
                                user_service_pb.CheckOAuthSignatureResponse),
    },
    'xmpp': {
        'GetPresence': (xmpp_service_pb.PresenceRequest,
                        xmpp_service_pb.PresenceResponse),
        'BulkGetPresence': (xmpp_service_pb.BulkPresenceRequest,
                            xmpp_service_pb.BulkPresenceResponse),
        'SendMessage': (xmpp_service_pb.XmppMessageRequest,
                        xmpp_service_pb.XmppMessageResponse),
        'SendInvite': (xmpp_service_pb.XmppInviteRequest,
                       xmpp_service_pb.XmppInviteResponse),
        'SendPresence': (xmpp_service_pb.XmppSendPresenceRequest,
                         xmpp_service_pb.XmppSendPresenceResponse),
        'CreateChannel': (channel_service_pb.CreateChannelRequest,
                          channel_service_pb.CreateChannelResponse),
        'SendChannelMessage': (channel_service_pb.SendMessageRequest,
                               api_base_pb.VoidProto),
    },
}
