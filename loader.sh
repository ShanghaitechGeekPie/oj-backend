#!/bin/bash
# -*- coding: utf-8 -*-
#
# Copyright 2018 ericdiao <hi@ericdiao.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

cd app

python3 manage.py migrate

nohup gunicorn oj_backend.wsgi:application -b 0.0.0.0:8080 --workers 4 --worker-connections 65535&
service nginx start

while true
do
    sleep 1
done
