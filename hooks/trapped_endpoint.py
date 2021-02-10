import json
import time

import hooker

trigger_alias = 'action.php'
LOGFILE = 'wormnest_trap.ndjson'

@hooker.hook("pre_process")  # <-- This declares a hook when a GET request arrives 
def trapped_endpoint(request, url_alias):
    if trigger_alias not in url_alias:
        return None
    log_line = {
		'ip' : request.remote_addr,
                'host' : request.host,
                'referrer' : request.referrer,
                'protocol' : request.scheme,
                'method' : request.method,
		'path' : request.full_path,
		'time' : time.time(),
                'data' : str(request.get_data(),'utf8') if not request.is_json else None,
                'json_data' : request.get_json(),
                'headers' : dict(request.headers)
                }
    with open(LOGFILE, 'a') as logs:
        print (json.dumps(log_line), file=logs)


