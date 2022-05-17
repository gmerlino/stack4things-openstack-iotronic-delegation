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

from iotronicclient.common.apiclient import exceptions
from iotronicclient.common import cliutils
from iotronicclient.common.i18n import _
from iotronicclient.v1 import resource_fields as res_fields


@cliutils.arg('delegation', metavar='<delegation>',
              help="UUID of the delegation.")
def do_delegation_show(cc, args):
    """Show detailed information about a delegation."""
    delegation = cc.delegation.get(args.delegation)
    data = dict([(f, getattr(delegation, f, '')) for f in
                 res_fields.DELEGATION_DETAILED_RESOURCE.fields])
    cliutils.print_dict(data, wrap=72, json_flag=args.json)


@cliutils.arg('delegation', metavar='<delegation>', nargs='+',
              help="UUID of the delegation to delete.")
def do_delegation_delete(cc, args):
    """Unregister delegations for a resource."""
    failures = []
    for n in args.delegation:
        try:
            cc.delegation.delete(n)
            print(_('Deleted delegation %s') % n)
        except exceptions.ClientException as e:
            failures.append(_("Failed to delete delegation " +
                              "%(delegation)s: %(error)s")
                            % {'delegation': n, 'error': e})
    if failures:
        raise exceptions.ClientException("\n".join(failures))


@cliutils.arg('delegation', metavar='<delegated>',
              help="UUID of the delegation to update.")
@cliutils.arg('role', metavar='<role>',
              help="Role to assign on this resource.")
def do_delegation_update(cc, args):
    """Update a delegation for a resource."""
    field_list = ['role']

    fields = dict((k, v) for (k, v) in vars(args).items()
                  if k in field_list and not (v is None))

    delegation = cc.delegation.update(args.delegation, **fields)
    data = dict([(f, getattr(delegation, f, '')) for f in
                 res_fields.DELEGATION_DETAILED_RESOURCE.fields])
    cliutils.print_dict(data, wrap=72, json_flag=args.json)
