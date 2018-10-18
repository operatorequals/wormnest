"""
This hook serves a different wormnest alias
depending on string found in Request's User Agent

"""
import hooker
from wormnest.utils import check_filename_for_hook

from flask import redirect
import os, sys
import random
import urllib3
import io

'''
This dict has keys/values of String/Alias.
If a key is found in the processed user agent,
the response will serve the corresponding alias 

Please configure according to the needs:
'''
UA_Urls =  {
	
	'win' : "",
	'lin' : "",
	'mac' : "",
	'ios' : "",
	'android' : "",
	'DEFAULT' : "goaway"
}

'''
This hook can serve using 2 Behaviors:
PROXY: serves the file directly from the alias that triggered the hook (no change in client's URL bar)
REDIRECT: serves a 302 HTTP Redirect to the corresponding alias
'''
Behaviors = ['PROXY', "REDIRECT"]
Behavior = Behaviors[1]

http = urllib3.PoolManager()

@hooker.hook("on_request")
def os_dependent_serve(filename, request, retvals={}):

	# If not a directory, this hook is not handling th request
	func_name = sys._getframe().f_code.co_name
	if not check_filename_for_hook(filename, func_name):
		return None
	print ("Running the HOOK")

	ua = request.headers.get("User-Agent", "N/A")

	final_url = UA_Urls['DEFAULT']
	for key, value in UA_Urls.items():
		if key.lower() in ua.lower():
		 	final_url = UA_Urls[key]
		 	break

	final_url = request.url_root + final_url

	if Behavior == "PROXY":
		response = http.request('GET', final_url, preload_content=False)
		file = response
		retvals['fd'] = file
		return file

	else Behavior == "REDIRECT":
		ret = redirect(final_url, code=302)
		retvals['resp'] = ret
		return ret
	# fd = tempfile.NamedTemporaryFile('rb', suffix=extension)
