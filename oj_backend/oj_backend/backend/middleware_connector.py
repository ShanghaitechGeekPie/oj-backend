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

# TODO: implement this part accordding to interfaces provided by `oj-gitlab-middleware`.

import os
import simplejson
import logging
from secrets import choice
from string import ascii_letters, digits
import requests
from urllib.parse import quote
from requests.exceptions import RequestException, ConnectionError, HTTPError, Timeout
from uuid import UUID

OJBN_GITLAB_ADDR = os.environ['OJBN_GITLAB_ADDR']
middleware_logger = logging.getLogger('backend.main')


def get_course_project_name(code, year, semaster):
    return "{}-{}{}".format(code, year, semaster)


def get_repo_addr(assignment, user):
    assignment_name = ''.join(assignment.short_name.split())
    course = assignment.course
    course_proj = get_course_project_name(
        course.code, course.year, course.semaster)
    personal_repo = user.email.split("@")[0]
    # TODO: change `oj.geekpie.club`
    return "git@oj.geekpie.club/{}/{}/{}.git".format(course_proj, assignment_name, personal_repo)


class MiddlewareError(BaseException):

    '''
    Base exception class for middleware error.
    '''
    pass


class MWUpdateError(MiddlewareError):

    '''
    Exception for the middleware failed to update a user's information, because of bad parameters.
    '''
    pass


class baseMiddlewareAdopter:
    '''
    This is the base adopter for web interface provided by oj-middleware.
    '''

    def __init__(self, api_server=None, interface=None, action="POST", payload=None):
        self.api_server = api_server
        self.interface = interface
        self.response = None
        self._send_request(payload, action)

    def _send_request(self, payload, action):
        api_url = "{}{}".format(self.api_server, self.interface)
        action_func = requests.post
        try:
            action_func = getattr(requests, action.lower())
        except AttributeError:
            middleware_logger.error(
                'Could not identify the method {} given.'.format(action))
            raise MiddlewareError('Could not identify the method {} given.'.format(action))
        try:
            request = action_func(api_url, json=payload)
            request.raise_for_status()
        except (ConnectionError, Timeout):
            cause = 'The connection to middleware server is either broken or timeout.'
            middleware_logger.error(
                'Connection to the gitlab-middleware server is either broken or timeout. Remote: {}'.format(api_url))
            raise MiddlewareError(cause)
        except HTTPError:
            middleware_logger.error('Middleware server rejected our request by status code {}. Payload: {}. Response: {}'.format(
                request.status_code, payload, request.text))
            try:
                cause = request.json()['cause']
            except:
                cause = "Middleware server returns with an unexplianed status code {}.".format(
                    request.status_code)
            raise MWUpdateError(cause)
        self.response = request

    @staticmethod
    def gen_passwd():
        dict = ascii_letters + digits
        return ''.join(choice(dict) for _ in range(16))


class MWUpdateUser(baseMiddlewareAdopter):

    def __init__(self, user_email, api_server=OJBN_GITLAB_ADDR):
        middleware_logger.debug('Updating user {} on git.'.format(user_email))
        payload = {'email': user_email,
                   'password': baseMiddlewareAdopter.gen_passwd()}
        super().__init__(api_server=api_server, interface='/users', payload=payload)


class MWUpdateUserKey(baseMiddlewareAdopter):

    def __init__(self, user_email, user_key, api_server=OJBN_GITLAB_ADDR):
        middleware_logger.debug(
            'Updating user {}\'s key on git.'.format(user_email))
        payload = {'key': user_key}
        interface = '/users/{}/key'.format(quote(user_email))
        super().__init__(api_server=api_server, interface=interface, payload=payload)


class MWUpdateCourse(baseMiddlewareAdopter):

    def __init__(self, course_name, course_uid, api_server=OJBN_GITLAB_ADDR):
        middleware_logger.debug(
            'Updating course {}-{} on git.'.format(course_name, course_uid))
        course_uid = str(course_uid)
        payload = {"name": course_name.lower(), "uuid": course_uid}
        super().__init__(api_server=api_server, interface='/courses', payload=payload)


class MWCourseAddInstr(baseMiddlewareAdopter):

    def __init__(self, course_uid, instr_email, api_server=OJBN_GITLAB_ADDR):
        middleware_logger.debug(
            'Updating course {} instructor {} on git.'.format(course_uid, instr_email))
        course_uid = str(course_uid)
        payload = {"instructor_name": instr_email}
        interface = '/courses/{}/instructors'.format(course_uid)
        super().__init__(api_server=api_server, interface=interface, payload=payload)


class MWCourseAddAssignment(baseMiddlewareAdopter):

    def __init__(self, course_uid, assignment_name, assignment_uid, api_server=OJBN_GITLAB_ADDR):
        assignment_uid = str(assignment_uid)
        course_uid = str(course_uid)
        payload = {'name': assignment_name.lower(), 'uuid': assignment_uid}
        interface = '/courses/{}/assignments'.format(course_uid)
        super().__init__(api_server=api_server, interface=interface, payload=payload)


class MWCourseAddRepo(baseMiddlewareAdopter):
    def __init__(self, course_uid, assignment_uid, owner_email, ddl, owner_uid=None, repo_name=None, api_server=OJBN_GITLAB_ADDR):
        assignment_uid = str(assignment_uid)
        course_uid = str(course_uid)
        ddl = str(ddl.date())
        if isinstance(owner_uid, UUID):
            owner_uid = [str(owner_uid)]
        elif isinstance(owner_uid, list):
            for i in range(len(owner_uid)):
                owner_uid[i] = str(owner_uid[i])
        interface = "/courses/{}/assignments/{}/repos".format(
            course_uid, assignment_uid)
        if repo_name == None:
            if not isinstance(owner_email, list):
                repo_name = owner_email.split('@')[0].lower()
                owner_email = [owner_email]
            else:
                repo_name = 'group_' + \
                    "_".join(user.split('@')[0]for user in owner_email).lower()
        middleware_logger.debug(
            'Adding repo for course {} , assignment {} on git. Repo name: {}; owners: {}; addtional data: {}; deadline: {}'.format(course_uid, assignment_uid, repo_name, owner_email, owner_uid, ddl))
        payload = {'owners': owner_email, 'repo_name': repo_name,
                   'additional_data': simplejson.dumps(owner_uid), 'ddl': ddl}
        super().__init__(api_server=api_server, interface=interface, payload=payload)

class MWCourseDelRepo(baseMiddlewareAdopter):
    def __init__(self, course_uid, assignment_uid, owner_email, repo_name=None, api_server=OJBN_GITLAB_ADDR):
        assignment_uid = str(assignment_uid)
        course_uid = str(course_uid)
        if not repo_name:
            if isinstance(owner_email, list):
                repo_name = 'group_' + \
                    "_".join(user.split('@')[0]for user in owner_email).lower()
            else:
                repo_name = repo_name = owner_email.split('@')[0].lower()
        middleware_logger.debug(
            'Deleting repo for course {} , assignment {} on git. Repo name: {}; owners: {}.'.format(course_uid, assignment_uid, repo_name, owner_email))
        interface = "/courses/{}/assignments/{}/repos/{}".format(course_uid, assignment_uid, repo_name)
        super().__init__(api_server=api_server, interface=interface, action='DELETE')

def MW_if_user_exists(email):
    r = requests.get('/user/{}'.format(quote(email)))
    if r.status_code == 204:
        return True
    return False
# TODO:
# Write adopters for downloading a user's repo and get its commit history.
# This function requries the backend to act like a reserve proxy between user and middleware.
