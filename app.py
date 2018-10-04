
from flask import Flask
from flask import request,send_file,redirect,render_template, abort

import os
import random

import requests

import wormnest.db_handler as db_handler
import wormnest.utils as utils

'''
To run the App:
FLASK_APP=wormnest/__main__.py python -m flask run --host=127.0.0.1 --port=8080
'''
app = Flask(__name__)

IP = "0.0.0.0"
PORT = 8080

SRV_DIR = "test_directory/"
ALIAS_DIGITS_MIN = 8
ALIAS_DIGITS_MAX = 8
LISTING_URL_DIR = 'listing'
MANAGE_URL_DIR = 'manage'
REDIRECT_URL = 'https://amazon.com'
DEFAULT_FILENAME = 'ClientDesktopApp'
USE_ORIGINAL_EXTENSION = True

DEFAULT_PATHS_FILE = "urls.default.json"

@app.route('/%s/load_defaults' % MANAGE_URL_DIR)
def load_defaults():

	if DEFAULT_PATHS_FILE:
		print("[+] Importing defaults from '{}'".format(DEFAULT_PATHS_FILE))
		import json
		with open(DEFAULT_PATHS_FILE) as url_defaults:
			defaults_url_dict = json.load(url_defaults)
			for path, url_params in defaults_url_dict.items():
				print(path, url_params)
				alias = url_params['alias']
				requests.get(
	"http://127.0.0.1:{port}/{man}/add?path={path}&alias={alias}&unchecked=True".format(
						port=PORT,
						man=MANAGE_URL_DIR,
						path=path,
						alias=alias,
						)
					)
	return json.dumps(defaults_url_dict, indent=2)


def redirect_away():
	return redirect(REDIRECT_URL, code=302)

def abort_404():
	return abort(404)

default_miss = abort_404
on_expired = abort_404
# default_miss = redirect_away
on_expired = redirect_away


def get_random_alias(length=None):
	assert ALIAS_DIGITS_MIN <= ALIAS_DIGITS_MAX
	if length == None:
		length = random.randint(ALIAS_DIGITS_MIN, ALIAS_DIGITS_MAX)
	return utils.randomword(length)


@app.route(
	'/%s/%s/' % (MANAGE_URL_DIR, LISTING_URL_DIR),
	defaults={'req_path': ''}
	)
@app.route('/%s/%s/<path:req_path>' %
 (MANAGE_URL_DIR, LISTING_URL_DIR),)
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

	return render_template('file.html', files=full_paths)


@app.route('/<url_alias>')
def resolve_url(url_alias):
	try:
		resolved_url = db_handler.get_path(url_alias)
	except KeyError:
		return default_miss()
	except utils.LinkExpired:
		return on_expired()

	return send_file(
		resolved_url.path,
		as_attachment = True,
		attachment_filename = resolved_url.attachment,
		)


@app.route('/%s/add' % MANAGE_URL_DIR)
def add_url():

	path = request.args.get("path")
	expires = request.args.get("clicks", -1)
	alias = request.args.get("alias")
	attach_name = request.args.get("filename")
	unchecked_path = request.args.get("unchecked", False)

	try:
		original_filename = path.split('/')[-1]
		original_extension = original_filename.split('.')[-1]
	except Exception as e:
		return render_template(
			'custom_error.html', 
			error_msg=e
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

	if not alias:
		alias = get_random_alias()

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


@app.route('/%s/show' % MANAGE_URL_DIR)
def show_all(path=None):
	entries = db_handler.get_all(path)
	return render_template(
				'show.html',
				entries = entries
				)


def main(*args, **kwargs):

	import sys
	print (sys.argv)
	app.run(
		# host=os.getenv('IP', '127.0.0.1'), 
		host=IP,
		# port=int(os.getenv('PORT',8080)),
		port=PORT,
		debug=True
		)

if __name__=="__main__":
	main()