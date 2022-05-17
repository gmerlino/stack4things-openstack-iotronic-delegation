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
from iotronicclient.common import utils
from iotronicclient.v1 import resource_fields as res_fields


def _print_role_show(role, fields=None, json=False):
    if fields is None:
        fields = res_fields.ROLE_DETAILED_RESOURCE.fields

    data = dict(
        [(f, getattr(role, f, '')) for f in fields])
    cliutils.print_dict(data, wrap=72, json_flag=json)


@cliutils.arg(
    'role',
    metavar='<name>',
    help="Name of the role")
@cliutils.arg(
    '--fields',
    nargs='+',
    dest='fields',
    metavar='<field>',
    action='append',
    default=[],
    help="One or more role fields. Only these fields will be fetched from "
         "the server.")
def do_role_show(cc, args):
    """Show detailed information about a role."""
    fields = args.fields[0] if args.fields else None
    utils.check_empty_arg(args.role, '<name>')
    utils.check_for_invalid_fields(
        fields, res_fields.ROLE_DETAILED_RESOURCE.fields)
    role = cc.role.get(args.role, fields=fields)
    _print_role_show(role, fields=fields, json=args.json)


@cliutils.arg(
    '--limit',
    metavar='<limit>',
    type=int,
    help='Maximum number of roles to return per request, '
         '0 for no limit. Default is the maximum number used '
         'by the Iotronic API Service.')
@cliutils.arg(
    '--marker',
    metavar='<role>',
    help='Role UUID (for example, of the last role in the list from '
         'a previous request). Returns the list of roles after this UUID.')
@cliutils.arg(
    '--sort-key',
    metavar='<field>',
    help='Role field that will be used for sorting.')
@cliutils.arg(
    '--sort-dir',
    metavar='<direction>',
    choices=['asc', 'desc'],
    help='Sort direction: "asc" (the default) or "desc".')
@cliutils.arg(
    '--detail',
    dest='detail',
    action='store_true',
    default=False,
    help="Show detailed information about the roles.")
@cliutils.arg(
    '--fields',
    nargs='+',
    dest='fields',
    metavar='<field>',
    action='append',
    default=[],
    help="One or more role fields. Only these fields will be fetched from "
         "the server. Can not be used when '--detail' is specified.")
def do_role_list(cc, args):
    """List the roles which are registered with the Iotronic service."""
    params = {}

    if args.detail:
        fields = res_fields.ROLE_DETAILED_RESOURCE.fields
        field_labels = res_fields.ROLE_DETAILED_RESOURCE.labels
    elif args.fields:
        utils.check_for_invalid_fields(
            args.fields[0], res_fields.ROLE_DETAILED_RESOURCE.fields)
        resource = res_fields.Resource(args.fields[0])
        fields = resource.fields
        field_labels = resource.labels
    else:
        fields = res_fields.ROLE_RESOURCE.fields
        field_labels = res_fields.ROLE_RESOURCE.labels

    sort_fields = res_fields.ROLE_DETAILED_RESOURCE.sort_fields
    sort_field_labels = res_fields.ROLE_DETAILED_RESOURCE.sort_labels

    params.update(utils.common_params_for_list(args,
                                               sort_fields,
                                               sort_field_labels))

    roles = cc.role.list(**params)
    cliutils.print_list(roles, fields,
                        field_labels=field_labels,
                        sortby_index=None,
                        json_flag=args.json)


@cliutils.arg(
    'name',
    metavar='<name>',
    help="Name of the role")
@cliutils.arg(
    'permissions',
    metavar='<base_role>',
    help="Base Role of the role")
@cliutils.arg(
    '--description',
    metavar='<description>',
    help='Description of the role.')
def do_role_create(cc, args):
    """Register a new role with the Iotronic service."""

    field_list = ['name', 'permissions', 'description']

    fields = dict((k, v) for (k, v) in vars(args).items()
                  if k in field_list and not (v is None))

    role = cc.role.create(**fields)

    data = dict([(f, getattr(role, f, '')) for f in
                 res_fields.ROLE_DETAILED_RESOURCE.fields])

    cliutils.print_dict(data, wrap=72, json_flag=args.json)


@cliutils.arg('role',
              metavar='<name>',
              nargs='+',
              help="Name or UUID of the role.")
def do_role_delete(cc, args):
    """Unregister role(s) from the Iotronic service.

    Returns errors for any roles that could not be unregistered.
    """

    failures = []
    for n in args.role:
        try:
            cc.role.delete(n)
            print(_('Deleted role %s') % n)
        except exceptions.ClientException as e:
            failures.append(_("Failed to delete role %(role)s: %(error)s")
                            % {'role': n, 'error': e})
    if failures:
        raise exceptions.ClientException("\n".join(failures))


@cliutils.arg('role', metavar='<role>', help="Name or UUID of the role.")
@cliutils.arg(
    'attributes',
    metavar='<path=value>',
    nargs='+',
    action='append',
    default=[],
    help="Values to be changed.")
def do_role_update(cc, args):
    """Update information about a registered role."""

    patch = {k: v for k, v in (x.split('=') for x in args.attributes[0])}

    role = cc.role.update(args.role, patch)
    _print_role_show(role, json=args.json)


def do_operations_list(cc, args):
    """Get the operations list."""

    ops = cc.role.get_operations()
    print([str(op) for op in ops])
