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

from django.views import View
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed, Http404, HttpResponse
from rest_framework import status, generics, mixins
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
try:
    from django.utils import simplejson
except:
    import simplejson

import redis
import time

import oj_backend.backend.middleware_connector as mw_connector
from oj_backend.backend.utils import student_active_test, student_test, insturctor_test, student_taking_course_test, student_submit_assignment_test, instructor_giving_course_test, regrade_assignment
from oj_backend.backend.models import *
from oj_backend.backend.serializers import *
from oj_backend.backend.permissions import *
from settings import redisConnectionPool


class studentInformation(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    '''
    `/student/<str:uid>`
    '''
    serializer_class = StudentInfoSerializer
    permission_classes = (userInfoReadWritePermission,)

    def get_queryset(self):
        student_uid = self.kwargs['uid']
        return Student.objects.get(uid=student_uid)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class insturctorInformation(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    '''
    `/instructor/<str:uid>/`
    '''
    serializer_class = InstructorInfoSerializer
    permission_classes = (userInfoReadWritePermission,)

    def get_queryset(self):
        instr_uid = self.kwargs['uid']
        return Instructor.objects.get(uid=instr_uid)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class courseList4Students(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/student/<str:uid>/course/`
    '''
    serializer_class = CoursesSerializer
    permission_classes = (courseReadWritePermission,)

    def get_queryset(self):
        student_uid = self.request.user.uid
        return Course.objects.filter(student__uid=student_uid)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class courseList4Instr(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
    `/insturctor/<str:uid>/course/`
    '''
    serializer_class = CoursesSerializer
    permission_classes = (courseReadWritePermission,)

    def get_queryset(self):
        instr_uid = self.request.user.uid
        return Course.objects.filter(instructor__uid=instr_uid)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class assignmentList4Student(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/student/<str:student_id>/course/<str:course_id>/assignment/`
    '''
    serializer_class = AssignmentSerializer  # TODO: change it!
    permission_classes = (assignmentInfoReadWritePermisson,)

    def get_queryset(self):
        this_student = self.kwargs['student_id']
        this_course = self.kwargs['course_id']
        return Assignment.objects.filter(course__uid=this_course, student__uid=this_student)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class courseInformation(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    '''
    `/course/<str:course_id>`
    '''
    serializer_class = CoursesSerializer
    permission_classes = (courseReadWritePermission,)

    def get_queryset(self):
        course_uid = self.kwargs['uid']
        return Course.objects.get(uid=course_uid)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class assignmentList4Instr(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
    `/course/<str:uid>/assignment/`
    '''
    serializer_class = AssignmentSerializer
    permission_classes = (assignmentInfoReadWritePermisson,)

    def get_queryset(self):
        this_assignment = self.kwargs['uid']
        this_instr = self.request.user.uid
        return Assignment.objects.filter(uid=this_assignment, course__instructor__uid=this_instr)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        #TODO: notify using redis.
        return self.create(request, *args, **kwargs)
        # deal with it!

class assignmentDetail(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    '''
    `/course/<str:course_id>/assignment/<str:assignment_id>`
    '''
    serializer_class = AssignmentSerializer
    permission_classes = (assignmentInfoReadWritePermisson, )

    def get_queryset(self):
        return Assignment.objects.filter(uid=self.kwargs['assignment_id'], course__uid=self.kwargs['course_id'])

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        #TODO: notify using redis.
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        #TODO: notify using redis.
        return self.delete(request, *args, **kwargs)

class courseInstrList(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
     `/course/<str:uid>/instructor/`
    '''
    serializer_class = InstructorBasicInfoSerializer
    permission_classes = (courseInstrInfoReadWritePermission,)

    def get_queryset(self):
        this_course = Course.objects.get(uid=self.kwargs['uid'])
        return this_course.instructor.all()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
        # TODO: do linking manually.

class courseInstrDetail(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.DestroyModelMixin):
    '''
    `/course/<str:course_id>/instructor/<str:instr_id>`
    '''
    serializer_class = InstructorBasicInfoSerializer # TODO: change it!
    # This class will delete THE USER!!!
    permission_classes = (courseInstrInfoReadWritePermission,)

    def get_queryset(self):
        this_course = Course.objects.get(uid=self.kwargs['course_id'])
        return this_course.instructor.get(uid=self.kwargs['instr_id'])

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
        # TODO: do linking manually.

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
        # TODO: do linking manually.

class courseJudgeList(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
    `/course/<str:course_id>/judge/`
    '''
    serializer_class = JudgerSerializer # TODO: change it!
    # This class will delete THE JUDGE!!!
    permission_classes = (courseJudgeReadWritePermisson,)

    def get_queryset(self):
        this_course = Course.objects.get(uid=self.kwargs['course_id'])
        return this_course.judge.all()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
        # TODO: do linking manually.

class submissionHistoryList(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/student/<str:student_id>/course/<str:course_id>/assignment/<str:assignment_id>/history/`
    '''
    serializer_class = SubmissionRecordSerializer
    permission_classes = (submissionRecordReadPermission,)

    def get_queryset(self):
        this_student = self.kwargs['student_id']
        this_assignment = self.kwargs['assignment_id']
        return Record.objects.filter(student__uid=this_student, assignment__uid=this_assignment)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class submissionHistoryDetail(generics.GenericAPIView, mixins.RetrieveModelMixin):
    '''
    `/student/<str:student_id>/course/<str:course_id>/assignment/<str:assignment_id>/history/<str:git_commit_id>`
    '''
    serializer_class = SubmissionRecordSerializer
    permission_classes = (submissionRecordReadPermission)

    def get_queryset(self):
        this_student = self.kwargs['student_id']
        this_assignment = self.kwargs['assignment_id']
        this_record = self.kwargs['git_commit_id']
        return Record.objects.filter(student__uid=this_student, assignment__uid=this_assignment, git_commit_id=this_record)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

class assignmentScoreboardDetail(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/course/<str:course_id>/assignment/<str:assignment_id>/scores/`
    '''
    serializer_class = ScoreBoardSerializer
    permission_classes = (recordReadOnly,)

    def get_queryset(self):
        this_assignment = self.kwargs['course_id']
        this_course = self.kwargs['assignment_id']
        this_course_student_list = Course.objects.get(uid=this_course).student.all()
        query_set = None
        for this_student in this_course_student_list:
            this_student_record = Record.objects.filter(
                student=this_student, assignment__uid=this_assignment).order_by('-submission_time')[0]
            if query_set:
                query_set = query_set | this_student_record
            else:
                query_set = this_course_student_list
        return query_set

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class internalSubmissionInterface(generics.GenericAPIView):
    '''
    `/internal/subbmission/`
    '''
    # TODO: add auth!

    def post(self, request, *args, **kwargs):
        this_submission = simplejson.dumps(request.DATA)
        this_redis = redis.Redis(connection_pool=redisConnectionPool)
        this_redis.zadd(name='pendingAssignment', mapping={this_submission: time.time()})
        return Response(status=201)
