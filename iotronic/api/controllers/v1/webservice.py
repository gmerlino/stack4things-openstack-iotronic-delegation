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
# from iotronic.common import policy
from iotronic import objects
import pecan
from pecan import rest
import wsme
from wsme import types as wtypes

_DEFAULT_RETURN_FIELDS = ('name', 'uuid', 'port', 'board_uuid', 'extra')


class Webservice(base.APIBase):
    """API representation of a webservice.

    """
    uuid = types.uuid
    name = wsme.wsattr(wtypes.text)
    port = wsme.types.IntegerType()
    board_uuid = types.uuid
    secure = types.boolean
    extra = types.jsontype

    links = wsme.wsattr([link.Link], readonly=True)

    def __init__(self, **kwargs):
        self.fields = []
        fields = list(objects.Webservice.fields)
        for k in fields:
            # Skip fields we do not expose.
            if not hasattr(self, k):
                continue
            self.fields.append(k)
            setattr(self, k, kwargs.get(k, wtypes.Unset))

    @staticmethod
    def _convert_with_links(webservice, url, fields=None):
        webservice_uuid = webservice.uuid
        if fields is not None:
            webservice.unset_fields_except(fields)

        webservice.links = [link.Link.make_link('self', url, 'webservices',
                                                webservice_uuid),
                            link.Link.make_link('bookmark', url, 'webservices',
                                                webservice_uuid, bookmark=True)
                            ]
        return webservice

    @classmethod
    def convert_with_links(cls, rpc_webservice, fields=None):
        webservice = Webservice(**rpc_webservice.as_dict())
        if fields is not None:
            api_utils.check_for_invalid_fields(fields, webservice.as_dict())

        return cls._convert_with_links(webservice, pecan.request.public_url,
                                       fields=fields)


class WebserviceCollection(collection.Collection):
    """API representation of a collection of webservices."""

    webservices = [Webservice]
    """A list containing webservices objects"""

    def __init__(self, **kwargs):
        self._type = 'webservices'

    @staticmethod
    def convert_with_links(webservices, limit, url=None, fields=None,
                           **kwargs):
        collection = WebserviceCollection()
        collection.webservices = [Webservice.convert_with_links(n,
                                                                fields=fields)
                                  for n in webservices]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection


