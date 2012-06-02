#!/usr/bin/env python2.5
 
import pexpect
import time
from subprocess import *
 
child = pexpect.spawn('pnatd');
child.send('at\r');
time.sleep(0.25);
child.send('at+cmgf=1\r');
time.sleep(0.25);
number = 'at+cmgs="+%s"\r' % ('7012027323')
child.send(number);
message = 'Hello world'
child.send(message);
child.send(chr(26));
child.send(chr(26));
child.sendeof();

