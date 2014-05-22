# Copyright 2014 Christopher Richard Dobbs <christopher.dobbs@evry.com>.
#
# This file is part of the python-fecru library.
#
# python-fecru is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# python-fecru is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with python-fecru.  If not, see <http://www.gnu.org/licenses/>.
#  
import json
import requests


class FecruServer(object):
    """Fecru server authentication object."""

    def __init__(self, fecru_url, app_name, app_pass):
        self.fecru_url = fecru_url
        self.app_name = app_name
        self.app_pass = app_pass
        self.rest_url = fecru_url.rstrip("/") + "/rest-service/auth-v1/login"
        self.session = requests.Session()
        self.session.auth = requests.auth.HTTPBasicAuth(app_name, app_pass)
        self.session.headers.update({
            "Content-type": "application/json",
            "Accept": "application/json"
        })


#           self.atlas= httplib.HTTPConnection(self.url)
#            args=urllib.urlencode({'userName':self.usr, 'password':self.psw})
#            headers={'accept':'application/json'}
#            self.atlas.request("post", "/rest-service/auth-v1/login", args, headers)
#            r = conn.getresponse() 
#            if r.status not in (200, 304):
#                raise Exception("Problems getting a token from codereview. %s %s" % (r.status, r))
#            else:
#                print "connected OK to FECRU!!! %s:%s"%(conn, r)           
#            print "RTN:%s"%self.atlas

        

    def __str__(self):
        return "Crowd Server at %s" % self.crowd_url

    def __repr__(self):
        return "<CrowdServer('%s', '%s', %s')>" % \
            (self.crowd_url, self.app_name, self.app_pass)

    def _get(self, *args, **kwargs):
        """Wrapper around Requests for GET requests

        Returns:
            Response:
                A Requests Response object
        """
        req = self.session.get(*args, **kwargs)
        return req

    def _post(self, *args, **kwargs):
        """Wrapper around Requests for POST requests

        Returns:
            Response:
                A Requests Response object
        """
        req = self.session.post(*args, **kwargs)
        return req

    def _delete(self, *args, **kwargs):
        """Wrapper around Requests for DELETE requests

        Returns:
            Response:
                A Requests Response object
        """
        req = self.session.delete(*args, **kwargs)
        return req

    def auth_ping(self):
        """Test that application can authenticate to Crowd.

        Attempts to authenticate the application user against
        the Crowd server. In order for user authentication to
        work, an application must be able to authenticate.

        Returns:
            bool:
                True if the application authentication succeeded.
        """

        url = self.rest_url + "/non-existent/location"
        response = self._get(url)

        if response.status_code == 401:
            return False
        elif response.status_code == 404:
            return True
        else:
            # An error encountered - problem with the Crowd server?
            return False

    def get_users(self):
        """Return all users for this application on the Crowd server.

        Args:
            None

        Returns:
            dict:
                A list of user found.
                

            None: If failure.
        """            
        response = self._get(self.rest_url + "/search",
                             params={"entity-type": "user"})

        if not response.ok:
            return None

        return [g['name'] for g in response.json()['users']]

    def auth_user(self, username, password):
        """Authenticate a user account against the Crowd server.

        Attempts to authenticate the user against the Crowd server.

        Args:
            username: The account username.

            password: The account password.

        Returns:
            dict:
                A dict mapping of user attributes if the application
                authentication was successful. See the Crowd documentation
                for the authoritative list of attributes.

            None: If authentication failed.
        """

        response = self._post(self.rest_url + "/authentication",
                              data=json.dumps({"value": password}),
                              params={"username": username})

        # ...otherwise return a dictionary of user attributes
        return True

    def add_user_to_group(self, username, group):
        """Add a user to group.


        Args:
            username: The account username.

            group: Group name

        Returns:
 
            None: If authentication failed.
        """

        response = self._post(self.rest_url + "/user/group/direct",
                              data=json.dumps({"name": group}),
                              params={"username": username})

        if response.ok:
            return True

        return(response)


    def get_session(self, username, password, remote="127.0.0.1"):
        """Create a session for a user.

        Attempts to create a user session on the Crowd server.

        Args:
            username: The account username.

            password: The account password.

            remote:
                The remote address of the user. This can be used
                to create multiple concurrent sessions for a user.
                The host you run this program on may need to be configured
                in Crowd as a trusted proxy for this to work.

        Returns:
            dict:
                A dict mapping of user attributes if the application
                authentication was successful. See the Crowd
                documentation for the authoritative list of attributes.

            None: If authentication failed.
        """

        params = {
            "username": username,
            "password": password,
            "validation-factors": {
                "validationFactors": [
                    {"name": "remote_address", "value": remote, }
                ]
            }
        }

        response = self._post(self.rest_url + "/session",
                              data=json.dumps(params),
                              params={"expand": "user"})

        # If authentication failed for any reason return None
        if not response.ok:
            return None

        # Otherwise return the user object
        return response.json()

    def validate_session(self, token, remote="127.0.0.1"):
        """Validate a session token.

        Validate a previously acquired session token against the
        Crowd server. This may be a token provided by a user from
        a http cookie or by some other means.

        Args:
            token: The session token.

            remote: The remote address of the user.

        Returns:
            dict:
                A dict mapping of user attributes if the application
                authentication was successful. See the Crowd
                documentation for the authoritative list of attributes.

            None: If authentication failed.
        """

        params = {
            "validationFactors": [
                {"name": "remote_address", "value": remote, }
            ]
        }

        url = self.rest_url + "/session/%s" % token
        response = self._post(url, data=json.dumps(params), params={"expand": "user"})

        # For consistency between methods use None rather than False
        # If token validation failed for any reason return None
        if not response.ok:
            return None

        # Otherwise return the user object
        return response.json()

    def terminate_session(self, token):
        """Terminates the session token, effectively logging out the user
        from all crowd-enabled services.

        Args:
            token: The session token.

        Returns:
            True: If session terminated

            None: If session termination failed
        """

        url = self.rest_url + "/session/%s" % token
        response = self._delete(url)

        # For consistency between methods use None rather than False
        # If token validation failed for any reason return None
        if not response.ok:
            return None

        # Otherwise return True
        return True

    def group_exists(self, groupname):
        """Determines if the group exists.

        Args:
            groupname: The group name.


        Returns:
            bool:
                True if the group exists in the Crowd application.
        """

        response = self._get(self.rest_url + "/group",
                             params={"groupname": groupname})

        if not response.ok:
            return None

        return True

    def delete_user(self, username):
        """Delete a username.

        Args:
            username: The user name.


        Returns:
            bool:
                True if successfull
        """

        response = self._delete(self.rest_url + "/user",
                             params={"username": username})

        if not response.ok:
            return None

        return True

    def add_group(self, group):
        """Add a new group


        Args:
            group: Group name

        Returns:
 
            None: If failed.
        """


        params = {
            "name": group,
            "type": "GROUP",
            "description": group,
            "active": "true"
        }


        response = self._post(self.rest_url + "/group",
                              data=json.dumps(params))

        if not response.ok:
            return False

        return(response)

    def add_user(self, usr, psw, email, dname, fname, lname):
        """Add a new usr


        Args:
            dict

        Returns:
 
            None: If failed.
        """
        usr_dict = {
            "name" : usr,
            "first-name" : fname,
            "last-name" : lname,
            "display-name" : dname,
            "email" : email,
            "password" : {
                "value" : psw
                },
            "active" : "true"
            }

