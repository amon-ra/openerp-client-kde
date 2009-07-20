##############################################################################
#
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
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

from PyQt4.uic import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from Koo.Common import Common

from Koo.Screen.Screen import Screen
from Koo.Model.Group import RecordGroup

(ScreenDialogUi, ScreenDialogBase) = loadUiType( Common.uiPath('dia_form_win_many2one.ui') ) 

class ScreenDialog( QDialog, ScreenDialogUi ):
	def __init__(self, parent):
		QWidget.__init__( self, parent )
		ScreenDialogUi.__init__( self )
		self.setupUi( self )

		self.setMinimumWidth( 800 )
		self.setMinimumHeight( 600 )

		self.connect( self.pushOk, SIGNAL("clicked()"), self.accepted )
		self.connect( self.pushCancel, SIGNAL("clicked()"), self.reject )
		self.record = None
		self.recordId = None
		self.screen = None
		self._context = {}
		self._domain = []

	def setup(self, model, id=None):
		if self.screen:
			return
		self.group = RecordGroup( model, context=self._context )
		self.group.setDomain( self._domain )
		self.screen = Screen(self)
		self.screen.setRecordGroup( self.group )
		self.screen.setViewTypes( ['form'] )
		if id:
			self.screen.load([id])
		else:
			self.screen.new()
		self.screen.display()
		self.layout().insertWidget( 0, self.screen  )
		self.screen.show()
		
	def setAttributes(self, attrs):
		if ('string' in attrs) and attrs['string']:
			self.setWindowTitle( self.windowTitle() + ' - ' + attrs['string'])

	def setContext(self, context):
		self._context = context

	def setDomain(self, domain):
		self._domain = domain

	def accepted( self ):
		self.screen.currentView().store()

		if self.screen.save():
			self.record = self.screen.currentRecord().name()
			self.recordId = self.screen.currentRecord().id
			self.accept()

