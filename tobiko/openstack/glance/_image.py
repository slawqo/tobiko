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

import contextlib
import io
import os
import tempfile
import time

from oslo_log import log
import requests

import tobiko
from tobiko.openstack.glance import _client
from tobiko.openstack.glance import _io


LOG = log.getLogger(__name__)


class GlanceImageStatus(object):

    #: The Image service reserved an image ID for the image in the catalog but
    # did not yet upload any image data.
    QUEUED = u'queued'

    #: The Image service is in the process of saving the raw data for the
    # image into the backing store.
    SAVING = u'saving'

    #: The image is active and ready for consumption in the Image service.
    ACTIVE = u'active'

    #: An image data upload error occurred.
    KILLED = u'killed'

    #: The Image service retains information about the image but the image is
    # no longer available for use.
    DELETED = u'deleted'

    #: Similar to the deleted status. An image in this state is not
    # recoverable.
    PENDING_DELETE = u'pending_delete'

    #: The image data is not available for use.
    DEACTIVATED = u'deactivated'

    #: Data has been staged as part of the interoperable image import process.
    # It is not yet available for use. (Since Image API 2.6)
    UPLOADING = u'uploading'

    #: The image data is being processed as part of the interoperable image
    # import process, but is not yet available for use. (Since Image API 2.6)
    IMPORTING = u'importing'


class GlanceImageFixture(tobiko.SharedFixture):

    client = None
    image_name = None
    username = None
    password = None
    image = None
    wait_interval = 1.

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

    def get_image(self):
        images = _client.list_images(client=self.client,
                                     filters={'name': self.image_name},
                                     limit=1)
        if images:
            self.image = image = images[0]
            LOG.debug('Found image %r (%r): %r', self.image_name, image['id'],
                      image)
            return image
        else:
            self.image = None
            LOG.debug('Glance image %r not found', self.image_name)
            return None

    def delete_image(self, image_id=None):
        if not image_id:
            image_id = self.image_id
            self.image = None
        LOG.debug('Deleting Glance image %r (%r)...', self.image_name,
                  image_id)
        if _client.delete_image(image_id=image_id, client=self.client):
            LOG.debug('Deleted Glance image %r (%r).', self.image_name,
                      image_id)

    @property
    def image_id(self):
        return (self.image or self.get_image()).id

    @property
    def image_status(self):
        return (self.image or self.get_image()).status

    def wait_for_image_active(self, check=True):
        return self.wait_for_image_status(
            expected_status={GlanceImageStatus.ACTIVE}, check=check)

    def wait_for_image_deleted(self, check=True):
        return self.wait_for_image_status(
            expected_status={GlanceImageStatus.DELETED}, check=check)

    def wait_for_getting_active_image(self, check=True):
        return self.wait_for_image_status(
            expected_status=GETTING_ACTIVE_STATUS, check=check)

    def wait_for_image_status(self, expected_status, check=True):
        """Waits for the image to reach the given status."""
        image = self.image or self.get_image()
        while (image and image.status not in expected_status and
               is_image_status_changing(image)):

            LOG.debug("Waiting for %r (id=%r) stack status "
                      "(observed=%r, expected=%r)", self.image_name,
                      image.id, image.status, expected_status)
            time.sleep(self.wait_interval)
            image = self.get_image()

        if check:
            self.check_image_status(image, expected_status)
        return image

    def check_image_status(self, image, expected_status):
        image_status = image and image.status or GlanceImageStatus.DELETED
        if image_status not in expected_status:
            raise InvalidGlanceImageStatus(image_name=self.image_name,
                                           image_id=image.id,
                                           actual_status=image_status,
                                           expected_status=expected_status)


