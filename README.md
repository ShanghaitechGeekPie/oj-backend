# GeekPie OJ Project: Backend Part

*⚠️ 建设中*

This part provides a RESTful API of user management, course/assignment details for the GeekPie OJ Project. This project is devleloped using `Python 3.7`, ` Django 2.1.3` and also the latest version of `Django RESTful Framework` directly cloned from GitHub.

## Deploy

This project use `MySQL` as its database. Before installing, make sure you has an accessiable `MySQL` server. Also, this project is designed to work with other micro-service to provide a git-based online programming homework grading system.

Deploying using `Docker` is recommended. Make sure you set the following environment variables correctly before staring the service.


environment variable | description | example
---|---|---|
`OJBN_DB_HOST` | the host where the database is hosted. | `localhost`
`OJBN_DB_NAME` | the database name. | `ojdb`
`OJBN_DB_USER` | the user used to acssess the database. | `geekpie`
`OJBN_DB_PASSWD` | the database password for the given user. | `gouliguojiashengsiyi`
`OJBN_HOSTNAME` | the `host` header allowed in a HTTP request. | `oj.geekpie.club`
`OJBN_GITLAB_ADDR` | the address where the gitlab middleware is hosted. | `localhost:8080`

## API Schema

### User Login/Logout

Registered at `/login` and `/logout` respectively. Users are required to login in order to access any API.

### For student

#### Student's Basic Information

Supported method: `POST`, `GET`

Registered at `/student/<str:id>/` where id is the uid of the student in the database.

It will return the student's basic information, inluding `uid`, `name`, `email` and `student_id` in the following format.

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "王大锤",
    "nickname": "hammerWang",
    "email": "wangdch@shanghaitech.edu.cn",
    "student_id": "19260817",
    "rsa_pub_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDwnExnO3zHIE16iR00SlZXSX468auyeGG7Vp2U5NRVdxXeeE1/Nn7HAWDzgB0Q8XNqcgkiobpBiCVvRO/H4tFi...."
}
```

#### Student's Courses List

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
        "instructor":["b3b17c00f16511e8b3dfdca9047a0f14", "b3b17c00f16511e8b3dfdca9047a0f14"]
    }
]
```

#### Student's submission history

This API is accessiable by instructor.

Supported method: `GET`

Registered at `/student/<str:id>/course/<str:course_id>/assignment/<str:assignment_id>/history/`.

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

#### Student's submission history

This API is accessiable by instructor.

Supported method: `GET`

Registered at `/student/<str:id>/course/<str:course_id>/assignment/<str:assignment_id>/history/<str:commit_id>`.

It provides student's one specific submission under an assignment.

```json
    {
        "git_commit_id": "b3b17c00f16511e8b3dfdca9047a0f14",
        "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "message": "1. Accepted\n",
        "score": 10,
        "overall_score": 10,
        "submission_time": 157000000,
        "delta": 0
    }
```

### For Course

#### Course's Assignment List

Supported method: `GET`

Registered at `course/<str:course_id>/assignment/`.

`overall_score` is the score the student get in his/she last commit.

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "name": "Homework1: Postfix Calculator",
        "deadline":  157000000,
        "release_date": 157000000,
        "descr_link": "https://shtech.org/course/si100c/17f/hw/1",
        "score": 3.14,
        "overall_score": 10.0
    }
]
```

#### Assignment Detail

Supported method: `GET`

Registered at `/course/<str:course_id>/assignment/<str:assignment_id>/`

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "Homework1: Postfix Calculator",
    "deadline":  157000000,
    "release_date": 157000000,
    "descr_link": "https://shtech.org/course/si100c/17f/hw/1",
    "score": 3.14,
    "overall_score": 10.0
}
```

#### Assignment Scoreboard

Supported method: `GET`

Registerd at `/course/<str:course_id>/assignment/<str:assignment_id>/scores/`

```json
[
    {
        "nickname": "hammerWang",
        "score": 10,
        "overall_score": 10,
        "submission_time": 157000000,
        "delta": 0
    }
]
```

#### Pending assignment list

Supported method: `GET`.

Registerd at `/course/<str:course_id>/queue`.

