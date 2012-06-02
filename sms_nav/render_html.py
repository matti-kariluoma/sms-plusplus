#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Matti Kariluoma Mar 2012 <matti@kariluo.ma>

import time, datetime
from os import sep
from subprocess import Popen, STDOUT, PIPE
from urllib import urlopen

SLEEP_SECS = 5.0 # sleep for 5 seconds

def addsep(path_list):
	"""
	I am convinced there exists a standard library function to do this 
	for me. Where is it!?
	"""
	result = ''
	for item in path_list:
		result = '%s%s%s' % (result, sep, item)
	return result

def render_url(url):
	process = Popen([addsep(['usr','bin','links']),'-dump',url], stdout=PIPE, stderr=STDOUT)
	(stdout, stderr) = process.communicate()
	if process.poll() == None: # if the process is running
		process.kill()
	return stdout

def render_url_remotely(url, remote):
	try:
		file = urlopen("%s?url_to_render=%s" % (remote, url))
		render = file.read()
	except IOError:
		render = ''
	return str(render)
	

def main():
	print "html rendering server started!"
	try:
		import fileinput	
		while(True):
			for url in fileinput.input():
				for line in str(render_url(url.strip())).splitlines(True):
					print line.strip(' \t')
					
	except KeyboardInterrupt:
		print '^C received, shutting down server'

if __name__ == '__main__':
	main()
	
		
