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
from iotronic.api.controllers.v1.enabledwebservice import EnabledWebservice
from iotronic.api.controllers.v1 import location as loc
from iotronic.api.controllers.v1 import types
from iotronic.api.controllers.v1 import utils as api_utils
from iotronic.api.controllers.v1.webservice import Webservice
from iotronic.api.controllers.v1.webservice import WebserviceCollection
from iotronic.api import expose
from iotronic.common import authorization
from iotronic.common import exception
# from iotronic.common import policy
from iotronic import objects
from oslo_utils import uuidutils
import pecan
from pecan import rest
import wsme
from wsme import types as wtypes

from oslo_log import log as logging

LOG = logging.getLogger(__name__)

_DEFAULT_RETURN_FIELDS = ('name', 'code', 'status', 'uuid', 'session', 'type',
                          'fleet', 'lr_version', 'connectivity')
_DEFAULT_WEBSERVICE_RETURN_FIELDS = ('name', 'uuid', 'port', 'board_uuid',
                                     'extra')


class Board(base.APIBase):
    """API representation of a board.

    """
    uuid = types.uuid
    code = wsme.wsattr(wtypes.text)
    status = wsme.wsattr(wtypes.text)
    name = wsme.wsattr(wtypes.text)
    type = wsme.wsattr(wtypes.text)
    owner = types.uuid
    session = wsme.wsattr(wtypes.text)
    project = types.uuid
    fleet = types.uuid
    mobile = types.boolean
    lr_version = wsme.wsattr(wtypes.text)
    connectivity = types.jsontype
    links = wsme.wsattr([link.Link], readonly=True)
    location = wsme.wsattr([loc.Location])
    extra = types.jsontype

    def __init__(self, **kwargs):
        self.fields = []
        fields = list(objects.Board.fields)
        for k in fields:
            # Skip fields we do not expose.
            if not hasattr(self, k):
                continue
            self.fields.append(k)
            setattr(self, k, kwargs.get(k, wtypes.Unset))

    @staticmethod
    def _convert_with_links(board, url, fields=None):
        board_uuid = board.uuid
        if fields is not None:
            board.unset_fields_except(fields)

        # rel_name, url, resource, resource_args,
        #              bookmark=False, type=wtypes.Unset
        board.links = [link.Link.make_link('self', url, 'boards',
                                           board_uuid),
                       link.Link.make_link('bookmark', url, 'boards',
                                           board_uuid, bookmark=True)
                       ]
        return board

    @classmethod
    def convert_with_links(cls, rpc_board, fields=None):
        board = Board(**rpc_board.as_dict())

        try:
            session = objects.SessionWP.get_session_by_board_uuid(
                pecan.request.context, board.uuid)
            board.session = session.session_id
        except Exception:
            board.session = None

        try:
            list_loc = objects.Location.list_by_board_uuid(
                pecan.request.context, board.uuid)
            board.location = loc.Location.convert_with_list(list_loc)
        except Exception:
            board.location = []

        # to enable as soon as a better session and location management
        # is implemented
        # if fields is not None:
        #    api_utils.check_for_invalid_fields(fields, board_dict)

        return cls._convert_with_links(board,
                                       pecan.request.public_url,
                                       fields=fields)


class BoardCollection(collection.Collection):
    """API representation of a collection of boards."""

    boards = [Board]
    """A list containing boards objects"""

    def __init__(self, **kwargs):
        self._type = 'boards'

    @staticmethod
    def convert_with_links(boards, limit, url=None, fields=None, **kwargs):
        collection = BoardCollection()
        collection.boards = [Board.convert_with_links(n, fields=fields)
                             for n in boards]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection


class Port(base.APIBase):
    board_uuid = types.uuid
    uuid = types.uuid
    VIF_name = wtypes.text
    MAC_add = wtypes.text
    ip = wtypes.text
    network = wtypes.text

    def __init__(self, **kwargs):
        self.fields = []
        fields = list(objects.Port.fields)
        fields.remove('board_uuid')
        for k in fields:
            # Skip fields we do not expose.
            if not hasattr(self, k):
                continue
            self.fields.append(k)
            setattr(self, k, kwargs.get(k, wtypes.Unset))
        setattr(self, 'uuid', kwargs.get('uuid', wtypes.Unset))


