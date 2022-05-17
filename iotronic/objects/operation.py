# coding=utf-8
#
#
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

from iotronic.db import api as db_api
from iotronic.objects import base
from iotronic.objects import utils as obj_utils


class Operation(base.IotronicObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = db_api.get_instance()

    fields = {
        'name': obj_utils.str_or_none,
        'description': obj_utils.str_or_none
    }

    @staticmethod
    def _from_db_object(ops, db_ops):
        """Converts a database entity to a formal object."""
        for field in ops.fields:
            ops[field] = db_ops[field]
        ops.obj_reset_changes()
        return ops

    @base.remotable_classmethod
    def oplist(cls, context, limit=None, sort_key=None, sort_dir=None,
               filters=None):
        """Return a list of Operation objects.

        :param context: Security context.
        :param limit: maximum number of resources to return in a single result.
        :param filters: Filters to apply.
        :returns: a list of :class:`Operation` object.

        """
        db_ops = cls.dbapi.get_ops_list(filters=filters, limit=limit,
                                        sort_key=sort_key,
                                        sort_dir=sort_dir)
        return [Operation._from_db_object(cls(context), obj) for obj in db_ops]
