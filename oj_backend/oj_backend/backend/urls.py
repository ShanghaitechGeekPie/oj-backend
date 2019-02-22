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

from django.urls import path, include
from .views import *

urlpatterns = [
    path('student/<str:uid>', studentInformation.as_view()),
    path('instructor/<str:uid>', insturctorInformation.as_view()),
    path('user/role', userRole.as_view()),
    path('user/login/oauth/param', oauthLoginParam.as_view()),
    path('student/<str:uid>/course/', courseList4Students.as_view()),
    path('instructor/<str:uid>/course/', courseList4Instr.as_view()),
    path('student/<str:student_id>/course/<str:course_id>/assignment/',
         assignmentList4Student.as_view()),
    path('course/<str:course_id>', courseInformation.as_view()),
    path('course/<str:uid>/assignment/', assignmentList4Instr.as_view()),
    path('course/<str:course_id>/assignment/<str:assignment_id>',
         assignmentDetail.as_view()),
    path('course/<str:uid>/instructor/', courseInstrList.as_view()),
    path('course/<str:course_id>/instructor/<str:instr_email>',
         courseInstrDetail.as_view()),
    path('course/<str:course_id>/student/', courseStudentList.as_view()),
    path('course/<str:course_id>/student/<str:student_email>',
         courseStudentDetail.as_view()),
    path('course/<str:course_id>/judge/', courseJudgeList.as_view()),
    path('course/<str:course_id>/judge/<str:judge_id>',
         courseJudgeDetail.as_view()),
    path('course/<str:course_id>/assignment/<str:assignment_id>/judge/',
         assignmentJudgeList.as_view()),
    path('course/<str:course_id>/assignment/<str:assignment_id>/judge/<str:judge_id>',
         assignmentJudgeDetail.as_view()),
    path('course/<str:course_id>/assignment/<str:assignment_id>/scores/',
         assignmentScoreboardDetail.as_view()),
    path('student/<str:student_id>/course/<str:course_id>/assignment/<str:assignment_id>/history/',
         submissionHistoryList.as_view()),
    path('student/<str:student_id>/course/<str:course_id>/assignment/<str:assignment_id>/history/<str:git_commit_id>',
         submissionHistoryDetail.as_view()),
    path('judge/', instrJudgeList.as_view()),
    path('judge/<str:uid>', instrJudgeDetail.as_view()),
    path('internal/submission/', internalSubmissionInterface.as_view())
]