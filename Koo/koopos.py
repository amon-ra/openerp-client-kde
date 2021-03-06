#!/usr/bin/python

##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
# Copyright (c) 2007-2011 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (c) 2011 P. Christeas <xrg@hellug.gr>
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

# Added so py2exe properly packs xml.etree.ElementTree
from xml.etree.ElementTree import parse, SubElement

import sys, os
import logging

if os.name == 'nt':
	sys.path.append('.')

from distutils.sysconfig import get_python_lib
terp_path = "/".join([get_python_lib(), 'Koo'])
sys.path.append(terp_path)

from Koo.Common.Settings import Settings, setup_logging
from Koo.Common import CommandLine
from Koo.Common import Localization

# Note that we need translations in order to parse command line arguments
# because we might have to print information to the user. However, koo's
# language configuration is stored in the .rc file users might provide in 
# the command line.
#
# To solve this problem we load translations twice: one before command line
# parsing and another one after, with the definitive language.
#
# Under windows, loading language twice doesn't work, and the first one loaded
# will be the one used so we first load settings from default file and registre,
# then load translations based on that file, then parse command line arguments
# and eventually load definitive translations (which windows will ignore silently).
Settings.loadFromFile()
Settings.loadFromRegistry()
Localization.initializeTranslations(Settings.value('client.language'))

arguments = CommandLine.parseArguments(sys.argv)

setup_logging()
Localization.initializeTranslations(Settings.value('client.language'))


imports={}

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from Koo.Common import Notifier, Common
from Koo.Common import DBus

# Declare notifier handlers for the whole application
Notifier.errorHandler = Common.error
Notifier.warningHandler = Common.warning
Notifier.concurrencyErrorHandler = Common.concurrencyError


logger = logging.getLogger('koopos')

### Main application loop
if Common.isKdeAvailable:
	from PyKDE4.kdecore import ki18n, KAboutData, KCmdLineArgs
	from PyKDE4.kdeui import KApplication

	appName     = "Koo"
	catalog     = ""
	programName = ki18n ("Koo")
	version     = "1.0"
	description = ki18n ("KDE OpenObject Client")
	license     = KAboutData.License_GPL
	copyright   = ki18n ("(c) 2009 Albert Cervera i Areny")
	text        = ki18n ("none")
	homePage    = "www.nan-tic.com"
	bugEmail    = "albert@nan-tic.com"
	 
	aboutData   = KAboutData (appName, catalog, programName, version, description,
				license, copyright, text, homePage, bugEmail)

	KCmdLineArgs.init (arguments, aboutData)
	 
	app = KApplication ()
else:
	app = QApplication( arguments )

logger.debug('init application')
app.setApplicationName( 'Koo POS' )
app.setOrganizationDomain( 'www.NaN-tic.com' )
app.setOrganizationName( 'NaN' )

try:
	f = open( Settings.value('koo.stylesheet') or  'Koo/Pos/pos.qss', 'r' )
	try:
		app.setStyleSheet( f.read() )
	finally:
		f.close()
except Exception:
        # TODO narrow down
        logger.warning("could not apply stylesheet", exc_info=True)
	pass

Localization.initializeQtTranslations(Settings.value('client.language'))


from Koo.Dialogs.KooMainWindow import *
from Koo.Dialogs.WindowService import *
import Koo.Actions

mainWindow = QMainWindow(None, Qt.CustomizeWindowHint)

if Settings.value('koo.show_pos_toolbar', True):

	toolBar = QToolBar(mainWindow)

	if Settings.value('koo.show_pos_button_new', True):

		def executeNew():
			mainWindow.centralWidget().new()

		actionNew = QAction( mainWindow )
		actionNew.setIcon( QIcon( ':/images/new.png' ) )
		QObject.connect(actionNew, SIGNAL('triggered()'), executeNew)
		toolBar.addAction( actionNew )

	if Settings.value('koo.show_pos_button_switch_view', True):

		def executeSwitchView():
			mainWindow.centralWidget().switchView()

		actionSwitchView = QAction( mainWindow )
		actionSwitchView.setIcon( QIcon( ':/images/switch_view.png' ) )
		QObject.connect(actionSwitchView, SIGNAL('triggered()'), executeSwitchView)
		toolBar.addAction( actionSwitchView )

        def executeClose():
            mainWindow.centralWidget().new()

        actionClose = QAction( mainWindow )
        actionClose.setIcon( QIcon( ':/images/close.png' ) )
        QObject.connect(actionClose, SIGNAL('triggered()'), mainWindow.close)
        toolBar.addAction( actionClose )

	mainWindow.addToolBar( Qt.LeftToolBarArea, toolBar )

from Koo.Common import Api

class KooApi(Api.KooApi):
	def execute(self, actionId, data={}, type=None, context={}):
		Koo.Actions.execute( actionId, data, type, context )

	def executeReport(self, name, data={}, context={}):
		return Koo.Actions.executeReport( name, data, context )

	def executeAction(self, action, data={}, context={}):
		Koo.Actions.executeAction( action, data, context )
		
	def executeKeyword(self, keyword, data={}, context={}):
		return Koo.Actions.executeKeyword( keyword, data, context )

	def createWindow(self, view_ids, model, res_id=False, domain=None, 
			view_type='form', window=None, context=None, mode=None, name=False, autoReload=False, 
			target='current'):
		WindowService.createWindow( view_ids, model, res_id, domain, 
			view_type, window, context, mode, name, autoReload, target )

	def windowCreated(self, window, target):
		mainWindow.setCentralWidget( window )
		window.setParent( mainWindow )
		window.show()

Api.instance = KooApi()

if Settings.value('koo.pos_mode'):
        import Koo.Pos
        logger.debug("POS mode on")
	app.installEventFilter( Koo.Pos.PosEventFilter(mainWindow) )

if Settings.value('koo.enter_as_tab'):
	from Koo.Common import EnterEventFilter
	app.installEventFilter( EnterEventFilter.EnterEventFilter(mainWindow) )

from Koo.Common import ArrowsEventFilter
app.installEventFilter( ArrowsEventFilter.ArrowsEventFilter(mainWindow) )

from Koo.Common import WhatsThisEventFilter
app.installEventFilter( WhatsThisEventFilter.WhatsThisEventFilter(mainWindow) )

# Load default wizard
logger.debug("Before login")
if not Settings.value( 'login.url'):
	sys.exit( "Error: No connection parameters given." )
if not Settings.value( 'login.db'):
	sys.exit( "Error: No database given." )

if not Rpc.login_session( Settings.value('login.url'), Settings.value('login.db') ):
	sys.exit( "Error: Invalid credentials." )

logger.debug("after login")
id = Rpc.RpcProxy('res.users').read([Rpc.session.get_uid()], ['action_id','name'], Rpc.session.context)

# Store the menuId so we ensure we don't open the menu twice when
# calling openHomeTab()
logger.debug("action id: %r", id)

if not (id[0]['action_id']):
    logger.error("User \"%s\" %d does not have a default action, please set it up!",
            id[0]['name'], id[0]['id'])
    sys.exit(1)

menuId = id[0]['action_id'][0]

# After this "event", we must call the application loop, so only fire it
# if we have no other failures.

# TODO: configurable
mainWindow.showFullScreen()


Api.instance.execute(menuId)

app.exec_()

logger.info("Application exiting normally")
#eof