#        print "Add user to %s"%self.rest_url
        response = self._post(self.rest_url + "/user",
                              data=json.dumps(usr_dict))

        if not response.ok:
            return False

        return(response)

    def remove_user_from_group(self, username, group):
        """Removes a user from a group.

        Returns:
            None: If failed.
        """
        usr_dict = {
            "groupname" : group,
            "username" : username
        }
        
        #DELETE /group/user/direct?groupname=GROUPNAME&username=USERNAME
        response = self._delete(self.rest_url + "/user/group/direct",
                              params={"groupname": group, "username": username})

        return(response)

    def get_groups(self, username):
        """Retrieves a list of group names that have <username> as a direct member.

        Returns:
            list:
                A list of strings of group names.
        """

        response = self._get(self.rest_url + "/user/group/direct",
                             params={"username": username})

        if not response.ok:
            return None

        return [g['name'] for g in response.json()['groups']]

    def get_nested_groups(self, username):
        """Retrieve a list of all group names that have <username> as a direct or indirect member.

        Args:
            username: The account username.


        Returns:
            list:
                A list of strings of group names.
        """

        response = self._get(self.rest_url + "/user/group/nested",
                             params={"username": username})

        if not response.ok:
            return None

        return [g['name'] for g in response.json()['groups']]

    def get_nested_group_users(self, groupname):
        """Retrieves a list of all users that directly or indirectly belong to the given groupname.

        Args:
            groupname: The group name.


        Returns:
            list:
                A list of strings of user names.
        """

        response = self._get(self.rest_url + "/group/user/nested",
                             params={"groupname": groupname,
                                     "start-index": 0,
                                     "max-results": 99999})

        if not response.ok:
            return None

        return [u['name'] for u in response.json()['users']]

    def user_exists(self, username):
        """Determines if the user exists.

        Args:
            username: The user name.


        Returns:
            bool:
                True if the user exists in the Crowd application.
        """

        response = self._get(self.rest_url + "/user",
                             params={"username": username})

        if not response.ok:
            return None

        return True
