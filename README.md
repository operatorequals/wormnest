# wormnest
A Web Server to hide stuff. A place where worms live and reproduce, but you can't prove it...

A **Python3** Flask / SQL-Alchemy Web Server for URL minification and manipulated file serving.

Heavily inspired by [@bluscreenofjeff](https://github.com/bluscreenofjeff/), and his [great blog post about expiring URLs](https://bluescreenofjeff.com/2016-04-19-expire-phishing-links-with-apache-rewritemap/) I spinned my own version of a web server that serves files, creates custom URLs for them, expires them, and more...



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
```bash
IP - defaults to "0.0.0.0"
PORT - defaults to 8000
SRV_DIR - defaults to "test_directory/"
ALIAS_DIGITS_MIN - defaults to 8
ALIAS_DIGITS_MAX - defaults to 8
MANAGE_URL_DIR - defaults to 'manage' # NO SLASHES HERE!
REDIRECT_URL - defaults to "https://amazon.com"
DEFAULT_FILENAME - defaults to "ClientDesktopApp"
USE_ORIGINAL_EXTENSION - defaults to "True" # Uses the extension of the Original file
DEFAULT_PATHS_FILE - defaults to "urls.default.json"
```

### The "*urls.default.json*"
Simple as a JSON that contains a *URL Alias* and a *Path* in the served directory:

```json
{
  "download_now":{
    "path":"metasploit/generated/meter_pinning_443.exe",
    "filename":"CrazyTaxi_cracked_singlefile_by_Raz0r_team_2006.exe"
  },
  "android":{
    "path":"metasploit/generated/meter_pinning_443.apk",
  },
  [.. More definitions ..]
}
```

The above will make the default setup of `wormnest` route the following:
* `http[s]://payload-server:8000/download_now`
to serve `metasploit/generated/meter_pinning_443.exe` with a `"Content-Disposition" HTTP Header` containing `CrazyTaxi_cracked_singlefile_by_Raz0r_team_2006.exe` as the `filename` argument

* `http[s]://payload-server:8000/android`
to serve `metasploit/generated/meter_pinning_443.apk` with the default filename of `ClientDesktopApp` and the file's original extension (`USE_ORIGINAL_EXTENSION` parameter).
Hence `ClientDesktopApp.apk` will be placed in the `"Content-Disposition" HTTP Header`.

### For *Cobalt Strikers*
Generating payloads from the CS client directly to the (remote) *Worm Nest* deployment is as simple as [`sshfs`](https://github.com/libfuse/sshfs) to that served directory (`SRV_DIR`). People tend to forget that `scp` is by far NOT THE ONLY WAY!


## Securing your *Worm Nest*!
There is **no authentication** to use the management endpoint of this service. This effectively means that anyone going under the `/manage/` directory will be able to see, add, delete all URL aliases, and list the whole served directory.

Yet, adding authentication, is (at least at this point) out of scope. That's why the `MANAGE_URL_DIR` exists in the first place. A *passwordish* string here will prevent anyone (not able to guess it) to reach the management endpoint. A password in the URL sucks (I now), but combined with some HTTPS (needed in case of actual use), and with no Intercepting HTTP Proxy between your host and the *Worm Nest* deployment you'll be good enough!

Have Fun!


