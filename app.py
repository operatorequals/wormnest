
from flask import Flask
from flask import flash,request,send_file,send_from_directory,redirect,render_template, abort

from werkzeug.utils import secure_filename
from ipaddress import ip_address, ip_network


import os
import random
import imp

import requests
import hooker

hooker.EVENTS.append("pre_process",
	help="Before any processing of the URL alias starts. Useful for UA filters, blacklists, etc")
hooker.EVENTS.append("pre_file",
	help="Before the alias resolves to a file")
hooker.EVENTS.append("pre_response",
	help="Before the created request is sent")

import wormnest.db_handler as db_handler
import wormnest.utils as utils

'''
To run the App:
python3 app.py
'''
app = Flask(__name__)


def get_random_alias(length=None):
	assert ALIAS_DIGITS_MIN <= ALIAS_DIGITS_MAX
	if length == None:
		length = random.randint(ALIAS_DIGITS_MIN, ALIAS_DIGITS_MAX)
	return utils.randomword(length)


def log_spawn(filename, mgmt_key, port):
	import time
	now = time.strftime("%c")
	manage_key_file = filename
	
	print (
		"[!] The Management Route is '{}'\nNoted in '{}'".format(
			mgmt_key,
			manage_key_file
		)
	)
	with open(manage_key_file, 'a') as f:
		f.write("/{} - {} - ({})\n".format(
			mgmt_key,
			port,
			now
			)
		)

IP = os.getenv("IP", "0.0.0.0")
PORT = os.getenv("PORT", 8000)

SRV_DIR = os.getenv("SRV_DIR","test_directory/")
try:
	os.mkdir(SRV_DIR)
	print("[+] Directory: '{}' created!".format(SRV_DIR))
except Exception as e:
	print("[+] Directory: '{}' found!".format(SRV_DIR))

app.config['UPLOAD_FOLDER'] = SRV_DIR

ALIAS_DIGITS_MIN = os.getenv("ALIAS_DIGITS_MIN", 8)
ALIAS_DIGITS_MAX = os.getenv("ALIAS_DIGITS_MAX", 8)

MANAGE_URL_DIR = os.getenv("MANAGE_URL_DIR", 'manage')
if MANAGE_URL_DIR == '*':
	MANAGE_URL_DIR = get_random_alias(12)

MISS = os.getenv("MISS", 'abort')
EXPIRE = os.getenv("EXPIRE", 'abort')
BLACKLISTED = os.getenv("BLACKLISTED", 'abort')

LOG_SPAWN_FILE = os.getenv("LOG_SPAWN_FILE", "wormnest.mgmt_route.txt")

REDIRECT_URL = os.getenv(
	"REDIRECT_URL",
	'https://amazon.com'
	)
DEFAULT_FILENAME = os.getenv(
	"DEFAULT_FILENAME",
	'ClientDesktopApp'
	)
USE_ORIGINAL_EXTENSION = os.getenv(
	"USE_ORIGINAL_EXTENSION",
	True
	)
DEFAULT_PATHS_FILE = os.getenv(
	"DEFAULT_PATHS_FILE",
	"urls.default.json"
	)

IP_WHITELIST = os.getenv(
	"IP_WHITELIST",
	"0.0.0.0/0"
	)
try:
	IP_WHITELIST_tmp = []
	ip_net_str_toks = IP_WHITELIST.split(',')

	for ip_net_str in ip_net_str_toks:
		print ("[->] "+ip_net_str)
		ip_net = ip_network(ip_net_str, strict=False)
		print (ip_net)
		IP_WHITELIST_tmp.append(ip_net)
		print ("Added Subnet")
	IP_WHITELIST = IP_WHITELIST_tmp

except Exception as e:
	print ("[-] 'IP_WHITELIST' is used as:")
	print ("   IP_WHITELIST='127.0.0.1/8,192.168.0.0/16'")
	print (IP_WHITELIST)
	sys.exit(10)


print(IP_WHITELIST)
# sys.exit(10)

SERVER_HEADER = os.getenv("SERVER_HEADER", "Apache httpd 2.2.10") # Intentionally old


HOOK_SCRIPTS = os.getenv("HOOK_SCRIPTS","")
hook_list = enumerate(HOOK_SCRIPTS.split(":"))
for i, hook in hook_list:
	if hook == '': continue
	print("[+] Loading hook {}".format(hook))
	ext_module = imp.load_source(
		'hook_{}'.format(i),
		hook
	)


def redirect_away():
	return redirect(REDIRECT_URL, code=302)

def abort_404():
	return abort(404)

behaviours = {
	'abort' : abort_404,
	'redir' : redirect_away,
}

