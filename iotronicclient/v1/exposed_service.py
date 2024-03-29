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
from iotronicclient.common.i18n import _
from iotronicclient.common import utils
from iotronicclient import exc


LOG = logging.getLogger(__name__)
_DEFAULT_POLL_INTERVAL = 2


class ExposedService(base.Resource):
    def __repr__(self):
        return "<ExposedService %s>" % self._info


class ExposedServiceManager(base.Manager):
    resource_class = ExposedService
    _resource_name = 'boards'

    def services_on_board(self, board_ident, marker=None, limit=None,
                          detail=False, sort_key=None, sort_dir=None,
                          fields=None):
        """Retrieve the list of services on the board.

        :param board_ident: the UUID or name of the board.

        :param marker: Optional, the UUID of a board, eg the last
                       board from a previous result set. Return
                       the next result set.
        :param limit: The maximum number of results to return per
                      request, if:

            1) limit > 0, the maximum number of boards to return.
            2) limit == 0, return the entire list of boards.
            3) limit param is NOT specified (None), the number of items
               returned respect the maximum imposed by the Iotronic API
               (see Iotronic's api.max_limit option).

        :param detail: Optional, boolean whether to return detailed information
                       about boards.

        :param sort_key: Optional, field used for sorting.

        :param sort_dir: Optional, direction of sorting, either 'asc' (the
                         default) or 'desc'.

        :param fields: Optional, a list with a specified set of fields
                       of the resource to be returned. Can not be used
                       when 'detail' is set.

        :returns: A list of services injected on a board.

        """
        if limit is not None:
            limit = int(limit)

        if detail and fields:
            raise exc.InvalidAttribute(_("Can't fetch a subset of fields "
                                         "with 'detail' set"))

        filters = utils.common_filters(marker, limit, sort_key, sort_dir,
                                       fields)

        path = "%s/services" % board_ident

        if filters:
            path += '?' + '&'.join(filters)

        if limit is None:
            return self._list(self._path(path), "exposed")
        else:
            return self._list_pagination(self._path(path), "exposed",
                                         limit=limit)

    def service_action(self, board_ident, service_ident, action):
        if service_ident:
            path = "%(board)s/services/%(service)s/action" % \
                   {'board': board_ident,
                    'service': service_ident}
        else:
            path = "%(board)s/services/restore" % {
                'board': board_ident}

        body = {"action": action
                }
        return self._update(path, body, method='POST')

    def restore_services(self, board_ident):

        path = "%(board)s/services/restore" % {
            'board': board_ident}
        return self._list(self._path(path), "exposed")
