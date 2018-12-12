# GeekPie OJ Project: Backend Part

*⚠️ 建设中*

This part provides a RESTful API of user management, course/assignment details for the GeekPie OJ Project. This project is devleloped using `Python 3.7`, ` Django 2.1.3` and also the latest version of `Django RESTful Framework` directly cloned from GitHub.

## Deploy

This project use `MySQL` as its database. Before installing, make sure you has an accessiable `MySQL` server. Also, this project is designed to work with other micro-service to provide a git-based online programming homework grading system.

Deploying using `Docker` is recommended. Make sure you set the following environment variables correctly before staring the service.


environment variable | description | example
---|---
`OJBN_DB_HOST` | the host where the database is hosted. | `localhost`
`OJBN_DB_NAME` | the database name. | `ojdb`
`OJBN_DB_USER` | the user used to acssess the database. | `geekpie`
`OJBN_DB_PASSWD` | the database password for the given user. | `gouliguojiashengsiyi`
`'OJBN_HOSTNAME'` | the `host` header allowed in a HTTP request. | `oj.geekpie.club`

## API Schema

### User Login/Logout

Registered at `/student/login` and `/student/logout` respectively. Users are required to login in order to access any API.

### Basic User Information

Supported method: `POST`, `GET`

Registered at `/student/<str:id>/` where id is the uid of the student in the database.

It will return the student's basic information, inluding `uid`, `name`, `email` and `student_id` in the following format.

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "王大锤",
    "email": "wangdch@shanghaitech.edu.cn",
    "student_id": "19260817"
}
```

### User Courses List

Supported method: `GET`

Registered at `/student/<str:id>/course/`.

It will return the courses in which the student with this `uid` enrolled in in the following format.

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "name": "Introduction to Computer Science",
        "code": "SI 100C",
        "semaster": "Fall",
        "year": 2017,
        "homepage": "https://shtech.org/course/si100c/17f/",
        "instructor":["Hao Chen", "Soren Sch"]
    }
]
```

### Course Assignment List

Supported method: `GET`

Registered at `/student/<str:id>/course/<str:course_id>` and `course/<str:course_id>/`.

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "name": "Homework1: Postfix Calculator",
        "deadline":  157000000,
        "release_date": 157000000,
        "descr_link": "https://shtech.org/course/si100c/17f/hw/1"
    }
]
```

### Student's submission history

Supported method: `GET`

Registered at `/student/<str:id>/course/<str:course_id>/<str:assignment_id>/history/`.

It provides student's submission history under an assignment.

```json
[
    {
        "git_commit_id": "b3b17c00f16511e8b3dfdca9047a0f14",
        "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "message": "1. Accepted\n",
        "score": 10,
        "overall_score": 10,
        "submission_time": 157000000,
        "delta": 0
    }
]
```

### Assignment Detail

Supported method: `GET`

Registered at `/course/<str:course_id>/<str:assignment_id>/`

```json
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "name": "Homework1: Postfix Calculator",
        "deadline":  157000000,
        "release_date": 157000000,
        "descr_link": "https://shtech.org/course/si100c/17f/hw/1"
    }
```

### Assignment Scoreboard

Supported method: `GET`

Registerd at `/course/<str:course_id>/<str:assignment_id>/scores/`

```json
[
    {
        "git_commit_id": "b3b17c00f16511e8b3dfdca9047a0f14",
        "nickname": "hammerLi",
        "score": 10,
        "overall_score": 10,
        "submission_time": 157000000,
        "delta": 0
    }
]
```

## Lisence

```
Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
```
