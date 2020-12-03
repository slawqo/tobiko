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


import sys


import tobiko


def import_lzma():
    try:
        import lzma
    except ImportError:
        from backports import lzma
    return lzma


def has_lzma():
    try:
        return import_lzma()
    except ImportError:
        return None


def open_file(filename, mode):
    try:
        lzma = import_lzma()
    except ImportError:
        tobiko.skip_test(
            "Package lzma or backports.lzma is required to decompress "
            f"{filename!r} (mode={mode!r}) XZ image file "
            f"({sys.version!r}).")

    return lzma.LZMAFile(filename=filename, mode=mode)
