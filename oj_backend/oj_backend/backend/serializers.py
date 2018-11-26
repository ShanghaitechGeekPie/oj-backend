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

from rest_framework import serializers
from oj_backend.backend.models import Student, Instructor, Course, Assignment, Record


class StudentBasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ('uid', 'email', 'name', 'student_id', )


class StudentCoursesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('uid', 'name', 'year', 'semaster', 'homepage', 'instructor')


class StudentAssignmentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name')

    class Meta:
        model = Assignment
        fields = ('uid', 'course_name', 'name', 'descr_link',
                  'grade', 'deadline', 'release_date')


class StudentSubmissionRecordSerializer(serializers.ModelSerializer):
    assignment_id = serializers.CharField(source='assginment.uid')
    overall_score = serializers.IntegerField(source='assignment.grade')

    class Meta:
        model = Record
        fields = ('git_commit_id', 'grade', 'overall_score',
                  'message', 'assignment_id', 'delta')


class ScoreBoardSerializer(serializers.ModelSerializer):
    student_nickname = serializers.CharField(source='student.nickname')
    overall_score = serializers.IntegerField(source='assignment.grade')

    class Meta:
        model = Record
        fields = ('student_nickname', 'overall_score', 'score', 'submission_time', 'delta')
