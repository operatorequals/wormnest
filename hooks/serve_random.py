'''
This hook serves random data when a certain filename is requests
Serves as Hook Coding Example/Template. No Practical use...
'''
import hooker
from wormnest.utils import check_filename_for_hook
import os, sys
import tempfile

@hooker.hook("on_request")  # <-- This declares a hook when a GET request is made
def serve_random(filename, request, retvalss={}):
	'''
filename: The filename that is registered as returned file. Most of the time non-existent
request: The Flask request object that triggered the hook
retvals: Hooker reserved dict. The return value is expected in the 'fd' key.
	'''
  # Standard code, checks if the requested filename contains this function's name before the last dot.
  # This is used as sign to trigger the rest of the code.
	func_name = sys._getframe().f_code.co_name
	if not check_filename_for_hook(filename, func_name):
		return None

  # A Temporary File is created - read only
	fd = tempfile.NamedTemporaryFile('rb')
	generated_file = fd.name

  # A 'dd' command to get random data populated in the file
	command = "dd if=/dev/urandom of={} count=128".format(generated_file)
	print("[!] '{}'".format(command))
	os.system(command)

  # The file is returned using the 'hookers' interface
	retvals['fd'] = fd
  # Irrelevant
	return fd