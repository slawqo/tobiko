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

import mock

import tobiko


class PatchMixin(object):
    """Mixin class with mock method helpers"""

    def patch(self, obj, attribute, value=mock.DEFAULT, spec=None,
              create=False, spec_set=None, autospec=None,
              new_callable=None, **kwargs):
        # pylint: disable=arguments-differ
        context = mock.patch.object(target=obj, attribute=attribute, new=value,
                                    spec=spec, create=create,
                                    spec_set=spec_set, autospec=autospec,
                                    new_callable=new_callable, **kwargs)
        mocked = context.start()
        self.addCleanup(context.stop)
        return mocked


class PatchFixture(PatchMixin, tobiko.SharedFixture):
    """Fixture class with mock method helpers"""
