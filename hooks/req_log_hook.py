import hooker
import os, sys
import json
import hashlib
import time
LOGFILE = 'wormnest_access.ndjson'

@hooker.hook("pre_file")  # <-- This declares a hook just before a file is served 
def req_log_hook(filename, request):
    with open(filename, 'rb') as f:
        log_line = {
		'ip' : request.remote_addr,
                'host' : request.host,
                'referrer' : request.referrer,
                'protocol' : request.scheme,
                'method' : request.method,
		'ua' : request.headers.get("User-Agent", "N/A"),
		'path' : request.full_path,
                'filename' : filename,
                'md5' : hashlib.md5(f.read()).hexdigest(),
		'time' : time.time()
                }
    with open(LOGFILE, 'a') as logs:
        print (json.dumps(log_line), file=logs)

@hooker.hook("pre_process")  # <-- This declares a hook when a GET request arrives 
def req_log_hook(request, url_alias):
    log_line = {
		'ip' : request.remote_addr,
                'host' : request.host,
                'referrer' : request.referrer,
                'protocol' : request.scheme,
                'method' : request.method,
		'ua' : request.headers.get("User-Agent", "N/A"),
		'path' : request.full_path,
		'time' : time.time()
                }
    with open(LOGFILE, 'a') as logs:
        print (json.dumps(log_line), file=logs)


   
