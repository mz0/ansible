# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright: (c) 2018 Mark Zhitomirski <marcuzero0gmail.com>
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
from datetime import datetime


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


def hmn(aruba_ts):
    """
    :param aruba_ts: string like "/Date(1544909024817+0100)/"
    :return: Human-readable date-time "2018-12-15T21:23:44"
    """
    return datetime.utcfromtimestamp(int(aruba_ts[6:16])).isoformat('T')


def detail2(server):
    z = "DatacenterId"  # 1
    i = "ServerId"      # 2926
    n = "Name"
    a = "ActiveJobs"    # []
    b = "CreationDate"
    c = "EasyCloudIPAddress"
    ci = "Value"
    d = "NetworkAdapters"
    dd = "IPAddresses"
    dd6 = "StartRangeIPv6"
    dm = "MacAddress"
    t = "OSTemplate"
    ti = "Id"
    tn = "Name"
    r = "RenewDateSmart"
    s = "ServerStatus"  # 2 - Off, 3 - On
    sz = "EasyCloudPackageID" # 1
    keys = (a, b, d, t, r, sz)
    if all(k in server for k in keys):
        szi = {
            1: "S",
            6: "M",
            7: "L",
            8: "X",
            9:  "M",
            10: "L",
            11: "X",
        }
        return dict(
            dc=server[z],
            id=server[i],
            name=server[n],
            templateId=server[t][ti],
            tplateName=server[t][tn],
            isON=(server[s] == 3),
            busy=True if (len(server[a]) > 0) else False,
            size=szi.get(server[sz]),
            jobs=server[a],
            MAC=server[d][0][dm],
            ip6=server[d][0][dd][0][dd6],
            ip4=server[c][ci],
            created=hmn(server[b]),
            recharge=hmn(server[r]),
        )
    else:
        return None


def detail1(server):
    z = "DatacenterId"  # 1
    i = "ServerId"      # 2926
    t = "OSTemplateId"  # 1723
    s = "ServerStatus"  # 2 - Off, 3 - On
    b = "Busy"          # false
    h = "HypervisorType"  # 4 = Smart
    n = "Name"
    c = "CPUQuantity"   # 1
    r = "RAMQuantity"   # 1
    keys = (z, i, t, s, b, h, n, c, r)
    if all(k in server for k in keys):
        if server[h] == 4:
            if   server[c] == 1 and server[r] == 1:
                size = "S"
            elif server[c] == 1 and server[r] == 2:
                size = "M"
            elif server[c] == 2 and server[r] == 4:
                size = "L"
            elif server[c] == 4 and server[r] == 8:
                size = "X"
            else:
                size = "Smart-Unknown-C" + str(server[c]) + "R" + str(server[r])
        else:
            size = "H" + str(server[h]) + "C" + str(server[c]) + "R" + str(server[r])
        det = dict(
            dc=server[z],
            id=server[i],
            name=server[n],
            templateId=server[t],
            isON=(server[s] == 3),
            busy=server[b],
            size=size
        )
    else:
        det = dict()
    return det


class ArubaCloudAPI(object):

    def __init__(self, module):
        self.module = module
        self.auser = module.params.get('user')
        self.passwd = module.params.get('password')
        self.timeout = module.params.get('timeout', 30)
        self.tpl_url = "https://api.dc{0}.computing.cloud.it/WsEndUser/v2.9/WsEndUser.svc/json/{1}"

    def _url_builder(self, dc, cmd):
        return self.tpl_url.format(dc, cmd)

    def send(self, method, dc, cmd, xtra_data):
        url = self._url_builder(dc, cmd)
        cmdict = dict(
            ApplicationId=cmd,
            RequestId    =cmd,
            SessionId    =cmd,
            Password=self.passwd,
            Username=self.auser,
        )
        if xtra_data is not None:
            cmdict.update(xtra_data)
        cmd_data = json.dumps(cmdict)
        timeout = self.module.params['timeout']
        headers = {'Content-Type': 'application/json', 'Content-Length': str(len(cmd_data))}
        resp, info = fetch_url(self.module, url, data=cmd_data, headers=headers, method=method, timeout=timeout)
        return Response(resp, info)

    def post(self, dc, cmd, xtra_data=None):
        return self.send('POST', dc, cmd, xtra_data)

    @staticmethod
    def it_aruba_argument_spec():
        return dict(
            user=dict(required=True),
            password=dict(no_log=True, required=True),
            timeout=dict(type='int', default=60),
            dc=dict(type='int', required=True),
        )

    @staticmethod
    def detail(srvlist):
        servers = []
        for server in srvlist:
            servers.append(detail1(server))
        return servers

    def get_servers(self, dc):
        cmd = "GetServers"
        response = self.post(dc=dc, cmd=cmd)
        status_code = response.status_code
        r = response.json
        sva = 'Value'
        suc = 'Success'
        if status_code == 200 and sva in r and suc in r and r[suc]:
            return self.detail(r[sva])
        else:
            self.module.fail_json(msg='Error fetching server list [{0}: {1}]'.format(
                status_code, response.json['message']))

    def get_server(self, dc, server_id):
        cmd = "GetServerDetails"
        xd  = dict(ServerId=server_id)
        response = self.post(dc, cmd, xd)
        status_code = response.status_code
        r = response.json
        sva = 'Value'
        suc = 'Success'
        if status_code == 200 and sva in r and suc in r and r[suc]:
            return detail2(r[sva])
        else:
            self.module.fail_json(msg='Error fetching server details [{0}: {1}]'.format(
                status_code, response.json['message']))
