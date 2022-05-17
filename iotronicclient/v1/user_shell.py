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


def _print_user_show(user, fields=None, json=False):
    if fields is None:
        fields = res_fields.USER_DETAILED_RESOURCE.fields

    data = dict(
        [(f, getattr(user, f, '')) for f in fields])
    cliutils.print_dict(data, wrap=72, json_flag=json)


@cliutils.arg(
    'user',
    metavar='<user>',
    help="Name or UUID of the user ")
@cliutils.arg(
    '--fields',
    nargs='+',
    dest='fields',
    metavar='<field>',
    action='append',
    default=[],
    help="One or more user fields. Only these fields will be fetched from "
         "the server.")
def do_user_show(cc, args):
    """Show detailed information about a user."""
    fields = args.fields[0] if args.fields else None
    utils.check_empty_arg(args.user, '<user>')
    utils.check_for_invalid_fields(
        fields, res_fields.USER_DETAILED_RESOURCE.fields)
    user = cc.user.get(args.user, fields=fields)
    _print_user_show(user, fields=fields, json=args.json)


@cliutils.arg(
    '--limit',
    metavar='<limit>',
    type=int,
    help='Maximum number of users to return per request, '
         '0 for no limit. Default is the maximum number used '
         'by the Iotronic API Service.')
@cliutils.arg(
    '--marker',
    metavar='<user>',
    help='User UUID (for example, of the last user in the list from '
         'a previous request). Returns the list of users after this UUID.')
@cliutils.arg(
    '--sort-key',
    metavar='<field>',
    help='User field that will be used for sorting.')
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
    help="Show detailed information about the users.")
@cliutils.arg(
    '--fields',
    nargs='+',
    dest='fields',
    metavar='<field>',
    action='append',
    default=[],
    help="One or more user fields. Only these fields will be fetched from "
         "the server. Can not be used when '--detail' is specified.")
def do_user_list(cc, args):
    """List the users which are registered with the Iotronic service."""
    params = {}

    if args.detail:
        fields = res_fields.USER_DETAILED_RESOURCE.fields
        field_labels = res_fields.USER_DETAILED_RESOURCE.labels
    elif args.fields:
        utils.check_for_invalid_fields(
            args.fields[0], res_fields.USER_DETAILED_RESOURCE.fields)
        resource = res_fields.Resource(args.fields[0])
        fields = resource.fields
        field_labels = resource.labels
    else:
        fields = res_fields.USER_RESOURCE.fields
        field_labels = res_fields.USER_RESOURCE.labels

    sort_fields = res_fields.USER_DETAILED_RESOURCE.sort_fields
    sort_field_labels = res_fields.USER_DETAILED_RESOURCE.sort_labels

    params.update(utils.common_params_for_list(args,
                                               sort_fields,
                                               sort_field_labels))

    users = cc.user.list(**params)
    cliutils.print_list(users, fields,
                        field_labels=field_labels,
                        sortby_index=None,
                        json_flag=args.json)


@cliutils.arg(
    'uuid',
    metavar='<uuid>',
    help="UUID of the user")
@cliutils.arg(
    'name',
    metavar='<name>',
    help="Name of the user")
@cliutils.arg(
    'base_role',
    metavar='<base_role>',
    help="Base Role of the user")
def do_user_create(cc, args):
    """Register a new user with the Iotronic service."""

    field_list = ['uuid', 'name', 'base_role']

    fields = dict((k, v) for (k, v) in vars(args).items()
                  if k in field_list and not (v is None))

    user = cc.user.create(**fields)

    data = dict([(f, getattr(user, f, '')) for f in
                 res_fields.USER_DETAILED_RESOURCE.fields])

    cliutils.print_dict(data, wrap=72, json_flag=args.json)


@cliutils.arg('user',
              metavar='<user>',
              nargs='+',
              help="Name or UUID of the user.")
def do_user_delete(cc, args):
    """Unregister user(s) from the Iotronic service.

    Returns errors for any users that could not be unregistered.
    """

    failures = []
    for n in args.user:
        try:
            cc.user.delete(n)
            print(_('Deleted user %s') % n)
        except exceptions.ClientException as e:
            failures.append(_("Failed to delete user %(user)s: %(error)s")
                            % {'user': n, 'error': e})
    if failures:
        raise exceptions.ClientException("\n".join(failures))


@cliutils.arg('user', metavar='<user>', help="Name or UUID of the user.")
@cliutils.arg(
    'attributes',
    metavar='<path=value>',
    nargs='+',
    action='append',
    default=[],
    help="Values to be changed.")
def do_user_update(cc, args):
    """Update information about a registered user."""

    patch = {k: v for k, v in (x.split('=') for x in args.attributes[0])}

    user = cc.user.update(args.user, patch)
    _print_user_show(user, json=args.json)
