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

"""oj_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from oj_backend.backend import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('student/login', views.student_login),
    path('student/logout', views.student_logout),
    path('student/<str:id>/', views.student_info),
    path('student/<str:id/course/', views.student_course_list),
    path('student/<str:id>/course/<str:course_id>', views.student_course_assginment_list),
    path('student/<str:id>/course/<str:course_id>/<str:assignment_id>/', views.student_assignment_detail),
    path('student/<str:id>/course/<str:course_id>/<str:assignment_id>/history/', views.stutdent_assignment_history_list),
    path('course/<str:course_id>/', views.course_info),
    path('course/<str:course_id>/', views.course_judging_queue),
    path('course/<str:course_id>/<str:assignment_id>/', views.course_assignment_info),
    path('course/<str:course_id>/<str:assignment_id>/scores/', views.course_assignment_scores),
]
