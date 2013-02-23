========
Changes
========


jsonTV .1.1
------------

* HTTP responses other than 200 now use the requests 
  library error raising.
* Errors returned in JSON (via SchedulesDirect) now 
  raise JSONErrors.
* Adjusted the example readout.py, now takes 2 args, 
  username and password
* All methods now return either the response object 
  (converted to Python) or a ZippedJsonHandler, with
  exception to get_randhash which returns True (or 
  raises a JSONError).

jsonTV .1
------------

* Initial commit
