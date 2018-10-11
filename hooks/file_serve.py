
import hooker
# from wormnest.utils import check_filename_for_hook
import os

hooker.hook("on_request")
def file_serve(filename):
	
	func_name = sys._getframe().f_code.co_name
	if not check_filename_for_hook(filename, func_name): return None

	fd = open(filename, 'rb')
	return fd