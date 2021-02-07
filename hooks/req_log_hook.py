import hooker
from wormnest.utils import check_filename_for_hook
import os, sys
import tempfile

@hooker.hook("pre_process")  # <-- This declares a hook when a GET request is made
def req_log_hook(request, url_alias):
	log_line = "{ip} - {method} - '{ua}' - '{url}'".format(
		ip = request.remote_addr,
                method = request.method,
		ua = request.headers.get("User-Agent", "N/A"),
		url = request.full_path,
		)
	print (log_line)
