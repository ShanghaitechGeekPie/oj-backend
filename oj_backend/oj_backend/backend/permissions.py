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

from rest_framework import permissions
from oj_backend.backend.models import Student, Instructor, Course, Assignment, Record, Judge, PendingAssignment
from utils import get_course_uid_from_path as get_course_uid


class userInfoReadWritePermission(permissions.BasePermission):

    '''
    This class provides permission class for users to read and write
    user information.
    '''

    def has_object_permission(self, request, view, obj):
        return request.user.uid == obj.uid


class submissionRecordReadPermission(permissions.BasePermission):
    '''
    This class provides permission control for student's submission history.

    Student: only the student that submits the homework has the permission to view one record;

    Instructor: only insturctor that gives this course could access this record.
    '''

    def has_object_permission(self, request, view, obj):
        this_user = request.user
        this_student = obj.student
        this_instr = obj.assignment.course.instructor.get(uid=this_user.uid)
        if this_user.uid == this_student.uid:
            return True
        return this_instr.exists()


class assignmentInfoReadWritePermisson(permissions.BasePermission):
    '''
    This class provides permission control for assignment.

    Student: only allowed to read assignment of course that they currently enrolled in;

    Instructor: allowed to motify any assigment that they gives lecture to.
    '''

    def has_object_permission(self, request, view, obj):
        this_course = obj.course
        this_user = request.user
        this_student = this_course.student.get(uid=this_user.uid)
        this_instr = this_course.instructor.get(uid=this_user.uid)
        if request.method in permissions.SAFE_METHODS:
            return this_instr.exists() or this_student.exists()
        else:
            return this_instr.exists()
        return False


class courseInstrInfoReadWritePermission(permissions.BasePermission):
    '''
    This class provides permission for course's insturctor.

    Student: only allowed to read instructor's list.

    Instructor: allowed to motify instructor list, along with read.
    '''

    def has_object_permission(self, request, view, obj):
        this_course = Course.objects.get(uid=get_course_uid(request.path))
        if this_course:
            this_student = this_course.student.get(uid=request.user.uid)
            this_instr = this_course.instructor.get(uid=request.user.uid)
        else:
            return False
        if request.method in permissions.SAFE_METHODS:
            # for any user.
            return this_student.exists() or this_instr.exists()
        else:
            # for instructor.
            return this_instr.exists()
        return False


class courseJudgeReadWritePermisson(permissions.BasePermission):
    '''
    This class provides permission for course's judges.

    Student: does not allowed.

    Instructor: allowed to motify and also read.
    '''

    def has_object_permission(self, request, view, obj):
        this_course = Course.objects.get(uid=get_course_uid(request.path))
        if this_course:
            return this_course.instr.get(uid=request.user.uid)
        return False


class courseReadWritePermission(permissions.BasePermission):

    '''
    This class provides permission class for users that are in a
    class to read and write something.
    '''

    def has_object_permission(self, request, view, obj):
        instr = obj.instructor.get(uid=request.user.uid)
        student = obj.student.get(uid=request.user.uid)
        if request.method in permissions.SAFE_METHODS:
            # for any users in this class.
            return instr.exists() or student.exists()
        else:
            return instr.exists()


class courseRelatedObjReadWritebyInstr(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.instructor.get(uid=request.user.uid).exists()


class recordReadOnly(permissions.BasePermission):

    '''
    This class provides read only permission to student's submission record.
    '''

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            if obj.student.uid == request.user.uid:
                return True
            if obj.assignment.course.instructor.get(uid=request.user.uid).exists():
                return True
        return False
