from __future__ import with_statement, print_function
"""Copyright 2013 Justin Hall

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

""" Schedules Direct API Access

This module accesses Schedules Direct's new JSON API (in beta) and returns
the data as a python dict/list.
"""
import sys
import json
import hashlib
import zipfile
import requests
from io import BytesIO

class JSONError(Exception):
    """ Exception raised based on results from the server. This will
    likely get replaced once SD implements relevant HTTP response codes
    
    Attributes:
        code   -- the "HTTPish" error
        msg    -- the explanation of the error
    """
    def __init__(self, code, msg):
        self.code = code
        self.action = action


class UnknownActionError(Exception):
    """ Exception raised when an action is called that doesn't exist
    
    Attributes:
        action -- the called action that doesn't exist
        msg    -- the explanation of the error
    """
    def __init__(self, action, msg):
        self.action = action
        self.msg = msg


class _Request(object):
    """ Handles building and sending requests and parsing responses"""

    def __init__(self, base_url, api_version):
        """ Set the default arguments
        
        Attributes:
            base_url -- the base_url of the json server
            api_version -- the current api version
        """
        self.base_url = base_url
        self.api_version = api_version
        self.response = None
        self.is_json = True

    def send_request(self):
        """ Sends the payload via the requests library

        Attributes:
            base_url    -- the base_url of the ,json server
            api_version -- the current api version
        """        
        payload = {'request': json.dumps(self.payload, separators=(',', ':')), 'submit': 'submit' }
        self.response = requests.post(self.base_url, data=payload)
        self.response.raise_for_status();
    
    def generate_request(self, action, request, randhash=None):
        """ Generates the request json object
        
            Attributes:
                action   -- the action required (get, set, update, delete)
                request  -- the object being requested
                randhash -- the random hash key generated by SD
        """
        self.payload = {'api': self.api_version, 
                   'action': action, 
                   'object': request}
    
        if (randhash is not None):
            self.payload['randhash'] = randhash
            
    def get_response_text(self):
        """ Attempts to decode the jston response string. If a TypeError 
            occurs we assume it's a zip archive.
        
            Attributes:
                response -- the requests response object
        """
        try:
            self.is_json = True
            return json.loads(self.response.text)
        except TypeError:
            self.is_json = False
            return BytesIO(self.response.content)


class ZipedJsonHandler(object):
    """ Handles zipped, json-formatted files """
    def __init__(self, memory_zip):
        """ Set default
        
        Attributes:
            memory_zip -- the in memory zip file (string)
        """
        self.zipfile = zipfile.ZipFile(memory_zip)
        
    def read(self):
        """ A generator that reads the in memory zip files, opens them 
            and returns the content, one file at a time. 
        """
        file_content = {}

        with self.zipfile as zipfile:
            for files in zipfile.namelist():
                if files == 'serverID.txt':
                    continue
                self.file_name = files.replace('.json.txt', '')
                file_pointer = zipfile.open(files)
                file_bytes = file_pointer.read()
                """ Could be a more useful class if it didn't assume
                that content of txt files are JSON """
                file_content = json.loads(file_bytes.decode('utf-8'))
                yield file_content


class SchedulesDirect(object):
    """ Interface for the Schedules Direct API """
    base_url = 'https://data2.schedulesdirect.org/request.php'
    api_version = 20130107
    get_options = ['status', 'headends', 'lineups', 'programs', 'schedules', 'randhash', 'metadata']
    request = _Request(base_url, api_version)

    def __init__(self, username, password):
        """ Sets the default values and sha1's the password
        
        Attributes:
            username -- SchedulesDirect username
            password -- SchedulesDirect password (plain text)
        """
        self.username = username
        self.password = hashlib.sha1(password.encode('utf-8')).hexdigest()
        self.randhash = None
        self.use_randhash = False

    def _get_action(self, option):
        """ Validates whether the requested object is valid not sure if this is entirely 
            neccesary since we are interfacing via getters/setters
        
        Attributes:
            object -- the object we are requesting

        """
        if option in SchedulesDirect.get_options: 
            return option
        else: 
            return None

    def _generate_request(self, action, request):
        """ Preps for _Request:generate_request() lineups
        
        Attributes:
            object -- the object we are requesting
        """
        request = self._get_action(request)
        
        if self.use_randhash:
            randhash = self.randhash
        else:
            randhash = None
        
        if request is not None:
            self.request.generate_request(action, request, randhash)
        else:
            raise UnknownActionError(request, 'The requested object does not exist.')

    def _send_request(self):
        """ Preps for _Request:send_request() """
        self.request.send_request()
        self.response = self.request.get_response_text()
        
        if self.response['response'] == "ERROR" and self.response.is_json:
            raise JSONError(self.response['code'], self.response['message']);
        
    def get_randhash(self):
        """ Requests a random hashkey from the SD server """
        self._generate_request('get', 'randhash')
        self.request.payload.update({'request': {'password': self.password, 'username': self.username }})
        
        self.randhash = self.response['randhash']
        self.use_randhash = True
        return True

    def get_status(self):
        """ Requests the servers status"""
        self._generate_request('get', 'status')
        return self.response

    def get_subscribed_headends(self, zipcode=None):
        """ Gets the headends the user is currently subscribed to
        
        Attributes:
            zipcode -- limits the headends to those within this zipcode
        """
        self._generate_request('get', 'headends')
        
        if zipcode is not None:
            self.request.payload['request'] = 'PC:' + str(zipcode)
        
        return self.response
         
    def get_headends(self, zipcode):
        """ Gets the headends available in zipcode
        
        Attributes:
            zipcode -- the zipcode to search with
        """
        self.use_randhash = False
        headends = self.get_subscribed_headends(zipcode)
        self.use_randhash = True
        return headends

    def add_headend(self, headend, action_type='add'):
        """ Adds a headend to the users account
        
        Attributes:
            headend -- the headend id to add
        """
        self._generate_request(action_type, 'headends')
        self.request.payload['request'] = headend
        
        return self.response
            
    def delete_headend(self, headend):
        """ Adds a headend to the users account
        
        Attributes:
            headend -- the headend id to add
        """
        return self.add_headend(headend, 'delete')
        
    def get_lineups(self, headend, obj='lineups'):
        """ Gets the lineups for the requested headends
        
        Attributes:
            headend -- the headend id (str) or ids (list) to get lineups for
        """
        self._generate_request('get', obj)

        try:
            headends = [] + headend
        except:
            headends = [headend]

        self.request.payload['request'] = headends;
                
        lineup = ZipedJsonHandler(self.response)
        return lineup

    def get_schedules(self, station):
        """ Gets the schedules for the requested station(s). Calls get_lineups
        
        Attributes:
            station -- the station id
        """
        return self.get_lineups(station, 'schedules')
            
    def get_programs(self, program):
        """ Gets the requested program(s). Calls get_lineups
        
        Attributes:
            schedule -- the program id
        """
        return self.get_lineups(program, 'programs')
        
    def update_metadata(self, program_id, source, comment, field, current, suggested):
        """ Gets the requested program(s). Calls get_lineups
        
        Attributes:
            source -- the source of the data (tvdb)
            comment -- a 1024 character explanation of the error
            suggested -- the value to change the seriesID to (0 implies there IS no replacement)
            current -- the value to change the seriesID from (0 implies there isn't one, but should be)
            program_id -- the programID (see get_programs)
            field -- the field that's incorrect (seriesID)
        """
        self._generate_request('update', 'metadata')
            
        data = {'request': {}}
        data['request']['source'] = source
        data['request']['comment'] = comment
        data['request']['suggested'] = suggested [:1024]
        data['request']['current'] = current
        data['request']['program_id'] = program_id
        data['request']['field'] = field
        
        self.request.payload['request'] = data

        return True