class PortCollection(collection.Collection):
    """API representation of a collection of ports."""

    ports = [Port]

    def __init__(self, **kwargs):
        self._type = 'ports'

    @staticmethod
    def get_list(ports, fields=None):
        collection = PortCollection()
        collection.ports = [Port(**n.as_dict())
                            for n in ports]
        return collection


class InjectionPlugin(base.APIBase):
    plugin = types.uuid_or_name
    board_uuid = types.uuid_or_name
    status = wtypes.text
    onboot = types.boolean

    def __init__(self, **kwargs):
        self.fields = []
        fields = list(objects.InjectionPlugin.fields)
        fields.remove('board_uuid')
        for k in fields:
            # Skip fields we do not expose.
            if not hasattr(self, k):
                continue
            self.fields.append(k)
            setattr(self, k, kwargs.get(k, wtypes.Unset))
        setattr(self, 'plugin', kwargs.get('plugin_uuid', wtypes.Unset))


class InjectionCollection(collection.Collection):
    """API representation of a collection of injection."""

    injections = [InjectionPlugin]

    def __init__(self, **kwargs):
        self._type = 'injections'

    @staticmethod
    def get_list(injections, fields=None):
        collection = InjectionCollection()
        collection.injections = [InjectionPlugin(**n.as_dict())
                                 for n in injections]
        return collection


class ExposedService(base.APIBase):
    service = types.uuid_or_name
    board_uuid = types.uuid_or_name
    public_port = wsme.types.IntegerType()

    def __init__(self, **kwargs):
        self.fields = []
        fields = list(objects.ExposedService.fields)
        fields.remove('board_uuid')
        for k in fields:
            # Skip fields we do not expose.
            if not hasattr(self, k):
                continue
            self.fields.append(k)
            setattr(self, k, kwargs.get(k, wtypes.Unset))
        setattr(self, 'service', kwargs.get('service_uuid', wtypes.Unset))


class ExposedCollection(collection.Collection):
    """API representation of a collection of injection."""

    exposed = [ExposedService]

    def __init__(self, **kwargs):
        self._type = 'exposed'

    @staticmethod
    def get_list(exposed, fields=None):
        collection = ExposedCollection()
        collection.exposed = [ExposedService(**n.as_dict())
                              for n in exposed]
        return collection


class PluginAction(base.APIBase):
    action = wsme.wsattr(wtypes.text)
    parameters = types.jsontype


class ServiceAction(base.APIBase):
    action = wsme.wsattr(wtypes.text)
    parameters = types.jsontype


class Network(base.APIBase):
    network = types.jsontype
    subnet = types.jsontype
    security_groups = types.jsontype


