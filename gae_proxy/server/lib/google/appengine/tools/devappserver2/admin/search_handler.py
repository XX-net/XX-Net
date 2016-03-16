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
"""Handlers that display full-text search indexes and documents."""

import urllib

from google.appengine.api import search
from google.appengine.tools.devappserver2.admin import admin_request_handler


class BaseSearchHandler(admin_request_handler.AdminRequestHandler):
  _MAX_RESULTS_PER_PAGE = 20

  def _handle_paging(self, start, has_more, values):
    if has_more:
      values['next_url'] = self._construct_url(
          add={'start': start + self._MAX_RESULTS_PER_PAGE})
      values['paging'] = True
    if start > 0:
      values['previous_url'] = self._construct_url(
          add={'start': max(0, start - self._MAX_RESULTS_PER_PAGE)})
      values['paging'] = True


class SearchIndexesListHandler(BaseSearchHandler):

  def get(self):
    start = self.request.get_range('start', min_value=0, default=0)
    namespace = self.request.get('namespace', default_value=None)
    resp = search.get_indexes(offset=start,
                              limit=self._MAX_RESULTS_PER_PAGE + 1,
                              namespace=namespace or '')
    has_more = len(resp.results) > self._MAX_RESULTS_PER_PAGE
    indexes = resp.results[:self._MAX_RESULTS_PER_PAGE]

    values = {
        'namespace': namespace or '',
        'has_namespace': namespace is not None,
        'indexes': indexes}
    self._handle_paging(start, has_more, values)

    self.response.write(self.render('search.html', values))


class SearchIndexHandler(BaseSearchHandler):

  def _process_search_response(self, response):

    documents = []
    field_names = set()

    # Collect field names.
    for result in response.results:
      fields = dict((field.name, field.value) for field in result.fields)
      field_names.update(fields)
      documents.append((result.doc_id, fields))

    field_names = sorted(field_names)
    template_documents = []

    for doc_id, fields in documents:
      doc_fields = [fields.get(field_name, '') for field_name in field_names]
      template_documents.append({'doc_id': doc_id, 'fields': doc_fields})

    return {'documents': template_documents, 'field_names': field_names}

  def get(self):
    index_name = self.request.get('index')
    if not index_name:
      self.redirect('/search')
      return
    start = self.request.get_range('start', min_value=0, default=0)
    query = self.request.get('query')
    namespace = self.request.get('namespace')
    index = search.Index(name=index_name, namespace=namespace)
    resp = index.search(query=search.Query(
        query_string=query,
        options=search.QueryOptions(offset=start,
                                    limit=self._MAX_RESULTS_PER_PAGE)))
    has_more = resp.number_found > start + self._MAX_RESULTS_PER_PAGE

    values = {
        'namespace': namespace,
        'index': index_name,
        'start': start,
        'query': query,
        'values': self._process_search_response(resp),
    }
    self._handle_paging(start, has_more, values)
    self.response.write(self.render('search_index.html', values))

  def post(self):
    index_name = self.request.get('index')
    namespace = self.request.get('namespace')
    start = self.request.get_range('start', min_value=0, default=0)

    index = 0
    num_docs = int(self.request.get('numdocs'))
    docs = self.request.params.getall('doc_id')
    if len(docs) == num_docs:
      start = max(0, start - self._MAX_RESULTS_PER_PAGE)

    index = search.Index(name=index_name, namespace=namespace)
    index.delete(docs)
    self.redirect('/search/index?%s' % urllib.urlencode(
        {'namespace': namespace,
         'index': index_name,
         'start': start}))


class SearchDocumentHandler(BaseSearchHandler):

  def get(self):
    index_name = self.request.get('index')
    doc_id = self.request.get('id')
    namespace = self.request.get('namespace')
    doc = None
    index = search.Index(name=index_name, namespace=namespace)
    resp = index.get_range(start_id=doc_id, limit=1)
    if resp.results and resp.results[0].doc_id == doc_id:
      doc = resp.results[0]

    values = {
        'namespace': namespace,
        'index': index_name,
        'doc_id': doc_id,
        'doc': doc,
    }
    self.response.write(self.render('search_document.html', values))
