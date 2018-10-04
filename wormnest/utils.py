import string
import random

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