class BoardPluginsController(rest.RestController):
    def __init__(self, board_ident):
        self.board_ident = board_ident

    def _get_plugins_on_board_collection(self, authorized_board_plugins,
                                         board_uuid, fields=None):
        injections = objects.InjectionPlugin.list(pecan.request.context,
                                                  authorized_board_plugins,
                                                  board_uuid)

        return InjectionCollection.get_list(injections,
                                            fields=fields)

    @expose.expose(InjectionCollection,
                   status_code=200)
    def get_all(self):
        """Retrieve a list of plugins of a board.

        """
        rpc_board = api_utils.get_rpc_board(self.board_ident)

        authorized_board_plugins = authorization.authorize('board:plugin_get')

        return self._get_plugins_on_board_collection(authorized_board_plugins,
                                                     rpc_board.uuid)

    @expose.expose(wtypes.text, types.uuid_or_name, body=PluginAction,
                   status_code=200)
    def post(self, plugin_ident, PluginAction):

        if not PluginAction.action:
            raise exception.MissingParameterValue(
                ("Action is not specified."))

        if not PluginAction.parameters:
            PluginAction.parameters = {}

        rpc_board = api_utils.get_rpc_board(self.board_ident)
        rpc_plugin = api_utils.get_rpc_plugin(plugin_ident)

        authorization.authorize('board:plugin_post', rpc_board.uuid)
        if not rpc_plugin.public:
            authorization.authorize('plugin:post', rpc_plugin.uuid)

        rpc_board.check_if_online()

        if objects.plugin.want_customs_params(PluginAction.action):
            valid_keys = list(rpc_plugin.parameters.keys())
            if not all(k in PluginAction.parameters for k in valid_keys):
                raise exception.InvalidParameterValue(
                    "Parameters are different from the valid ones")

        result = pecan.request.rpcapi.action_plugin(pecan.request.context,
                                                    rpc_plugin.uuid,
                                                    rpc_board.uuid,
                                                    PluginAction.action,
                                                    PluginAction.parameters)
        return result

    @expose.expose(wtypes.text, body=InjectionPlugin,
                   status_code=200)
    def put(self, Injection):
        """inject a plugin into a board.

        :param plugin_ident: UUID or logical name of a plugin.
        :param board_ident: UUID or logical name of a board.
        """

        if not Injection.plugin:
            raise exception.MissingParameterValue(
                ("Plugin is not specified."))

        if not Injection.onboot:
            Injection.onboot = False

        rpc_board = api_utils.get_rpc_board(self.board_ident)
        rpc_plugin = api_utils.get_rpc_plugin(Injection.plugin)

        authorization.authorize('board:plugin_put', rpc_board.uuid)
        if not rpc_plugin.public:
            authorization.authorize('plugin:put', rpc_plugin.uuid)

        rpc_board.check_if_online()
        result = pecan.request.rpcapi.inject_plugin(pecan.request.context,
                                                    rpc_plugin.uuid,
                                                    rpc_board.uuid,
                                                    Injection.onboot)
        return result

    @expose.expose(wtypes.text, types.uuid_or_name,
                   status_code=204)
    def delete(self, plugin_uuid):
        """Remove a plugin from a board.

        :param plugin_ident: UUID or logical name of a plugin.
        :param board_ident: UUID or logical name of a board.
        """
        rpc_board = api_utils.get_rpc_board(self.board_ident)
        authorization.authorize('board:plugin_delete', rpc_board.uuid)

        rpc_board.check_if_online()
        rpc_plugin = api_utils.get_rpc_plugin(plugin_uuid)
        return pecan.request.rpcapi.remove_plugin(pecan.request.context,
                                                  rpc_plugin.uuid,
                                                  rpc_board.uuid)


class BoardServicesController(rest.RestController):
    _custom_actions = {
        'action': ['POST'],
        'restore': ['GET']
    }

    def __init__(self, board_ident):
        self.board_ident = board_ident

    def _get_services_on_board_collection(self, board_uuid, fields=None):
        services = objects.ExposedService.list(pecan.request.context,
                                               board_uuid)

        return ExposedCollection.get_list(services,
                                          fields=fields)

    @expose.expose(ExposedCollection,
                   status_code=200)
    def get_all(self):
        """Retrieve a list of services of a board.

        """
        rpc_board = api_utils.get_rpc_board(self.board_ident)
        authorization.authorize('board:service_get', rpc_board.uuid)

        return self._get_services_on_board_collection(rpc_board.uuid)

    @expose.expose(wtypes.text, types.uuid_or_name, body=ServiceAction,
                   status_code=200)
    def action(self, service_ident, ServiceAction):

        if not ServiceAction.action:
            raise exception.MissingParameterValue(
                ("Action is not specified."))

        rpc_board = api_utils.get_rpc_board(self.board_ident)
        authorization.authorize('board:service_action', rpc_board.uuid)

        rpc_service = api_utils.get_rpc_service(service_ident)
        rpc_board.check_if_online()

        result = pecan.request.rpcapi.action_service(pecan.request.context,
                                                     rpc_service.uuid,
                                                     rpc_board.uuid,
                                                     ServiceAction.action)
        return result

    @expose.expose(ExposedCollection,
                   status_code=200)
    def restore(self):
        rpc_board = api_utils.get_rpc_board(self.board_ident)
        authorization.authorize('board:service_restore', rpc_board.uuid)

        rpc_board.check_if_online()

        pecan.request.rpcapi.restore_services_on_board(
            pecan.request.context,
            rpc_board.uuid)

        return self._get_services_on_board_collection(rpc_board.uuid)


