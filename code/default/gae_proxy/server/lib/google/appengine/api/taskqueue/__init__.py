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




"""Task Queue API module."""

from taskqueue import *

__all__ = [

    'BadTaskStateError', 'BadTransactionState', 'BadTransactionStateError',
    'DatastoreError', 'DuplicateTaskNameError', 'Error', 'InternalError',
    'InvalidQueueError', 'InvalidQueueNameError', 'InvalidTaskError',
    'InvalidTaskNameError', 'InvalidUrlError', 'PermissionDeniedError',
    'TaskAlreadyExistsError', 'TaskTooLargeError', 'TombstonedTaskError',
    'TooManyTasksError', 'TransientError', 'UnknownQueueError',
    'InvalidLeaseTimeError', 'InvalidMaxTasksError', 'InvalidDeadlineError',
    'InvalidQueueModeError', 'TransactionalRequestTooLargeError',
    'TaskLeaseExpiredError', 'QueuePausedError', 'InvalidEtaError',
    'InvalidTagError',

    'MAX_QUEUE_NAME_LENGTH', 'MAX_TASK_NAME_LENGTH', 'MAX_TASK_SIZE_BYTES',
    'MAX_PULL_TASK_SIZE_BYTES', 'MAX_PUSH_TASK_SIZE_BYTES',
    'MAX_LEASE_SECONDS', 'MAX_TASKS_PER_ADD',
    'MAX_TASKS_PER_LEASE',
    'MAX_URL_LENGTH',

    'DEFAULT_APP_VERSION',

    'Queue', 'QueueStatistics', 'Task', 'TaskRetryOptions', 'add', 'create_rpc']
