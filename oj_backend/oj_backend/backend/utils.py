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
from django.contrib.auth.models import User as authUser
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
try:
    from django.utils import simplejson
except:
    import simplejson
from oj_backend.backend.models import Student, Instructor, Course, Assignment, Record


def get_course_uid_from_path(path):
    path = path.split("/")
    for i in range(len(path)):
        if path[i] == "course" and i+1 < len(path):
            return path[i+1]
    return None


def student_test(request, student):
    if not request.user.is_authenticated:
        return False
    return (request.user.student.uid == student)


def insturctor_test(request, instr):
    if not request.user.is_authenticated:
        return False
    return (request.user.insturctor.uid == instr)


def student_taking_course_test(request, course):
    this_student = request.user.student
    if this_student:
        this_student_courses = this_student.course_set.get(uid=course)
        return (len(this_student_courses) != 0)
    return False


def student_submit_assignment_test(request, assignment):
    this_student = request.user.student
    if this_student:
        this_student_submissions = this_student.record_set.get(
            commit_tag=assignment)
        return len(this_student_submissions) != 0
    return False


def student_active_test(request):
    return not request.user.student.disabled


def instructor_giving_course_test(request, course):
    this_instr = request.user.instructor
    if this_instr:
        this_instr_courses = this_instr.course_set.get(uid=course)
        return len(this_instr_courses) != 0
    return False


def create_assignment(course_id):
    pass


def regrade_assignment(assignment_id, course_id):
    pass


def return_http_200():
    return JsonResponse({'message': 'HTTP 200 OK'}, status=200)


def return_http_401():
    return JsonResponse({'message': 'HTTP 401 Unauthorized'}, status=401)


def return_http_405():
    return JsonResponse({'message': 'HTTP 405 Not Allowed'}, status=405)


def return_http_404():
    return JsonResponse({'message': 'HTTP 404 Not Found'}, status=404)


def return_http_403():
    return JsonResponse({'message': 'HTTP 403 Forbidden'}, status=403)


def return_http_400():
    return JsonResponse({'message': 'HTTP 400 Bad Request'}, status=400)
