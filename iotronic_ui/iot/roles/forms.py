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


class CreateRoleForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Role Name"))
    permissions = forms.CharField(
        label=_("Permissions"),
        widget=forms.SelectMultiple(
            attrs={'class': 'switchable',
                   'data-slug': 'source',
                   'style': 'height:160px;', }),
        help_text=_("Role permissions")
    )
    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(
            attrs={'class': 'switchable', 'style': 'height:80px;'}),
        help_text=_("Role description"),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(CreateRoleForm, self).__init__(*args, **kwargs)
        choices = [(i, _(i)) for i in kwargs["initial"]["opers"]]
        self.fields["permissions"].widget.choices = choices

    def handle(self, request, data):
        try:
            perms = str(data["permissions"].encode('ascii').split(
                ',')).replace('u\'', '').replace('\'', '').replace(' ', '')
            iotronic.role_create(request, {"name": data["name"],
                                           "permissions": perms,
                                           "description": data["description"]})
            messages.success(request, _("Role created successfully."))
            return True
        except Exception as ex:
            exceptions.handle(request, _('Unable to create role.\n') + str(ex))


class UpdateRoleForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Role Name"))
    permissions = forms.CharField(
        label=_("Permissions"),
        widget=forms.SelectMultiple(
            attrs={'class': 'switchable',
                   'data-slug': 'source',
                   'style': 'height:160px;', }),
        help_text=_("Role permissions")
    )
    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(
            attrs={'class': 'switchable', 'style': 'height:80px;'}),
        help_text=_("Role description"),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(UpdateRoleForm, self).__init__(*args, **kwargs)
        choices = [(i, _(i)) for i in kwargs["initial"]["opers"]]
        self.fields["permissions"].widget.choices = choices
        self.fields["permissions"].initial = kwargs["initial"]["curr_perms"]
        self.fields["name"].widget.attrs = {'readonly': 'readonly'}

    def handle(self, request, data):

        try:
            perms = str(data["permissions"].encode('ascii').split(
                ',')).replace('u\'', '').replace('\'', '').replace(' ', '')
            iotronic.role_update(request, data["name"],
                                 {"permissions": perms,
                                  "description": data["description"]})
            messages.success(request, _("Role updated successfully."))
            return True

        except Exception as ex:
            exceptions.handle(request, _('Unable to update role.\n') + str(ex))
