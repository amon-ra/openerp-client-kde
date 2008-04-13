##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: form.py 4444 2006-11-05 11:12:27Z pinky $
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

import types
import gettext

import rpc
from win_search import SearchDialog
import win_export
import win_import

from common import common
import service
from common import options
import copy

from widget.screen import Screen
from widget.model.group import ModelRecordGroup
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
from win_gotoid import *


class form( QWidget ):
	# form constructor:
	# model -> Name of the model the form should handle
	# res_id -> List of ids of type 'model' to load
	# domain -> Domain the models should be in
	# view_type -> type of view: form, tree, graph, calendar, ...
	# view_ids -> Id's of the views 'ir.ui.view' to show
	# context -> Context for the current data set
	# parent -> Parent widget of the form
	# name -> User visible title of the form
	def __init__(self, model, res_id=False, domain=[], view_type=None, view_ids=[], context={}, parent=None, name=False):
		QWidget.__init__(self,parent)
		loadUi( common.uiPath('formcontainer.ui'), self ) 

		if not view_type:
			view_type = ['form','tree']
		else:
			if view_type[0] in ['graph'] and not res_id:
				res_id = rpc.session.execute('/object', 'execute', model, 'search', domain)
		fields = {}
		self.model = model
		self.previous_action = None
		self.fields = fields
		self.domain = domain
		self.context = context

		self.group = ModelRecordGroup( self.model, context=self.context )
		self.group.setDomain( domain )

		self.screen = Screen(self)
		self.screen.setModelGroup( self.group )
		#self.screen.setDomain( domain )
		self.screen.setEmbedded( False )
		self.connect( self.screen, SIGNAL('activated()'), self.switchView )

		self._allowOpenInNewWindow = True

		# Remove ids with False value
		view_ids = [x for x in view_ids if x]
		if view_ids:
			self.screen.setViewIds( view_ids )
		else:
			self.screen.setViewTypes( view_type )

		self.connect(self.screen, SIGNAL('recordMessage(int,int,int)'), self.updateRecordStatus)
		if name:
			self.name = name
		else:
			self.name = self.screen.current_view.title

		# TODO: Use desinger's widget promotion
		self.layout().insertWidget(0, self.screen )

		self.has_backup = False
		self.backup = {}

		self.handlers = {
			'New': self.sig_new,
			'Save': self.sig_save,
			'Export': self.sig_export,
			'Import': self.sig_import,
			'Repeat': self.repeatLastPrint,
			'Delete': self.sig_remove,
			'Find': self.sig_search,
			'Previous': self.previous,
			'Next':  self.next,
			'GoToResourceId':  self.sig_goto,
			'AccessLog':  self.showLogs,
			'Reload': self.reload,
			'Switch': self.switchView,
			'Attach': self.showAttachments,
			'Plugins': self.executePlugins,
			'Duplicate': self.duplicate
		}
		if res_id:
			if isinstance(res_id, int):
				res_id = [res_id]
			self.screen.load(res_id)
		else:
			if len(view_type) and view_type[0]=='form':
				self.sig_new(autosave=False)
		self.updateStatus()
		self.updateRecordStatus(-1,self.group.count(),None)

	def setAllowOpenInNewWindow( self, value ):
		self._allowOpenInNewWindow = value

	def sig_goto(self, *args):
		if not self.modified_save():
			return
		dialog = GoToIdDialog( self )
		if dialog.exec_() == QDialog.Rejected:
			return
		self.screen.load( [dialog.result] )
		
	def ids_get(self):
		return self.screen.ids_get()

	def id_get(self):
		return self.screen.id_get()

	def showAttachments(self, widget=None):
		id = self.screen.id_get()
		if id:
			import win_attach
			win = win_attach.win_attach(self.model, id, self)
			win.show()
			self.updateStatus()
		else:
			self.updateStatus(_('No resource selected !'))

	def switchView(self):
		if not self.modified_save():
			return
		if ( self._allowOpenInNewWindow and QApplication.keyboardModifiers() & Qt.ControlModifier ) == Qt.ControlModifier:
			obj = service.LocalService('gui.window')
			obj.create(None, self.model, self.screen.id_get(), view_type='form', mode='form,tree')
		else:
			self.screen.switchView()

	def _id_get(self):
		return self.screen.id_get()

	def showLogs(self, widget=None):
		id = self._id_get()
		if not id:
			self.updateStatus(_('You have to select one resource!'))
			return False
		res = rpc.session.execute('/object', 'execute', self.model, 'perm_read', [id])
		message = ''
		for line in res:
			todo = [
				('id', _('ID')),
				('create_uid', _('Creation User')),
				('create_date', _('Creation Date')),
				('write_uid', _('Latest Modification by')),
				('write_date', _('Latest Modification Date')),
				('uid', _('Owner')),
				('gid', _('Group Owner')),
				('level', _('Access Level'))
			]
			for (key,val) in todo:
				if line[key] and key in ('create_uid','write_uid','uid'):
					line[key] = line[key][1]
				message+=val+': '+str(line[key] or '/')+'\n'
		QMessageBox.information(self, '', message)

	def sig_remove(self):
		value = QMessageBox.question(self,_('Question'),_('Are you sure you want to remove these records?'),QMessageBox.Yes|QMessageBox.No)
		if value == QMessageBox.Yes:
			if not self.screen.remove(unlink=True):
				self.updateStatus(_('Resource not removed !'))
			else:
				self.updateStatus(_('Resource removed.'))

	def sig_import(self):
		fields = []
		dialog = win_import.win_import(self.model, self.screen.fields, fields)
		dialog.exec_()

	def sig_export(self):
		fields = []
		dialog = win_export.win_export(self.model, self.screen.ids_get(), self.screen.fields, fields)
		dialog.exec_()

	def sig_new(self, widget=None, autosave=True):
		if autosave:
			if not self.modified_save():
				return
		self.screen.new()
	
	def duplicate(self):
		if not self.modified_save():
			return
		res_id = self._id_get()
		new_id = rpc.session.execute('/object', 'execute', self.model, 'copy', res_id, {}, rpc.session.context)
		self.screen.load([new_id])
		self.updateStatus(_('Working now on the duplicated document !'))

	def _form_save(self, auto_continue=True):
		pass

	def sig_save(self, widget=None, sig_new=True, auto_continue=True):
		modification = self.screen.current_model.id
		id = self.screen.save_current()
		if id:
			self.updateStatus(_('Document saved !'))
			if not modification:
				self.screen.new()
		else:
			self.updateStatus(_('Invalid form !'))
		return bool(id)

	def previous(self, widget=None):
		if not self.modified_save():
			return
		self.screen.display_prev()
		self.updateStatus()

	def next(self, widget=None):
		if not self.modified_save():
			return
		self.screen.display_next()
		self.updateStatus()

	def reload(self):
		if self.screen.current_view.view_type == 'form':
			self.screen.cancel_current()
			self.screen.display()
		else:
			id = self.screen.id_get()
			ids = self.screen.ids_get()
			self.screen.clear()
			self.screen.load(ids)
			for model in self.screen.models:
				if model.id == id:
					self.screen.current_model = model
					self.screen.display()
					break
		self.updateStatus()

	def executeAction(self, keyword='client_action_multi', previous=False, report_type='pdf', adds={}):
		ids = self.screen.ids_get()
		if self.screen.current_model:
			id = self.screen.current_model.id
		else:
			id = False
		if self.screen.current_view.view_type == 'form':
			id = self.screen.save_current()
			if not id:
				return False
			ids = [id]
		if len(ids):
			obj = service.LocalService('action.main')
			if previous and self.previous_action:
				obj._exec_action(self.previous_action[1], {'model':self.screen.resource, 'id': id or False, 'ids':ids, 'report_type': report_type})
			else:
				res = obj.exec_keyword(keyword, {'model':self.screen.resource, 'id': id or False, 'ids':ids, 'report_type': report_type}, adds=adds)
				if res:
					self.previous_action = res
			self.reload()
		else:
			self.updateStatus(_('No record selected!'))

	def repeatLastPrint(self):
		self.executeAction('client_print_multi', True)

	def sig_search(self, widget=None):
		if not self.modified_save():
			return
		dom = self.domain
		dialog = SearchDialog(self.model, domain=self.domain, context=self.context, parent=self)
		if dialog.exec_() == QDialog.Rejected:
			return
		self.screen.clear()
		self.screen.load( dialog.result )

	def updateStatus(self, message=''):
		if self.model and self.screen.current_model and self.screen.current_model.id:
			ids=rpc.session.execute('/object', 'execute', 'ir.attachment', 'search', [('res_model','=',self.model),('res_id','=',self.screen.current_model.id)])
			message = ( _("(%s attachments) ") % len(ids) ) + message
		self.uiStatus.setText( message )

	def updateRecordStatus(self, position, count, value):
		if not count:
			msg = _('No records')
		else:
			pos = '_'
			if position >= 0:
				pos = str(position+1)
			if value == None:
				# Value will be None only when it's called by the constructor
				edit = _('No document selected')
			else:
				# Other times it'll either be 0 (new document) or the appropiate
				# object i
				edit = _('New document')
				if value > 0:
					edit = _('Editing document (id: %s)') % str(value)
			msg = _('Record: %(name)s / %(count)s - %(name2)s') % { 'name': pos, 'count': str(count), 'name2': edit }

		self.statForm.setText( msg )

	def modified_save(self):
		if self.screen.isModified():
			value = QMessageBox.question(self, _('Question'), _('This record has been modified do you want to save it?'),QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel)
			if value == QMessageBox.Save:
				return self.sig_save()
			elif value == QMessageBox.Discard:
				self.reload()
				return True
			else:
				return False
		return True

	def canClose(self, urgent=False):
		return self.modified_save()

	def actions(self):
		return self.screen.actions

	def executePlugins(self):
		import plugins
		datas = {'model': self.model, 'ids':self.screen.ids_get(), 'id' : self.screen.id_get()}
		plugins.execute(datas)

