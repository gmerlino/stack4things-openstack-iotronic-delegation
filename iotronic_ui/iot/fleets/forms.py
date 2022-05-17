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
from openstack_dashboard import policy

LOG = logging.getLogger(__name__)


class CreateFleetForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Fleet Name"))

    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(
            attrs={'class': 'switchable', 'data-slug': 'slug-description'})
    )

    def handle(self, request, data):
        try:
            iotronic.fleet_create(request, data["name"],
                                  data["description"])

            messages.success(request, _("Fleet " + str(data["name"]) +
                                        " created successfully."))
            return True

        except Exception:
            exceptions.handle(request, _('Unable to create fleet.'))


class UpdateFleetForm(forms.SelfHandlingForm):
    uuid = forms.CharField(label=_("Fleet ID"), widget=forms.HiddenInput)
    name = forms.CharField(label=_("Fleet Name"))
    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(
            attrs={'class': 'switchable', 'data-slug': 'slug-description'})
    )

    def __init__(self, *args, **kwargs):

        super(UpdateFleetForm, self).__init__(*args, **kwargs)

        # Admin
        if policy.check((("iot", "iot:update_fleets"),), self.request):
            # LOG.debug("ADMIN")
            pass

        # Manager or Admin of the iot project
        elif (policy.check((("iot", "iot_manager"),), self.request) or
              policy.check((("iot", "iot_admin"),), self.request)):
            # LOG.debug("NO-edit IOT ADMIN")
            pass

        # Other users
        else:
            if self.request.user.id != kwargs["initial"]["owner"]:
                # LOG.debug("IMMUTABLE FIELDS")
                self.fields["name"].widget.attrs = {'readonly': 'readonly'}
                self.fields["description"].widget.attrs = {
                    'readonly': 'readonly'}

    def handle(self, request, data):
        try:
            iotronic.fleet_update(request, data["uuid"],
                                  {"name": data["name"],
                                   "description": data["description"]})

            messages.success(request, _("Fleet updated successfully."))
            return True

        except Exception:
            exceptions.handle(request, _('Unable to update fleet.'))

# Delegation


class UpdateFleetDelegationForm(forms.SelfHandlingForm):
    fleet = forms.CharField(label=_("Fleet ID"), widget=forms.HiddenInput)
    delegation = forms.CharField(
        label=_("Delegation ID"), widget=forms.HiddenInput)
    delegated = forms.CharField(label=_("Delegated ID"))
    delegator = forms.CharField(label=_("Delegator Name"))
    role = forms.ChoiceField(
        label=_("Base Role List"),
        widget=forms.Select(
            attrs={'class': 'switchable', 'data-slug': 'slug-role'}),
        help_text=_("Select a User base role")
    )

    def __init__(self, *args, **kwargs):
        super(UpdateFleetDelegationForm, self).__init__(*args, **kwargs)
        self.fields["delegated"].widget.attrs = {'readonly': 'readonly'}
        self.fields["delegator"].widget.attrs = {'readonly': 'readonly'}
        current_role = kwargs["initial"]["current_role"]
        roles = kwargs["initial"]["roles"]
        roles_name = []
        for rl in roles:
            roles_name.append((rl.name, _(rl.name)))
        self.fields["role"].choices = roles_name
        self.fields["role"].initial = current_role

    def handle(self, request, data):
        try:
            iotronic.node_update_delegation(request, data["delegation"],
                                            {"role": data["role"]})
            messages.success(request, _("Delegation updated successfully."))
            return True

        except Exception as ex:
            exceptions.handle(request, _(
                'Unable to update delegation.\n') + str(ex))


class DeleteFleetDelegationForm(forms.SelfHandlingForm):
    fleet = forms.CharField(label=_("Fleet ID"))
    delegation = forms.CharField(label=_("Delegation ID"))

    def __init__(self, *args, **kwargs):
        super(DeleteFleetDelegationForm, self).__init__(*args, **kwargs)
        self.fields["fleet"].widget.attrs = {'readonly': 'readonly'}
        self.fields["delegation"].widget.attrs = {'readonly': 'readonly'}

    def handle(self, request, data):
        try:
            iotronic.node_delete_delegation(request, data["delegation"])
            messages.success(request, _("Delegation deleted successfully."))
            return True

        except Exception as ex:
            exceptions.handle(request, _(
                'Unable to delete delegation.\n') + str(ex))


class FleetDelegateForm(forms.SelfHandlingForm):

    fleet_uuid = forms.CharField(label=_("Fleet ID"))
    user = forms.ChoiceField(
        label=_("User List"),
        widget=forms.Select(
            attrs={'class': 'switchable', 'data-slug': 'slug-user'}),
        help_text=_("Select a User")
    )
    role = forms.ChoiceField(
        label=_("Role List"),
        widget=forms.Select(
            attrs={'class': 'switchable', 'data-slug': 'slug-role'}),
        help_text=_("Select a role")
    )

    def __init__(self, *args, **kwargs):
        super(FleetDelegateForm, self).__init__(*args, **kwargs)
        self.fields["role"].choices = [
            (rl.name, _(rl.name)) for rl in kwargs["initial"]["roles"]
        ]
        self.fields["user"].choices = [
            (us.uuid, _(us.uuid + ' (' + us.name + ')')) for us in
            kwargs["initial"]["users"]
        ]
        self.fields["fleet_uuid"].widget.attrs = {'readonly': 'readonly'}

    def handle(self, request, data):
        try:
            iotronic.node_create_delegation(request, data['fleet_uuid'],
                                            {'delegated': data['user'],
                                             'role': data['role'],
                                             'type': 'fleet'})
            messages.success(request, _("Delegation created."))
            return True

        except Exception as ex:
            message_text = "Unable to create delegation.\n" + str(ex)
            exceptions.handle(request, _(message_text))
