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

apt update && apt install python3 python3-pip git nginx python3-dev libmysqlclient-dev && python3 -m pip install django mysqlclient simplejson&&
git clone https://github.com/encode/django-rest-framework.git &&
cd django-rest-framework &&
python3 -m pip install -r requirements.txt &&
python3 setup.py install
