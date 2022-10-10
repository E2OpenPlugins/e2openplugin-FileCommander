#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# ported from OpenATV to OpenPLi by mrvica April 2019
# fixed, added features, rebuilded in May 2020 ims
# based on Filebrowser plugin

from . import _

from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigYesNo, ConfigText

##################################
pname = _("File Commander")
pdesc = _("manage local Files")

config.plugins.filecommander = ConfigSubsection()
config.plugins.filecommander.add_mainmenu_entry = ConfigYesNo(default=False)
config.plugins.filecommander.add_extensionmenu_entry = ConfigYesNo(default=False)

# #####################
# ## Start routines ###
# #####################


def filescan_open(list, session, **kwargs):
	path = "/".join(list[0].path.split("/")[:-1]) + "/"
	from Plugins.Extensions.FileCommander import ui
	session.open(ui.FileCommanderScreen, path_left=path)


def start_from_filescan(**kwargs):
	from Components.Scanner import Scanner, ScanPath
	return \
		Scanner(
			mimetypes=None,
			paths_to_scan=[
				ScanPath(path="", with_subdirs=False),
			],
			name=pname,
			description=_("Open with File Commander"),
			openfnc=filescan_open,
		)


def start_from_mainmenu(menuid, **kwargs):
	# starting from main menu
	if menuid == "mainmenu":
		return [(pname, start_from_pluginmenu, "filecommand", 1)]
	return []


def start_from_pluginmenu(session, **kwargs):
	from Plugins.Extensions.FileCommander import ui
	session.openWithCallback(exit, ui.FileCommanderScreen)


def exit(session, result):
	if not result:
		from Plugins.Extensions.FileCommander import ui
		session.openWithCallback(exit, ui.FileCommanderScreen)


def Plugins(path, **kwargs):
	desc_mainmenu = PluginDescriptor(name=pname, description=pdesc, where=PluginDescriptor.WHERE_MENU, fnc=start_from_mainmenu)
	desc_pluginmenu = PluginDescriptor(name=pname, description=pdesc, where=PluginDescriptor.WHERE_PLUGINMENU, icon="FileCommander.png", fnc=start_from_pluginmenu)
	desc_extensionmenu = PluginDescriptor(name=pname, description=pdesc, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=start_from_pluginmenu)
	desc_filescan = PluginDescriptor(name=pname, where=PluginDescriptor.WHERE_FILESCAN, fnc=start_from_filescan)
	list = []
	list.append(desc_pluginmenu)
####
# 	buggy
# 	list.append(desc_filescan)
####
	if config.plugins.filecommander.add_extensionmenu_entry.value:
		list.append(desc_extensionmenu)
	if config.plugins.filecommander.add_mainmenu_entry.value:
		list.append(desc_mainmenu)
	return list