class UploadGranceImageFixture(GlanceImageFixture):

    disk_format = "raw"
    container_format = "bare"
    create_image_retries = None

    def __init__(self, disk_format=None, container_format=None, **kwargs):
        super(UploadGranceImageFixture, self).__init__(**kwargs)

        if container_format:
            self.container_format = disk_format
        tobiko.check_valid_type(self.container_format, str)

        if disk_format:
            self.disk_format = disk_format
        tobiko.check_valid_type(self.disk_format, str)

    def setup_image(self):
        self.create_image()

    def create_image(self, retries=None):
        with self._cleanup_image_ids() as cleanup_image_ids:
            retries = retries or self.create_image_retries or 1
            while retries >= 0:
                image = self.wait_for_getting_active_image(
                    check=(not retries))
                if is_image_getting_active(image):
                    break
                retries -= 1

                if image:
                    LOG.debug('Delete existing image: %r (id=%r)',
                              self.image_name, image.id)
                    self.delete_image(image.id)
                    self.wait_for_image_deleted()

                # Cleanup cached objects
                self.image = image = None

                try:
                    LOG.debug('Creating Glance image %r (re-tries left %d)...',
                              self.image_name, retries)
                    image_id = _client.create_image(
                        client=self.client,
                        name=self.image_name,
                        disk_format=self.disk_format,
                        container_format=self.container_format)['id']
                except Exception:
                    LOG.exception('Image creation failed %r.', self.image_name)
                else:
                    cleanup_image_ids.add(image_id)
                    LOG.debug('Created image %r (id=%r)...', self.image_name,
                              image_id)

            if image:
                if image.id in cleanup_image_ids:
                    LOG.debug('Image created: %r (id=%r)',
                              self.image_name, image.id)
                    self.upload_image()
                else:
                    LOG.debug('Existing image found: %r (id=%r)',
                              self.image_name, image.id)

            image = self.wait_for_image_active()
            if image and image.id in cleanup_image_ids:
                # Having an active image we can remove image created from this
                # process from cleanup image list so that it is not going to
                # be deleted
                cleanup_image_ids.remove(image.id)

        return image

    @contextlib.contextmanager
    def _cleanup_image_ids(self):
        created_image_ids = set()
        try:
            yield created_image_ids
        finally:
            for image_id in created_image_ids:
                LOG.warning("Delete duplicate image %r (id=%r).",
                            self.image_name, image_id)
                try:
                    self.delete_image(image_id)
                except Exception:
                    LOG.exception('Error deleting image %r (%r)',
                                  self.image_name, image_id)

    def upload_image(self):
        self.check_image_status(self.image, {GlanceImageStatus.QUEUED})
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
    compression_type = None

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
        LOG.debug('Uploading image %r data from file %r (%d bytes)',
                  self.image_name, image_file, image_size)
        image_data = _io.open_image_file(
            filename=image_file, mode='rb',
            compression_type=self.compression_type)
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
        download_image = True
        if expected_size:
            try:
                actual_size = os.path.getsize(image_file)
            except Exception as ex:
                LOG.debug("Unable to get image %r data from file %r: %s",
                          self.image_name, image_file, ex)
            else:
                if actual_size == expected_size:
                    LOG.debug("Cached image %r file %r found (%d bytes)",
                              self.image_name, image_file, actual_size)
                    download_image = False

        if download_image:
            LOG.debug("Downloading image %r from URL %r to file %r "
                      "(%d bytes)", self.image_name, self.image_url,
                      image_file, expected_size)
            self._download_image_file(image_file=image_file,
                                      chunks=chunks,
                                      expected_size=expected_size)
        return super(URLGlanceImageFixture, self).get_image_data()

    def _download_image_file(self, image_file, chunks, expected_size):
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


class InvalidGlanceImageStatus(tobiko.TobikoException):
    message = ("Invalid image {image_name!r} (id {image_id!r}) status: "
               "{actual_status!r} not in {expected_status!r}")


class GlanceImageCreationFailed(tobiko.TobikoException):
    message = ("Failed creating image {image_name!r}: status "
               "({observed!r}) not in ({expected!r})")


CHANGING_STATUS = {GlanceImageStatus.QUEUED,
                   GlanceImageStatus.IMPORTING,
                   GlanceImageStatus.PENDING_DELETE,
                   GlanceImageStatus.SAVING,
                   GlanceImageStatus.UPLOADING}


def is_image_status_changing(image):
    return image and image.status in CHANGING_STATUS


GETTING_ACTIVE_STATUS = {GlanceImageStatus.QUEUED,
                         GlanceImageStatus.SAVING,
                         GlanceImageStatus.ACTIVE}


def is_image_getting_active(image):
    return image and image.status in GETTING_ACTIVE_STATUS
