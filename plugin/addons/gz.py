#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from __future__ import print_function
from Components.config import config
# commented out
#from Tools.Directories import shellquote
# added
from Plugins.Extensions.FileCommander.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from Plugins.Extensions.FileCommander.addons.unarchiver import ArchiverMenuScreen, ArchiverInfoScreen
from os.path import splitext

# for locale (gettext)
from . import _

pname = _("File Commander - gzip Addon")
pdesc = _("unpack gzip Files")
pversion = "0.2-r1"


class GunzipMenuScreen(ArchiverMenuScreen):

	def __init__(self, session, sourcelist, targetlist):
		super(GunzipMenuScreen, self).__init__(session, sourcelist, targetlist)
		self.skinName = "ArchiverMenuScreen"
		self.list.append((_("Unpack to current folder"), 1))
		self.list.append((_("Unpack to %s") % self.targetDir, 2))
		self.list.append((_("Unpack to %s") % config.usage.default_path.value, 3))

		self.pname = pname
		self.pdesc = pdesc
		self.pversion = pversion

	def unpackModus(self, id):
		print("[GunzipMenuScreen] unpackModus", id)
		pathName = self.sourceDir + self.filename
		if id == 1:
			cmd = ("gunzip", pathName)
		elif id in (2, 3):
			baseName, ext = splitext(self.filename)
			if ext != ".gz":
				return
			if id == 2:
				dest = self.targetDir
			elif id == 3:
				dest = config.usage.default_path.value
			dest += baseName
			cmd = "gunzip -c %s > %s && rm %s" % (shellquote(pathName), shellquote(dest), shellquote(pathName))
		self.unpackEConsoleApp(cmd)


class UnpackInfoScreen(ArchiverInfoScreen):

	def __init__(self, session, list, sourceDir, filename):
		super(UnpackInfoScreen, self).__init__(session, list, sourceDir, filename)
		self.skinName = "ArchiverInfoScreen"
		self.pname = pname
		self.pdesc = pdesc
		self.pversion = pversion
