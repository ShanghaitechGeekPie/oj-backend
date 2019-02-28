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

import logging
from oj_database.models import User
from oj_database.models import Student
from oj_database.models import Instructor
from oj_backend.backend.middleware_connector import *

auth_logger = logging.getLogger('backend.main')


def oidc_create_user_handler(oidc_user, claims):
    auth_logger.info('User info got from OIDC backend. OIDC User: {}'.format(oidc_user))
    addEmail = claims.get('email')
    addName = claims.get('identification', {}).get('shanghaitech', {}).get(
         'realname', claims.get('family_name', '')+claims.get('given_name', ''))
    #user = User(email=addEmail, name=addName, rsa_pub_key="", first_name=claims.get(
    #     'family_name', ''), last_name=claims.get('given_name', ''), username=addEmail)
    user = User.objects.get(email=addEmail)
    user.name = addName
    user.save()
    oidc_user.user = user
    oidc_user.save()
    auth_logger.info('User {} is created via OIDC. Name: {}; Email: {}'.format(
         user, user.name, user.email))
    MWUpdateUser(user.email)
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
        auth_logger.info('Student {} is linked with {}. Student ID: {}; Nickname: {}'.format(
                thisStudent, user, thisStudent.student_id, thisStudent.nickname))
        for course in thisStudent.course_set.all():
            for assignment in course.assignment.all():
                MWCourseAddRepo(course.uid, assignment.uid,
                                user.email, assignment.deadline, owner_uid=user.uid)
    except Student.DoesNotExist:
        thisStudent = create_student_from_oidc_claim(claims)
        if thisStudent:
            thisStudent.user = user
            thisStudent.save()
            auth_logger.info('Student {} is created for {}. Student ID: {}; Nickname: {}'.format(
                    thisStudent, user, thisStudent.student_id, thisStudent.nickname))
    try:
        thisInstr = Instructor.objects.get(enroll_email=addEmail)
        thisInstr.user = user
        thisInstr.save()
        auth_logger.info(
                'Instructor {} is linked with {}.'.format(thisInstr, user))
    except Instructor.DoesNotExist:
        thisInstr = create_instructor_from_oidc_claim(claims)
        if thisInstr:
            thisInstr.user = user
            thisInstr.save()
            auth_logger.info('Instructor {} is created for {}.'.format(
                    thisInstr, thisInstr.user))


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
