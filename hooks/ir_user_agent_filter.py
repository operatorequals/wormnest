'''
Inspired by "Block Common IR user Agents"
https://bluescreenofjeff.com/2016-04-12-combatting-incident-responders-with-apache-mod_rewrite/
'''

import hooker

IR_UAs = "wget|curl|HTTrack|crawl|google|bot|b-o-t|spider|baidu".split('|')
behaviour = "redir"

print("Blocked User Agents:%s" % str(IR_UAs))

@hooker.hook("pre_process")
def ua_filter(request, url_alias):
	ua = request.headers.get("User-Agent", "")
	if ua == '':
		return behaviour

	for ir_ua in IR_UAs:
		if ir_ua in ua.lower():
			return behaviour

	return None