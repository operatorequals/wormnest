'''
This hook serves random data when a certain filename is requests
Serves as Hook Coding Example/Template. No Practical use...
'''
import hooker
from wormnest.utils import check_filename_for_hook
import os, sys
import tempfile

trigger_filename = "random_file.bin"

@hooker.hook("pre_file")  # <-- This declares a hook when a GET request is made
def serve_random(filename, request):
	'''
filename: The filename that is registered as returned file. Most of the time non-existent
request: The Flask request object that triggered the hook
	'''
  # Standard code, checks if the "trigger_filename" is in the requested filename 
  # This is used as sign to trigger the rest of the code.
	if trigger_filename not in filename:
		return None

  # A Temporary File is created - read only
	fd = tempfile.NamedTemporaryFile('rb')
	generated_file = fd.name

  # A 'dd' command to get random data populated in the file
	command = "dd if=/dev/urandom of={} count=128".format(generated_file)
	print("[!] '{}'".format(command))
  #	Not using Python's "random" to show how to escape to shell for file creation
  #	Useful for script calling to create custom files (msfvenom, etc)
	os.system(command)

	return fd