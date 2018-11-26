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

from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
try:
    from django.utils import simplejson
except:
    import simplejson

from oj_backend.backend.models import Student, Instructor, Course, Assignment, Record


def student_test(request, student):
    return (request.user.uid == student)


def student_taking_course_test(request, course):
    this_student = Student.objects.get(uid=request.user.uid)
    if this_student:
        this_student_courses = this_student.course_set.get(uid=course)
        return (len(this_student_courses) != 0)
    return False


def student_submit_assignment_test(request, assignment):
    this_student = Student.objects.get(uid=request.user.uid)
    if this_student:
        this_student_submissions = this_student.record_set.get(
            git_commit_id=assignment)
        return len(this_student_submissions) != 0
    return False


def student_active_test(request, assignment):
    pass

def return_http_401():
    return JsonResponse(simplejson.dumps({'message': 'HTTP 401 Unauthorized'}, status=401))

def return_http_405():
    return JsonResponse(simplejson.dumps({'message': 'HTTP 401 Not Allowed'}, status=405))