default_miss = behaviours.get(MISS,'abort')
on_expired = behaviours.get(EXPIRE,'abort')
blacklisted = behaviours.get(BLACKLISTED,'abort')


@app.after_request
def add_header(response):
	response.headers['Cache-Control'] = 'no-store'
	del response.headers['Expires']
	response.headers['Server'] = SERVER_HEADER
	del response.headers['Date']
	return response


log_spawn(LOG_SPAWN_FILE, MANAGE_URL_DIR, PORT)

@app.route('/%s/' % MANAGE_URL_DIR)
def show_manage():
	return render_template(
		"manage_help.html",
		manage_url = request.base_url
		)

@app.route('/%s/load_defaults' % MANAGE_URL_DIR)
def load_defaults():
	add_url_template = "http://127.0.0.1:{port}/{man}/add?path={path}&alias={alias}&unchecked=True"
	if DEFAULT_PATHS_FILE:
		print("[+] Importing defaults from '{}'".format(DEFAULT_PATHS_FILE))
		import json
		with open(DEFAULT_PATHS_FILE) as url_defaults:
			defaults_url_dict = json.load(url_defaults)
			for path, url_params in defaults_url_dict.items():
				print(path, url_params)
				alias = url_params['alias']
				filename = url_params.get('filename',None)
				print (filename)
				if filename:
					add_url_template += '&filename={filename}'
				requests.get(add_url_template.format(
						port=PORT,
						man=MANAGE_URL_DIR,
						path=path,
						alias=alias,
						filename=filename,
						)
					)
	return "<pre>{}</pre>".format(
		json.dumps(defaults_url_dict, indent=2)
		)

@app.route(
	'/%s/list/' % MANAGE_URL_DIR,
	defaults={'req_path': ''}
	)
@app.route('/%s/list/<path:req_path>' % MANAGE_URL_DIR)
def dir_listing(req_path):
	'''
	Found here:
https://stackoverflow.com/questions/23718236/python-flask-browsing-through-directory-with-files
	'''
	# Joining the base and the requested path
	abs_path = os.path.join(SRV_DIR, req_path)

	# Return 404 if path doesn't exist
	if not os.path.exists(abs_path):
		return abort(404)

	# Check if path is a file and serve
	if os.path.isfile(abs_path):
		return send_file(abs_path)

	# Show directory contents
	files = os.listdir(abs_path)
	full_paths = []
	for f in files:
		full_paths.append(
			(f, os.path.join(request.base_url, f))
		)
	# print (full_paths)
	add_url_link = "%s%s/add" % (request.url_root, MANAGE_URL_DIR)
	return render_template('file.html',
		files=full_paths,
		add_url=add_url_link
		)


@app.route('/%s/add' % MANAGE_URL_DIR)
def add_url():

	path = request.args.get("path")
	expires = request.args.get("clicks", -1)
	alias = request.args.get("alias", get_random_alias())
	attach_name = request.args.get("filename")
	unchecked_path = request.args.get("unchecked", False)
	if not request.args:
		return render_template(
			'add_help.html', 
		)
	try:
		original_filename = path.split('/')[-1]
		original_extension = original_filename.split('.')[-1]
	except Exception as e:
		return render_template(
			'custom_error.html', 
			error_msg="The 'path' variable does not validate"
			)

	if original_filename == original_extension:
		# If they are the same, there is no extension
		original_extension = ''
	else:
		original_extension = '.' + original_extension

	if not attach_name:

		if not DEFAULT_FILENAME:
			# The filename is the path's filename
			attach_name = original_filename
		else:
			attach_name = DEFAULT_FILENAME
			if USE_ORIGINAL_EXTENSION:
				attach_name += original_extension

	path = os.path.join(SRV_DIR, path)
	if not os.path.isfile(path) and not unchecked_path:
		return render_template(
			'custom_error.html', 
			error_msg="The path '{}' is NOT a file".format(path)
			)

	try:
		if expires is not None: 
			int(expires)
	except:
		return render_template(
			'custom_error.html', 
			error_msg="Parameter 'clicks' must be positive Integer"
			)
	try:
		db_handler.add_url(path, alias, expires, attach_name)
	except Exception as e:
		print (e)
		err =  "Error adding alias '{}'' for path '{}'".format(alias, path)
		return render_template(
			'custom_error.html', 
			error_msg=err
			)
	full_link = request.url_root + alias
	return render_template(
			'added_alias.html', 
			alias=alias,
			path=path,
			clicks=expires,
			link=full_link
			)

@app.route('/%s/del' % MANAGE_URL_DIR)
def del_url():
	alias = request.args.get("alias", None)
	if alias is None:
		return render_template(
			'del_help.html'
			)
	try:
		deleted = db_handler.del_url(alias)
	except KeyError:
		deleted = False
	return "Deleted" if deleted else "NOT deleted"


