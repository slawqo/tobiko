# Copyright (c) 2021 Red Hat, Inc.
#
# All Rights Reserved.
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

from tobiko.shell.curl import _execute
from tobiko.shell.curl import _process


execute_curl = _execute.execute_curl

CurlHeader = _process.CurlHeader
CurlProcessFixture = _process.CurlProcessFixture
assert_downloaded_file = _process.assert_downloaded_file
download_file = _process.download_file
default_download_dir = _process.default_download_dir
get_url_header = _process.get_url_header
