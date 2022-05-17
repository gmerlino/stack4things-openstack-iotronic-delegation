# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import iotronic

LOG = logging.getLogger(__name__)


class CreateUserForm(forms.SelfHandlingForm):
    uuid = forms.ChoiceField(
        label=_("User"),
        widget=forms.Select(
            attrs={'class': 'switchable', 'data-slug': 'source'}),
        help_text=_("Select a User Id")
    )
    base_role = forms.ChoiceField(
        label=_("Base Role List"),
        widget=forms.Select(
            attrs={'class': 'switchable', 'data-slug': 'type_list'}),
        help_text=_("Select a User base role")
    )

    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        roles = kwargs["initial"]["roles"]
        users = kwargs["initial"]["users"]
        roles_name = []
        users_id = []
        for role in roles:
            roles_name.append((role.name, _(role.name)))
        for user in users:
            users_id.append((user.id + ':' + user.name,
                             str(user.id) + ' (' + str(user.name) + ')'))
        self.fields["base_role"].choices = roles_name
        self.fields["uuid"].choices = users_id

    def handle(self, request, data):
        try:
            uid, name = data["uuid"].split(':')
            iotronic.user_create(
                request, {"uuid": uid, "name": name,
                          "base_role": data["base_role"]})
            messages.success(request, _("User created successfully."))
            return True

        except Exception as ex:
            exceptions.handle(request, _('Unable to create user.\n')
                              + str(ex))


class UpdateUserForm(forms.SelfHandlingForm):
    uuid = forms.CharField(label=_("User ID"))
    name = forms.CharField(label=_("User Name"))
    base_role = forms.ChoiceField(
        label=_("Base Role List"),
        widget=forms.Select(
            attrs={'class': 'switchable', 'data-slug': 'type_list'}),
        help_text=_("Select a User base role")
    )

    def __init__(self, *args, **kwargs):
        super(UpdateUserForm, self).__init__(*args, **kwargs)
        current_role = kwargs["initial"]["current_role"]
        roles = kwargs["initial"]["roles"]
        roles_name = []
        for role in roles:
            roles_name.append((role.name, _(role.name)))
        self.fields["base_role"].choices = roles_name
        self.fields["base_role"].initial = current_role
        self.fields["uuid"].widget.attrs = {'readonly': 'readonly'}
        self.fields["name"].widget.attrs = {'readonly': 'readonly'}

    def handle(self, request, data):

        try:

            iotronic.user_update(request, data["uuid"],
                                 {"base_role": data["base_role"]})
            messages.success(request, _("User updated successfully."))
            return True

        except Exception as ex:
            exceptions.handle(request, _('Unable to update user.\n') + str(ex))
