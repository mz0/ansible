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
              "dc": 5,
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
        self.dc = self.module.params.pop('dc')
        self.wait = self.module.params.pop('wait', True)
        self.wait_time = self.module.params.pop('wait_time', 120)
        self.name = self.module.params.pop('name')
        self.id = self.module.params.pop('id')
        self.isON = None
        self.busy = False
        self.det1 = None

    def get_by_id(self, server_id):
        if not server_id:
            return None
        cmd = "GetServerDetails"
        xd  = dict(ServerId=server_id)
        response = self.api.post(self.dc, cmd, xd)
        json = response.json
        sva = 'Value'
        suc = 'Success'
        if response.status_code == 200 and sva in json and suc in json and json[suc]:
            return json
        return None

    def get_by_name(self, name):
        if not name:
            return None
        servers = self.api.get_servers(self.dc)
        byname = [s for s in servers if s['name'] == name]
        if len(byname) == 1:
            return byname[0]
        elif len(byname) == 0:
            self.module.fail_json(msg='VM not found by name')
        elif len(byname) > 1:
            self.module.fail_json(msg='This Server name is not unique! More then 1 found')
        return None

    def get_vm(self):
        det1 = self.get_by_id(self.id)
        if not det1 and self.name:
            det1 = self.get_by_name(self.name)
        z = 'dc'
        i = 'id'
        o = 'isON'
        b = 'busy'
        n = 'name'
        keys = (z, i, o, b, n)
        if det1 and  all(k in det1 for k in keys):
            self.id   = det1[i]
            self.name = det1[n]
            self.isON = det1[o]
            self.busy = det1[b]
        return det1

    def powerOff(self, server_id):
        if not self.isON:
            self.module.exit_json(changed=False, srv='VM not found')
        cmd = "SetEnqueueServerPowerOff"
        xd = dict(ServerId=server_id)
        response = self.api.post(self.dc, cmd, xd)
        if self.wait:
            end_time = time.time() + self.wait_time
            while time.time() < end_time:
                json_data = response.json
                if json_data['droplet']['status'] == 'active':
                    return json_data
                time.sleep(min(2, end_time - time.time()))
            self.module.fail_json(msg='Power-off wait time is over.')

    def down(self, wait):
        json_data = self.get_vm()
        if json_data:
            if self.isON:
                self.powerOff(self.id, wait)
            else:
                self.module.exit_json(changed=False, srv=json_data)
        else:
            self.module.fail_json(changed=False, msg='VM not found')


def core(module):
    state = module.params.pop('state')
    vm = SmartVM(module)
    if state == 'offline':
        vm.down(wait=vm.wait)


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
        ),
        supports_check_mode=True,
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
