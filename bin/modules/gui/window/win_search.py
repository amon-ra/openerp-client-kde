##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#					Fabien Pinckaers <fp@tiny.Be>
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

import gettext
from common import common

import rpc

from widget.screen import Screen
from widget.model.group import ModelRecordGroup
import widget_search


from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.uic import *

class SearchDialog( QDialog ):
	def __init__(self, model, sel_multi=True, ids=[], context={}, domain = [], parent = None):
		QDialog.__init__( self, parent )
		loadUi( common.uiPath('win_search.ui'), self )
		self.setModal( True )

		self.result=None
		self.context = context
		self.context.update(rpc.session.context)
		self.allowMultipleSelection = sel_multi

		self.modelGroup = ModelRecordGroup( model )
		self.modelGroup.setDomain( domain )

		self.screen = Screen( self )
		self.screen.setModelGroup( self.modelGroup )
		self.screen.setViewTypes( ['tree'] )

		self.view = self.screen.current_view
		self.view.setAllowMultipleSelection( sel_multi )
		self.view.setReadOnly( True )
		self.connect( self.view, SIGNAL('activated()'), self.accepted )

		self.advFrame.hide()

		self.model_name = model

		view_form = rpc.session.execute('/object', 'execute', self.model_name, 'fields_view_get', False, 'form', self.context)
		self.form = widget_search.SearchFormWidget( self )
		self.form.setup( view_form['arch'], view_form['fields'], model )
		self.form.hideButtons()

		self.title = _('Tiny ERP Search: %s') % self.form.name
		self.title_results = _('Tiny ERP Search: %s (%%d result(s))') % self.form.name

		self.setWindowTitle( self.title )

		self.ids = ids
		if self.ids:
			self.reload()
			model = self.view.widget.model()

		# TODO: Use Designer Widget Promotion instead
		layout = self.layout()
		layout.insertWidget(0, self.screen )
		layout.insertWidget(0, self.form )

		self.form.setFocus()

		self.connect( self.pushAccept, SIGNAL( "clicked()"), self.accepted )
		self.connect( self.pushCancel , SIGNAL( "clicked()"), self.reject )
		self.connect( self.pushFind, SIGNAL( "clicked()"), self.find )
		self.connect( self.advance, SIGNAL( "stateChanged(int)" ), self.slotAdvanceChecked )


	def find(self):
		#limit = self.limit.value()
		#offset = self.offset.value()

		#v = self.form.getValue(  )
		#self.ids = rpc.session.execute('/object', 'execute', self.model_name, 'search', v, offset, limit)
		#self.reload()
		self.modelGroup.setFilter( self.form.getValue() )
		self.reload()
		self.setWindowTitle( self.title_results % len( self.ids ))

	def reload(self):
		#self.screen.clear()
		#self.screen.load(self.ids)
		self.modelGroup.update()
		if self.allowMultipleSelection:
			self.view.widget.selectAll()

	def accepted( self ):
		self.result = self.screen.selectedIds() or self.ids
		self.accept()

	def slotAdvanceChecked( self, state ):
		if self.advance.isChecked():
			self.advFrame.show()
		else:
			self.advFrame.hide()
		
# vim:noexpandtab:
