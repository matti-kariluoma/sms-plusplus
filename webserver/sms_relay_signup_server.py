#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Hello.
#
#Matti Kariluoma <matti@kariluo.ma> Mar 2012

from bottle import Bottle, run, view, static_file, TEMPLATE_PATH, request
from bottle_sqlite import SQLitePlugin
from render_html import render_url
db_filename = 'sqlite.db'
root_path = './'
static_path = root_path+"static/"

server = Bottle()
del TEMPLATE_PATH[0:len(TEMPLATE_PATH)]
TEMPLATE_PATH.append('./templates/')
sqlplugin = SQLitePlugin(dbfile=db_filename)
server.install(sqlplugin)

"""
# Python decorators:
# http://www.ibm.com/developerworks/linux/library/l-cpdecor/index.html

# With decorations:
@server.route('/hello')
def hello():
	return "No.\n"
	
#Without decorations:
def again():
	return "Yes.\n"
again = server.route('/again')(again)
"""

@server.error(404)
def error404(error):
	return """<h3>404</h3>
<p>Please, don't do that.</p>"""

@server.route('/') # index.html
@view('main') # looks for a 'main.tpl' in the TEMPLATE_PATH list
def index():
	return dict(name="Guest", root=root_path)
	
@server.route('/register') # index.html
@view('register') # looks for a 'main.tpl' in the TEMPLATE_PATH list
def index():
	return dict(root=root_path)
	
@server.route('/render') # index.html
@view('render') # looks for a 'main.tpl' in the TEMPLATE_PATH list
def index():	
	dered = render_url(request.query.url_to_render.replace('>','?').replace('<','&'))
	dered = str(dered).replace('&quot;','"').replace('#039;',"'")
	return dict(rendered=dered)

def setup_sqldb():
	pass
	"""
	import sqlite3
	with open('sqlite.db.sql') as f:
		sql = ''.join([line for line in f])
	sqlite3.connect(db_filename).cursor().executescript(sql)	
	"""

def setup_static():
	@server.route('/static/<filename:path>')
	def send_static(filename):
		return static_file(filename, root=static_path)

def main():
	#setup_sqldb()
	setup_static()
	server.run(host='www.atarkri.com', port='8080', debug=True)
	
if __name__ == '__main__':
	main()
