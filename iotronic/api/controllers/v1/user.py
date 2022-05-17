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


class User(base.APIBase):
    """API representation of a user.

    """
    uuid = types.uuid
    name = wsme.wsattr(wtypes.text)
    base_role = wsme.wsattr(wtypes.text)
    links = wsme.wsattr([link.Link], readonly=True)

    def __init__(self, **kwargs):
        self.fields = []
        fields = list(objects.User.fields)
        for k in fields:
            if not hasattr(self, k):
                continue
            self.fields.append(k)
            setattr(self, k, kwargs.get(k, wtypes.Unset))

    @staticmethod
    def _convert_with_links(user, url, fields=None):
        user_uuid = user.uuid
        if fields is not None:
            user.unset_fields_except(fields)

        user.links = [link.Link.make_link('self', url, 'users',
                                          user_uuid),
                      link.Link.make_link('bookmark', url, 'users',
                                          user_uuid, bookmark=True)
                      ]
        return user

    @classmethod
    def convert_with_links(cls, rpc_user, fields=None):
        user = User(**rpc_user.as_dict())
        if fields is not None:
            api_utils.check_for_invalid_fields(fields, user.as_dict())

        return cls._convert_with_links(user, pecan.request.public_url,
                                       fields=fields)


class UserCollection(collection.Collection):
    """API representation of a collection of users."""

    users = [User]

    def __init__(self, **kwargs):
        self._type = 'users'

    @staticmethod
    def convert_with_links(users, limit, url=None, fields=None, **kwargs):
        collection = UserCollection()
        collection.users = [User.convert_with_links(n, fields=fields)
                            for n in users]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection


class UsersController(rest.RestController):

    """REST controller for Users."""

    def _get_users_collection(self, limit,
                              sort_key, sort_dir, filters=None):

        limit = None
        sort_dir = api_utils.validate_sort_dir(sort_dir)
        users = objects.User.list(pecan.request.context, limit,
                                  sort_key=sort_key, sort_dir=sort_dir,
                                  filters=filters)
        parameters = {'sort_key': sort_key, 'sort_dir': sort_dir}

        return UserCollection.convert_with_links(users, limit, **parameters)

    @expose.expose(User, types.uuid_or_name, types.listtype)
    def get_one(self, user_ident, fields=None):
        """Retrieve information about the given user.

        :param user_ident: UUID or logical name of a user.
        :param fields: Optional, a list with a specified set of fields
            of the resource to be returned.
        """
        authorization.authorize('user:get_one')

        rpc_user = api_utils.get_rpc_user(user_ident)

        return User.convert_with_links(rpc_user, fields=fields)

    @expose.expose(UserCollection, int, wtypes.text, wtypes.text)
    def get_all(self, limit=None, sort_key='id', sort_dir='asc'):
        """Retrieve a list of users.

        :param limit: maximum number of resources to return in a single result.
                      This value cannot be larger than the value of max_limit
                      in the [api] section of the ironic configuration, or only
                      max_limit resources will be returned.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        authorization.authorize('user:get')

        return self._get_users_collection(limit, sort_key, sort_dir)

    @expose.expose(User, body=User, status_code=201)
    def post(self, User):
        """Create a new User.

        :param User: a User within the request body.
        """
        authorization.authorize('user:create')

        if not User.uuid:
            raise exception.MissingParameterValue(
                ("UUID is not specified."))
        if not User.name:
            raise exception.MissingParameterValue(
                ("Name is not specified."))
        if not User.base_role:
            raise exception.MissingParameterValue(
                ("Base Role is not specified."))

        new_User = objects.User(pecan.request.context,
                                **User.as_dict())

        new_User.create()

        return User.convert_with_links(new_User)

    @expose.expose(None, types.uuid_or_name, status_code=204)
    def delete(self, user_ident):
        """Delete a user.

        :param user_ident: UUID or logical name of a user.
        """
        authorization.authorize('user:delete')

        rpc_user = api_utils.get_rpc_user(user_ident)
        rpc_user.destroy()

    @expose.expose(User, types.uuid_or_name, body=User, status_code=200)
    def patch(self, user_ident, val_User):
        """Update a user.

        :param user_ident: UUID or logical name of a user.
        :param User: values to be changed
        :return updated_user: updated_user
        """

        authorization.authorize('user:update')

        user = api_utils.get_rpc_user(user_ident)
        val_User = val_User.as_dict()
        for key in val_User:
            try:
                user[key] = val_User[key]
            except Exception:
                pass

        user.save()
        return User.convert_with_links(user)
