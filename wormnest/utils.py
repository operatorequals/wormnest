import string
import random
import os
import sys
from ipaddress import ip_address, ip_network
import urllib.request
import json

import hooker

GEOLOCATION_CACHE = {}
GEOLOCATION_SEARCHABLES = ['state', 'country_code', 'country_name', 'city']

def randomword(length):
  '''
https://stackoverflow.com/questions/2030053/random-strings-in-python
  '''
  chars = string.ascii_letters
  chars += string.digits
  return ''.join(random.choice(chars) for i in range(length))


class LinkExpired(Exception):
  ''' This Exception is raised when a link is expired! '''
  pass


def check_filename_for_hook(filename, hook_name):
  toks = filename.split('.')
  if len(toks) < 3: return False

  but_last_tok = toks[-2]
  return but_last_tok == hook_name


def is_listed(IP_LIST, host):
  for ip_net in IP_LIST:
#    print(host, ip_net, host in ip_net, type(ip_net))
    if host in ip_net:
      return True
  return False


def geolocation(ip_address, api_key=''):
  if ip_address in GEOLOCATION_CACHE:
      return GEOLOCATION_CACHE[ip_address]
  with urllib.request.urlopen(f"https://geolocation-db.com/json/{ip_address}") as url:
    data = url.read()
    data = json.loads(data)
    GEOLOCATION_CACHE[ip_address] = data
  return data 


def is_geolocation_listed(GEOLOCATION_LIST, ip_address, api_key=''):
  geolocation_dict = geolocation(ip_address)
  for geoloc in GEOLOCATION_LIST:
    for term in GEOLOCATION_SEARCHABLES:
      if geoloc.lower() == geolocation_dict[term].lower():
        return True
  return False


def parse_subnets(subnet_str):
  try:
    if not subnet_str:
        return []
    subnet_list = []
    ip_net_str_toks = subnet_str.split(',')

    for ip_net_str in ip_net_str_toks:
      ip_net = ip_network(ip_net_str, strict=False)
      print ("[->] "+ip_net_str, ip_net)
      subnet_list.append(ip_net)
    return subnet_list

  except Exception as e:
    print (e)
    print ("[-] 'IP_WHITELIST' and 'IP_BLACKLIST' are used as:")
    print ("   IP_WHITELIST='127.0.0.1/8,192.168.0.0/16,10.10.10.1/32'")
    print ("Currently Set as: '{}'".format(subnet_str))
    sys.exit(10)


def parse_config():

  CONFIG = {}
  CONFIG['IP'] = os.getenv("IP", "0.0.0.0")
  CONFIG['PORT'] = os.getenv("PORT", 8000)

  CONFIG['SRV_DIR'] = os.getenv("SRV_DIR","test_directory/")
  try:
    os.mkdir(CONFIG['SRV_DIR'])
    print("[+] Directory: '{}' created!".format(CONFIG['SRV_DIR']))
  except Exception as e:
    print("[+] Directory: '{}' found!".format(CONFIG['SRV_DIR']))


  CONFIG['ALIAS_DIGITS_MIN'] = os.getenv("ALIAS_DIGITS_MIN", 8)
  CONFIG['ALIAS_DIGITS_MAX'] = os.getenv("ALIAS_DIGITS_MAX", 8)

  CONFIG['MANAGE_URL_DIR'] = os.getenv("MANAGE_URL_DIR", 'manage')
  if CONFIG['MANAGE_URL_DIR'] == '*':
    CONFIG['MANAGE_URL_DIR'] = get_random_alias(12)

  CONFIG['MISS'] = os.getenv("MISS", 'abort')
  CONFIG['EXPIRE'] = os.getenv("EXPIRE", 'abort')
  CONFIG['BLACKLISTED'] = os.getenv("BLACKLISTED", 'abort')

  CONFIG['LOG_SPAWN_FILE'] = os.getenv("LOG_SPAWN_FILE", "wormnest.mgmt_route.txt")

  CONFIG['REDIRECT_URL'] = os.getenv(
    "REDIRECT_URL",
    'https://amazon.com'
    )
  CONFIG['DEFAULT_FILENAME'] = os.getenv(
    "DEFAULT_FILENAME",
    'ClientDesktopApp'
    )
  CONFIG['USE_ORIGINAL_EXTENSION'] = os.getenv(
    "USE_ORIGINAL_EXTENSION",
    True
    )
  CONFIG['DEFAULT_PATHS_FILE'] = os.getenv(
    "DEFAULT_PATHS_FILE",
    "urls.default.json"
    )

  CONFIG['IP_WHITELIST'] = os.getenv(
    "IP_WHITELIST",
    "0.0.0.0/0"
    )
  CONFIG['IP_BLACKLIST'] = os.getenv(
    "IP_BLACKLIST",
    ""
    )

  CONFIG['IP_WHITELIST'] = parse_subnets(CONFIG['IP_WHITELIST'])
  CONFIG['IP_BLACKLIST'] = parse_subnets(CONFIG['IP_BLACKLIST'])

  CONFIG['SERVER_HEADER'] = os.getenv("SERVER_HEADER", "Apache httpd 2.2.10") # Intentionally old

  CONFIG['GEOLOCATION_BLACKLIST'] = os.getenv("GEOLOCATION_BLACKLIST", "").split(',')

  CONFIG['HOOK_SCRIPTS'] = os.getenv("HOOK_SCRIPTS","")
  hook_list = enumerate(CONFIG['HOOK_SCRIPTS'].split(":"))
  for i, hook in hook_list:
    if hook == '': continue
    print("[+] Loading hook {}".format(hook))
    hooker.load(hook)
    # ext_module = imp.load_source(
    #   'hook_{}'.format(i),
    #   hook
    # )
  return CONFIG


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
