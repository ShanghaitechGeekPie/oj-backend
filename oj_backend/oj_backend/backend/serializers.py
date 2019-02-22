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
from oj_backend.backend.models import Student, Instructor, Course, Assignment, Record, Judge


class StudentInfoSerializer(serializers.ModelSerializer):
    """
    Returns a student's information including `name`, `email`, `student_id`,
    `rsa_pub_key` and `nickname`.
    """
    uid = serializers.UUIDField(source='user.uid')
    email = serializers.EmailField(source='user.email')
    name = serializers.CharField(source='user.name')
    rsa_pub_key = serializers.CharField(source='user.rsa_pub_key')

    class Meta:
        model = Student
        fields = ('uid', 'email', 'name', 'student_id',
                  'nickname', 'rsa_pub_key',)
        related_fields = ('user',)

    def update(self, instance, validated_data):
        for related_obj_name in self.Meta.related_fields:
            data = validated_data.pop(related_obj_name)
            related_instance = getattr(instance, related_obj_name)
            for attr_name, value in data.items():
                setattr(related_instance, attr_name, value)
            related_instance.save()
        return super(StudentInfoSerializer, self).update(instance, validated_data)


class StudentBasicInfoSerializer(serializers.ModelSerializer):
    """
    Returns a student's basic information including `name`, `email`, `student_id`.
    """
    class Meta:
        model = Student
        fields = ('name', 'enroll_email', 'student_id')


class InstructorInfoSerializer(serializers.ModelSerializer):
    """
    Returns a instructor's all information.
    """
    uid = serializers.UUIDField(source='user.uid')
    email = serializers.EmailField(source='user.email')
    name = serializers.CharField(source='user.name')
    rsa_pub_key = serializers.CharField(source='user.rsa_pub_key')

    class Meta:
        model = Instructor
        fields = ('uid', 'name', 'email', 'rsa_pub_key')
        related_fields = ('user',)

    def update(self, instance, validated_data):
        for related_obj_name in self.Meta.related_fields:
            data = validated_data.pop(related_obj_name)
            related_instance = getattr(instance, related_obj_name)
            for attr_name, value in data.items():
                setattr(related_instance, attr_name, value)
            related_instance.save()
        return super(InstructorInfoSerializer, self).update(instance, validated_data)


class InstructorBasicInfoSerializer(serializers.ModelSerializer):
    """
    Returns a instructor's `name` and `email`. used in CoursesSerialier and
    other APIs that requires privacy.
    """
    class Meta:
        model = Instructor
        fields = ('enroll_email')


class CoursesSerializer(serializers.ModelSerializer):
    instructor = serializers.SlugRelatedField(many=True, read_only=True, slug_field='enroll_email')

    class Meta:
        model = Course
        fields = ('uid', 'name', 'year', 'semester',
                  'homepage', 'instructor', 'code')


class AssignmentSerializer(serializers.ModelSerializer):
    #course_uid = serializers.CharField(source='course.uid')

    class Meta:
        model = Assignment
        fields = ('uid', 'course', 'name', 'descr_link',
                  'grade', 'deadline', 'release_date', 'state')


class SubmissionRecordSerializer(serializers.ModelSerializer):
    #assignment_id = serializers.CharField(source='assginment.uid')
    overall_score = serializers.IntegerField(source='assignment.grade')

    class Meta:
        model = Record
        fields = ('git_commit_id', 'grade', 'overall_score',
                  'message', 'assignment', 'delta')


class ScoreBoardSerializer(serializers.ModelSerializer):
    student_nickname = serializers.CharField(source='student.nickname')
    overall_score = serializers.FloatField(source='assignment.grade')
    score = serializers.FloatField(source='grade')

    class Meta:
        model = Record
        fields = ('student_nickname', 'overall_score',
                  'score', 'submission_time', 'delta')

    @property
    def delta(self):
        return -1


class JudgeSerializer(serializers.ModelSerializer):
    """
    Returns information of a judger.
    """
    class Meta:
        model = Judge
        fields = ('uid', 'host', 'max_job',
                  'client_key', 'client_cert', 'cert_ca')

class courseJudgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Judge
        fields = ('uid',)
