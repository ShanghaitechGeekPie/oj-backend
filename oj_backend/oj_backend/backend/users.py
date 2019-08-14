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
from oidc_rp.signals import oidc_user_created

auth_logger = logging.getLogger('backend.main')


def oidc_create_user_callback(request, oidc_user, **kwargs):
    auth_logger.info(
        'User creation callback triggered for OIDC user {}.'.format(oidc_user))
    user = oidc_user.user
    claims = oidc_user.userinfo
    email = claims.get('email')
    name = claims.get('identification', {}).get('shanghaitech', {}).get(
        'realname', claims.get('family_name', '')+claims.get('given_name', ''))
    user.name = name
    user.email = email
    if not email:
        user.is_active = False
    user.save()
    auth_logger.info('User {} is created via OIDC. Name: {}; Email: {}; OIDC User {}'.format(
        user, user.name, user.email, oidc_user))
    try:
        MWUpdateUser(user.email)
    except MWUpdateError:
        auth_logger.error(
            'User {} already exists in git server. Skipped. It is probabaly becuase this user is already added as a student or instructor in a course on the server.')
    this_student, _ = generate_student_for_user(user, claims)
    generate_instructor_for_user(user, claims)
    if this_student:
        for course in this_student.course_set.all():
            for assignment in course.assignment_set.all():
                MWCourseAddRepo(course.uid, assignment.uid, this_student.enroll_email,
                                assignment.deadline, owner_uid=user.uid)


oidc_user_created.connect(oidc_create_user_callback,
                          dispatch_uid='oj_backend.users.oidc_create_user_callback')


def oidc_user_update_handler(oidc_user, claims):
    auth_logger.info(
        'User info got from OIDC backend. OIDC User: {}'.format(oidc_user))
    user = oidc_user.user
    if claims.get('email') and user.is_active == False:
        user.email = claims.get('email')
        user.is_active = True
        user.save()
    this_student, _ = generate_student_for_user(user, claims)
    generate_instructor_for_user(user, claims)
    if user.email != claims.get('email'):
        for course in this_student.course_set.all():
            for assignment in course.assignment_set.all():
                MWCourseAddRepo(course.uid, assignment.uid, this_student.enroll_email,
                                assignment.deadline, owner_uid=user.uid)


def generate_student_for_user(user, claims):
    addEmail = claims.get('email')
    is_new = False
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
    except Student.DoesNotExist:
        is_new = True
        thisStudent = create_student_from_oidc_claim(claims)
        if thisStudent:
            thisStudent.user = user
            thisStudent.save()
            auth_logger.info('Student {} is created for {}. Student ID: {}; Nickname: {}'.format(
                thisStudent, user, thisStudent.student_id, thisStudent.nickname))
    return thisStudent, is_new


def generate_instructor_for_user(user, claims):
    addEmail = claims.get('email')
    is_new = False
    try:
        thisInstr = Instructor.objects.get(enroll_email=addEmail)
        thisInstr.user = user
        thisInstr.save()
        auth_logger.info(
            'Instructor {} is linked with {}.'.format(thisInstr, user))
    except Instructor.DoesNotExist:
        is_new = True
        thisInstr = create_instructor_from_oidc_claim(claims)
        if thisInstr:
            thisInstr.user = user
            thisInstr.save()
            auth_logger.info('Instructor {} is created for {}.'.format(
                thisInstr, thisInstr.user))
    return thisInstr, is_new


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
