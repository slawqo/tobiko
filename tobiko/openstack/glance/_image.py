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

import io
import os
import tempfile
import time

from oslo_log import log
import requests

import tobiko
from tobiko.openstack.glance import _client

LOG = log.getLogger(__name__)


class GlanceImageStatus(object):

    #: The Image service reserved an image ID for the image in the catalog but
    # did not yet upload any image data.
    QUEUED = 'queued'

    #: The Image service is in the process of saving the raw data for the
    # image into the backing store.
    SAVING = 'saving'

    #: The image is active and ready for consumption in the Image service.
    ACTIVE = 'active'

    #: An image data upload error occurred.
    KILLED = 'killed'

    #: The Image service retains information about the image but the image is
    # no longer available for use.
    DELETED = 'deleted'

    #: Similar to the deleted status. An image in this state is not
    # recoverable.
    PENDING_DELETE = 'pending_delete'

    #: The image data is not available for use.
    DEACTIVATE = 'deactivated'

    #: Data has been staged as part of the interoperable image import process.
    # It is not yet available for use. (Since Image API 2.6)
    UPLOADING = 'uploading'

    #: The image data is being processed as part of the interoperable image
    # import process, but is not yet available for use. (Since Image API 2.6)
    IMPORTING = 'importing'


class GlanceImageFixture(tobiko.SharedFixture):

    client = None
    image_name = None
    username = None
    password = None
    _image = None
    sleep_interval = 1.

    def __init__(self, image_name=None, username=None, password=None,
                 client=None):
        super(GlanceImageFixture, self).__init__()

        if client:
            self.client = client

        if image_name:
            self.image_name = image_name
        elif not self.image_name:
            self.image_name = self.fixture_name
        tobiko.check_valid_type(self.image_name, str)

        if username:
            self.username = username

        if password:
            self.password = password

    def setup_fixture(self):
        self.setup_client()
        self.setup_image()

    def cleanup_fixture(self):
        self.delete_image()

    def setup_client(self):
        self.client = _client.glance_client(self.client)

    def setup_image(self):
        return self.wait_for_image_active()

    def wait_for_image_active(self):
        image = self.get_image()
        while GlanceImageStatus.ACTIVE != image.status:
            check_image_status(image, {GlanceImageStatus.QUEUED,
                                       GlanceImageStatus.SAVING})
            LOG.debug('Waiting for image %r to change from %r to %r...',
                      self.image_name, image.status, GlanceImageStatus.ACTIVE)
            time.sleep(self.sleep_interval)
            image = self.get_image()

    @property
    def image(self):
        return self._image or self.get_image()

    def get_image(self, **kwargs):
        self._image = image = _client.find_image(
            self.image_name, client=self.client, **kwargs)
        LOG.debug('Got image %r: %r', self.image_name, image)
        return image

    def delete_image(self, image_id=None):
        try:
            if not image_id:
                image_id = self.image_id
                self._image = None
            _client.delete_image(image_id=image_id, client=self.client)
        except _client.GlanceImageNotFound:
            LOG.debug('Image %r not deleted because not found',
                      image_id or self.image_name)
            return None
        else:
            LOG.debug("Deleted image %r: %r", self.image_name, image_id)

    @property
    def image_id(self):
        return self.image.id

    @property
    def image_status(self):
        return self.image.status


class UploadGranceImageFixture(GlanceImageFixture):

    disk_format = "raw"
    container_format = "bare"

    def __init__(self, disk_format=None, container_format=None, **kwargs):
        super(UploadGranceImageFixture, self).__init__(**kwargs)

        if container_format:
            self.container_format = disk_format
        tobiko.check_valid_type(self.container_format, str)

        if disk_format:
            self.disk_format = disk_format
        tobiko.check_valid_type(self.disk_format, str)

    def setup_image(self):
        try:
            return self.wait_for_image_active()
        except _client.GlanceImageNotFound:
            pass
        except InvalidGlanceImageStatus as ex:
            self.delete_image(image_id=ex.image_id)

        new_image = self.create_image()
        image = self.get_image()
        if image['id'] != new_image['id']:
            self.delete_image(image_id=new_image['id'])
        else:
            check_image_status(image, {GlanceImageStatus.QUEUED})
            self.upload_image()
        return self.wait_for_image_active()

    def create_image(self):
        image = _client.create_image(client=self.client,
                                    name=self.image_name,
                                    disk_format=self.disk_format,
                                    container_format=self.container_format)
        LOG.debug("Created image %r: %r", self.image_name, image)
        return image

    def upload_image(self):
        image_data, image_size = self.get_image_data()
        with image_data:
            _client.upload_image(image_id=self.image_id,
                                 image_data=image_data,
                                 image_size=image_size)
            LOG.debug("Image uploaded %r", self.image_name)

    def get_image_data(self):
        raise NotImplementedError


