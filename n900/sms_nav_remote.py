#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Matti Kariluoma Mar 2012 <matti@kariluo.ma>

import time, datetime
from render_html import render_url_remotely

sms_max_length = 160

sms_help_msg = """Welcome to sms++! Commands are:
help - this message
next - display next page
prev - display previous page
page n - display the nth page
url www.example.com - return the provided url
wiki topic - return the english wikipedia page for "topic"
ebay product - return ebay price results for "product"
login - log in
logout - log out
email - fetch email for associated account
email name@example.com - fetch email for specific account
"""

cal_defaults = [
	'Daylight Saving Time Ends', 'Tax Day', "April Fool's Day", "Father's Day", 
	"New Year's Day", 'Daylight Saving Time Begins', 'Christmas', "St. Patrick's Day",
	'Christmas Eve', "Mother's Day", "Valentine's Day", 'Cinco de Mayo', 'Groundhog Day', 
	"New Year's Eve", 'Flag Day', 'Presidents Day', 'Columbus Day', 'Veterans Day', 
	"John F. Kennedy's Birthday", 'Thanksgiving', 'Election Day', 'Patriot Day', 
	"Lincoln's Birthday", 'Labor Day', 'Memorial Day', 'Earth Day', 'Halloween',
	'Independence Day', "Martin Luther King, Jr's Day"
]

msgs = {}
pages = {}

def digest_sms_precalc(message):
	header = 'Reply "help" for command usage\n'
	footer = '\nPage 1 of 1'
	message = str(message) # ensure we are dealing with a string
	
	## Find the number of pages to be made, msg_max
	msg_len = len(message)
	msg_len -= sms_max_length - len(header) - len(footer) # first message has header
	msg_num = 1
	msg_num += msg_len % (sms_max_len - len(footer))
	msg_max = msg_num
	while (msg_num >= 1.0):
		msg_num /= 10
		pass # recalculate with the footer + 1 character for the next power of messages
		
	## Make the pages and return the result
	result = []
	for i in range(msg_max):
		footer = 'Page %d of %d' % (i+1, msg_max)
		if i > 0: # After the first
			header = ''
		skip = sms_max_length - len(header) - len(footer)
		result.append('%s%s%s' % (header, message[skip*i:skip*(i+1)], footer))
	
	return result
	
def digest_sms(message):
	message = str(message)
	result = []
	i = 0
	header = 'Reply "help" for command usage\n'
	est_max = (len(message) + len(header)) / (sms_max_length - len('\nPage 1 of 10'))
	est_max = int(round(est_max, 0)) + 1
	while len(message) > 0:
		footer = '\nPage %d of %d' % (i+1, est_max)
		if i > 0: # After the first
			header = ''
		skip = sms_max_length - len(header) - len(footer)
		result.append('%s%s%s' % (header, message[0:skip], footer))
		message = message[skip::]
		i+=1

	return result

def process_sms_command(user, command):
	cmd = str(command).split(' ')[0].strip().lower()
	global msgs
	global pages
	
	try:
		page = pages[user]
		msg = msgs[user]
	except KeyError:
		page = 0
		msg = []
		pages[user] = page
		msgs[user] = msg

	if cmd.startswith('prev'):
		page -= 1
		if page < 0:
			page = 0
	elif cmd.startswith('next'):
		page += 1
	elif cmd.startswith('page'):
		error = True
		try:
			page_num = int(float(str(command).split(' ')[1]))
			error = False
		except:
			pass
		
		if not error:
			if page_num > len(msg):
				page = len(msg) - 1 
			else:
				page = page_num - 1 
	elif cmd.startswith('url'):
		error = True
		try:
			webpage = render_url_remotely(str(command).split(' ')[1], "http://www.atarkri.com:8080/render")
			error = False
		except IndexError:
			pass
			
		if not error:
			page = 0
			buf = []
			for line in webpage.splitlines(True):
				buf.append(line.strip(' \t')) # remove space and tab formatting
			msg = digest_sms(''.join(buf))
	elif cmd.startswith('mail'):
		phonenumber = user.split('@')[0]
		print phonenumber
		error = True
		try:
			webpage = render_url_remotely('http://134.129.125.232:8080/smsplusplus/query.action;service=mail&phone=%s' % (phonenumber), "http://www.atarkri.com:8080/render")
			print len(webpage)
			lines = webpage.splitlines()
			for line in lines:
				line.strip()
			webpage = ''.join(lines)
			message = webpage
			# error is html page with "Bad Request" in the body with no surronding tag
			if webpage != 'Bad Request':
				emails = eval(str(webpage)) #XSS ATTACK! #the return should be a json dictionary
				if isinstance(emails, dict):
					try:
						num = 0
						message = ''
						for email in emails['entry']:
							message += "%d: %s (%s)\n" % (num, email['title'], email['author']['email'])
							num += 1
					except KeyError:
						message = webpage
				else:
					message = webpage
				error = False
		except IndexError:
			pass

		if not error:
			page = 0
			msg = digest_sms(message)	

	elif cmd.startswith('cal'):
		phonenumber = user.split('@')[0]
		global cal_defaults
		error = True
		try:
			webpage = render_url_remotely('http://134.129.125.232/gcalendar.php?number=%s&mode=json' % (phonenumber), "http://www.atarkri.com:8080/render")
			lines = webpage.splitlines()
			for line in lines:
				line.strip()
			webpage = ''.join(lines)
			message = webpage
			# error is html page with "error" in the body with no surronding tag
			if webpage != 'error':
				cals = eval(str(webpage)) #XSS ATTACK! #the return should be a json dictionary
				message = ''
				num = 0
				for cal in cals['events']:
					creator = ''
					try:
						creator = cal['creator']
					except KeyError:
						pass
					if creator != 'US Holidays':
						if cal['summary'] not in cal_defaults:
							try:
								message += "%d: %s (%s)\n" % (num, cal['summary'], cal['startDate'])
							except KeyError:
								try:
									 message += "%d: %s (%s)\n" % (num, cal['summary'], cal['startDateTime'])
								except KeyError:
									pass
							num += 1
				error = False
		except IndexError:
			pass
			
		if not error:
			page = 0
			msg = digest_sms(message)	
	else:
		msg = digest_sms(sms_help_msg)
	
	try: 
		message = msg[page]
	except IndexError:
		page = len(msg)-1
		message = ''
		if page >= 0:
			message = msg[page]
		if message is None or message is '':
			msg = digest_sms(sms_help_msg)
			page = 0
			message = msg[page]
			
	msgs[user] = msg
	pages[user] = page

	return message

def main():
	print "sms command interpreter server started!"
	try:
		import fileinput	
		while(True):
			for line in fileinput.input():
				print process_sms_command("nobody", line.strip())				
					
	except KeyboardInterrupt:
		print '^C received, shutting down server'

if __name__ == '__main__':
	main()
	
		