class BoardWebservicesController(rest.RestController):
    _custom_actions = {
        'enable': ['POST'],
        'disable': ['DELETE']
    }

    invalid_sort_key_list = ['extra', ]

    def __init__(self, board_ident):
        self.board_ident = board_ident

    def _get_webservices_collection(self, authorized_webservices, board,
                                    marker, limit, sort_key, sort_dir,
                                    fields=None):

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
        filters['board_uuid'] = board
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

        rpc_board = api_utils.get_rpc_board(self.board_ident)

        filters = {}
        filters['board_uuid'] = rpc_board.uuid

        if fields is None:
            fields = _DEFAULT_WEBSERVICE_RETURN_FIELDS
        return self._get_webservices_collection(authorized_webservices,
                                                rpc_board.uuid, marker,
                                                limit, sort_key, sort_dir,
                                                fields=fields)

    @expose.expose(Webservice, body=Webservice, status_code=201)
    def put(self, Webservice):
        """Create a new Webservice.

        :param Webservice: a Webservice within the request body.
        """
        rpc_board = api_utils.get_rpc_board(self.board_ident)
        authorization.authorize('board:webservice_create', rpc_board.uuid)

        if not Webservice.name:
            raise exception.MissingParameterValue(
                ("Name is not specified."))

        if Webservice.name:
            if not api_utils.is_valid_name(Webservice.name):
                msg = ("Cannot create webservice with invalid name %(name)s")
                raise wsme.exc.ClientSideError(msg % {'name': Webservice.name},
                                               status_code=400)

        new_Webservice = objects.Webservice(pecan.request.context,
                                            **Webservice.as_dict())

        new_Webservice.board_uuid = rpc_board.uuid
        new_Webservice = pecan.request.rpcapi.create_webservice(
            pecan.request.context,
            new_Webservice)

        # add delegation
        new_Delegation = objects.Delegation(pecan.request.context)
        new_Delegation.uuid = uuidutils.generate_uuid()
        new_Delegation.delegated = pecan.request.context.user_id
        new_Delegation.role = 'owner'
        new_Delegation.node = new_Webservice.uuid
        new_Delegation.type = 'webservice'
        new_Delegation.create()

        return Webservice.convert_with_links(new_Webservice)

    class EnabledWebserverData(base.APIBase):
        dns = wtypes.text
        zone = wtypes.text
        email = wtypes.text

    @expose.expose(EnabledWebservice, body=EnabledWebserverData,
                   status_code=201)
    def enable(self, EnabledWebserverData):
        """Create a new Webservice.

        :param Webservice: a Webservice within the request body.
        """

        rpc_board = api_utils.get_rpc_board(self.board_ident)
        # authorization.authorize('board:webservice_enable', rpc_board.uuid)

        if not EnabledWebserverData.dns:
            raise exception.MissingParameterValue(
                ("dns is not specified."))
        if not EnabledWebserverData.zone:
            raise exception.MissingParameterValue(
                ("zone is not specified."))
        if not EnabledWebserverData.email:
            raise exception.MissingParameterValue(
                ("email is not specified."))

        new_EnWebservice = pecan.request.rpcapi.enable_webservice(
            pecan.request.context,
            EnabledWebserverData.dns,
            EnabledWebserverData.zone,
            EnabledWebserverData.email,
            rpc_board.uuid)

        return EnabledWebservice.convert_with_links(new_EnWebservice)

    @expose.expose(None, status_code=204)
    def disable(self):
        """Disable webservices in a board.

        :param board_ident: UUID or logical name of a board.
        """

        rpc_board = api_utils.get_rpc_board(self.board_ident)
        # authorization.authorize('board:webservice_disable', rpc_board.uuid)

        pecan.request.rpcapi.disable_webservice(pecan.request.context,
                                                rpc_board.uuid)


