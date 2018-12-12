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
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.it_aruba import ArubaCloudAPI


def detail(srvlist):
    a = "DatacenterId"  # 1
    b = "ServerId"      # 29265
    c = "OSTemplateId"  # 1723
    d = "ServerStatus"  # 2 - Off, 3 - On
    e = "Busy"          # false,
    f = "HypervisorType"  # 4 = Smart
    g = "Name"          # "La
    h = "CPUQuantity"   # 1
    i = "RAMQuantity"   # 1
    keys = (a, b, c, d, e, f, g, h, i)
    servers = []
    for server in srvlist:
        if all(k in server for k in keys):
            if server[f] == 4:
                if   server[h] == 1 and server[i] == 1:
                    typ = "S"
                elif server[h] == 1 and server[i] == 2:
                    typ = "M"
                elif server[h] == 2 and server[i] == 4:
                    typ = "L"
                elif server[h] == 4 and server[i] == 8:
                    typ = "X"
                else:
                    typ = "C"+str(server[h])+"R"+str(server[i])
            else:
                typ = "H"+str(server[f])+"C"+str(server[h])+"R"+str(server[i])
            det = dict(
                DC=server[a],
                id=server[b],
                templateId=server[b],
                isON=(server[d] == 3),
                busy=server[e],
                kind=typ
            )
        else:
            det = dict()
        servers.append(det)
    return servers


def core(module):
    cmd = "GetServers"
    api = ArubaCloudAPI(module)
    response = api.post(dc="dc1", cmd=cmd)
    status_code = response.status_code
    json = response.json
    sva = "Value"
    suc = "Success"
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
