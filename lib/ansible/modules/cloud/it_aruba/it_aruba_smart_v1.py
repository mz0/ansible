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
              "image": 448,
              "ip": "192.168.2.1",
              "ipv6":"2001:DB8::1",
              "charge":"2018....11:00"
              "created":"2016....11:00"
              "size": "S",
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
        self.wait = self.module.params.pop('wait')
        self.wait_time = self.module.params.pop('wait_time')
        self.name = self.module.params.pop('name')
        self.id = self.module.params.pop('id')
        self.isON = None
        self.busy = None
        self.det1 = None
        self.cmdQ = None

    def get_by_id(self, server_id):
        if not server_id:
            return None
        return self.api.get_server(self.dc, server_id)

    def get_by_name(self):
        n = self.name
        servers = self.api.get_servers(self.dc)
        byname = [s for s in servers if s['name'] == n]
        if len(byname) == 1:
            return byname[0]
        elif len(byname) == 0:
            return None
        elif len(byname) > 1:
            self.module.fail_json(msg='Server name {} is not unique in DC{}! More then 1 found'.format(n, self.dc))
        return None

    def get_vm(self):
        det1 = self.get_by_id(self.id)
        if not det1 and self.name:
            det1 = self.get_by_name()
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
        else:
            return None

    def waitOK(self):
        end_time = time.time() + self.wait_time
        while time.time() < end_time:
            time.sleep(min(2, end_time - time.time()))
            self.get_vm()
            if self.busy is not None and not self.busy: return True
        return False

    def powerOff(self, server_id, wait=False):
        if self.busy is not None and self.busy and not self.waitOK():
            self.module.fail_json(msg='Server was busy, wait_time is over.')
        cmd = "SetEnqueueServerPowerOff"
        xd = dict(ServerId=server_id)
        r = self.api.post(self.dc, cmd, xd)
        suc = 'Success'
        if r.status_code==200 and suc in r.json and r.json[suc]:
            pass
        else:
            self.module.fail_json(msg='VM turn Off error:{}'.format(r.body))
        if not wait:
            self.module.exit_json(changed=True, srv=self.api.get_server(self.dc, server_id))
        else:
            if self.waitOK():
                self.module.exit_json(changed=True, srv=self.api.get_server(self.dc, server_id))
            else:
                self.module.fail_json(msg='VM turn Off wait time is over. Response was:{}'.format(r.json))

    def down(self, wait):
        json_data = self.get_vm()
        if json_data:
            if self.isON:
                self.powerOff(self.id, wait)
            else:
                self.module.exit_json(changed=False, srv=json_data)
        else:
            self.module.fail_json(changed=False, msg='VM not found')

    def createVM(self):
        self.module.fail_json(changed=False, msg='VM {} in DC{} not found. '
                'createVM is not implemented yet!'.format(self.name, self.dc))

    def powerON(self, server_id, wait=False):
        if self.busy is not None and self.busy and not self.waitOK():
            self.module.fail_json(msg='Server was busy, wait_time is over. Not turning ON!')
        cmd = "SetEnqueueServerStart"
        xd = dict(ServerId=server_id)
        r = self.api.post(self.dc, cmd, xd)
        suc = 'Success'
        if r.status_code==200 and suc in r.json and r.json[suc]:
            pass
        else:
            self.module.fail_json(msg='VM turn ON error:{}'.format(r.body))
        if not wait:
            self.module.exit_json(changed=True, srv=self.api.get_server(self.dc, server_id))
        else:
            if self.waitOK():
                self.module.exit_json(changed=True, srv=self.api.get_server(self.dc, server_id))
            else:
                self.module.fail_json(msg='VM turn Off wait time is over. Response was:{}'.format(r.json))

    def up(self, wait):
        json_data = self.get_vm()
        if json_data:
            if self.isON is not None:
                if self.isON:
                    self.module.exit_json(changed=False, srv=json_data)
                else:
                    self.powerON(self.id, wait)
        else:
            self.createVM()

def core(module):
    state = module.params.pop('state')
    vm = SmartVM(module)
    if state == 'offline':
        vm.down(wait=vm.wait)
    if state == 'present':
        vm.up(wait=vm.wait)


def main():
    argument_spec = ArubaCloudAPI.it_aruba_argument_spec()
    argument_spec.update(dict(
            state=dict(choices=['present', 'absent', 'offline', 'pristine'], default='offline'),
            name=dict(type='str'),
            id=dict(type='int', default=None),
            wait=dict(type='bool', default=False),
            wait_time=dict(type='int', default=77),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()

'''
powerOff(..,wait=False) =>
"jobs": [
                {
                    "CreationDate": "/Date(1544909024817+0100)/",
                    "JobId": 862231,
                    "LastUpdateDate": "/Date(1544909024817+0100)/",
                    "LicenseId": null,
                    "OperationName": "StopVirtualMachineSmartVMWare",
                    "Progress": 0,
                    "ResourceId": null,
                    "ResourceValue": null,
                    "ServerId": 1265,
                    "ServerName": "de1",
                    "Status": 1,
                    "UserId": 70331,
                    "Username": "AWI-71331"
                }
            ]

powerON(..,wait=False) =>
"jobs": [
                {
                    "CreationDate": "/Date(1544973491997+0100)/",
                    "JobId": 8022656,
                    "LastUpdateDate": "/Date(1544973491997+0100)/",
                    "LicenseId": null,
                    "OperationName": "StartVirtualMachineSmartVMWare",
                    "Progress": 0,
                    "ResourceId": null,
                    "ResourceValue": null,
                    "ServerId": 1265,
                    "ServerName": "de1",
                    "Status": 1,
                    "UserId": 70331,
                    "Username": "AWI-71331"
                }
            ]
'''
