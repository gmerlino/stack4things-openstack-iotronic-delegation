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


from iotronicclient.common import utils
from iotronicclient.v1 import board_shell
from iotronicclient.v1 import delegation_shell
from iotronicclient.v1 import exposed_service_shell
from iotronicclient.v1 import fleet_shell
from iotronicclient.v1 import plugin_injection_shell
from iotronicclient.v1 import plugin_shell
from iotronicclient.v1 import port_shell
from iotronicclient.v1 import user_shell
from iotronicclient.v1 import role_shell
from iotronicclient.v1 import service_shell
from iotronicclient.v1 import webservice_shell

COMMAND_MODULES = [
    user_shell,
    role_shell,
    delegation_shell,
    board_shell,
    plugin_shell,
    plugin_injection_shell,
    service_shell,
    exposed_service_shell,
    port_shell,
    fleet_shell,
    webservice_shell,
]


def enhance_parser(parser, subparsers, cmd_mapper):
    """Enhance parser with API version specific options.

    Take a basic (nonversioned) parser and enhance it with
    commands and options specific for this version of API.

    :param parser: top level parser
    :param subparsers: top level parser's subparsers collection
                       where subcommands will go
    """
    for command_module in COMMAND_MODULES:
        utils.define_commands_from_module(subparsers, command_module,
                                          cmd_mapper)
