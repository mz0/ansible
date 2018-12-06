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

    def __init__(self, module):
        self.module = module
        self.auser = module.params.get('user')
        self.passwd = module.params.get('password')
        self.timeout = module.params.get('timeout', 30)
        self.tpl_url = "https://api.{0}.computing.cloud.it/WsEndUser/v2.9/WsEndUser.svc/json/{1}"

    def _url_builder(self, dc, cmd):
        return self.tpl_url.format(dc, cmd)

    def send(self, method, dc, cmd, data):
        url = self._url_builder(dc, cmd)
        data = self.module.jsonify(data)
        timeout = self.module.params['timeout']
        headers = {'Content-Type': 'application/json', 'Content-Length': str(len(data))}
        resp, info = fetch_url(self.module, url, data=data, headers=headers, method=method, timeout=timeout)

        return Response(resp, info)

    def post(self, dc, cmd, data):
        return self.send('POST', dc, cmd, data)


def core(module):
    auser = module.params['user']
    apassw = module.params['password']
    state = module.params['state']
#   name = module.params['name']
#   ssh_pub_key = module.params['ssh_pub_key']
    cmd = "GetServers"
    cmd_data = '{{"ApplicationId": "{}", "RequestId": "{}", "SessionId": "{}", "Password": "{}", "Username": "{}"}}'\
        .format(cmd, cmd, cmd, apassw, auser)
    api = ArubaCloudAPI(module)
    response = api.post(dc="dc1", cmd=cmd, data=cmd_data)
    json1 = response.json
    module.exit_json(changed=False, data=json1)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent', 'fresh'], default='present'),
            user=dict(required=True),
            password=dict(no_log=True, required=True),
            timeout=dict(type='int', default=30),
        ),
        supports_check_mode=False,
    )

    core(module)


if __name__ == '__main__':
    main()
