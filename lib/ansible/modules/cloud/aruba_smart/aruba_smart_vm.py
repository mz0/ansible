#!/usr/bin/python

# Copyright: (c) 2018, Mark Zhitomirsky <mz@exactpro.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: aruba_smart_vm

short_description: This is my sample module

version_added: "2.8"

description:
    - "This is my longer description explaining my sample module"

options:
    user:
        description:
            - Aruba Cloud ClientID
        required: true
    password:
        description:
            - Aruba Cloud management password
        required: true
    dc:
        description:
            - List of DCs or DC name
        required: false
    size:
        description:
            - choose one of S,M,L,XL (vCPU-RAM-SSD-Traffic, Eur per month)
            - S - 1-1GB-020GB-02TB, 2.79
            - M - 1-2GB-040GB-05TB, 4.50
            - L - 2-4GB-080GB-12TB, 8.50
            - XL- 4-8GB-160GB-25TB, 15.0
    root_pw:
        description:
            - root password, will be auto-generated?
        required: false

extends_documentation_fragment:
    - aruba_cloud

author:
    - Mark Zhitomirski (@mz0)
'''

EXAMPLES = '''
# list VMs
- name: Test with a message and changed output
  aruba_smart_vm:
    name: hello world
    new: true
'''

RETURN = '''
data:
    description: List of VMs
    type: dict
sample: { FIXME
}
'''
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


class Response(object):

    def __init__(self, resp, info):
        self.body = None
        if resp:
            self.body = resp.read()
        self.info = info

    @property
    def json(self):
        if not self.body:
            if "body" in self.info:
                return json.loads(self.info["body"])
            return None
        try:
            return json.loads(self.body)
        except ValueError:
            return None

    @property
    def status_code(self):
        return self.info["status"]


class ArubaCloudAPI(object):

    def __init__(self, module, headers):
        self.module = module
        self.headers = headers
        self.auser = module.params.get('user')
        self.passwd = module.params.get('password')
        self.timeout = module.params.get('timeout', 30)
        self.tpl_url = "https://api.{0}.computing.cloud.it/WsEndUser/v2.9/WsEndUser.svc/json/{1}"

    def _url_builder(self, dc, cmd):
        return self.tpl_url.format(dc, cmd)

    def send(self, method, dc, cmd, data=None):
        url = self._url_builder(dc, cmd)
        data = self.module.jsonify(data)
        timeout = self.module.params['timeout']
        headers = {'Content-Type': 'application/json', 'Content-Length': str(len(data))}
        resp, info = fetch_url(self.module, url, data=data, headers=headers, method=method, timeout=timeout)

        # Exceptions in fetch_url may result in a status -1, the ensures a
        if info['status'] == -1:
            self.module.fail_json(msg=info['msg'])

        return Response(resp, info)

    def post(self, dc, cmd, data=None):
        return self.send('POST', dc, cmd, data, headers)


def core(module):
    auser = module.params['user']
    apassw = module.params['password']
#   state = module.params['state']
#   name = module.params['name']
#   ssh_pub_key = module.params['ssh_pub_key']
    cmd = "GetServers"
    cmd_data = '{{"ApplicationId": "{}", "RequestId": "{}", "SessionId": "{}", "Password": "{}", "Username": "{}"}}'\
        .format(cmd,cmd,cmd,apassw,auser)
    reqest = ArubaCloudAPI(module, "dc1", cmd, cmd_data)

    module.exit_json(**result)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            name=dict(required=False),
            ssh_pub_key=dict(required=False),
            creds=dict(
                no_log=True,
                required=True,
            ),
            validate_certs=dict(type='bool', default=True),
            timeout=dict(type='int', default=30),
        ),
        required_one_of=(
            ('fingerprint', 'ssh_pub_key'),
        ),
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
