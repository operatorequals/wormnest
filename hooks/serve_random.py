import hooker
from wormnest.utils import check_filename_for_hook
import os, sys
import tempfile


@hooker.hook("on_request")
def serve_random(filename, retval={}):
	func_name = sys._getframe().f_code.co_name
	if not check_filename_for_hook(filename, func_name):
		return None

	fd = tempfile.NamedTemporaryFile('rb')
	generated_file = fd.name

	# generated_file = "/tmp/rand_gen"
	command = "dd if=/dev/urandom of={} count=128".format(generated_file)
	print("[!] '{}'".format(command))
	os.system(command)

	# try:
	# 	# fd = open(generated_file, 'rb')
	# 	fd = TemporaryFile(generated_file, 'rb')
	# except FileNotFoundError:
	# 	print ("[-] Could not Return the Fresh MSF payload")
	# 	fd = None
	# except Exception:
	# 	print ("[-] " + e)

	retval['fd'] = fd
	return fd

