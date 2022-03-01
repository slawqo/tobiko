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

from tobiko.actors import _actor
from tobiko.actors import _proxy

call_proxy = _proxy.create_call_proxy
call_proxy_class = _proxy.create_call_proxy_class
CallProxy = _proxy.CallProxy
CallProxyBase = _proxy.CallProxyBase

actor_method = _actor.actor_method
cleanup_actor = _actor.cleanup_actor
setup_actor = _actor.setup_actor
start_actor = _actor.start_actor
stop_actor = _actor.stop_actor
Actor = _actor.Actor
ActorRef = _actor.ActorRef
