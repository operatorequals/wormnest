"""
This hook serves a random file in an existing directory.
The 'path' when using the /add endpoint has to point to that directory

Useful 
"""
import hooker
from wormnest.utils import check_filename_for_hook
import os, sys
import random


@hooker.hook("on_request")
def random_from_directory(filename, request, retval={}):

  # Standard code, checks if the requested filename contains this function's name before the last dot.
  # This is used as sign to trigger the rest of the code.
	func_name = sys._getframe().f_code.co_name
	if not check_filename_for_hook(filename, func_name):
		return None

	# If not a directory, this hook is not handling th request
	if not os.path.isdir(filename): return None

	dir_contents = os.listdir(filename)
	if not dir_contents : return None

	chosen_file = random.choice(dir_contents)
	full_name = os.path.join(filename, chosen_file)
	fd = open(full_name, 'rb')

	retval['fd'] = fd
	return fd