```json
[
    {
        "git_commit_id": "b3b17c00f16511e8b3dfdca9047a0f14",
        "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "submission_time": 157000000,
        "submitter": "hammerWang"
    }
]

```

#### Intructor's basic information

Supported method: `GET`

Registered at `/course/<str:course_id>/instructor/<str:instr_id>/`

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "Keyi Yuan",
    "email": "weidaxz@shanghaitech.edu.cn"
}
```


### For Instructor

NOTE: this part has not been fully implmented yet.

#### Instructor's Basic Information

Supported method: `POST`, `GET`

Registered at `/instructor/<str:id>/` where id is the uid of the student in the database.

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "王大锤",
    "email": "wangdch@shanghaitech.edu.cn",
    "rsa_pub_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDwnExnO3zHIE16iR00SlZXSX468auyeGG7Vp2U5NRVdxXeeE1/Nn7HAWDzgB0Q8XNqcgkiobpBiCVvRO/H4tFi...."
}
```

#### Instructor's Course list

Supported method: `POST`, `GET`

Registered at `/instructor/<str:uid>/course/`.

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "name": "Introduction to Computer Science",
        "code": "SI 100C",
        "semaster": "Fall",
        "year": 2017,
        "homepage": "https://shtech.org/course/si100c/17f/",
        "instructor":["b3b17c00f16511e8b3dfdca9047a0f14", "b3b17c00f16511e8b3dfdca9047a0f14"]
    }
]
```


#### Course basic information

Supported method: `POST`, `GET`, `DELETE`

Registered at `/course/<str:id>`.

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "Introduction to Computer Science",
    "code": "SI 100C",
    "semaster": "Fall",
    "year": 2017,
    "homepage": "https://shtech.org/course/si100c/17f/",
    "instructor":["b3b17c00f16511e8b3dfdca9047a0f14", "b3b17c00f16511e8b3dfdca9047a0f14"]
}
```

#### Course students list

Supported method: `POST`, `GET`

Registered at `/course/<str:id>/students/`.

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "name": "王大锤",
        "email": "wangdch@shanghaitech.edu.cn",
        "student_id": "19260817",
    }
]
```

#### Course student

Supported method: `POST`, `GET`, `DELETE`

Registered at `/course/<str:id>/students/<id:uid>`.

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "王大锤",
    "email": "wangdch@shanghaitech.edu.cn",
    "student_id": "19260817",
}
```

#### Course instrctors list

Supported method: `POST`, `GET`

Registered at `/course/<str:id>/instructor/`

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "name": "Keyi Yuan",
        "email": "weidaxz@shanghaitech.edu.cn"
    }
]
```

#### Course instructor

Supported method: `GET`, `POST`, `DELETE`

Registered at `/course/<str:id>/instructor/<str:uid>`

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "Keyi Yuan",
    "email": "weidaxz@shanghaitech.edu.cn"
}
```

#### Course assignments list

Supported method: `GET`, `POST`

Registered at `/course/<str:id>/assignment/`

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

TODO: export all assignments.

#### Course assignment

Supported method: `GET`, `POST`, `DELETE`

Registered at `/course/<str:id>/assignment/<str:uid>`

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

#### Course judges list

Supported method: `GET`, `POST`

Registered at `/course/<str:id>/judge/`

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    }
]
```

#### Course judge

Supported method: `GET`, `POST`, `DELETE`

Registered at `/course/<str:id>/judge/<str:uid>`

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
}
```

#### Judges list

Suppoerted method: `GET`, `POST`

Registered at `/judge/`

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "host": "10.19.171.56:443",
        "cert": "thisisthecert",
        "max_job": 4
    }
]
```

#### Judge

Supported method: `GET`, `POST`, `DELETE`

Registered at `/judge/<str:uid>`

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "host": "10.19.171.56:443",
    "cert": "thisisthecert",
    "max_job": 4
}
```

## Interface for internal communication

### Interface with `oj-middleware*`

Supported method: `POST`

Registered at `/internal/subbmission`.

Authorization: TBD

```json
{
    "assignment_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "upstream": "git@git.oj.geekpie.club/si100c-17f/hw1-diaozh.git"
}
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
