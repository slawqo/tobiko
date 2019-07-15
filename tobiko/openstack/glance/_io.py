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

from tobiko.openstack.glance import _lzma


LOG = log.getLogger(__name__)

COMPRESSED_FILE_TYPES = {}


def comressed_file_type(cls):
    COMPRESSED_FILE_TYPES[cls.compression_type] = cls
    return cls


@comressed_file_type
class BZ2FileType(object):
    file_magic = b'\x42\x5a\x68'
    compression_type = 'bz2'
    open_file = bz2.BZ2File


@comressed_file_type
class GzipFileType(gzip.GzipFile):
    file_magic = b'\x1f\x8b\x08'
    compression_type = 'gz'
    open_file = gzip.GzipFile


@comressed_file_type
class XzFileType(object):
    file_magic = b'\xfd7zXZ\x00'
    compression_type = 'xz'
    open_file = staticmethod(_lzma.open_file)


@comressed_file_type
class ZipFileType(object):
    file_magic = b'\x50\x4b\x03\x04'
    compression_type = 'zip'
    open_file = zipfile.ZipFile


def open_image_file(filename, mode, compression_type=None):
    if compression_type is None:
        max_magic_len = max(len(cls.file_magic)
                            for cls in COMPRESSED_FILE_TYPES.values())
        with io.open(filename, 'rb') as f:
            magic = f.read(max_magic_len)
        for cls in COMPRESSED_FILE_TYPES.values():
            if magic.startswith(cls.file_magic):
                compression_type = cls.compression_type
                LOG.debug("Compression type %r of file %r got from file magic",
                          compression_type, filename)
                break

    if compression_type:
        LOG.debug("Open compressed file %r (mode=%r, compression_type=%r)",
                  filename, mode, compression_type)
        open_func = COMPRESSED_FILE_TYPES[compression_type].open_file
    else:
        LOG.debug("Open flat file %r (mode=%r)", filename, mode)
        open_func = io.open

    return open_func(filename, mode)
