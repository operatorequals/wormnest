"""
This hook serves a random file in an existing directory.
The 'path' when using the /add endpoint has to point to that directory.

Useful when you don't want to spread the same malware,
but generating on request is takes time.

Just pre-generate a bunch of executables, HTAs, whatevers and put them in the folder
"""
import hooker
import os
import random


@hooker.hook("pre_file")
def random_from_directory(filename, request):

	# If not a directory, this hook is not handling th request
	if not os.path.isdir(filename): return None

	dir_contents = os.listdir(filename)
	if not dir_contents : return None

	chosen_file = random.choice(dir_contents)
	full_name = os.path.join(filename, chosen_file)
	fd = open(full_name, 'rb')

	return fd