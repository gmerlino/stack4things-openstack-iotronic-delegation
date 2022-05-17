#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging

from iotronicclient.common import base
from iotronicclient import exc

LOG = logging.getLogger(__name__)
_DEFAULT_POLL_INTERVAL = 2


class Delegation(base.Resource):
    def __repr__(self):
        return "<Delegation %s>" % self._info


class DelegationManager(base.CreateManager):
    resource_class = Delegation
    _creation_attributes = []
    delegation_class = Delegation
    _resource_name = 'delegations'

    def list(self, node_id, type):
        resp, body = self.api.json_request('GET', self._path(),
                                           body={'node_id': node_id,
                                                 'type': type})

        object_list = []
        obj_class = self.resource_class
        data = self._format_body_data(body, 'delegations')
        for obj in data:
            object_list.append(obj_class(self, obj, loaded=True))
        return object_list

    def get(self, dele_id):
        path = dele_id
        url = self._path(path)
        resp, body = self.api.json_request('GET', url)
        if body:
            return self.delegation_class(self, body)

    def create(self, node_id, **kwargs):
        path = node_id
        new = {}
        invalid = []
        for (key, value) in kwargs.items():
            if key in ['delegated', 'role', 'type']:
                new[key] = value
            else:
                invalid.append(key)
        if invalid:
            raise exc.InvalidAttribute(
                'The attribute(s) "%(attrs)s" are invalid; they are not '
                'needed to create delegation.'
                % {'attrs': '","'.join(invalid)})
        url = self._path(path)
        resp, body = self.api.json_request('POST', url, body=new)
        if body:
            return self.delegation_class(self, body)

    def delete(self, dele_id):
        path = dele_id
        url = self._path(path)
        return self.api.raw_request('DELETE', url)

    def update(self, dele_id, **kwargs):
        path = dele_id
        new = {}
        invalid = []
        for (key, value) in kwargs.items():
            if key in ['role']:
                new[key] = value
            else:
                invalid.append(key)
        if invalid:
            raise exc.InvalidAttribute(
                'The attribute(s) "%(attrs)s" are invalid; they are not '
                'needed to create delegation.'
                % {'attrs': '","'.join(invalid)})
        url = self._path(path)
        resp, body = self.api.json_request('PATCH', url, body=new)
        if body:
            return self.delegation_class(self, body)
