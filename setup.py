#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setup for Koo (taken from OpenERP GTK client)
#   taken from straw http://www.nongnu.org/straw/index.html
#   taken from gnomolicious http://www.nongnu.org/gnomolicious/
#   adapted by Nicolas Évrard <nicoe@altern.org>

import imp
import sys
import os
import glob

from stat import ST_MODE

from distutils.file_util import copy_file
from distutils.sysconfig import get_python_lib
from distutils.core import setup

try:
  import py2exe

  # Override the function in py2exe to determine if a dll should be included
  dllList = ('mfc90.dll','msvcp90.dll')
  origIsSystemDLL = py2exe.build_exe.isSystemDLL
  def isSystemDLL(pathname):
    if os.path.basename(pathname).lower() in dllList:
      return 0
    return origIsSystemDLL(pathname)
  py2exe.build_exe.isSystemDLL = isSystemDLL
  
  using_py2exe = True
except:
  using_py2exe = False
  pass

opj = os.path.join

name = 'koo'
version = '1.0.0-beta2'

# get python short version
py_short_version = '%s.%s' % sys.version_info[:2]

required_modules = [
	('PyQt4.QtCore', 'Qt4 Core python bindings'),
	('PyQt4.QtGui', 'Qt4 Gui python bindings'),
	('PyQt4.uic', 'Qt4 uic python bindings'),
	('PyQt4.QtWebKit', 'Qt4 WebKit python bindings')
]

def check_modules():
	ok = True
	for modname, desc in required_modules:
		try:
			exec('import %s' % modname)
		except ImportError:
			ok = False
			print 'Error: python module %s (%s) is required' % (modname, desc)

	if not ok:
		sys.exit(1)

def data_files():
	'''Build list of data files to be installed'''
	files = [
		(opj('share','man','man1',''),[ opj('man','koo.1')]),
		(opj('share', 'doc', 'koo', 'manual' ), [f for f in glob.glob(opj('doc','html','*')) if os.path.isfile(f)]),
		(opj('share', 'doc', 'koo', 'api' ), [f for f in glob.glob(opj('doc','doxygen','html','*')) if os.path.isfile(f)]),
		(opj('share', 'Koo'), [ opj('Koo','kootips.txt')]),
		(opj('share', 'Koo', 'ui'), glob.glob( opj('Koo','ui','*.ui') ) ),
		(opj('share', 'Koo', 'l10n'), glob.glob( opj('Koo','l10n','*.qm')) )
	]
	if using_py2exe:
		#trans = []
		dest = opj('share','locale','%s','LC_MESSAGES')
		#src = opj('Koo','l10n','%s','LC_MESSAGES','%s.mo')
		#for po in glob.glob( opj('Koo','l10n','*.po') ):
		    #lang = os.path.splitext(os.path.basename(po))[0]
		    #files.append( (dest % (lang, name), src % (lang, name) ) )
		    #print "ADDING: ", ( dest % (lang, name), src % (lang, name) )
		for src in glob.glob( opj('Koo','l10n','*','LC_MESSAGES','koo.mo') ):
			lang = src.split(os.sep)[2]
			files.append( ( (dest % lang), [src] ) )
	return files

def findPlugins( module ):
	result = []
	plugins = [x for x in glob.glob( opj('Koo', module,'*') ) if os.path.isdir(x)]
	for plugin in plugins:
		for dirpath, dirnames, filenames in os.walk(plugin):
			if '__init__.py' in filenames:
				result.append( dirpath.replace(os.path.sep, '.') )
	return result

def translations():
    trans = []
    dest = opj('share','locale','%s','LC_MESSAGES','%s.mo')
    for po in glob.glob( opj('Koo','l10n','*.po') ):
        lang = os.path.splitext(os.path.basename(po))[0]
        trans.append((dest % (lang, name), po))
    return trans




long_desc = '''\
=====================================
Koo Client and Development Platform
=====================================

Koo is a Qt/KDE based client for Open ERP, a complete ERP and CRM. Koo 
aims for great flexibility allowing easy creation of plugins and views, high
integration with KDE4 under Unix, Windows and Mac, as well as providing
a development platform for new applications using the Open ERP server.

A set of server side modules is also provided among the Koo distribution
which provide better attachments handling and full text search capabilities.
'''

classifiers = """\
Development Status :: 4 - Beta
License :: OSI Approved :: GNU General Public License (GPL)
Programming Language :: Python
Topic :: Desktop Environment :: K Desktop Environment (KDE)
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: MacOS
Topic :: Office/Business
"""

check_modules()

# create startup script
start_script = """
cd %s/Koo
exec %s ./koo.py $@
""" % ( get_python_lib(), sys.executable)
# write script
f = open('koo.py', 'w')
f.write(start_script)
f.close()

# todo: use 
command = sys.argv[1]

packages = [
	'Koo', 
	'Koo.Actions', 
	'Koo.Common', 
	'Koo.Dialogs',
	'Koo.KooChart',
	'Koo.Model',
	'Koo.Plugins',
	'Koo.Printer',
	'Koo.Rpc',
	'Koo.Screen',
	'Koo.Search',
	'Koo.View',
	'Koo.Fields',
        ] + findPlugins('Plugins') + findPlugins('View') + findPlugins('Fields')

setup(name             = name,
      version          = version,
      description      = "Koo Client",
      long_description = long_desc,
      url              = 'http://sf.net/projects/ktiny',
      author           = 'NaN',
      author_email     = 'info@nan-tic.com',
      classifiers      = filter(None, classifiers.splitlines()),
      license          = 'GPL',
      data_files       = data_files(),
      translations     = translations(),
      pot_file         = opj('Koo','l10n','koo.pot'),
      scripts          = ['koo.py'],
      windows          = [{'script': opj('Koo','koo.py')}],
      #console          = ['Koo/koo.py'],
      packages         = packages ,
      package_dir      = {'Koo': 'Koo'},
      provides         = [ 'Koo' ],
      options          = { 'py2exe': {
                                'includes': ['sip', 'PyQt4.QtNetwork',
					'PyQt4.QtWebKit'] + packages 
                                }
                         }
      )
