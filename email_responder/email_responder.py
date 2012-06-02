#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Matti Kariluoma Mar 2012 <matti@kariluo.ma>

import imaplib, smtplib, email, time, datetime
from email.parser import Parser

username = 'none'

def get_mail(imap, folder):
	"""
	imap is an imap instance, already logged in.
	folder is the imap folder you like to get mail from.
	
	returns a sorted list of tuples: (int(message_num), headers_dict,
	                                  str(message_body), str(raw_message))
	"""
	mail = []

	imap.select(folder, readonly=True)
	(typ, data) = imap.search(None, '(UNSEEN)')
	for num in data[0].split():
		(typ, data) = imap.fetch(num, '(RFC822)')
		imap.store(num, '+FLAGS', '\Seen') # mark as read
		headers = Parser().parsestr(data[0][1])
		mail.append((int(num), dict(headers), headers._payload, data[0][1]))

	return sorted(mail)

def respond_to_email(mail):
	"""
	mail is a sorted tuple of (int(message_num), headers_dict, 
                             str(message_body), str(raw_message))
	"""
	for message in mail:
		body = message[2]
		headers = message[1]
		print '%s\tResponding to message "%s"' % (str(datetime.datetime.now()), body[0:-1])
		new_message = email.message.Message()
		new_message.set_unixfrom(username)
		new_message['To'] = headers['From']
		new_message['From'] = username+'@kariluo.ma'
		#new_message['Subject'] = 'Re: '+headers['Subject']
		new_message['Subject'] = ''
		new_message.set_payload(body)
		
		s = smtplib.SMTP('localhost')
		try:
			refused_recipients_dict = s.sendmail(
				new_message['From'], 
				new_message['To'].split(','), 
				new_message.as_string()
			)
			mail_sent = True
		except:
			mail_sent = False
		finally:
			s.quit()

def main():
	global username
	username = 'sms'
	password = 'sms2012'
	folder = 'INBOX'
	print "email auto-responding server started!"
	try:	
		while(True):
			imap = imaplib.IMAP4() # localhost, port 143
			imap.login(username, password)

			sorted_mail = get_mail(imap, folder)
			respond_to_email(sorted_mail)
			
			imap.close()
			imap.logout()
			time.sleep(5.0) # sleep for 5 seconds
	except KeyboardInterrupt:
		print '^C received, shutting down server'

if __name__ == '__main__':
	main()
	
		
