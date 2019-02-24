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
        addName = claims.get('identification', {}).get('shanghaitech', {}).get(
            'realname', claims.get('family_name', '')+claims.get('given_name', ''))
        user = User(email=addEmail, name=addName, rsa_pub_key="", first_name=claims.get(
            'family_name', ''), last_name=claims.get('given_name', ''), username=addEmail)
        user.save()
        try:
            thisStudent = Student.objects.get(enroll_email=addEmail)
            thisStudent.user = user
            thisStudent.nickname = claims.get('nickname', '')
            enrolled_in = 0
            student_id = ''
            for i in claims.get('identification', {}).get('shanghaitech', {}).get('identities', {}):
                if i.get('enrolled_in', 0) > enrolled_in:
                    student_id = i.get('student_id', '')
            thisStudent.student_id = student_id
            thisStudent.save()
            for course in thisStudent.course_set.all():
                for assignment in course.assignment.all():
                    MWCourseAddRepo(course.uid, assignment.uid,
                                    user.email, assignment.deadline, owner_uid=user.uid)
        except Student.DoesNotExist:
            thisStudent = create_student_from_oidc_claim(claims)
            if thisStudent:
                thisStudent.user = user
                thisStudent.save()
        try:
            thisInstr = Instructor.objects.get(enroll_email=addEmail)
            thisInstr.user = user
            thisInstr.save()
        except Instructor.DoesNotExist:
            thisInstr = create_instructor_from_oidc_claim(claims)
            if thisInstr:
                thisInstr.user = user
                thisInstr.save()
        return user

    def update_user(self, olduser, claims):
        Student.objects.filter(enroll_email=olduser.email).update(user=None)
        Instructor.objects.filter(enroll_email=olduser.email).update(user=None)
        olduser.email = claims.get('email')
        olduser.name = claims.get('identification', {}).get('shanghaitech', {}).get(
            'realname', claims.get('family_name', '')+claims.get('given_name', ''))
        olduser.save()
        Student.objects.filter(enroll_email=olduser.email).update(user=olduser)
        Instructor.objects.filter(
            enroll_email=olduser.email).update(user=olduser)
        return olduser


def create_student_from_oidc_claim(claims):
    is_student = False
    for i in claims.get('identification', {}).get('shanghaitech', {}).get('identities', {}):
        if i.get('role', None) == 'student':
            is_student = True
    if is_student:
        enrolled_in = 0
        students_id = ''
        for i in claims.get('identification', {}).get('shanghaitech', {}).get('identities', {}):
            if i.get('enrolled_in', 0) > enrolled_in:
                students_id = i.get('student_id', '')
        student = Student(enroll_email=claims.get('email'), nickname=claims.get(
            'nickname', ''), student_id=students_id)
        student.save()
        return student
    else:
        return None
    # create student.


def create_instructor_from_oidc_claim(claims):
    is_employee = False
    for i in claims.get('identification', {}).get('shanghaitech', {}).get('identities', {}):
        if i.get('role', None) == 'employee':
            is_employee = True
    if is_employee:
        instructor = Instructor(enroll_email=claims.get('email'))
        instructor.save()
        return instructor
    else:
        return None
    # create instructor.