class BoardPortsController(rest.RestController):

    def __init__(self, board_ident):
        self.board_ident = board_ident

    def _get_ports_on_board_collection(self, board_uuid, fields=None):
        filters = {}
        filters['board_uuid'] = board_uuid
        ports = objects.Port.list(pecan.request.context,
                                  filters=filters)

        return PortCollection.get_list(ports, fields=fields)

    def get_port_detail(self, board_uuid, port_uuid):
        filters = {}
        filters['board_uuid'] = board_uuid
        ports = objects.Port.list(pecan.request.context,
                                  filters=filters)
        for port in ports:
            if port.uuid == port_uuid:
                return port

    @expose.expose(wtypes.text, types.uuid_or_name, body=Network,
                   status_code=200)
    def put(self, Network):

        if not Network.network:
            raise exception.MissingParameterValue(
                ("Network is not specified."))

        rpc_board = api_utils.get_rpc_board(self.board_ident)

        rpc_board.check_if_online()

        result = pecan.request.rpcapi. \
            create_port_on_board(pecan.request.context, rpc_board.uuid,
                                 Network.network, Network.subnet,
                                 Network.security_groups)
        return result

    @expose.expose(wtypes.text, types.uuid_or_name,
                   status_code=204)
    def delete(self, port):

        if not port:
            raise exception.MissingParameterValue(
                ("Port is not specified."))

        rpc_board = api_utils.get_rpc_board(self.board_ident)
        # authorization.authorize('board:port_delete', rpc_board.uuid)
        rpc_port = api_utils.get_rpc_port(port)

        rpc_board.check_if_online()

        result = pecan.request.rpcapi.remove_port_from_board(
            pecan.request.context, rpc_board.uuid, rpc_port.uuid)

        return result

    @expose.expose(PortCollection, status_code=200)
    def get_all(self):

        rpc_board = api_utils.get_rpc_board(self.board_ident)
        authorization.authorize('board:port_get', rpc_board.uuid)

        return self._get_ports_on_board_collection(rpc_board.uuid)

    @expose.expose(Port, types.uuid_or_name, status_code=200)
    def get_one(self, port_ident):

        rpc_board = api_utils.get_rpc_board(self.board_ident)
        authorization.authorize('board:port_get_one', rpc_board.uuid)

        return self.get_port_detail(rpc_board, port_ident)


