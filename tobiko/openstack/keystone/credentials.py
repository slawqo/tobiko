# Copyright 2019 Red Hat
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from __future__ import absolute_import

import collections

from tobiko.common import exceptions


class KeystoneCredentials(collections.namedtuple(
        'KeystoneCredentials', ['auth_url',
                                'username',
                                'project_name',
                                'password',
                                'api_version',
                                'user_domain_name',
                                'project_domain_name'])):

    def to_dict(self):
        return collections.OrderedDict(
            (k, v)
            for k, v in self._asdict().items()
            if v is not None)

    def __repr__(self):
        params = self.to_dict()
        if 'password' in params:
            params['password'] = '***'
        return 'keystone_credentials({!s})'.format(
            ", ".join("{!s}={!r}".format(k, v)
                      for k, v in params.items()))

    required_params = ('auth_url', 'username', 'project_name', 'password')

    def validate(self, required_params=None):
        required_params = required_params or self.required_params
        missing_params = [p
                          for p in required_params
                          if not getattr(self, p)]
        if missing_params:
            reason = "undefined parameters: {!s}".format(
                ', '.join(missing_params))
            raise InvalidKeystoneCredentials(credentials=self, reason=reason)


def keystone_credentials(api_version=None, auth_url=None,
                         username=None, password=None, project_name=None,
                         user_domain_name=None, project_domain_name=None,
                         cls=KeystoneCredentials):
    return cls(api_version=api_version, username=username,
               password=password, project_name=project_name,
               auth_url=auth_url, user_domain_name=user_domain_name,
               project_domain_name=project_domain_name)


class InvalidKeystoneCredentials(exceptions.TobikoException):
    message = "Invalid Keystone credentials (%(credentials)r): %(reason)s."
