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
import pecan
from pecan import rest
import wsme
from wsme import types as wtypes


class Role(base.APIBase):
    """API representation of a role.

    """
    name = wsme.wsattr(wtypes.text)
    permissions = types.listtype
    description = wsme.wsattr(wtypes.text)
    links = wsme.wsattr([link.Link], readonly=True)

    def __init__(self, **kwargs):
        self.fields = []
        fields = list(objects.Role.fields)
        for k in fields:
            if not hasattr(self, k):
                continue
            self.fields.append(k)
            setattr(self, k, kwargs.get(k, wtypes.Unset))

    @staticmethod
    def _convert_with_links(role, url, fields=None):
        role_name = role.name
        if fields is not None:
            role.unset_fields_except(fields)

        role.links = [link.Link.make_link('self', url, 'roles',
                                          role_name),
                      link.Link.make_link('bookmark', url, 'roles',
                                          role_name, bookmark=True)
                      ]
        return role

    @classmethod
    def convert_with_links(cls, rpc_role, fields=None):
        role = Role(**rpc_role.as_dict())
        if fields is not None:
            api_utils.check_for_invalid_fields(fields, role.as_dict())

        return cls._convert_with_links(role, pecan.request.public_url,
                                       fields=fields)


class Operation(base.APIBase):
    """API representation of a role.

    """
    name = wsme.wsattr(wtypes.text)

    def __init__(self, **kwargs):
        self.fields = []
        fields = list(objects.Operation.fields)
        for k in fields:
            if not hasattr(self, k):
                continue
            self.fields.append(k)
            setattr(self, k, kwargs.get(k, wtypes.Unset))


class RoleCollection(collection.Collection):
    """API representation of a collection of roles."""

    roles = [Role]

    def __init__(self, **kwargs):
        self._type = 'roles'

    @staticmethod
    def convert_with_links(roles, limit, url=None, fields=None, **kwargs):
        collection = RoleCollection()
        collection.roles = [Role.convert_with_links(n, fields=fields)
                            for n in roles]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection


class RolesController(rest.RestController):

    """REST controller for Roles."""

    _custom_actions = {
        'operations': ['GET'],
    }

    def _get_ops_list(self, limit, sort_key, sort_dir, filters=None):

        limit = None
        sort_dir = api_utils.validate_sort_dir(sort_dir)
        ops = objects.Operation.oplist(pecan.request.context, limit,
                                       sort_key=sort_key, sort_dir=sort_dir,
                                       filters=filters)
        return [op.name for op in ops]

    def _get_roles_collection(self, limit, sort_key, sort_dir, filters=None):

        limit = None
        sort_dir = api_utils.validate_sort_dir(sort_dir)
        roles = objects.Role.list(pecan.request.context, limit,
                                  sort_key=sort_key, sort_dir=sort_dir,
                                  filters=filters)
        parameters = {'sort_key': sort_key, 'sort_dir': sort_dir}

        return RoleCollection.convert_with_links(roles, limit, **parameters)

    @expose.expose(Role, types.uuid_or_name, types.listtype)
    def get_one(self, role_ident, fields=None):
        """Retrieve information about the given role.

        :param role_ident: UUID or logical name of a role.
        :param fields: Optional, a list with a specified set of fields
            of the resource to be returned.
        """
        authorization.authorize('role:get_one')

        rpc_role = api_utils.get_rpc_role(role_ident)

        return Role.convert_with_links(rpc_role, fields=fields)

    @expose.expose(RoleCollection, int, wtypes.text, wtypes.text)
    def get_all(self, limit=None, sort_key='id', sort_dir='asc'):
        """Retrieve a list of roles.

        :param limit: maximum number of resources to return in a single result.
                      This value cannot be larger than the value of max_limit
                      in the [api] section of the ironic configuration, or only
                      max_limit resources will be returned.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        authorization.authorize('role:get')

        return self._get_roles_collection(limit, sort_key, sort_dir)

    @expose.expose(types.listtype, int, wtypes.text, wtypes.text)
    def operations(self, limit=None, sort_key='id', sort_dir='asc'):
        """Retrieve a list of roles.

        :param limit: maximum number of resources to return in a single result.
                      This value cannot be larger than the value of max_limit
                      in the [api] section of the ironic configuration, or only
                      max_limit resources will be returned.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        authorization.authorize('role:get_ops')

        return self._get_ops_list(limit, sort_key, sort_dir)

    @expose.expose(Role, body=Role, status_code=201)
    def post(self, Role):
        """Create a new Role.

        :param Role: a Role within the request body.
        """
        authorization.authorize('role:create')

        if not Role.name:
            raise exception.MissingParameterValue(
                ("Name is not specified."))
        if not Role.permissions:
            raise exception.MissingParameterValue(
                ("Permissions are not specified."))

        new_Role = objects.Role(pecan.request.context,
                                **Role.as_dict())

        new_Role.create()

        return Role.convert_with_links(new_Role)

    @expose.expose(None, types.uuid_or_name, status_code=204)
    def delete(self, role_ident):
        """Delete a role.

        :param role_ident: UUID or logical name of a role.
        """
        authorization.authorize('role:delete')

        rpc_role = api_utils.get_rpc_role(role_ident)
        rpc_role.destroy()

    @expose.expose(Role, types.uuid_or_name, body=Role, status_code=200)
    def patch(self, role_ident, val_Role):
        """Update a role.

        :param role_ident: logical name of a role.
        :param Role: values to be changed
        :return updated_role: updated_role
        """

        authorization.authorize('role:update')

        role = api_utils.get_rpc_role(role_ident)
        val_Role = val_Role.as_dict()
        for key in val_Role:
            try:
                role[key] = val_Role[key]
            except Exception:
                pass

        role.save()
        return Role.convert_with_links(role)