class FileGlanceImageFixture(UploadGranceImageFixture):

    image_file = None
    image_dir = None

    def __init__(self, image_file=None, image_dir=None, **kwargs):
        super(FileGlanceImageFixture, self).__init__(**kwargs)

        if image_file:
            self.image_file = image_file
        elif not self.image_file:
            self.image_file = self.fixture_name
        tobiko.check_valid_type(self.image_file, str)

        if image_dir:
            self.image_dir = image_dir
        elif not self.image_dir:
            from tobiko import config
            CONF = config.CONF
            self.image_dir = CONF.tobiko.glance.image_dir or "."
        tobiko.check_valid_type(self.image_dir, str)

    @property
    def real_image_dir(self):
        return os.path.realpath(os.path.expanduser(self.image_dir))

    @property
    def real_image_file(self):
        return os.path.join(self.real_image_dir, self.image_file)

    def get_image_data(self):
        image_file = self.real_image_file
        image_size = os.path.getsize(image_file)
        image_data = io.open(image_file, 'rb')
        LOG.debug('Reading image %r data from file %r (%d bytes)',
                  self.image_name, image_file, image_size)
        return image_data, image_size


class URLGlanceImageFixture(FileGlanceImageFixture):

    image_url = None

    def __init__(self, image_url=None, **kwargs):
        super(URLGlanceImageFixture, self).__init__(**kwargs)
        if image_url:
            self.image_url = image_url
        else:
            image_url = self.image_url
        tobiko.check_valid_type(image_url, str)

    def get_image_data(self):
        http_request = requests.get(self.image_url, stream=True)
        expected_size = int(http_request.headers.get('content-length', 0))
        image_file = self.real_image_file
        chunks = http_request.iter_content(chunk_size=io.DEFAULT_BUFFER_SIZE)
        try:
            if expected_size:
                actual_size = os.path.getsize(image_file)
                if actual_size == expected_size:
                    LOG.debug("Cached image %r file %r found (%d bytes)",
                              self.image_name, image_file, actual_size)
                    return super(URLGlanceImageFixture, self).get_image_data()

        except Exception as ex:
            LOG.debug("Unable to get image %r file %r size: %s",
                      self.image_name, image_file, ex)

        LOG.debug('Downloading image %r from URL %r to file %r (%d bytes)',
                  self.image_name, self.image_url, image_file,
                  expected_size)

        image_dir = os.path.dirname(image_file)
        if not os.path.isdir(image_dir):
            LOG.debug('Creating image directory: %r', image_dir)
            os.makedirs(image_dir)

        fd, temp_file = tempfile.mkstemp(dir=image_dir)
        with io.open(fd, 'wb', io.DEFAULT_BUFFER_SIZE) as image_data:
            for chunk in chunks:
                image_data.write(chunk)

        actual_size = os.path.getsize(temp_file)
        LOG.debug('Downloaded image %r from URL %r to file %r (%d bytes)',
                  self.image_name, self.image_url, image_file,
                  actual_size)

        if expected_size and actual_size != expected_size:
            message = "Download file size mismatch: {!s} != {!r}".format(
                expected_size, actual_size)
            raise RuntimeError(message)
        os.rename(temp_file, image_file)
        return super(URLGlanceImageFixture, self).get_image_data()


def check_image_status(image, expected_status):
    if image.status not in expected_status:
        raise InvalidGlanceImageStatus(image_name=image.name,
                                       image_id=image.id,
                                       actual_status=image.status,
                                       expected_status=expected_status)


class InvalidGlanceImageStatus(tobiko.TobikoException):
    message = ("Invalid image {image_name!r} (id {image_id!r}) status: "
               "{actual_status!r} not in {expected_status!r}")
