#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Matti Kariluoma Mar 2012 <matti@kariluo.ma>

import imaplib, smtplib, email, time, datetime
from email.parser import Parser
from sms_nav import process_sms_command
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
		body = str(message[2])
		try:
			if isinstance(message[2][0], email.message.Message) and len(message[2][0]) > 0:
				body = ''
				for part in message[2]:
					if part.is_multipart():
						continue
					else:
						body += part.get_payload()
					
		except IndexError:
			pass
			
		headers = message[1]
		new_message = email.message.Message()
		new_message.set_unixfrom(username)
		user = headers['From']
		print '%s\tResponding to message "%s" from %s' % (str(datetime.datetime.now()), body[0:-1], user)
		new_message['To'] = user
		new_message['From'] = username+'@kariluo.ma'
		#new_message['Subject'] = 'Re: '+headers['Subject']
		new_message['Subject'] = ''
		new_message.set_payload(process_sms_command(user, body.strip()))
		
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
	
		