class BoardsController(rest.RestController):
    """REST controller for Boards."""

    _subcontroller_map = {
        'plugins': BoardPluginsController,
        'services': BoardServicesController,
        'ports': BoardPortsController,
        'webservices': BoardWebservicesController,
    }

    invalid_sort_key_list = ['extra', 'location']

    _custom_actions = {
        'detail': ['GET'],
    }

    @pecan.expose()
    def _lookup(self, ident, *remainder):
        try:
            ident = types.uuid_or_name.validate(ident)
        except exception.InvalidUuidOrName as e:
            pecan.abort('400', e.args[0])
        if not remainder:
            return

        subcontroller = self._subcontroller_map.get(remainder[0])
        if subcontroller:
            return subcontroller(board_ident=ident), remainder[1:]

    def _get_boards_collection(self, authorized_boards, status, marker, limit,
                               sort_key, sort_dir,
                               project=None,
                               resource_url=None, fields=None):

        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)

        marker_obj = None
        if marker:
            marker_obj = objects.Board.get_by_uuid(pecan.request.context,
                                                   marker)

        if sort_key in self.invalid_sort_key_list:
            raise exception.InvalidParameterValue(
                ("The sort_key value %(key)s is an invalid field for "
                 "sorting") % {'key': sort_key})

        filters = {}

        # bounding the request to a project
        if project:
            filters['project_id'] = project
        else:
            filters['project_id'] = pecan.request.context.project_id

        if status:
            filters['status'] = status

        boards = objects.Board.list(pecan.request.context, authorized_boards,
                                    limit, marker_obj, sort_key=sort_key,
                                    sort_dir=sort_dir, filters=filters)

        parameters = {'sort_key': sort_key, 'sort_dir': sort_dir}

        return BoardCollection.convert_with_links(boards, limit,
                                                  url=resource_url,
                                                  fields=fields,
                                                  **parameters)

    @expose.expose(Board, types.uuid_or_name, types.listtype)
    def get_one(self, board_ident, fields=None):
        """Retrieve information about the given board.

        :param board_ident: UUID or logical name of a board.
        :param fields: Optional, a list with a specified set of fields
            of the resource to be returned.
        """

        rpc_board = api_utils.get_rpc_board(board_ident)
        authorization.authorize('board:get_one', rpc_board.uuid)

        return Board.convert_with_links(rpc_board, fields=fields)

    @expose.expose(BoardCollection, wtypes.text, types.uuid, int, wtypes.text,
                   wtypes.text, types.listtype, wtypes.text)
    def get_all(self, status=None, marker=None,
                limit=None, sort_key='id', sort_dir='asc',
                fields=None, project=None):
        """Retrieve a list of boards.

        :param status: Optional string value to get only board in
                                that status.
        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
                      This value cannot be larger than the value of max_limit
                      in the [api] section of the ironic configuration, or only
                      max_limit resources will be returned.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        :param fields: Optional, a list with a specified set of fields
                       of the resource to be returned.
        """
        authorized_boards = authorization.authorize('board:get')

        if fields is None:
            fields = _DEFAULT_RETURN_FIELDS
        return self._get_boards_collection(authorized_boards, status, marker,
                                           limit, sort_key, sort_dir,
                                           fields=fields, project=project)

    @expose.expose(Board, body=Board, status_code=201)
    def post(self, Board):
        """Create a new Board.

        :param Board: a Board within the request body.
        """
        authorization.authorize('board:create')

        if not Board.name:
            raise exception.MissingParameterValue(
                ("Name is not specified."))
        if not Board.code:
            raise exception.MissingParameterValue(
                ("Code is not specified."))
        if not Board.location:
            raise exception.MissingParameterValue(
                ("Location is not specified."))

        if Board.name:
            if not api_utils.is_valid_board_name(Board.name):
                msg = ("Cannot create board with invalid name %(name)s")
                raise wsme.exc.ClientSideError(msg % {'name': Board.name},
                                               status_code=400)

        new_Board = objects.Board(pecan.request.context,
                                  **Board.as_dict())

        new_Board.owner = pecan.request.context.user_id
        new_Board.project = pecan.request.context.project_id

        new_Location = objects.Location(pecan.request.context,
                                        **Board.location[0].as_dict())

        new_Board = pecan.request.rpcapi.create_board(pecan.request.context,
                                                      new_Board, new_Location)
        # add delegation
        new_Delegation = objects.Delegation(pecan.request.context)
        new_Delegation.uuid = uuidutils.generate_uuid()
        new_Delegation.delegated = pecan.request.context.user_id
        new_Delegation.role = 'owner'
        new_Delegation.node = new_Board.uuid
        new_Delegation.type = 'board'
        new_Delegation.create()

        return Board.convert_with_links(new_Board)

    @expose.expose(None, types.uuid_or_name, status_code=204)
    def delete(self, board_ident):
        """Delete a board.

        :param board_ident: UUID or logical name of a board.
        """

        rpc_board = api_utils.get_rpc_board(board_ident)
        authorization.authorize('board:delete', rpc_board.uuid)

        pecan.request.rpcapi.destroy_board(pecan.request.context,
                                           rpc_board.uuid)

        # remove all board delegations
        objects.Delegation.destroy_by_node_uuid(
            pecan.request.context, rpc_board.uuid, 'board')

    @expose.expose(Board, types.uuid_or_name, body=Board, status_code=200)
    def patch(self, board_ident, val_Board):
        """Update a board.

        :param board_ident: UUID or logical name of a board.
        :param Board: values to be changed
        :return updated_board: updated_board
        """

        board = api_utils.get_rpc_board(board_ident)
        authorization.authorize('board:update', board.uuid)

        val_Board = val_Board.as_dict()
        for key in val_Board:
            try:
                board[key] = val_Board[key]
            except Exception:
                pass

        updated_board = pecan.request.rpcapi.update_board(
            pecan.request.context,
            board)
        return Board.convert_with_links(updated_board)

    @expose.expose(BoardCollection, wtypes.text, types.uuid, int, wtypes.text,
                   wtypes.text, types.listtype, wtypes.text)
    def detail(self, status=None, marker=None,
               limit=None, sort_key='id', sort_dir='asc',
               fields=None, project=None):
        """Retrieve a list of boards.

        :param status: Optional string value to get only board in
                                that status.
        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
                      This value cannot be larger than the value of max_limit
                      in the [api] section of the ironic configuration, or only
                      max_limit resources will be returned.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        :param project: Optional string value to get only boards
                        of the project.
        :param fields: Optional, a list with a specified set of fields
                       of the resource to be returned.
        """

        authorized_boards = authorization.authorize('board:get')

        # /detail should only work against collections
        parent = pecan.request.path.split('/')[:-1][-1]
        if parent != "boards":
            raise exception.HTTPNotFound()

        return self._get_boards_collection(authorized_boards, status, marker,
                                           limit, sort_key, sort_dir,
                                           project=project, fields=fields)
