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
from myapp.models import Profile


class OJOIDCAuthenticationBackend(OIDCAuthenticationBackend):

    def filter_users_by_claims(self, claims):
        email = claims.get('email')
        if not email:
            return self.UserModel.objects.none()

        try:
            profile = Profile.objects.get(email=email)
            return profile.user

        except Profile.DoesNotExist:
            return self.UserModel.objects.none()

    def create_user(self, claims):

        addEmail = claims.get('email')
        addName = claims.get('name')
        user = User.objects(email=addEmail, name=addName, rsa_pub_key="")
        user.save()
        try:
            thisStudent = Student.objects.get(enroll_email=addEmail)
            thisStudent.user = user
            thisStudent.nickname = claims.get('nickname')
            for course in thisStudent.course_set.all():
                for assignment in course.assignment.all():
                    MWCourseAddRepo(course.uid, assignment.uid, user.email, owner_uid=user.uid)
        except:
            pass
        try:
            thisInstr = Instructor.objects.get(enroll_email=addEmail)
            thisInstr.user = user
        except:
            pass
        return user

    def update_user(self, olduser, claims):

        Student.object.filter(enroll_email=olduser.email).update(user=None)
        Instructor.object.filter(enroll_email=olduser.email).update(user=None)
        olduser.email = claims.get('email')
        olduser.name = claims.get('name')
        olduser.save()
        Student.object.filter(enroll_email=olduser.email).update(user=olduser)
        Instructor.object.filter(
            enroll_email=olduser.email).update(user=olduser)

        return olduser
