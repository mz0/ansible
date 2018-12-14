#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
'''

EXAMPLES = '''
'''

RETURN = '''
srv:
    description: Aruba Cloud Smart server create(view)/delete/re-init
    returned: success and no resource constraint
    type: dict
    sample: {
              "DC": 5,
              "busy": false,
              "id": 29652,
              "isON": true,
              "kind": "S",
              "image": 448,
              "ip": "192.168.2.1",
              "ipv6":"2001:DB8::1",
              "charge":"2018....11:00"
              "created":"2016....11:00"
            }
    ]
'''

import time
import traceback
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.it_aruba import ArubaCloudAPI


class SmartVM(object):
    def __init__(self, module):
        self.api = ArubaCloudAPI(module)
        self.module = module
        self.wait = self.module.params.pop('wait', True)
        self.wait_time = self.module.params.pop('wait_time', 120)
        self.name = self.module.params.pop('name')
        self.id = self.module.params.pop('id')

    def get_by_id(self, server_id):
        if not server_id:
            return None
        cmd = "GetServerDetails"
        xd  = dict(ServerId=server_id)
        response = self.api.post(self.module.params['dc'], cmd, xd)
        json = response.json
        sva = 'Value'
        suc = 'Success'
        if response.status_code == 200 and sva in json and suc in json and json[suc]:
            return json
        return None

    def get_vm(self):
        json_data = self.get_by_id(self.module.params['id'])
        if not json_data and self.name:
            json_data = self.get_by_name(self.name)
        return json_data

    def powerOff(self, server_id):
        cmd = "SetEnqueueServerPowerOff"
        xd = dict(ServerId=server_id)
        response = self.api.post(self.module.params['dc'], cmd, xd)

        if self.wait:
            end_time = time.time() + self.wait_time
            while time.time() < end_time:
                json_data = response.json
                if json_data['droplet']['status'] == 'active':
                    return json_data
                time.sleep(min(2, end_time - time.time()))
            self.module.fail_json(msg='Power-off wait time is over.')

    def drop(self, wait=True):
        json_data = self.get_vm()
        if json_data:
            if self.module.check_mode:
                self.module.exit_json(changed=True)
         #  if response.status_code == 200:
         #      self.module.exit_json(changed=True, msg='VM deleted')
            self.module.fail_json(changed=False, msg='Failed to delete VM (besides, not implemented!')
        else:
            self.module.exit_json(changed=False, msg='VM not found')

    def reinit(self, wait=True):
        json_data = self.get_vm()
        if json_data:
            if self.module.check_mode:
                self.module.exit_json(changed=True)

    def down(self):
        json_data = self.get_vm()
        if json_data:
            if self.module.check_mode:
                self.module.exit_json(changed=True)
         #  if response.status_code == 200:
         #      ?
            self.module.fail_json(changed=False, msg='Failed to power-off VM (besides, not implemented!')
        else:
            self.module.exit_json(changed=False, msg='VM not found')


def core(module):
    state = module.params.pop('state')
    vm = SmartVM(module)
    if state == 'present':
        vm.up()
    elif state == 'absent':
        vm.down(wait=vm.wait)
        vm.drop(wait=vm.wait)
    elif state == 'offline':
        vm.down(wait=vm.wait)
    elif state == 'pristine':
        vm.down(wait=True)
        vm.reinit(wait=vm.wait)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            user=dict(required=True),
            password=dict(no_log=True, required=True),
            timeout=dict(type='int', default=90),
            dc=dict(type='int', required=True),
            state=dict(choices=['present', 'absent', 'offline', 'pristine'], default='offline'),
            name=dict(type='str'),
            id=dict(type='int', default=None),
            wait=dict(type='bool', default=True),
            image=dict(type='int'),
            pubkey=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