@app.route('/%s/show' % MANAGE_URL_DIR)
def show_all(path=None):
	entries = db_handler.get_all(path)
	return render_template(
				'show.html',
				entries = entries
				)


@app.route(
	'/%s/upload' % MANAGE_URL_DIR,
	methods=['POST', 'GET']
	)
def file_upload():
	if request.method == 'POST':
		# check if the post request has the file part
		if 'file' not in request.files:
			return render_template(
					'upload_page.html',
					manage_url = MANAGE_URL_DIR,
					message = "No file submitted"
				)
		file = request.files['file']
		# if user does not select file, browser also
		# submit a empty part without filename
		if file.filename == '':
			return render_template(
						'upload_page.html',
						manage_url = MANAGE_URL_DIR,
						message = "No filename submitted"
					)
		if file:
			filename = request.form.get('filename', file.filename)
			filename = secure_filename(filename)
			try:
				file.save(
					os.path.join(
						app.config['UPLOAD_FOLDER'],
						filename
						)
					)
			except IsADirectoryError:
				return render_template(
							'upload_page.html',
							manage_url = MANAGE_URL_DIR,
							message = "Filename exists"
						)

			if request.form.get("create_alias",
				default = False,
				type = bool):
				return redirect(
					"{manage_url}/add?path={filepath}".format(
						manage_url = MANAGE_URL_DIR,
						filepath = filename
						)
					)
			return render_template(
						'upload_page.html',
						manage_url = MANAGE_URL_DIR,
						message = "File '{}' uploaded successfully!".format(filename)
					)
	return render_template(
				'upload_page.html',
				manage_url = MANAGE_URL_DIR,
			)
				

#	Default Behaviour
@app.route('/<url_alias>')
def resolve_url(url_alias):

	ret_response = None
	# Check if whitelisted IP
	remote_host = ip_address(request.remote_addr)
	if not utils.is_whitelisted(IP_WHITELIST, remote_host):
		ret_response = blacklisted()
		return hook_n_respond(request, ret_response)

	# Run "pre_process" hook checks
	hook_ret = hooker.EVENTS["pre_process"](
		request=request,
		url_alias=url_alias,
	)
	#	In case the hook changed the original request
	url_alias = request.path
	print("[*] %s" % url_alias)
	try:
		behaviour = hook_ret.popitem()[1]
		# Get the behavior from the list and generate its response:
		if behaviour is not None:
			ret_response = behaviours.get(behaviour, abort_404)()
			return hook_n_respond(request, ret_response)
	except KeyError:
		pass

	# Check if URL Alias exists
	try:
		alias_db_obj = db_handler.get_path(url_alias)
	except KeyError:
		# Non-existent
		ret_response = default_miss()
		return hook_n_respond(request, ret_response)
	except utils.LinkExpired:
		# Existent and expired
		ret_response = on_expired()
		return hook_n_respond(request, ret_response)


	path = alias_db_obj.path
	# Run the hooks for iconic filenames
	hook_ret = hooker.EVENTS["pre_file"](
		filename=path,
		request=request,
		)
	try:
		iconic_fd = hook_ret.popitem()[1]
	except KeyError:
		iconic_fd = None

	if iconic_fd:
		print(
			"[+] Filename '{}' HOOKED! A Custom file is served!".format(
				alias_db_obj.path
				)
			)
	# If it succeds the returned fd will be served 
		ret_fd = iconic_fd
		ret_response = send_file(
				filename_or_fp = ret_fd,
				as_attachment = True,
				attachment_filename = alias_db_obj.attachment,
			)
		return hook_n_respond(request, ret_response)

	# Else the file file system is checked for real files
	if not os.path.isfile(path):
		# If doensn't exist, 'miss' behaviour is triggered
		ret_response = default_miss()
		return hook_n_respond(request, ret_response)

	ret_fd = open(path,'rb')
	ret_response = send_file(
			filename_or_fp = ret_fd,
			as_attachment = True,
			attachment_filename = alias_db_obj.attachment,
		)

	return hook_n_respond(request, ret_response)


def hook_n_respond(request, response):
	hook_ret = hooker.EVENTS["pre_response"](
		request=request,
		response=response
		)
	try:
		ret_response_final = hook_ret.popitem()[1]
	except KeyError:
		ret_response_final = response
	return ret_response_final


def main(*args, **kwargs):

	import sys
	print (sys.argv)
	app.run(
		host=IP,
		port=PORT,
		debug=os.getenv("DEBUG", False)
	)

if __name__=="__main__":
	main()