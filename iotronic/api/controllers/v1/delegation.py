#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.


from iotronic.api.controllers import base
from iotronic.api.controllers import link
from iotronic.api.controllers.v1 import collection
from iotronic.api.controllers.v1 import types
from iotronic.api.controllers.v1 import utils as api_utils
from iotronic.api import expose
from iotronic.common import authorization
from iotronic.common import exception
from iotronic import objects
from oslo_utils import uuidutils
import pecan
from pecan import rest
from wsme import types as wtypes


class Delegation(base.APIBase):
    uuid = types.uuid
    delegated = types.uuid
    delegator = types.uuid
    parent = types.uuid
    role = wtypes.text
    node = types.uuid
    type = wtypes.text

    def __init__(self, **kwargs):
        self.fields = []
        fields = list(objects.Delegation.fields)
        for k in fields:
            if not hasattr(self, k):
                continue
            self.fields.append(k)
            setattr(self, k, kwargs.get(k, wtypes.Unset))
        setattr(self, 'uuid', kwargs.get('uuid', wtypes.Unset))

    @staticmethod
    def _convert_with_links(delegation, url, fields=None):
        delegation_uuid = delegation.uuid
        if fields is not None:
            delegation.unset_fields_except(fields)

        delegation.links = [link.Link.make_link('self', url, 'delegations',
                                                delegation_uuid),
                            link.Link.make_link('bookmark', url, 'delegations',
                                                delegation_uuid, bookmark=True)
                            ]
        return delegation

    @classmethod
    def convert_with_links(cls, rpc_delegation, fields=None):
        delegation = Delegation(**rpc_delegation.as_dict())
        if fields is not None:
            api_utils.check_for_invalid_fields(fields, delegation.as_dict())

        return cls._convert_with_links(delegation, pecan.request.public_url,
                                       fields=fields)


class DelegationCollection(collection.Collection):
    """API representation of a collection of delegationss."""

    delegations = [Delegation]

    def __init__(self, **kwargs):
        self._type = 'delegations'

    @staticmethod
    def get_list(delegations, fields=None):
        collection = DelegationCollection()
        collection.delegations = [Delegation(**n.as_dict())
                                  for n in delegations]
        return collection


class DelegationsController(rest.RestController):

    def _get_delegations_on_node_collection(self, node_uuid, fields=None):
        delegations = objects.Delegation.list(
            pecan.request.context, node_uuid)
        return DelegationCollection.get_list(delegations, fields=fields)

    @expose.expose(DelegationCollection, body=types.jsontype, status_code=200)
    def get_all(self, node):
        if not node['node_id']:
            raise exception.MissingParameterValue(
                ("Resource is not specified."))
        if not node['type']:
            raise exception.MissingParameterValue(
                ("Resource type is not specified."))
        authorization.authorize(node['type']+':delegation_get',
                                node['node_id'])
        return self._get_delegations_on_node_collection(node['node_id'])

    @expose.expose(Delegation, types.uuid_or_name, status_code=200)
    def get_one(self, delegation_ident):
        delegation = objects.Delegation.get_by_uuid(pecan.request.context,
                                                    delegation_ident)
        authorization.authorize(delegation.type+':delegation_get_one',
                                delegation.node)
        return delegation

    @expose.expose(Delegation, types.uuid_or_name, body=Delegation,
                   status_code=200)
    def patch(self, delegation_ident, val_Delegation):
        """Update a delegation.

        :param delegation_ident: UUID or logical name of a delegation.
        :param Delegation: values to be changed
        :return updated_delegation: updated_delegation
        """

        delegation = api_utils.get_rpc_delegation(delegation_ident)
        authorization.authorize(delegation.type+':delegation_get_one',
                                delegation.node)
        user_uuid = pecan.request.context.user_id
        user_delegation = api_utils.get_rpc_current_delegation(
            user_uuid, delegation.node)
        delegation = api_utils.get_rpc_delegation(delegation_ident)
        val_Delegation = val_Delegation.as_dict()
        if 'role' not in val_Delegation:
            raise exception.MissingParameterValue(("role is not specified."))
        api_utils.check_role_assignment(
            user_delegation.role, val_Delegation['role'], delegation.type)

        for key in val_Delegation:
            try:
                delegation[key] = val_Delegation[key]
            except Exception:
                pass
        delegation.save()
        return Delegation.convert_with_links(delegation)

    @expose.expose(None, types.uuid_or_name, status_code=204)
    def delete(self, delegation_ident):
        """Delete a delegation.

        :param delegation_ident: UUID or logical name of a delegation.
        """

        delegation = objects.Delegation.get_by_uuid(pecan.request.context,
                                                    delegation_ident)
        authorization.authorize(delegation.type+':undelegate',
                                delegation.node)

        # remove delegations
        objects.Delegation.destroy_by_uuid(
            pecan.request.context, delegation_ident, delegation.type)

    @expose.expose(Delegation, types.uuid_or_name, body=Delegation,
                   status_code=201)
    def post(self, node_ident, Delegation):
        """Create a new Delegation.
        """

        if not Delegation.delegated:
            raise exception.MissingParameterValue(
                ("delegated is not specified."))
        if not uuidutils.is_uuid_like(Delegation.delegated):
            raise exception.InvalidInvalidUUID(uuid=Delegation.delegated)
        if not Delegation.type:
            raise exception.MissingParameterValue(
                ("type is not specified."))
        if not Delegation.role:
            raise exception.MissingParameterValue(
                ("role is not specified."))

        authorization.authorize(Delegation.type+':delegate', node_ident)
        user_uuid = pecan.request.context.user_id
        current_delegation = api_utils.get_rpc_current_delegation(
            user_uuid, node_ident)
        api_utils.check_role_assignment(
            current_delegation.role, Delegation.role, Delegation.type)

        # add delegation
        new_Delegation = objects.Delegation(pecan.request.context)
        new_Delegation.uuid = uuidutils.generate_uuid()
        new_Delegation.delegated = Delegation.delegated
        new_Delegation.delegator = user_uuid
        new_Delegation.parent = current_delegation.uuid
        new_Delegation.role = Delegation.role
        new_Delegation.node = node_ident
        new_Delegation.type = Delegation.type
        new_Delegation.create()

        return Delegation.convert_with_links(new_Delegation)
