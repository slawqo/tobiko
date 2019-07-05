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

import bz2
import gzip
import io
import zipfile

from oslo_log import log


LOG = log.getLogger(__name__)


class BZ2FileType(object):
    file_magic = b'\x42\x5a\x68'
    compression_type = 'bz2'
    open = bz2.BZ2File


class GzipFileType(gzip.GzipFile):
    file_magic = b'\x1f\x8b\x08'
    compression_type = 'gz'
    open = gzip.GzipFile


class ZipFileType(object):
    file_magic = b'\x50\x4b\x03\x04'
    compression_type = 'zip'
    open = zipfile.ZipFile


COMPRESSION_FILE_TYPES = {'bz2': BZ2FileType,
                          'gz': GzipFileType,
                          'zip': ZipFileType}


def open_file(filename, mode, compression_type=None):
    if compression_type is None:
        max_magic_len = max(len(cls.file_magic)
                            for cls in COMPRESSION_FILE_TYPES.values())
        with io.open(filename, 'rb') as f:
            magic = f.read(max_magic_len)
        for cls in COMPRESSION_FILE_TYPES.values():
            if magic.startswith(cls.file_magic):
                compression_type = cls.compression_type
                LOG.debug("Compression type %r of file %r got from file magic",
                          compression_type, filename)
                break

    if compression_type:
        LOG.debug("Open compressed file %r (mode=%r, compression_type=%r)",
                  filename, mode, compression_type)
        open_func = COMPRESSION_FILE_TYPES[compression_type].open
    else:
        LOG.debug("Open flat file %r (mode=%r)",
                  filename, mode)
        open_func = io.open

    return open_func(filename, mode)
