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
    description: Aruba Cloud Smart servers
    returned: success and no resource constraint
    type: list
    sample: [
         {
              "DC": 5,
              "busy": false,
              "id": 29652,
              "isON": true,
              "kind": "S",
              "templateId": 448
         }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.it_aruba import ArubaCloudAPI, detail1


def detail(srvlist):
    servers = []
    for server in srvlist:
        servers.append(detail1(server))
    return servers


def core(module):
    cmd = "GetServers"
    api = ArubaCloudAPI(module)
    response = api.post(dc=module.params['dc'], cmd=cmd)
    status_code = response.status_code
    json = response.json
    sva = 'Value'
    suc = 'Success'
    if status_code == 200 and sva in json and suc in json and json[suc]:
        servers = detail(json[sva])
        module.exit_json(changed=False, srv=servers)
    else:
        module.fail_json(msg='Error fetching facts [{0}: {1}]'.format(
            status_code, response.json['message']))


def main():
    module = AnsibleModule(
        argument_spec=ArubaCloudAPI.it_aruba_argument_spec(),
        supports_check_mode=False,
    )

    core(module)


if __name__ == '__main__':
    main()
