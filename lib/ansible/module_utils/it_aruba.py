# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Ansible Project 2018
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import json
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_text


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
                return json.loads(to_text(self.info["body"]))
            return None
        try:
            return json.loads(to_text(self.body))
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

    def send(self, method, dc, cmd, xtra_data):
        url = self._url_builder(dc, cmd)
        cmd_data = '{{"ApplicationId": "{}", "RequestId": "{}", "SessionId": "{}", "Password": "{}", "Username": "{}"' \
                   '}}'.format(cmd, cmd, cmd, self.passwd, self.auser)

        # data = self.module.jsonify(data)
        timeout = self.module.params['timeout']
        headers = {'Content-Type': 'application/json', 'Content-Length': str(len(cmd_data))}
        resp, info = fetch_url(self.module, url, data=cmd_data, headers=headers, method=method, timeout=timeout)
        return Response(resp, info)

    def post(self, dc, cmd, xtra_data=''):
        return self.send('POST', dc, cmd, xtra_data)

    @staticmethod
    def it_aruba_argument_spec():
        return dict(
            validate_certs=dict(type='bool', required=False, default=True),
            user=dict(required=True),
            password=dict(no_log=True, required=True),
            timeout=dict(type='int', default=60),
        )
