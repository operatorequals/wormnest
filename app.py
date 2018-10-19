
from flask import Flask
from flask import flash,request,send_file,send_from_directory,redirect,render_template, abort

from werkzeug.utils import secure_filename

import os
import random
import imp

import requests
import hooker
hooker.EVENTS.append(["on_request"])

import wormnest.db_handler as db_handler
import wormnest.utils as utils

'''
To run the App:
python3 app.py
'''
app = Flask(__name__)

@app.after_request
def add_header(response):
	response.headers['Cache-Control'] = 'no-store'
	del response.headers['Expires']
	response.headers['Server'] = "Apache httpd 2.2.10"	# Intentionally old
	del response.headers['Date']
	return response

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

behaviors = {
	'abort' : abort_404,
	'redir' : redirect_away,
}

default_miss = behaviors.get(MISS,'abort')
on_expired = behaviors.get(EXPIRE,'abort')


log_spawn(LOG_SPAWN_FILE, MANAGE_URL_DIR, PORT)


# @app.route('/%s/' % MANAGE_URL_DIR)
# def show_manage_redir():
# 	print(request.base_url[:-1])
# 	return redirect(request.base_url[:-1])

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
			flash('No file part')
			return redirect(request.url)
		file = request.files['file']
		# if user does not select file, browser also
		# submit a empty part without filename
		if file.filename == '':
			flash('No selected file')
			return redirect(request.url)
		if file:
			filename = request.form.get('filename', file.filename)
			filename = secure_filename(filename)
			file.save(
				os.path.join(
					app.config['UPLOAD_FOLDER'],
					filename
					)
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
			return redirect(request.url)

	return render_template(
				'upload_page.html',
				manage_url = MANAGE_URL_DIR
			)
				

#	Default Behaviour
@app.route('/<url_alias>')
def resolve_url(url_alias):
	try:
		resolved_url = db_handler.get_path(url_alias)
	except KeyError:
		return default_miss()
	except utils.LinkExpired:
		return on_expired()

	# Run the hooks for iconic filenames
	returned_file = resolved_url.path
	hook_ret = {}
	hooker.EVENTS["on_request"](
		filename=resolved_url.path,
		request=request,
		retvals=hook_ret
		)
	fd = hook_ret.get('fd', None)
	resp = hook_ret.get('resp', None)

	if fd:
		print(
			"[+] Filename '{}' HOOKED! A Custom file is served!".format(
				resolved_url.path
				)
			)
		# If it succeds the returned fd will be served 
		returned_file = fd
	elif resp:
		print(
			"[+] Filename '{}' HOOKED! A Custom response is served!".format(
				resolved_url.path
				)
			)
		return resp

	else:
		# Else check if the file is real
		if not os.path.isfile(returned_file):
			return default_miss()

	return send_file(
		filename_or_fp = returned_file,
		as_attachment = True,
		attachment_filename = resolved_url.attachment,
		)

def main(*args, **kwargs):

	import sys
	print (sys.argv)
	app.run(
		host=IP,
		port=PORT,
		debug=False
		)

if __name__=="__main__":
	main()