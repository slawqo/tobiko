# Copyright 2018 Red Hat
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

import json
import itertools

import fixtures
from oslo_log import log
import six
import testtools
from testtools import content
import yaml


LOG = log.getLogger(__name__)


def gather_details(source_dict, target_dict):
    """Merge the details from ``source_dict`` into ``target_dict``.

    ``gather_details`` evaluates all details in ``source_dict``. Do not use it
    if the details are not ready to be evaluated.

    :param source_dict: A dictionary of details will be gathered.
    :param target_dict: A dictionary into which details will be gathered.
    """
    for name, content_object in source_dict.items():
        try:
            content_id = get_details_content_id(content_object)
            new_name = get_unique_detail_name(name=name,
                                              content_id=content_id,
                                              target_dict=target_dict)
            if new_name not in target_dict:
                target_dict[new_name] = copy_details_content(
                    content_object=content_object, content_id=content_id)
        except Exception:
            LOG.exception('Error gathering details')


def get_unique_detail_name(name, content_id, target_dict):
    disambiguator = itertools.count(1)
    new_name = name
    while new_name in target_dict:
        if content_id == get_details_content_id(target_dict[new_name]):
            break
        new_name = '{!s}-{!s}'.format(name, next(disambiguator))
    return new_name


testtools.testcase.gather_details = gather_details
fixtures.fixture.gather_details = gather_details


def copy_details_content(content_object, content_id):
    content_bytes = list(content_object.iter_bytes())
    return details_content(content_type=content_object.content_type,
                           get_bytes=lambda: content_bytes,
                           content_id=content_id)


def details_content(content_id, content_type=None, get_bytes=None,
                    get_text=None, get_json=None, get_yaml=None):
    content_type = content_type or content.UTF8_TEXT
    if get_bytes is None:
        if get_text:
            get_bytes = get_text_to_get_bytes(get_text=get_text)
        elif get_json:
            get_bytes = get_json_to_get_bytes(get_json=get_json)
        elif get_yaml:
            get_bytes = get_yaml_to_get_bytes(get_yaml=get_yaml)
        else:
            message = ("Any of get_bytes, get_text or get_json parameters has "
                       "been specified")
            raise ValueError(message)
    content_object = content.Content(content_type=content_type,
                                     get_bytes=get_bytes)
    content_object.content_id = content_id
    return content_object


def get_text_to_get_bytes(get_text):
    assert callable(get_text)

    def get_bytes():
        text = get_text()
        if text:
            if isinstance(text, six.string_types):
                yield text.encode(errors='ignore')
            else:
                for t in text:
                    yield t.encode(errors='ignore')

    return get_bytes


def get_json_to_get_bytes(get_json):
    assert callable(get_json)

    def get_text():
        obj = get_json()
        yield json.dumps(obj, indent=4, sort_keys=True).encode(errors='ignore')

    return get_text


def get_yaml_to_get_bytes(get_yaml):
    assert callable(get_yaml)

    def get_text():
        obj = get_yaml()
        yield yaml.dump(obj).encode(errors='ignore')

    return get_text


def get_details_content_id(content_object):
    try:
        return content_object.content_id
    except AttributeError:
        return id(content_object)
