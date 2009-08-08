##############################################################################
#
# Copyright (c) 2007-2008 Albert Cervera i Areny <albert@nan-tic.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
from PyQt4.QtWebKit import *
from PyQt4.QtNetwork import *
from Koo.Common import Common
from Koo.Fields.AbstractFieldWidget import *

(WebFieldWidgetUi, WebFieldWidgetBase) = loadUiType( Common.uiPath('web.ui') ) 

## @brief The CookieJar class inherits QNetworkCookieJar to make a couple of functions public.
class CookieJar(QNetworkCookieJar):
	def __init__(self, parent=None):
		QNetworkCookieJar.__init__(self, parent)

	def allCookies(self):
		return QNetworkCookieJar.allCookies(self)
	
	def setAllCookies(self, cookieList):
		QNetworkCookieJar.setAllCookies(self, cookieList)

class WebFieldWidget(AbstractFieldWidget, WebFieldWidgetUi):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		WebFieldWidgetUi.__init__(self)
		self.setupUi( self )
		self.cookieJar = CookieJar()
		self.uiWeb.page().networkAccessManager().setCookieJar( self.cookieJar )

	def store(self):
		pass

	def clear( self ):
		self.uiWeb.setUrl(QUrl(''))

	def showValue(self):
		self.uiWeb.setUrl(QUrl(self.record.value(self.name) or ''))

	def setReadOnly(self, value):
		# We always enable the browser so the user can use links.
		self.uiWeb.setEnabled( True )

	def saveState(self):
		cookieList = self.cookieJar.allCookies()
		raw = []
		for cookie in cookieList:
			# We don't want to store session cookies
			if cookie.isSessionCookie():
				continue
			# Store cookies in a list as a dict would occupy
			# more space and we want to minimize network bandwidth
			raw.append( [
				str(cookie.name().toBase64()), 
				str(cookie.value().toBase64()), 
				str(cookie.path()),
				str(cookie.domain()),
				str(cookie.expirationDate().toString()),
				str(cookie.isHttpOnly()),
				str(cookie.isSecure()),
			])
		return QByteArray( str( raw ) )

	def restoreState(self, value):
		if not value:
			return
		raw = eval( str( value ) )
		cookieList = []
		for cookie in raw:
			name = QByteArray.fromBase64( cookie[0] )
			value = QByteArray.fromBase64( cookie[1] )
			networkCookie = QNetworkCookie( name, value )
			networkCookie.setPath( cookie[2] )
			networkCookie.setDomain( cookie[3] )
			networkCookie.setExpirationDate( QDateTime.fromString( cookie[4] ) )
			networkCookie.setHttpOnly( eval(cookie[5]) )
			networkCookie.setSecure( eval(cookie[6]) )
			cookieList.append( networkCookie )
		self.cookieJar.setAllCookies( cookieList )
		self.uiWeb.page().networkAccessManager().setCookieJar( self.cookieJar )

# vim:noexpandtab:

