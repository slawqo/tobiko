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


class TobikoException(Exception):
    """Base Tobiko Exception.

    To use this class, inherit from it and define a 'message' property.
    """
    message = "An unknown exception occurred."

    def __init__(self, *args, **kwargs):
        super(TobikoException, self).__init__()
        try:
            self._message = self.message % kwargs

        except Exception:
            self._message = self.message

        if len(args) > 0:
            args = ["%s" % arg for arg in args]
            self._messsage = (self._message +
                              "\nDetails: %s" % '\n'.join(args))

    def __str__(self):
        return self._message


class PingException(TobikoException):
    message = "Was unable to ping the IP address: %(ip)s"


class MissingInputException(TobikoException):
    message = "No %(input)s was provided"


class MissingTemplateException(TobikoException):
    message = "No such template. Existing templates:\n%(templates)s"
