#!/usr/bin/env python
#
# A copy and paste job from "Cue" http://talk.maemo.org/showpost.php?p=558430&postcount=57
#
# Matti Kariluoma Mar 2012 <matti@kariluo.ma>
import dbus, gobject
import datetime
from dbus.mainloop.glib import DBusGMainLoop
from sms_nav_remote import process_sms_command

import pexpect
import time
from subprocess import *

def octify(str):
	'''     
	Returns a list of octet bytes representing
	each char of the input str.		
	'''					
 
	bytes = map(ord, str)
	bitsconsumed = 0     
	referencebit = 7     
	octets = []	  
 
	while len(bytes):
		byte = bytes.pop(0)
		byte = byte >> bitsconsumed
 
		try:			
			nextbyte = bytes[0]
			bitstocopy = (nextbyte & (0xff >> referencebit)) << referencebit
			octet = (byte | bitstocopy)				     
 
		except:
			octet = (byte | 0x00)
 
		if bitsconsumed != 7:
			octets.append(byte | bitstocopy)
			bitsconsumed += 1		
			referencebit -= 1		
		else:				   
			bitsconsumed = 0		
			referencebit = 7		
 
	return octets
 
def semi_octify(str):
	'''	  
	Expects a string containing two digits.
	Returns an octet -		     
	first nibble in the octect is the first
	digit and the second nibble represents 
	the second digit.		      
	'''				    
	try:				   
		digit_1 = int(str[0])	  
		digit_2 = int(str[1])	  
		octet = (digit_2 << 4) | digit_1
	except:				 
		octet = (1 << 4) | digit_1      
 
	return octet
 
 
def deoctify(arr):
 
	referencebit = 1
	doctect = []    
	bnext = 0x00    
 
	for i in arr:
 
		bcurr = ((i & (0xff >> referencebit)) << referencebit) >> 1
		bcurr = bcurr | bnext				      
 
		if referencebit != 7:
			doctect.append( bcurr )
			bnext = (i & (0xff << (8 - referencebit)) ) >> 8 - referencebit
			referencebit += 1					      
		else:								  
			doctect.append( bcurr )					
			bnext = (i & (0xff << (8 - referencebit)) ) >> 8 - referencebit
			doctect.append( bnext )					
			bnext = 0x00						   
			referencebit = 1						
 
	return ''.join([chr(i) for i in doctect])
 
 
def createPDUmessage(number, msg):
	'''			
	Returns a list of bytes to represent a valid PDU message
	'''						     
	numlength = len(number)				 
	if (numlength % 2) == 0:				
		rangelength = numlength			 
	else:						   
		number = number + 'F'			   
		rangelength = len(number)			
 
	octifiednumber = [ semi_octify(number[i:i+2]) for i in range(0,rangelength,2) ]
	octifiedmsg = octify(msg)						      
	HEADER = 1								     
	FIRSTOCTETOFSMSDELIVERMSG = 10						 
	ADDR_TYPE = 129 #unknown format						
	number_length = len(number)						    
	msg_length = len(msg)							  
	pdu_message = [HEADER, FIRSTOCTETOFSMSDELIVERMSG, number_length, ADDR_TYPE]    
	pdu_message.extend(octifiednumber)					     
	pdu_message.append(0)							  
	pdu_message.append(0)							  
	pdu_message.append(msg_length)						 
	pdu_message.extend(octifiedmsg)						
	return pdu_message							     
 
 
def recv_sms(pdumsg, msgcenter, somestring, number):
 
	msglength = int(pdumsg[18])
	msgarray = pdumsg[19:len(pdumsg)]
 
	msg = deoctify(msgarray)
 
	if msg > 0:
		#print 'New message received from %s' % number
		#print 'Message length %d' % msglength
		#print 'Message: %s' % msg
		print '%s\tMessage from %s: %s' % (datetime.datetime.now(), number, msg)
 		time.sleep(10.0)
		send_sms(number, process_sms_command(number[2::], msg).strip())
		print 'Message sent!'

def send_sms(number, message):
	"""
	bus = dbus.SystemBus()
	smsobject = bus.get_object('com.nokia.phone.SMS', '/com/nokia/phone/SMS/ba212ae1')
	smsiface = dbus.Interface(smsobject, 'com.nokia.csd.SMS.Outgoing')
	arr = dbus.Array(createPDUmessage(number.replace('+','00'), message))

	msg = dbus.Array([arr])
	smsiface.Send(msg,'')
	"""
	child = pexpect.spawn('pnatd');
	child.send('at\r');
	time.sleep(0.25);
	child.send('at+cmgf=1\r');
	time.sleep(0.25);
	# send_to = 'at+cmgs="+17012342345"\r'
	send_to = 'at+cmgs="%s"\r' % (number)
	child.send(send_to);
	child.send(message);
	child.send(chr(26));
	child.send(chr(26));
	child.sendeof();

def main():
	DBusGMainLoop(set_as_default=True)
	bus = dbus.SystemBus() #should connect to system bus instead of session because the former is where the incoming signals come from
	bus.add_signal_receiver(recv_sms, path='/com/nokia/phone/SMS', dbus_interface='Phone.SMS', signal_name='IncomingSegment')
	print "sms auto-responding server started!"
	gobject.MainLoop().run()

if __name__ == '__main__':
	main()



