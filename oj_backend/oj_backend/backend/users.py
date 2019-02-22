#!/usr/bin/python
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

# This file provides some baisc integration of auth system.

from oj_database.models import User
from oj_database.models import Student
from oj_database.models import Instructor
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class OJOIDCAuthenticationBackend(OIDCAuthenticationBackend):

    def createFromOIDC(self, claims):

        addEmail = claims.get('email')
        addName = claims.get('first name')+claims.get('last name')
        user = User.objects(email=addEmail, name=addName, rsa_pub_key="")
        user.save()

        return user

    def updateUser(self, olduser, claims):

        Student.object.filter(enroll_email=olduser.email).update(user=None)
        Instructor.object.filter(enroll_email=olduser.email).update(user=None)
        olduser.email = claims.get('email')
        olduser.name = claims.get('first name')+claims.get('last name')
        olduser.save()
        Student.object.filter(enroll_email=olduser.email).update(user=olduser)
        Instructor.object.filter(
            enroll_email=olduser.email).update(user=olduser)

        return olduser
