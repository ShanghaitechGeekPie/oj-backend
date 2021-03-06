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
    uid = serializers.UUIDField(source='user.uid', read_only=True)
    email = serializers.EmailField(
        source='user.email', allow_null=True, read_only=True)
    name = serializers.CharField(
        source='user.name', allow_null=True, read_only=True)
    rsa_pub_key = serializers.CharField(
        source='user.rsa_pub_key', allow_null=True)

    class Meta:
        model = Student
        fields = ('uid', 'email', 'name', 'student_id',
                  'nickname', 'rsa_pub_key',)
        read_only_fields = ('student_id',)
        extra_kwargs = {'rsa_pub_key': {'write_only': True}}
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
    name = serializers.CharField(source='user.name', allow_null=True)

    class Meta:
        model = Student
        fields = ('name', 'enroll_email', 'student_id')


class InstructorInfoSerializer(serializers.ModelSerializer):
    """
    Returns a instructor's all information.
    """
    uid = serializers.UUIDField(source='user.uid', read_only=True)
    email = serializers.EmailField(
        source='user.email', allow_null=True, read_only=True)
    name = serializers.CharField(source='user.name', allow_null=True)
    rsa_pub_key = serializers.CharField(
        source='user.rsa_pub_key', allow_null=True)

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
    name = serializers.CharField(source='user.name', allow_null=True)

    class Meta:
        model = Instructor
        fields = ('enroll_email', 'name')


class CoursesCreateSerializer(serializers.ModelSerializer):
    instructor = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='enroll_email')

    class Meta:
        model = Course
        fields = ('uid', 'name', 'year', 'semester',
                  'homepage', 'instructor', 'code')


class CoursesViewSerializer(serializers.ModelSerializer):
    instructor = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='enroll_email')

    class Meta:
        model = Course
        fields = ('uid', 'name', 'year', 'semester',
                  'homepage', 'instructor', 'code')
        extra_kwargs = {'year': {'read_only': True},
                        'semester': {'read_only': True},
                        'code': {'read_only': True}
                        }


class AssignmentDetailSerializer(serializers.ModelSerializer):
    course_id = serializers.UUIDField(source='course.uid', read_only=True)

    class Meta:
        model = Assignment
        fields = ('uid', 'course_id', 'name', 'descr_link',
                  'grade', 'deadline', 'release_date', 'state', 'short_name')
        extra_kwargs = {'short_name': {'read_only': True}, }


class AssignmentCreateSerializer(serializers.ModelSerializer):
    course_id = serializers.UUIDField(source='course.uid', read_only=True)

    class Meta:
        model = Assignment
        fields = ('uid', 'course_id', 'name', 'descr_link',
                  'grade', 'deadline', 'release_date', 'state', 'short_name')


class SubmissionRecordSerializer(serializers.ModelSerializer):
    assignment_id = serializers.CharField(
        source='assginment.uid', read_only=True)
    overall_score = serializers.IntegerField(source='assignment.grade')
    score = serializers.IntegerField(source='grade')

    class Meta:
        model = Record
        fields = ('state', 'commit_tag', 'score', 'overall_score',
                  'message', 'assignment_id', 'submission_time', 'delta')


class JudgeSerializer(serializers.ModelSerializer):
    """
    Returns information of a judge.
    """
    class Meta:
        model = Judge
        fields = ('uid', 'host', 'max_job',
                  'client_key', 'client_cert', 'cert_ca')
        extra_kwargs = {
            'client_key': {'write_only': True},
            'client_cert': {'write_only': True},
            'cert_ca': {'write_only': True}
        }


class courseJudgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Judge
        fields = ('uid',)
