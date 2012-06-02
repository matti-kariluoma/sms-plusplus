import gobject, dbus
from dbus.mainloop.glib import DBusGMainLoop
 
def handle_sms(pdu, msgcenter, somestring, sendernumber):
    print 'New message from %s' % sendernumber
 
DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
bus.add_signal_receiver(handle_sms, path='/com/nokia/phone/SMS',   dbus_interface='Phone.SMS', signal_name='IncomingSegment')
gobject.MainLoop().run()

