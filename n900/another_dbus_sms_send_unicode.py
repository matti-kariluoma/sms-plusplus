#!/usr/bin/env python2.5
#coding=utf-8
import sched, time                
import dbus                       
import gobject
import sys
from dbus.mainloop.glib import DBusGMainLoop

# originally from http://ztbsauer.com/sender.py by pende
# patched by me Alexander Borunov http://borunov.ural.ru/sender.py
'''
Sent to me in an email, formatted code and translated comments.
Improves unicode support.
Released into public domain
Matti Kariluoma <matti@kariluo.ma> Dec 2014
'''

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
	number_length = len(number)
	
	if (numlength % 2) == 0:                                
		rangelength = numlength                         
	else:                                                   
		number = number + 'F'                           
		rangelength = len(number)                       
	
	octifiednumber = [ semi_octify(number[i:i+2]) for i in range(0,rangelength,2) ]
	#        octifiedmsg = octify(msg) теперь сообщение в unicode не будем его октифицировать
	#        octifiedmsg = octify(msg) now the message will not be in unicode 
	msg_length = len(msg)*2 # два байта на символ
	
	#        HEADER = 1                                                                     
	#        FIRSTOCTETOFSMSDELIVERMSG = 10                                                 
	#        ADDR_TYPE = 129 #unknown format
	#        pdu_message = [HEADER, FIRSTOCTETOFSMSDELIVERMSG, number_length, ADDR_TYPE]    
	
	PDU_TYPE = 0x11 
	MR = 0
	ADDR_TYPE = 0x91 #international format
	
	pdu_message = [PDU_TYPE, MR, number_length, ADDR_TYPE]
	pdu_message.extend(octifiednumber)
	
	pdu_message.append(0) #PID
	pdu_message.append(8) #DCS
	
	pdu_message.append(167) #VP 24 hours
	
	pdu_message.append(msg_length)
	# добвляем САМО сообщение а не октифицированную его версию!
	# append message, not its encoded version!
	#        pdu_message.extend(msg)
	for i in xrange (len(msg)) :
		digit = ord(msg[i])
		h_digit = digit >> 8
		l_digit = digit & 0xFF
		pdu_message.append(h_digit)
		pdu_message.append(l_digit)
	
	return pdu_message

def createPDUmessage_parted(number, msg, number_of_serie, part_number, number_of_parts):
	'''                       
	Returns a list of bytes to represent a valid PDU message
	'''                                                     
	numlength = len(number)
	number_length = len(number)
	
	# добавим к номеру в конце буковку F если длина номера нечетная
	# if length odd, add 'F' to end of number 
	if (numlength % 2) == 0:
		rangelength = numlength
	else:
		number = number + 'F'
		rangelength = len(number)
	# преобразуем номер получателя в принятый в заголовке формат
	# transform the recipient's phone number in the received header format
	octifiednumber = [ semi_octify(number[i:i+2]) for i in range(0,rangelength,2) ]
	
	# два байта на символ плюс 6 байт на заголовок в соощени что это длинное смс
	# two bytes per character plus 6 bytes header
	msg_length = len(msg)*2 + 6
	
	# добавили бит что перед телом сообщения будет заголовок гда информация о склейке
	# add a bit to the body of the message that will head the GDA information about gluing
	PDU_TYPE = 0x51 
	MR = 0
	ADDR_TYPE = 0x91 #international format
	
	pdu_message = [PDU_TYPE, MR, number_length, ADDR_TYPE]
	pdu_message.extend(octifiednumber)
	
	pdu_message.append(0) #PID
	pdu_message.append(8) #DCS
	
	pdu_message.append(167) #VP 24 hours
	
	pdu_message.append(msg_length)
	
	# добавим заголовок о том что у нас часть большого сообщения всего 6 байт
	# add a title that we have a large part of the message of 6 bytes
	pdu_message.append(5)
	pdu_message.append(0)
	# это всегда так
	# it is always the case
	pdu_message.append(3) 
	
	# уникальный для данной группы смс номер. хрен его знает как брать. будет пока 13
	# unique to this group sms number. hell knows how to take . will be until 13
	pdu_message.append(number_of_serie)
	# количество смс для склейки
	# number of sms for gluing
	pdu_message.append(number_of_parts)
	# порядковый номер смс
	# serial number of sms
	pdu_message.append(part_number)
	
	# добвляем САМО сообщение а не октифицированную его версию!
	# append message, not its encoded version!
	for i in xrange (len(msg)) :
		digit = ord(msg[i])
		h_digit = digit >> 8
		l_digit = digit & 0xFF
		pdu_message.append(h_digit)
		pdu_message.append(l_digit)
	
	return pdu_message

def send_single_message(number, message):
	bus = dbus.SystemBus()
	smsobject = bus.get_object('com.nokia.phone.SMS', '/com/nokia/phone/SMS/ba212ae1')
	smsiface = dbus.Interface(smsobject, 'com.nokia.csd.SMS.Outgoing')
	arr = dbus.Array(createPDUmessage(number, message))
	msg = dbus.Array([arr])
	smsiface.Send(msg,'')

def send_long_message(number, message):
	bus = dbus.SystemBus()
	smsobject = bus.get_object('com.nokia.phone.SMS', '/com/nokia/phone/SMS/ba212ae1')
	smsiface = dbus.Interface(smsobject, 'com.nokia.csd.SMS.Outgoing')
	# сюда будем складывать порезанные сообщения
	# here we add the chopped messages
	result = [] 
	# это длина большого сообщения
	# is the length of a large message
	l = len(message) 
	if l < 70:
		# строка помещается в одно сообщение
		# string is placed in one 
		send_single_message(number, message)
		#print "отправили одним сообщением"
		#print "sent one message"
		return
	else:
		#print "строка длинная, будем резать"
		#print "A string of length, will be "
		for i in xrange (0, l, 63) :
			result.append(message[i:i+63])
	
	l = len(result)
	for i in xrange(0,l):
		#print i
		#print l
		#print result[i].encode("utf-8")
		arr = dbus.Array(createPDUmessage_parted(number, result[i], 13, i+1, l))
		msg = dbus.Array([arr])
		smsiface.Send(msg,'')

if __name__ == '__main__':
	if sys.argv[1].isdigit():
		sendernumber = sys.argv[1]
		sms_message = unicode(sys.argv[2],"utf-8")
		send_long_message(sendernumber,sms_message)
