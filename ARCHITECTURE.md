# Architecture

## Frontend:
- HTML/CSS for constructing the skeleton of the page
- Standard JS API supported by most of the browsers

## Gateway:
- Go

## Database:
- PostgreSQL

## Communication:
- REST API

## System overview:
Browser
    |
    v
Go HTTP Server
    |
    v
PostgreSQL

## Website Pages:

Pages

- Home
- Members
- News
- Events
- Datasets
- Projects
- Publications
- Contacts

## User roles:

Roles

1. Visitor:
    - Read public pages

2. Administrator:
    - Create news
    - Create events
    - Edit members
    - Upload datasets

## Database entities

Photo
Administrator
Manager
Sessions
Events
ListOfParticipants
ISMLabMembers
Projects
Announcements
Publications
Datasets

## REST Endpoints

GET /api/photo/list/?Q
- This route must return the array of MIMETYPE objects. Here Q is either photo_id=# 
or photo_url=#. All users can access this route: visitors, admins, managers.

POST /api/photo/create/
- This route must recieve a MIMETYPE of a photo object and save it in the database with 
relevant URL, and generated photo ID. Only admin/manager.

PUT /api/photo/update/?Q
- This route must rewrite the photo uploaded previosly. The updating photo can be identified by
either url=# as Q or photo_id=# as Q. Only for admin/manager.

DELETE /api/photo/erase/?Q
- This route is for deleting the choosen photo. Here Q could be photo_id=# or photo_url=#. 
Both admins and managers can access this route.

GET /api/manager/list/?Q
- This route provides the manager's data. Here Q can be equal to mng_login=#, or mng_email=#,
or target=all. Only admin/manager can access this route.

POST /api/manager/create/
- This route creates a new manager. This route is accesible only for administrator.

PUT /api/manager/update/?Q
- This route allows the user to update personal data of the manager. It is accesible by
manager and administrator. Here the Q can be mng_login=# or mng_email=#.

DELETE /api/manager/erase/?Q
- This route allows the user to delete the particular manager. It is accesible by admin only.
Here the Q can be equal to mng_login=# or mng_email=#.

GET /api/sessions/active/
- This route is for getting the list of active managers and admins. This route is accesible
only by administrator and managers.

POST /api/sessions/login/
- This route is for logging in. It must receive the login/email, and then, password hash and sign the user.
Accesible for administrators and managers.

PUT /api/sessions/refresh/
- This route is for getting the fresh session-id token. It is accesible for logged managers and admins.

DELETE /api/sessions/logout/
- This route is for logging out of the session. It is accesible for logged managers and admins.

GET /api/events/list/?Q
- This route is for getting the events data. Here Q could be target=all, or event_id=#. 
It is accesible for visitors, managers, admins.

POST /api/events/create/
- This route is for creating a new event. It is available for managers and admins.

PUT /api/events/update/?Q
- This route is for updating the information for the event. Here Q can be event_id=#. Only managers and admins 
can access this route.

DELETE /api/events/erase/?Q
- This route is for deleting the event. Here Q can be event_id=#. Only admins can access this route.
No managers.

GET /api/participants/list/?Q
- This route is for getting the data about the participants of some event. Here Q could be target=all, or 
participant_id=#, or attending_event=#. This route is for visitors, admins, and managers.

POST /api/participants/create/
- This route is for creating a new participants. It is for managers and admins.

PUT /api/participants/update/?Q
- This route is for updating a participant information. Here Q could be participant_id=#.
This route is accesible for managers and admins.

DELETE /api/participants/erase/?Q
- This route is for deleting a participant from the list. Here Q could be participant_id=#.
This route is accesible for admins only. No managers.

GET /api/members/list/?Q
- This route is for getting the information about a lab member. Here Q could be member_id=#, or member_email=#,
or target=all. This route is accesible for all of the users: visitors, managers, admins.

POST /api/members/create/
- This route is for creating a new member. It can be accessed by managers and admins.

PUT /api/members/update/?Q
- This route is for updating the personal information of the members of the lab. Here Q can be member_id=#, or
member_email=#. Only managers and admins can access this route.

DELETE /api/members/erase/?Q
- This route is for deleting the particular member. Here Q could be member_id=#, or member_email=#. Only admins
can access this route. No managers.

GET /api/projects/list/?Q
- This route is for aggregating the information about the projects. Here Q could be project_id=#, or target=all.
All of the users can access this route: visitors, admins, managers.

POST /api/projects/create/
- This route is for creating a new project page. It is accesible for managers and admins only. 

PUT /api/projects/update/?Q
- This route is for updating the project page. Here Q could be project_id=#. It is only for admins 
and managers.

DELETE /api/projects/erase/?Q
- This route is for deleting the project page. Here Q could be project_id=#. It is for admins. No managers.

GET /api/announcements/list/?Q
- This route is for fetching the information about the announcements. Here Q can be announce_id=#, 
or target=all. All users can access this route: visitors, managers, admins.

POST /api/announcements/create/
- This route is for creating an announcement. Only managers and admins can access this route.

PUT /api/announcements/update/?Q
- This route is for updating the information about announcements. Here Q can be announce_id=#. This route
is accessible for managers and admins. 

DELETE /api/announcements/erase/?Q
- This route is for deleting the announcement page. Here Q can be announce_id=#. This route is accesible for
admin users only. No managers.

GET /api/publications/list/?Q
- This route is for fetching data about publications. Here Q can be pub_id=#, or target=all. 
All users can access it: visitors, managers, admins.

POST /api/publications/create/
- This route is for creating a new data block about a publication. It accesible for managers and admins.

PUT /api/publications/update/?Q
- This route is for updating the information about the publications. Here Q can be pub_id=#. Only managers
and administrators can access this route.

DELETE /api/publications/erase/?Q
- This route is for deleting the publication data. Here the Q can be pub_id=#. Only admins can access this route. 
No managers.

GET /api/datasets/list/?Q
- This route is for fetching the information about datasets. Here Q can be data_id=#, or target=all. 
It is accessible for everybody: visitors, admins, managers.

POST /api/datasets/create/
- This route is for creating a new block of page for datasets. Only admins and managers can access it.

PUT /api/datasets/update/?Q
- This route is for updating the dataset information. Here Q can be only data_id=#. Managers and admins can access it.

DELETE /api/datasets/erase/?Q
- This route is for deleting the page about dataset. Here Q can be only data_id=#. Only admins can access it. 
No managers.
