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


class CreateServiceForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Service Name"))
    port = forms.IntegerField(
        label=_("Port"),
        help_text=_("Service port")
    )

    protocol = forms.ChoiceField(
        label=_("Protocol"),
        choices=[('TCP', _('TCP')), ('UDP', _('UDP'))],
        widget=forms.Select(
            attrs={'class': 'switchable', 'data-slug': 'slug-protocol'},
        )
    )

    def handle(self, request, data):
        try:
            iotronic.service_create(request, data["name"],
                                    data["port"], data["protocol"])

            messages.success(request, _("Service " + str(data["name"]) +
                                        " created successfully."))
            return True

        except Exception:
            exceptions.handle(request, _('Unable to create service.'))


class UpdateServiceForm(forms.SelfHandlingForm):
    uuid = forms.CharField(label=_("Service ID"), widget=forms.HiddenInput)
    name = forms.CharField(label=_("Service Name"))
    port = forms.IntegerField(label=_("Port"))
    protocol = forms.ChoiceField(
        label=_("Protocol"),
        choices=[('TCP', _('TCP')), ('UDP', _('UDP'))],
        widget=forms.Select(
            attrs={'class': 'switchable', 'data-slug': 'slug-protocol'},
        )
    )

    def __init__(self, *args, **kwargs):

        super(UpdateServiceForm, self).__init__(*args, **kwargs)

        # Admin
        if policy.check((("iot", "iot:update_services"),), self.request):
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
                self.fields["port"].widget.attrs = {'readonly': 'readonly'}
                self.fields["protocol"].widget.attrs = {'readonly': 'readonly'}

    def handle(self, request, data):
        try:
            iotronic.service_update(request, data["uuid"],
                                    {"name": data["name"],
                                     "port": data["port"],
                                     "protocol": data["protocol"]})

            messages.success(request, _("Service updated successfully."))
            return True

        except Exception:
            exceptions.handle(request, _('Unable to update service.'))


class ServiceActionForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Plugin ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Service Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    board_list = forms.MultipleChoiceField(
        label=_("Boards List"),
        widget=forms.SelectMultiple(
            attrs={'class': 'switchable', 'data-slug': 'slug-select-boards'}),
        help_text=_("Select boards in this pool")
    )

    action = forms.ChoiceField(
        label=_("Action"),
        choices=[('ServiceEnable', _('Enable')),
                 ('ServiceDisable', _('Disable')),
                 ('ServiceRestore', _('Restore'))],
        widget=forms.Select(
            attrs={'class': 'switchable', 'data-slug': 'slug-action'},
        )
    )

    def __init__(self, *args, **kwargs):

        super(ServiceActionForm, self).__init__(*args, **kwargs)
        # input=kwargs.get('initial',{})

        self.fields["board_list"].choices = kwargs["initial"]["board_list"]

    def handle(self, request, data):

        counter = 0

        for board in data["board_list"]:
            for key, value in self.fields["board_list"].choices:
                if key == board:

                    try:
                        action = iotronic.service_action(request, key,
                                                         data["uuid"],
                                                         data["action"])
                        message_text = action
                        messages.success(request, _(message_text))

                        if counter != len(data["board_list"]) - 1:
                            counter += 1
                        else:
                            return True

                    except Exception:
                        message_text = "Unable to execute action on board " \
                                       + str(value) + "."
                        exceptions.handle(request, _(message_text))

                    break

# Delegation


class UpdateServiceDelegationForm(forms.SelfHandlingForm):
    service = forms.CharField(label=_("Service ID"), widget=forms.HiddenInput)
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
        super(UpdateServiceDelegationForm, self).__init__(*args, **kwargs)
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


class DeleteServiceDelegationForm(forms.SelfHandlingForm):
    service = forms.CharField(label=_("Service ID"))
    delegation = forms.CharField(label=_("Delegation ID"))

    def __init__(self, *args, **kwargs):
        super(DeleteServiceDelegationForm, self).__init__(*args, **kwargs)
        self.fields["service"].widget.attrs = {'readonly': 'readonly'}
        self.fields["delegation"].widget.attrs = {'readonly': 'readonly'}

    def handle(self, request, data):
        try:
            iotronic.node_delete_delegation(request, data["delegation"])
            messages.success(request, _("Delegation deleted successfully."))
            return True

        except Exception as ex:
            exceptions.handle(request, _(
                'Unable to delete delegation.\n') + str(ex))


class ServiceDelegateForm(forms.SelfHandlingForm):

    service_uuid = forms.CharField(label=_("Service ID"))
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
        super(ServiceDelegateForm, self).__init__(*args, **kwargs)
        self.fields["role"].choices = [
            (rl.name, _(rl.name)) for rl in kwargs["initial"]["roles"]
        ]
        self.fields["user"].choices = [
            (us.uuid, _(us.uuid + ' (' + us.name + ')')) for us in
            kwargs["initial"]["users"]
        ]
        self.fields["service_uuid"].widget.attrs = {'readonly': 'readonly'}

    def handle(self, request, data):
        try:
            iotronic.node_create_delegation(request, data['service_uuid'],
                                            {'delegated': data['user'],
                                             'role': data['role'],
                                             'type': 'service'})
            messages.success(request, _("Delegation created."))
            return True

        except Exception as ex:
            message_text = "Unable to create delegation.\n" + str(ex)
            exceptions.handle(request, _(message_text))
