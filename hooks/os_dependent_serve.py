"""
This hook serves a different wormnest alias
depending on string found in Request's User Agent

"""
import hooker

'''
This dict has keys/values of String/Alias.
If a key is found in the processed user agent,
the response will serve the corresponding alias 

Please configure according to the needs:
'''
UA_Aliases =  {
    
    'win' : "win_alias",
    'lin' : "lin_alias",
    'mac' : "mac_alias",
    'ios' : "ios_alias",
    'android' : "android_alias",
    'DEFAULT' : "unrecognised_os"
}

'''
TODO:
This hook can serve using 2 Behaviors:
PROXY: serves the file directly from the alias that triggered the hook (no change in client's URL bar)
REDIRECT: serves a 302 HTTP Redirect to the corresponding alias
'''

trigger_alias = 'download/'

@hooker.hook("pre_process")
def os_dependent_serve_proxy(request, url_alias):
    if trigger_alias not in url_alias:
        return None

    ua = request.headers.get("User-Agent", "N/A")

    final_url = UA_Aliases['DEFAULT']
    for key, value in UA_Aliases.items():
        if key.lower() in ua.lower():
             final_url = UA_Aliases[key]
             break

    #    Change the initial alias
    request.path = "/"+final_url
    request.full_path = "/"+final_url

