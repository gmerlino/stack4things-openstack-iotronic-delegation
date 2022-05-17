# Copyright (c) 2011 OpenStack Foundation
# All Rights Reserved.
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

"""Policy Engine For Ironic."""

from iotronic.db import api as db_api

from iotronic.common import exception
from iotronic.common import policy
from oslo_config import cfg
from oslo_log import log
import pecan
CONF = cfg.CONF
LOG = log.getLogger(__name__)

# NOTE(deva): We can't call these methods from within decorators because the
# 'target' and 'creds' parameter must be fetched from the call time
# context-local pecan.request magic variable, but decorators are compiled
# at module-load time.


def authorize(operation, target=None):
    """
    Checks authorization of a operation, and
    raises an exception if the rule is not defined.
    Always returns true if CONF.auth_strategy == noauth.
    """

    user = pecan.request.environ['HTTP_X_USER_ID']
    dbapi = db_api.get_instance()
    type, op = operation.split(':')
    cdict = pecan.request.context.to_policy_values()

    # Authorization with base role or policy
    if type == 'user' or type == 'role':
        try:
            user = dbapi.get_user_details(user)
            permissions = dbapi.get_role_permissions(
                user.base_role).permissions
            for perm in permissions:
                ptype, pop = perm.split(':')
                if (ptype == type) and (pop == op or pop == 'all'):
                    return
        except exception.UserNotFound:
            pass
        policy.authorize('iot:'+type+':'+op, cdict, cdict)
        # raise exception.HTTPForbidden(resource=operation)
    if op == 'create':
        try:
            user = dbapi.get_user_details(user)
            permissions = dbapi.get_role_permissions(
                user.base_role).permissions
            for perm in permissions:
                ptype, pop = perm.split(':')
                if (ptype == type or ptype == 'all') and (pop == op
                                                          or pop == 'all'):
                    return
        except exception.UserNotFound:
            pass
        policy.authorize('iot:'+type+':'+op, cdict, cdict)
        # raise exception.HTTPForbidden(resource=operation)

    # Authorization with delegation role
    if not target:
        authorized_nodes = []
        delegations = dbapi.get_node_delegations(user_uuid=user, type=type)
        for dele in delegations:
            if(dele.role == 'owner'):
                authorized_nodes.append(dele.node)
                continue
            permissions = dbapi.get_role_permissions(dele.role).permissions
            for perm in permissions:
                ptype, pop = perm.split(':')
                if (ptype == type or ptype == 'all') and (pop == op
                                                          or pop == 'all'):
                    authorized_nodes.append(dele.node)
                    break
        return authorized_nodes
    else:
        delegation = dbapi.get_node_delegation(user, type, target)
        if(delegation.role == 'owner'):
            return True
        permissions = dbapi.get_role_permissions(delegation.role).permissions
        for perm in permissions:
            ptype, pop = perm.split(':')
            if (ptype == type or ptype == 'all') and (pop == op
                                                      or pop == 'all'):
                return
        raise exception.HTTPForbidden(resource=target)
