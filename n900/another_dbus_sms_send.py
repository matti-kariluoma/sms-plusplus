#!/usr/bin/env python2.5	  
import sched, time		
import dbus			
import gobject		    
from dbus.mainloop.glib import DBusGMainLoop
 
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
 
 
def sendmessage(number, message):
 
	bus = dbus.SystemBus()
	smsobject = bus.get_object('com.nokia.phone.SMS', '/com/nokia/phone/SMS/ba212ae1')
	smsiface = dbus.Interface(smsobject, 'com.nokia.csd.SMS.Outgoing')
	arr = dbus.Array(createPDUmessage(number.replace('+', '00'), message))
 
	msg = dbus.Array([arr])
	smsiface.Send(msg,'')
 
 
def callback(pdumsg, msgcenter, somestring, sendernumber):
 
	msglength = int(pdumsg[18])
	msgarray = pdumsg[19:len(pdumsg)]
 
	msg = deoctify(msgarray)
 
	if msg > 0:
		print 'New message received from %s' % sendernumber
		print 'Message length %d' % msglength
		print 'Message: %s' % msg
 
		if msg == "ping":
			print "Sending reply: pong"
			sendmessage(sendernumber.replace("+","00"), "pong")
		else:
			print "Unknown command"
 
 
def listen():
	DBusGMainLoop(set_as_default=True)
	bus = dbus.SystemBus() #should connect to system bus instead of session because the former is where the incoming signals come from
	bus.add_signal_receiver(callback, path='/com/nokia/phone/SMS', dbus_interface='Phone.SMS', signal_name='IncomingSegment')
	gobject.MainLoop().run()
 
 
if __name__ == '__main__':
  import time
 
  def schedule_task(schedule, fn, *args):
      import sched
      s = sched.scheduler(time.time, time.sleep)
      startTime = time.mktime(time.strptime(schedule, '%b %d %H:%M %Y'))
      s.enterabs(startTime, 0, fn, args)
      s.run()
 
  import getopt, sys
  try:  
    opts, args = getopt.getopt(sys.argv[1:],"hlt:", ["help","listen","time="])
 
  except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)  
  listening = False 
  timeofday = ''
  for opt, arg in opts:
    if opt in ("-h", "--help"):
      usage()		     
      sys.exit()		  
    elif opt in ("-l", "--listen"):
      listening = True		 
    elif opt in ("-t", "--time"):
      timeofday = arg			   
    else:
      assert False, "unhandled option"
 
  number = args[0]	   
  msg = args[1]
  if msg != '':
    if timeofday == '':
	sendmessage(number, msg)
    else:
	today = time.strftime('%b %d x %Y', time.localtime())
	schedule = today.replace('x', timeofday)
	schedule_task(schedule, sendmessage, number, msg)
  if listening:
    listen()