class WebservicesController(rest.RestController):
    """REST controller for Webservices."""

    # _subcontroller_map = {
    #     'boards': WebserviceBoardsController,
    # }

    invalid_sort_key_list = ['extra', ]

    _custom_actions = {
        'detail': ['GET'],
    }

    # @pecan.expose()
    # def _lookup(self, ident, *remainder):
    #     try:
    #         ident = types.uuid_or_name.validate(ident)
    #     except exception.InvalidUuidOrName as e:
    #         pecan.abort('400', e.args[0])
    #     if not remainder:
    #         return
    #
    #     subcontroller = self._subcontroller_map.get(remainder[0])
    #     if subcontroller:
    #         return subcontroller(webservice_ident=ident), remainder[1:]

    def _get_webservices_collection(self, authorized_webservices, marker,
                                    limit, sort_key, sort_dir,
                                    project_id, fields=None):

        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)

        marker_obj = None
        if marker:
            marker_obj = objects.Webservice.get_by_uuid(pecan.request.context,
                                                        marker)

        if sort_key in self.invalid_sort_key_list:
            raise exception.InvalidParameterValue(
                ("The sort_key value %(key)s is an invalid field for "
                 "sorting") % {'key': sort_key})

        filters = {}
        filters['project_id'] = project_id

        webservices = objects.Webservice.list(pecan.request.context,
                                              authorized_webservices, limit,
                                              marker_obj,
                                              sort_key=sort_key,
                                              sort_dir=sort_dir,
                                              filters=filters)

        parameters = {'sort_key': sort_key, 'sort_dir': sort_dir}

        return WebserviceCollection.convert_with_links(webservices, limit,
                                                       fields=fields,
                                                       **parameters)

    @expose.expose(Webservice, types.uuid_or_name, types.listtype)
    def get_one(self, webservice_ident, fields=None):
        """Retrieve information about the given webservice.

        :param webservice_ident: UUID or logical name of a webservice.
        :param fields: Optional, a list with a specified set of fields
            of the resource to be returned.
        """

        rpc_webservice = api_utils.get_rpc_webservice(webservice_ident)
        authorization.authorize('webservice:get_one', rpc_webservice.uuid)

        return Webservice.convert_with_links(rpc_webservice, fields=fields)

    @expose.expose(WebserviceCollection, types.uuid, int, wtypes.text,
                   wtypes.text, types.listtype, types.boolean, types.boolean)
    def get_all(self, marker=None,
                limit=None, sort_key='id', sort_dir='asc',
                fields=None):
        """Retrieve a list of webservices.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
                      This value cannot be larger than the value of max_limit
                      in the [api] section of the ironic configuration, or only
                      max_limit resources will be returned.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        :param with_public: Optional boolean to get also public pluings.
        :param all_webservices: Optional boolean to get all the pluings.
                            Only for the admin
        :param fields: Optional, a list with a specified set of fields
                       of the resource to be returned.
        """
        authorized_webservices = authorization.authorize('webservice:get')

        project_id = pecan.request.context.project_id

        if fields is None:
            fields = _DEFAULT_RETURN_FIELDS
        return self._get_webservices_collection(authorized_webservices, marker,
                                                limit, sort_key, sort_dir,
                                                project_id=project_id,
                                                fields=fields)

    @expose.expose(None, types.uuid_or_name, status_code=204)
    def delete(self, webservice_ident):
        """Delete a webservice.

        :param webservice_ident: UUID or logical name of a webservice.
        """

        rpc_webservice = api_utils.get_rpc_webservice(webservice_ident)
        authorization.authorize('webservice:delete', rpc_webservice.uuid)

        pecan.request.rpcapi.destroy_webservice(pecan.request.context,
                                                rpc_webservice.uuid)
        # remove all webservice delegations
        objects.Delegation.destroy_by_node_uuid(
            pecan.request.context, rpc_webservice.uuid, 'webservice')

    # @expose.expose(Webservice, types.uuid_or_name, body=Webservice,
    #                status_code=200)
    # def patch(self, webservice_ident, val_Webservice):
    #     """Update a webservice.
    #
    #     :param webservice_ident: UUID or logical name of a webservice.
    #     :param Webservice: values to be changed
    #     :return updated_webservice: updated_webservice
    #     """
    #
    #     rpc_webservice = api_utils.get_rpc_webservice(webservice_ident)
    #     authorization.authorize('webservice:update',rpc_webservice.uuid)
    #
    #     val_Webservice = val_Webservice.as_dict()
    #     for key in val_Webservice:
    #         try:
    #             rpc_webservice[key] = val_Webservice[key]
    #         except Exception:
    #             pass
    #
    #     updated_webservice = pecan.request.rpcapi.update_webservice(
    #         pecan.request.context, rpc_webservice)
    #     return Webservice.convert_with_links(updated_webservice)

    @expose.expose(WebserviceCollection, types.uuid, int, wtypes.text,
                   wtypes.text, types.listtype, types.boolean, types.boolean)
    def detail(self, marker=None,
               limit=None, sort_key='id', sort_dir='asc',
               fields=None, with_public=False, all_webservs=False):
        """Retrieve a list of webservices.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
                      This value cannot be larger than the value of max_limit
                      in the [api] section of the ironic configuration, or only
                      max_limit resources will be returned.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        :param with_public: Optional boolean to get also public webservice.
        :param all_webservs: Optional boolean to get all the webservices.
                            Only for the admin
        :param fields: Optional, a list with a specified set of fields
                       of the resource to be returned.
        """

        authorized_webservices = authorization.authorize('webservice:get')

        # /detail should only work against collections
        parent = pecan.request.path.split('/')[:-1][-1]
        if parent != "webservices":
            raise exception.HTTPNotFound()

        return self._get_webservices_collection(authorized_webservices, marker,
                                                limit, sort_key, sort_dir,
                                                with_public=with_public,
                                                all_webservices=all_webservs,
                                                fields=fields)
