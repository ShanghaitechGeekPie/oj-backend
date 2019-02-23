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
from oj_backend.backend.middleware_connector import *
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class OJOIDCAuthenticationBackend(OIDCAuthenticationBackend):

    def create_user(self, claims):

        addEmail = claims.get('email')
        addName = claims.get('famaily_name')+claims.get('given_name')
        user = User.objects(email=addEmail, name=addName, rsa_pub_key="", first_name=claims.get(
            'famaily_name'), given_name=claims.get('given_name'))
        user.save()
        try:
            thisStudent = Student.objects.get(enroll_email=addEmail)
            thisStudent.user = user
            thisStudent.nickname = claims.get('nickname')
            thisStudent.save()
            for course in thisStudent.course_set.all():
                for assignment in course.assignment.all():
                    MWCourseAddRepo(course.uid, assignment.uid,
                                    user.email, owner_uid=user.uid)
        except Student.DoesNotExist:
            pass
            # TODO: if this user has a student identity, we need to create a new student and point it to this user.
        try:
            thisInstr = Instructor.objects.get(enroll_email=addEmail)
            thisInstr.user = user
            thisInstr.save()
        except Instructor.DoesNotExist:
            pass
        return user

    def update_user(self, olduser, claims):

        Student.object.get(enroll_email=olduser.email).update(user=None)
        Instructor.object.get(enroll_email=olduser.email).update(user=None)
        olduser.email = claims.get('email')
        olduser.name = claims.get('famaily_name')+claims.get('given_name')
        olduser.save()
        Student.objects.get(enroll_email=olduser.email).update(user=olduser)
        Instructor.objects.get(enroll_email=olduser.email).update(user=olduser)

        return olduser
