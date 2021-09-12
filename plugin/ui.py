#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from Plugins.Plugin import PluginDescriptor
from plugin import pname, pdesc

# Components
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText, ConfigDirectory, ConfigSelection, ConfigSet, NoSave, ConfigNothing, ConfigLocations, ConfigSelectionNumber, getConfigListEntry
from Components.Label import Label
# commented out
# from Components.FileTransfer import FileTransferJob, ALL_MOVIE_EXTENSIONS
from Components.Task import job_manager
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Sources.Boolean import Boolean
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.ChoiceList import ChoiceList, ChoiceEntryComponent
from Components.ConfigList import ConfigListScreen
from Components.Pixmap import Pixmap
from Components.Sources.Boolean import Boolean

# Screens
from Screens.Screen import Screen
# commented out
# from Screens.Console import Console
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.LocationBox import LocationBox
from Screens.HelpMenu import HelpableScreen
# commented out
# from Screens.TaskList import TaskListScreen
from Screens.MovieSelection import defaultMoviePath
from Screens.InfoBar import InfoBar
from Screens.VirtualKeyBoard import VirtualKeyBoard

# Tools
from Tools.BoundFunction import boundFunction
# commented out
#from Tools.UnitConversions import UnitScaler, UnitMultipliers
from Tools import Notifications

# Various
from enigma import eConsoleAppContainer, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, eTimer, getDesktop

import os
import stat
import string
import re

# System mods
from InputBox import InputBox
from FileList import FileList, MultiFileSelectList, EXTENSIONS
# added
from Console import Console
from UnitConversions import UnitScaler, UnitMultipliers
from TaskList import TaskListScreen
from FileTransfer import FileTransferJob, ALL_MOVIE_EXTENSIONS

# Addons
from addons.key_actions import key_actions, stat_info
from addons.type_utils import vEditor

# for locale (gettext)
from . import _, ngettext

pvers = "%s%s" % (_("v"), "2.12")

MOVIEEXTENSIONS = {"cuts": "movieparts", "meta": "movieparts", "ap": "movieparts", "sc": "movieparts", "eit": "movieparts"}


def _make_filter(media_type):
	return "(?i)^.*\.(" + '|'.join(sorted((ext for ext, type in EXTENSIONS.iteritems() if type == media_type))) + ")$"


def _make_rec_filter():
	return "(?i)^.*\.(" + '|'.join(sorted(["ts"] + [ext == "eit" and ext or "ts." + ext for ext in MOVIEEXTENSIONS.iterkeys()])) + ")$"


FULLHD = False
if getDesktop(0).size().width() >= 1920:
	FULLHD = True

movie = _make_filter("movie")
music = _make_filter("music")
pictures = _make_filter("picture")
records = _make_rec_filter()

dmnapi_py = "/usr/lib/enigma2/python/Plugins/Extensions/FileCommander/addons/dmnapi.py"
##################################

config.plugins.filecommander.savedir_left = ConfigYesNo(default=False)
config.plugins.filecommander.savedir_right = ConfigYesNo(default=False)

config.plugins.filecommander.editposition_lineend = ConfigYesNo(default=False)
config.plugins.filecommander.path_default = ConfigDirectory(default="")
config.plugins.filecommander.path_left = ConfigText(default="")
config.plugins.filecommander.path_right = ConfigText(default="")
config.plugins.filecommander.all_movie_ext = ConfigYesNo(default=True)
config.plugins.filecommander.cursorposition = ConfigYesNo(default=False)
config.plugins.filecommander.my_extension = ConfigText(default="", visible_width=15, fixed_size=False)
config.plugins.filecommander.extension = ConfigSelection(default="^.*", choices=[("^.*", _("without")), ("myfilter", _("My Extension")), (records, _("Records")), (movie, _("Movie")), (music, _("Music")), (pictures, _("Pictures"))])
config.plugins.filecommander.change_navbutton = ConfigSelection(default="no", choices=[("no", _("No")), ("always", _("Channel button always changes sides")), ("yes", _("Yes"))])
config.plugins.filecommander.select_across_dirs = ConfigYesNo(default=False)
config.plugins.filecommander.move_selector = ConfigYesNo(default=True)
#config.plugins.filecommander.input_length = ConfigInteger(default=40, limits=(1, 100))
config.plugins.filecommander.diashow = ConfigInteger(default=5000, limits=(1000, 10000))
config.plugins.filecommander.script_messagelen = ConfigSelectionNumber(default=3, stepwidth=1, min=1, max=10, wraparound=True)
config.plugins.filecommander.script_priority_nice = ConfigSelectionNumber(default=0, stepwidth=1, min=0, max=19, wraparound=True)
config.plugins.filecommander.script_priority_ionice = ConfigSelectionNumber(default=0, stepwidth=3, min=0, max=3, wraparound=True)
config.plugins.filecommander.unknown_extension_as_text = ConfigYesNo(default=False)
config.plugins.filecommander.sortDirs = ConfigSelection(default="0.0", choices=[
				("0.0", _("Name")),
				("0.1", _("Name reverse")),
				("1.0", _("Date")),
				("1.1", _("Date reverse"))])
choicelist = [
				("0.0", _("Name")),
				("0.1", _("Name reverse")),
				("1.0", _("Date")),
				("1.1", _("Date reverse")),
				("2.0", _("Size")),
				("2.1", _("Size reverse"))]
config.plugins.filecommander.sortFiles_left = ConfigSelection(default="1.1", choices=choicelist)
config.plugins.filecommander.sortFiles_right = ConfigSelection(default="1.1", choices=choicelist)
config.plugins.filecommander.firstDirs = ConfigYesNo(default=True)
config.plugins.filecommander.path_left_selected = ConfigYesNo(default=True)
config.plugins.filecommander.lastcursorposition = ConfigInteger(default=0)
config.plugins.filecommander.showTaskCompleted_message = ConfigYesNo(default=True)
config.plugins.filecommander.showScriptCompleted_message = ConfigYesNo(default=True)
config.plugins.filecommander.hashes = ConfigSet(key_actions.hashes.keys(), default=["MD5"])
config.plugins.filecommander.bookmarks = ConfigLocations()
config.plugins.filecommander.fake_entry = NoSave(ConfigNothing())

tmpLeft = '%s,%s' % (config.plugins.filecommander.sortDirs.value, config.plugins.filecommander.sortFiles_left.value)
tmpRight = '%s,%s' % (config.plugins.filecommander.sortDirs.value, config.plugins.filecommander.sortFiles_right.value)
config.plugins.filecommander.sortingLeft_tmp = NoSave(ConfigText(default=tmpLeft))
config.plugins.filecommander.sortingRight_tmp = NoSave(ConfigText(default=tmpRight))
config.plugins.filecommander.path_left_tmp = NoSave(ConfigText(default=config.plugins.filecommander.path_left.value))
config.plugins.filecommander.path_right_tmp = NoSave(ConfigText(default=config.plugins.filecommander.path_right.value))

config.plugins.filecommander.dir_size = ConfigYesNo(default=False)
config.plugins.filecommander.dir_sizewalk = NoSave(ConfigYesNo(default=False))
config.plugins.filecommander.sensitive = ConfigYesNo(default=False)
config.plugins.filecommander.search = ConfigSelection(default="begin", choices=[("begin", _("start title")), ("end", _("end title")), ("in", _("contains in title"))])
choicelist = []
for i in range(1, 11, 1):
	choicelist.append(("%d" % i))
choicelist.append(("15", "15"))
choicelist.append(("20", "20"))
config.plugins.filecommander.length = ConfigSelection(default="3", choices=[("0", _("No"))] + choicelist + [("255", _("All"))])
config.plugins.filecommander.endlength = ConfigSelection(default="4", choices=[("0", _("No"))] + choicelist + [("255", _("All"))])
config.plugins.filecommander.toggle_stop_pause = ConfigYesNo(default=False)
codepages = []
for i in range(1250, 1259, 1):
	codepages.append(("%s" % i, "CP%s" % i))
config.plugins.filecommander.cp = ConfigSelection(default="1250", choices=codepages)
config.plugins.filecommander.filename_header = ConfigYesNo(default=True)

cfg = config.plugins.filecommander

# ####################
# ## Config Screen ###
# ####################


class Setup(ConfigListScreen, Screen):
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skinName = ["FileCommanderSetup", "Setup"]

		self["help"] = Label(_("Select your personal settings:"))
		self["description"] = Label()
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["VKeyIcon"] = Boolean(False)

		self.list = []
		self.list.append(getConfigListEntry(_("Add plugin to main menu"), cfg.add_mainmenu_entry, _("Make FileCommander accessible from the main menu.")))
		self.list.append(getConfigListEntry(_("Add plugin to Extensions menu"), cfg.add_extensionmenu_entry, _("Make FileCommander accessible from the Extensions menu.")))
		self.list.append(getConfigListEntry(_("Save left folder on exit"), cfg.savedir_left, _("Save the left directory list location on exit.")))
		self.list.append(getConfigListEntry(_("Save right folder on exit"), cfg.savedir_right, _("Save the right folder list location on exit.")))
		self.list.append(getConfigListEntry(_("Save cursor position"), cfg.cursorposition, _("Save cursor position in active panel.")))
		self.list.append(getConfigListEntry(_("Show directories first"), cfg.firstDirs, _("Show directories on first or last positions in panel (to apply the changes FileCommander must be restarted).")))
		self.list.append(getConfigListEntry(_("Filenames in header"), cfg.filename_header, _("Display filenames in header. It is useful for filenames that are too long.")))
		self.list.append(getConfigListEntry(_("Show Task's completed message"), cfg.showTaskCompleted_message, _("Show message if FileCommander is not running and all Task's are completed.")))
		self.list.append(getConfigListEntry(_("Show Script completed message"), cfg.showScriptCompleted_message, _("Show message if a background script ends successfully. Has 'stout', then this is displayed as additional info.")))
		self.list.append(getConfigListEntry(_("Number of lines in script messages"), cfg.script_messagelen, _("Set for 'stout' and 'sterr' the number of lines in script info or script error messages.")))
		self.list.append(getConfigListEntry(_("Show unknown extension as text"), cfg.unknown_extension_as_text, _("Show unknown file extensions with 'Addon File-Viewer'.")))
		self.list.append(getConfigListEntry(_("Edit position is the line end"), cfg.editposition_lineend, _("If editing a file, you can set the cursor start position at end or begin of the line.")))
		self.list.append(getConfigListEntry(_("Change buttons for list navigation"), cfg.change_navbutton, _("Swap buttons right/left with channel +/- or the channel button changed always the side.")))
		self.list.append(getConfigListEntry(_("Move selector to next item"), cfg.move_selector, _("In multi-selection mode moves cursor to next item after marking.") + "\n\n" + _("Note - for switching this option in multi-selection mode you can use key '6' too.")))
		self.list.append(getConfigListEntry(_("Directories to group selections"), cfg.select_across_dirs, _("'Group selection' and 'Invert selection' in Multiselection mode can work with directories too.")))
		self.list.append(getConfigListEntry(_("Default file sorting left"), cfg.sortFiles_left, _("Default sorting method for files in left panel.")))
		self.list.append(getConfigListEntry(_("Default file sorting right"), cfg.sortFiles_right, _("Default sorting method for files in right panel.")))
		self.list.append(getConfigListEntry(_("Default directory sorting"), cfg.sortDirs, _("Default sorting method for directories in both panels (to apply the changes FileCommander must be restarted).")))
		self.list.append(getConfigListEntry(_("Default folder"), cfg.path_default, _("Press 'OK' and select from list or bookmarks directory for 'Go to default directory'. Eventually you can manage plugin's bookmarks here too.")))
		self.list.append(getConfigListEntry(_("All movie extensions"), cfg.all_movie_ext, _("All files in the directory with the same name as the selected movie will be copied or moved too.")))
		self.list.append(getConfigListEntry(_("My extension"), cfg.my_extension, _("Filter extension for 'My Extension' setting of 'Filter extension'. Use the extension name without a '.'.")))
		self.list.append(getConfigListEntry(_("Filter extension, (*) appears in title"), cfg.extension, _("Filter visible file classes by extension.")))
		self.list.append(getConfigListEntry(_("Count directory content size"), cfg.dir_size, _("Calculates the size of directory contents for 'Info'.") + "\n\n" + _("Note - independently of setting this item, there in list you can turn on/turn off counting and displaying directory content size with key '1'.")))
		self.list.append(getConfigListEntry(_("Swap buttons for reverse file sorting"), cfg.toggle_stop_pause, _("Useful if remote controller having 'pause' button left to 'stop' (to apply the changes FileCommander must be restarted).")))
		self.list.append(getConfigListEntry(_("CPU priority for script execution"), cfg.script_priority_nice, _("Default CPU priority (nice) for executed scripts. This can reduce the load so that scripts do not interfere with the rest of the system. (higher values = lower priority)")))
		self.list.append(getConfigListEntry(_("I/O priority for script execution"), cfg.script_priority_ionice, _("Default I/O priority (ionice) for executed scripts. This can reduce the load so that scripts do not interfere with the rest of the system. (higher values = lower priority)")))
		self.list.append(getConfigListEntry(_("File checksums/hashes"), cfg.hashes, _("Calculates file checksums.")))
		self.list.append(getConfigListEntry(_("Time for Slideshow"), cfg.diashow, _("Time between slides in image viewer slideshow.")))
		self.list.append(getConfigListEntry(_("Original subtitles codepage"), cfg.cp, _("Original subtitles codepage for conversion to UTF-8.")))

		ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changedEntry)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["Actions"] = ActionMap(["ColorActions", "SetupActions"],
		{
			"green": self.save,
			"red": self.cancel,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.ok,
		}, -2)
		self.onLayoutFinish.append(self.onLayout)

	def onLayout(self):
		self.setTitle("%s %s - %s" % (pname, pvers, _("Settings")))

	def getCurrentEntry(self):
		x = self["config"].getCurrent()
		if x:
			text = x[2] if len(x) == 3 else ""
			self["description"].setText(text)

	def ok(self):
		if self["config"].getCurrent()[1] is cfg.path_default:
			self.session.openWithCallback(self.pathSelected, LocationBox, text=_("Default Folder"), currDir=cfg.path_default.getValue(), bookmarks=cfg.bookmarks)

	def pathSelected(self, res):
		if res is not None:
			cfg.path_default.value = res

	def save(self):
		print "[FileCommander]: Settings saved"
		for x in self["config"].list:
			x[1].save()
		self.refreshPlugins()
		self.close(True)

	def cancel(self):
		print "[FileCommander]: Settings canceled"
		for x in self["config"].list:
			x[1].cancel()
		self.close(False)

	def refreshPlugins(self):
		from Components.PluginComponent import plugins
		from Tools.Directories import resolveFilename, SCOPE_PLUGINS
		plugins.clearPluginList()
		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))


def formatSortingTyp(sortDirs, sortFiles):
	sortDirs, reverseDirs = [int(x) for x in sortDirs.split('.')]
	sortFiles, reverseFiles = [int(x) for x in sortFiles.split('.')]
	sD = (_('n'), _('d'), _('s'))[sortDirs] #name, date, size
	sF = (_('n'), _('d'), _('s'))[sortFiles]
	rD = ('+', '-')[reverseDirs] #normal, reverse
	rF = ('+', '-')[reverseFiles]
	return _('[D]%s%s[F]%s%s') % (sD, rD, sF, rF)


def cutLargePath(path, label):
	def getStringSize(string, label):
		label.instance.setNoWrap(1)
		label.setText("%s" % string)
		return label.instance.calculateSize().width()
	if path != "/":
		path = path.rstrip('/')
	w = label.instance.size().width()	# label width
	path_w = getStringSize(path, label)	# text width
	if path_w > w:
		path = path.split('/')
		for i, idx in enumerate(path):
			x = "/" + (i - 1) * ".../" + '/'.join((path[i:]))
			if getStringSize(x, label) <= w:
				return x
		prefix = "%s..." % ((i - 1) * ".../")
		prefix_w = getStringSize(prefix, label)
		lastpath = path[len(path) - 1]
		for j, idx in enumerate(lastpath):
			lcutstr = lastpath[j:]
			lcutstr_w = getStringSize(lcutstr, label)
			if lcutstr_w < (w - prefix_w):
				return '%s%s' % (prefix, lcutstr)
	return path


def freeDiskSpace(path):
	try:
		fs = os.statvfs(path)
		free = fs.f_bfree * fs.f_bsize
		if free < 10000000:
			free = _("%d kB") % (free >> 10)
		elif free < 10000000000:
			free = _("%d MB") % (free >> 20)
		else:
			free = _("%d GB") % (free >> 30)
		return "%s" % free
	except:
		return "-?-"


###################
# ## Main Screen ###
###################

glob_running = False


class FileCommanderScreen(Screen, HelpableScreen, key_actions):
	if FULLHD:
		skin = """
		<screen position="40,80" size="1840,920" title="" >
			<widget name="list_left_head1" position="10,5" size="890,28" itemHeight="28" font="Regular;24" foregroundColor="#00cccc40"/>
			<widget name="list_left_filename" position="10,31" size="890,21" font="Regular;18" noWrap="1" foregroundColor="grey" backgroundColor="secondBG" transparent="1" zPosition="1"/>
			<widget name="list_left_select" position="10,50" size="890,30" zPosition="1" font="Regular;24" transparent="1" foregroundColor="#0000cc60"/>
			<widget source="list_left_head2" render="Listbox" position="10,50" size="890,30" foregroundColor="#00cccc40" selectionDisabled="1" transparent="1">
				<convert type="TemplatedMultiContent">
					{"template": [
						MultiContentEntryText(pos = (30, 0), size = (173, 30), font = 0, flags = RT_HALIGN_LEFT, text = 1), # index 1 is a symbolic mode
						MultiContentEntryText(pos = (250, 0), size = (135, 30), font = 0, flags = RT_HALIGN_RIGHT, text = 11), # index 11 is the scaled size
						MultiContentEntryText(pos = (500, 0), size = (390, 30), font = 0, flags = RT_HALIGN_LEFT, text = 15), # index 15 is the modification time
						],
						"fonts": [gFont("Regular", 24)],
						"itemHeight": 30,
						"selectionEnabled": False
					}
				</convert>
			</widget>
			<widget name="list_right_head1" position="900,5" size="890,28" itemHeight="28" font="Regular;24" foregroundColor="#00cccc40"/>
			<widget name="list_right_filename" position="900,31" size="890,21" font="Regular;18" noWrap="1" foregroundColor="grey" backgroundColor="secondBG" transparent="1" zPosition="1"/>
			<widget name="list_right_select" position="900,50" size="890,30" zPosition="1" font="Regular;24" transparent="1" foregroundColor="#0000cc60"/>
			<widget source="list_right_head2" render="Listbox" position="900,50" size="890,30" foregroundColor="#00cccc40" selectionDisabled="1" transparent="1">
				<convert type="TemplatedMultiContent">
					{"template": [
						MultiContentEntryText(pos = (30, 0), size = (173, 30), font = 0, flags = RT_HALIGN_LEFT, text = 1), # index 1 is a symbolic mode
						MultiContentEntryText(pos = (250, 0), size = (135, 30), font = 0, flags = RT_HALIGN_RIGHT, text = 11), # index 11 is the scaled size
						MultiContentEntryText(pos = (500, 0), size = (390, 30), font = 0, flags = RT_HALIGN_LEFT, text = 15), # index 15 is the modification time
						],
						"fonts": [gFont("Regular", 24)],
						"itemHeight": 30,
						"selectionEnabled": False
					}
				</convert>
			</widget>
			<widget name="list_left" position="10,80" size="890,765" itemHeight="45" scrollbarMode="showOnDemand"/>
			<widget name="list_right" position="900,80" size="890,765" itemHeight="45" scrollbarMode="showOnDemand"/>
			<widget name="list_left_free" position="30,845" size="200,25" font="Regular;22"/><!-- for FileCommanderScreenFileSelect, do not remove it -->
			<widget name="list_right_free" position="920,845" size="200,25" font="Regular;22"/><!-- for FileCommanderScreenFileSelect, do not remove it -->
			<widget name="sort_left" position="10,845" size="855,26" halign="center" font="Regular;23" foregroundColor="#00cccc40"/>
			<widget name="sort_right" position="900,845" size="855,26" halign="center" font="Regular;23" foregroundColor="#00cccc40"/>
			<widget source="key_red" render="Label" position="150,880" size="390,38" transparent="1" font="Regular;30"/>
			<widget source="key_green" render="Label" position="593,880" size="390,38"  transparent="1" font="Regular;30"/>
			<widget source="key_yellow" render="Label" position="1035,880" size="390,38" transparent="1" font="Regular;30"/>
			<widget source="key_blue" render="Label" position="1488,880" size="390,38" transparent="1" font="Regular;30"/>
			<ePixmap position="105,880" size="390,33" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FileCommander/pic/button_red.png" transparent="1" alphatest="on"/>
			<ePixmap position="548,880" size="390,33" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FileCommander/pic/button_green.png" transparent="1" alphatest="on"/>
			<ePixmap position="990,880" size="390,33" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FileCommander/pic/button_yellow.png" transparent="1" alphatest="on"/>
			<ePixmap position="1433,880" size="390,33" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FileCommander/pic/button_blue.png" transparent="1" alphatest="on"/>
		</screen>"""
	else:
		skin = """
		<screen position="40,80" size="1200,600" title="" >
			<widget name="list_left_head1" position="10,5" size="570,21" font="Regular;18" foregroundColor="#00cccc00"/>
			<widget name="list_left_filename" position="10,26" size="570,16" font="Regular;14" noWrap="1" foregroundColor="grey" backgroundColor="secondBG" transparent="1" zPosition="1"/>
			<widget name="list_left_select" position="10,42" size="570,20" zPosition="1" font="Regular;18" transparent="1" foregroundColor="#0000cc60"/>
			<widget source="list_left_head2" render="Listbox" position="10,42" size="570,20" foregroundColor="#00cccc00" selectionDisabled="1" transparent="1">
				<convert type="TemplatedMultiContent">
					{"template": [
						MultiContentEntryText(pos = (0, 0), size = (115, 20), font = 0, flags = RT_HALIGN_LEFT, text = 1), # index 1 is a symbolic mode
						MultiContentEntryText(pos = (130, 0), size = (90, 20), font = 0, flags = RT_HALIGN_RIGHT, text = 11), # index 11 is the scaled size
						MultiContentEntryText(pos = (235, 0), size = (260, 20), font = 0, flags = RT_HALIGN_LEFT, text = 15), # index 15 is the modification time
						],
						"fonts": [gFont("Regular", 18)],
						"itemHeight": 20,
						"selectionEnabled": False
					}
				</convert>
			</widget>
			<widget name="list_right_head1" position="610,5" size="570,21" font="Regular;18" foregroundColor="#00cccc00"/>
			<widget name="list_right_filename" position="610,26" size="570,16" font="Regular;14" noWrap="1" foregroundColor="grey" backgroundColor="secondBG" transparent="1" zPosition="1"/>
			<widget name="list_right_select" position="610,42" size="570,20" zPosition="1" font="Regular;18" transparent="1" foregroundColor="#0000cc60"/>
			<widget source="list_right_head2" render="Listbox" position="610,42" size="570,20" foregroundColor="#00cccc00" selectionDisabled="1" transparent="1">
				<convert type="TemplatedMultiContent">
					{"template": [
						MultiContentEntryText(pos = (0, 0), size = (115, 20), font = 0, flags = RT_HALIGN_LEFT, text = 1), # index 1 is a symbolic mode
						MultiContentEntryText(pos = (130, 0), size = (90, 20), font = 0, flags = RT_HALIGN_RIGHT, text = 11), # index 11 is the scaled size
						MultiContentEntryText(pos = (235, 0), size = (260, 20), font = 0, flags = RT_HALIGN_LEFT, text = 15), # index 15 is the modification time
						],
						"fonts": [gFont("Regular", 18)],
						"itemHeight": 20,
						"selectionEnabled": False
					}
				</convert>
			</widget>
			<widget name="list_left" position="10,70" size="570,466" itemHeight="31" scrollbarMode="showOnDemand"/>
			<widget name="list_right" position="610,70" size="570,466" itemHeight="31" scrollbarMode="showOnDemand"/>
			<widget name="list_left_free" position="10,536" size="100,17" font="Regular;15"/><!-- for FileCommanderScreenFileSelect, do not remove it -->
			<widget name="list_right_free" position="610,536" size="100,17" font="Regular;15"/><!-- for FileCommanderScreenFileSelect, do not remove it -->
			<widget name="sort_left" position="10,536" size="570,17" halign="center" font="Regular;15" foregroundColor="#00cccc00"/>
			<widget name="sort_right" position="610,536" size="570,17" halign="center" font="Regular;15" foregroundColor="#00cccc00"/>
			<widget source="key_red" render="Label" position="100,570" size="260,25" transparent="1" font="Regular;20"/>
			<widget source="key_green" render="Label" position="395,570" size="260,25"  transparent="1" font="Regular;20"/>
			<widget source="key_yellow" render="Label" position="690,570" size="260,25" transparent="1" font="Regular;20"/>
			<widget source="key_blue" render="Label" position="985,570" size="260,25" transparent="1" font="Regular;20"/>
			<ePixmap position="70,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FileCommander/pic/button_red.png" transparent="1" alphatest="on"/>
			<ePixmap position="365,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FileCommander/pic/button_green.png" transparent="1" alphatest="on"/>
			<ePixmap position="660,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FileCommander/pic/button_yellow.png" transparent="1" alphatest="on"/>
			<ePixmap position="955,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FileCommander/pic/button_blue.png" transparent="1" alphatest="on"/>
		</screen>"""

	def __init__(self, session, path_left=None):
		# path_left == "" means device list, whereas path_left == None means saved or default value

		path_left = cfg.path_left.value if os.path.isdir(cfg.path_left.value) else None
		path_right = cfg.path_right.value if os.path.isdir(cfg.path_right.value) else None

		if path_left and os.path.isdir(path_left) and path_left[-1] != "/":
			path_left += "/"

		if path_right and os.path.isdir(path_right) and path_right[-1] != "/":
			path_right += "/"

		if path_left == "":
			path_left = None
		if path_right == "":
			path_right = None

		self.session = session
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		# set filter
		filter = self.fileFilter()

		# disable actions
		self.disableActions_Timer = eTimer()

		self.jobs = 0
		self.jobs_old = 0

		self.updateDirs = set()
		self.containers = []

		# set current folder
		self["list_left_head1"] = Label(path_left)
		self["list_left_head2"] = List()
		self["list_left_filename"] = Label()
		self["list_left_free"] = Label()

		self["list_right_head1"] = Label(path_right)
		self["list_right_head2"] = List()
		self["list_right_filename"] = Label()
		self["list_right_free"] = Label()

		# set sorting
		sortDirs = cfg.sortDirs.value
		sortFilesLeft = cfg.sortFiles_left.value
		sortFilesRight = cfg.sortFiles_right.value
		firstDirs = cfg.firstDirs.value

		self["list_left"] = FileList(path_left, matchingPattern=filter, sortDirs=sortDirs, sortFiles=sortFilesLeft, firstDirs=firstDirs)
		self["list_right"] = FileList(path_right, matchingPattern=filter, sortDirs=sortDirs, sortFiles=sortFilesRight, firstDirs=firstDirs)

		sortLeft = formatSortingTyp(sortDirs, sortFilesLeft)
		sortRight = formatSortingTyp(sortDirs, sortFilesRight)
		self["sort_left"] = Label(sortLeft)
		self["sort_right"] = Label(sortRight)

		self["key_red"] = StaticText(_("Delete"))
		self["key_green"] = StaticText(_("Move"))
		self["key_yellow"] = StaticText(_("Copy"))
		self["key_blue"] = StaticText(_("Rename"))
		self["VKeyIcon"] = Boolean(False)

		if cfg.toggle_stop_pause.value:
			file_left_sort = (self.goYellowLong, _("Reverse right file sorting"))
			file_right_sort = (self.goGreenLong, _("Reverse left file sorting"))
		else:
			file_left_sort = (self.goGreenLong, _("Reverse left file sorting"))
			file_right_sort = (self.goYellowLong, _("Reverse right file sorting"))

		self["actions"] = HelpableActionMap(self, ["ChannelSelectBaseActions", "WizardActions", "NumberActions", "ColorActions", "InfobarActions", "EPGSelectActions", "MediaPlayerActions", "MediaPlayerSeekActions"], {
			"ok": (self.ok, _("Play/view/edit/install/extract/run file or enter directory")),
			"back": (self.exit, _("Leave File Commander")),
			"menu": (self.selectAction, _("Open settings/actions menu")),
			"nextMarker": (self.listRight, _("Activate right-hand file list as source")),
			"prevMarker": (self.listLeft, _("Activate left-hand file list as source")),
			"nextBouquet": (self.listRightB, _("Activate right-hand file list as source")),
			"prevBouquet": (self.listLeftB, _("Activate left-hand file list as source")),
			"0": (self.doRefresh, _("Refresh screen")),
			"1": (self.dirSizeWalk, _("Counting directory content size while walking (on/off)")),
			"2": (self.goBlue, _("Rename file/directory")),
			"3": (self.file_viewer, _("View or edit file (if size < 1MB)")),
			"7": (self.gomakeDir, _("Create directory")),
			"8": (self.openTasklist, _("Show task list")),
#			"9": self.downloadSubtitles,  # Unimplemented
			"red": (self.goRed, _("Delete file or directory (and all its contents)")),
			"green": (self.goGreen, _("Move file/directory to target directory")),
			"yellow": (self.goYellow, _("Copy file/directory to target directory")),
			"blue": (self.goBlue, _("Rename file/directory")),
			"info": (self.gofileStatInfo, _("File/Directory Status Information")),
			"keyRecord": (self.listSelect, _("Enter multi-file selection mode")),
			"showMovies": (self.listSelect, _("Enter multi-file selection mode")),
			"up": (self.goUp, _("Move up list")),
			"down": (self.goDown, _("Move down list")),
			"left": (self.goLeftB, _("Page up list")),
			"right": (self.goRightB, _("Page down list")),
			"seekBack": (self.goRedLong, _("Sorting left files by name, date or size")),
			"pause": file_right_sort,
			"stop": file_left_sort,
			"seekFwd": (self.goBlueLong, _("Sorting right files by name, date or size")),
		}, -1)

		global glob_running
		glob_running = True

		self.walkdirflag = ''
		self.onLayoutFinish.append(self.listLeftStart if cfg.path_left_selected.value else self.listRightStart)

		self.checkJobs_Timer = eTimer()
		self.checkJobs_Timer.callback.append(self.checkJobs_TimerCB)
		#self.onLayoutFinish.append(self.onLayout)
		self.onLayoutFinish.append(self.checkJobs_TimerCB)

	def setWalkdir(self):
		cfg.dir_sizewalk.value = not cfg.dir_sizewalk.value
		self.walkdirflag = ' *' if cfg.dir_sizewalk.value else ''

	def onLayout(self):
		if self.jobs_old:
			self.checkJobs_Timer.startLongTimer(5)

		if cfg.extension.value == "^.*":
			filtered = ""
		else:
			filtered = "(*)"

		if self.jobs or self.jobs_old:
			jobs = ngettext("(%d job)", "(%d jobs)", (self.jobs + self.jobs_old)) % (self.jobs + self.jobs_old)
		else:
			jobs = ""
		self.setTitle(pname + " " + filtered + " " + jobs)

	def checkJobs_TimerCB(self):
		self.jobs_old = 0
		for job in job_manager.getPendingJobs():
			if (job.name.startswith(_('copy file')) or job.name.startswith(_('copy folder')) or job.name.startswith(_('move file')) or job.name.startswith(_('move folder'))or job.name.startswith(_('Run script'))):
				self.jobs_old += 1
		self.jobs_old -= self.jobs
		self.onLayout()

	def viewable_file(self):
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		if (filename is None) or (sourceDir is None):
			return None
		longname = sourceDir + filename
		try:
			xfile = os.stat(longname)
			if (xfile.st_size < 1000000):
				return longname
		except:
			pass
		return None

	def file_viewer(self):
		if self.disableActions_Timer.isActive():
			return
		longname = self.viewable_file()
		if longname is not None:
			self.session.open(vEditor, longname)
			self.onFileActionCB(True)

	def exit(self):
		if self.disableActions_Timer.isActive():
			return
		if self["list_left"].getCurrentDirectory() and cfg.savedir_left.value:
			cfg.path_left.value = self["list_left"].getCurrentDirectory()
			cfg.path_left.save()

		if self["list_right"].getCurrentDirectory() and cfg.savedir_right.value:
			cfg.path_right.value = self["list_right"].getCurrentDirectory()
			cfg.path_right.save()

		cfg.path_left_selected.value = True if self.SOURCELIST == self["list_left"] else False
		cfg.path_left_selected.save()

		if cfg.cursorposition.value:
			cfg.lastcursorposition.value = self.SOURCELIST.getSelectionID()
			cfg.lastcursorposition.save()

		global glob_running
		glob_running = False

		self.close(self.session, True)

	def ok(self):
		if self.disableActions_Timer.isActive():
			return
		if self.SOURCELIST.canDescent():  # isDir
			self.SOURCELIST.descent()
			self.updateHead()
		else:
			self.onFileAction(self.SOURCELIST, self.TARGETLIST)
			# self.updateHead()
			self.doRefresh()

	def selectAction(self):
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		isFile = True if filename and sourceDir and sourceDir not in filename else False

		menu = []
		menu.append((_("Rename file/directory"), self.goBlue))
		keys = ["2"]
		if isFile:
			menu.append((_("View or edit file (if size < 1MB)"), self.file_viewer))		#3
			keys += ["3"]
		menu.append((_("Copy file/directory to target directory"), self.goYellow))		#5
		menu.append((_("Move file/directory to target directory"), self.goGreen))		#6
		menu.append((_("Create directory"), self.gomakeDir))					#7
		menu.append((_("Delete file or directory (and all its contents)"), self.goRed))		#8
		menu.append((_("File/Directory Status Information"), self.gofileStatInfo))		#info
		menu.append((_("Enter multi-file selection mode"), self.listSelect))			#green
		menu.append((_("Refresh screen"), self.doRefresh))					#0
		menu.append((_("Show task list"), self.openTasklist))					#red
		keys += ["5", "6", "7", "8", "info", "green", "0", "red"]
		if isFile:
			menu.append((_("Calculate file checksums"), self.run_hashes))
			keys += [""]
		if isFile:
			menu.append((_("Change execute permissions (755/644)"), self.call_change_mode))
			keys += [""]
		if isFile and filename[-4:] in (".srt", ".sub"):
			menu.append((_("Convert subtitles from '%s' to UTF-8") % cfg.cp(cfg.cp.value)[1], self.convertSubtitles))
			keys += [""]
		menu.append((_("Edit new file"), self.gomakeFile))					#
		menu.append((_("Create user-named symbolic link"), self.gomakeSym))			#
		menu.append((_("Go to parent directory"), self.goParentfolder))				#
		menu.append((_("Go to default directory"), self.goDefaultfolder))			#yellow
		menu.append((self.help_run_file(), self.run_file))					#
		menu.append((self.help_run_ffprobe(), self.run_ffprobe))				#
		menu.append((_("Settings..."), boundFunction(self.session.open, Setup)))		#menu
		menu.append((_("Go to bookmarked folder"), self.goBookmarkedfolder))			#blue
		keys += ["", "", "", "yellow", "", "", "menu", "blue"]

		item = self.help_uninstall_file()
		if item:
			menu.append((item, self.uninstall_file))
			keys += ["bullet"]
		item = self.help_uninstall_ffprobe()
		if item:
			menu.append((item, self.uninstall_ffprobe))
			keys += ["bullet"]

		dirname = self.SOURCELIST.getFilename()
		if dirname and dirname.endswith("/"):
			menu.append((dirname in cfg.bookmarks.value and _("Remove selected folder from bookmarks") or _("Add selected folder to bookmarks"), boundFunction(self.goBookmark, False)))
			keys += ["bullet"]
		dirname = self.SOURCELIST.getCurrentDirectory()
		if dirname:
			menu.append((dirname in cfg.bookmarks.value and _("Remove current folder from bookmarks") or _("Add current folder to bookmarks"), boundFunction(self.goBookmark, True)))
			keys += ["bullet"]

		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_("Select operation:"), list=menu, keys=["dummy" if key == "" else key for key in keys], skin_name="ChoiceBox")

	def menuCallback(self, choice):
		if choice is None:
			return
		if choice[1]:
			choice[1]()

	def goMenu(self):
		self.oldFilterSettings = self.filterSettings()
		# commented out
		# self.session.openWithCallback(self.goRestart, FileCommanderConfigScreen)
		self.session.openWithCallback(self.goRestart, Setup)

	def goBookmark(self, current):
		dirname = current and self.SOURCELIST.getCurrentDirectory() or self.SOURCELIST.getFilename()
		bookmarks = cfg.bookmarks.value
		if dirname in bookmarks:
			bookmarks.remove(dirname)
		else:
			bookmarks.insert(0, dirname)
			# commented out
			#order = config.misc.pluginlist.fc_bookmarks_order.value
			#if dirname not in order:
			#	order = dirname + "," + order
			#	config.misc.pluginlist.fc_bookmarks_order.value = order
			#	config.misc.pluginlist.fc_bookmarks_order.save()
		cfg.bookmarks.value = bookmarks
		cfg.bookmarks.save()

	def goDefaultfolder(self):
		if self.disableActions_Timer.isActive():
			return
		if cfg.path_default.value:
			self.SOURCELIST.changeDir(cfg.path_default.value)
			self.updateHead()

	def goBookmarkedfolder(self):
		if self.disableActions_Timer.isActive():
			return
		bookmarks = cfg.bookmarks.value
		if not bookmarks:
			if cfg.path_default.value:
				bookmarks.append(cfg.path_default.value)
			bookmarks.append('/home/root/')
			bookmarks.append(defaultMoviePath())
			cfg.bookmarks.value = bookmarks
			cfg.bookmarks.save()
		bookmarks = [(x, x) for x in bookmarks]
		bookmarks.append((_("Storage devices"), None))
		# commented out
		#self.session.openWithCallback(self.locationCB, ChoiceBox, title=_("Select a path"), list=bookmarks, reorderConfig="fc_bookmarks_order")
		self.session.openWithCallback(self.locationCB, ChoiceBox, title=_("Select a path"), list=bookmarks)

	def locationCB(self, answer):
		if answer:
			self.SOURCELIST.changeDir(answer[1])
			self.updateHead()

	def goParentfolder(self):
		if self.disableActions_Timer.isActive():
			return
		if self.SOURCELIST.getParentDirectory() != False:
			self.SOURCELIST.changeDir(self.SOURCELIST.getParentDirectory())
			self.updateHead()

	def goRestart(self, *answer):
		if hasattr(self, "oldFilterSettings"):
			if self.oldFilterSettings != self.filterSettings():
				filter = self.fileFilter()
				self["list_left"].matchingPattern = re.compile(filter)
				self["list_right"].matchingPattern = re.compile(filter)
				self.onLayout()
			del self.oldFilterSettings

		sortDirs = cfg.sortDirs.value
		sortFilesLeft = cfg.sortFiles_left.value
		sortFilesRight = cfg.sortFiles_right.value

		self["list_left"].setSortBy(sortDirs, True)
		self["list_right"].setSortBy(sortDirs, True)
		self["list_left"].setSortBy(sortFilesLeft)
		self["list_right"].setSortBy(sortFilesRight)

		self.doRefresh()

	def goLeftB(self):
		if self.disableActions_Timer.isActive():
			return
		if cfg.change_navbutton.value == 'yes':
			self.listLeft()
		else:
			self.goLeft()

	def goRightB(self):
		if self.disableActions_Timer.isActive():
			return
		if cfg.change_navbutton.value == 'yes':
			self.listRight()
		else:
			self.goRight()

	def goLeft(self):
		self.SOURCELIST.pageUp()
		self.updateHead()

	def goRight(self):
		self.SOURCELIST.pageDown()
		self.updateHead()

	def goUp(self):
		if self.disableActions_Timer.isActive():
			return
		self.SOURCELIST.up()
		self.updateHead()

	def goDown(self):
		if self.disableActions_Timer.isActive():
			return
		self.SOURCELIST.down()
		self.updateHead()

	def dirSizeWalk(self):
		self.setWalkdir()
		self.updateHead()

# ## Multiselect ###
	def listSelect(self):
		if not self.SOURCELIST.getCurrentDirectory() or self.disableActions_Timer.isActive():
			return
		selectedid = self.SOURCELIST.getSelectionID()
		cfg.path_left_tmp.value = self["list_left"].getCurrentDirectory() or ""
		cfg.path_right_tmp.value = self["list_right"].getCurrentDirectory() or ""
		cfg.sortingLeft_tmp.value = self["list_left"].getSortBy()
		cfg.sortingRight_tmp.value = self["list_right"].getSortBy()
		if self.SOURCELIST == self["list_left"]:
			leftactive = True
		else:
			leftactive = False

		self.session.openWithCallback(self.doRefreshDir, FileCommanderScreenFileSelect, self, leftactive, selectedid)
		self.updateHead()

	def openTasklist(self):
		if self.disableActions_Timer.isActive():
			return
		self.tasklist = []
		for job in job_manager.getPendingJobs():
			#self.tasklist.append((job, job.name, job.getStatustext(), int(100 * job.progress / float(job.end)), str(100 * job.progress / float(job.end)) + "%"))
			progress = job.getProgress()
			self.tasklist.append((job, job.name, job.getStatustext(), progress, str(progress) + " %"))
		self.session.open(TaskListScreen, self.tasklist)

	def addJob(self, job, updateDirs):
		self.jobs += 1
		self.onLayout()
		self.updateDirs.update(updateDirs)
		if isinstance(job, list):
			container = eConsoleAppContainer()
			container.appClosed.append(self.finishedCB)
			self.containers.append(container)
			retval = container.execute("rm", "rm", "-rf", *job)
			if retval:
				self.finishedCB(retval)
		else:
			job_manager.AddJob(job, onSuccess=self.finishedCB)

	def failCB(self, job, task, problems):
		task.setProgress(100)
		# commented out
		# from Screens.Standby import inStandby
		message = job.name + "\n" + _("Error") + ': %s' % (problems[0].getErrorMessage(task))
		messageboxtyp = MessageBox.TYPE_ERROR
		timeout = 0
		# commented out
		#if InfoBar.instance and not inStandby:
		#	InfoBar.instance.openInfoBarMessage(message, messageboxtyp, timeout)
		#else:
		Notifications.AddNotification(MessageBox, message, type=messageboxtyp, timeout=timeout, simple=True)
		if hasattr(self, "jobs"):
			self.finishedCB(None)
		return False

	def finishedCB(self, arg):
		if hasattr(self, "jobs"):
			self.jobs -= 1
			self.onLayout()
			if (self["list_left"].getCurrentDirectory() in self.updateDirs or
				self["list_right"].getCurrentDirectory() in self.updateDirs):
				self.doRefresh()
			if not self.jobs:
				self.updateDirs.clear()
				del self.containers[:]
		if not glob_running and cfg.showTaskCompleted_message.value:
			for job in job_manager.getPendingJobs():
				if (job.name.startswith(_('copy file')) or job.name.startswith(_('copy folder')) or job.name.startswith(_('move file')) or job.name.startswith(_('move folder'))or job.name.startswith(_('Run script'))):
					return
			# commented out
			# from Screens.Standby import inStandby
			message = _("File Commander - all Task's completed!")
			messageboxtyp = MessageBox.TYPE_INFO
			timeout = 30
			# commented out
			#if InfoBar.instance and not inStandby:
			#	InfoBar.instance.openInfoBarMessage(message, messageboxtyp, timeout)
			#else:
			Notifications.AddNotification(MessageBox, message, type=messageboxtyp, timeout=timeout, simple=True)

	def setSort(self, list, setDirs=False):
		sortDirs, sortFiles = list.getSortBy().split(',')
		if setDirs:
			sort, reverse = [int(x) for x in sortDirs.split('.')]
			sort += 1
			if sort > 1:
				sort = 0
		else:
			sort, reverse = [int(x) for x in sortFiles.split('.')]
			sort += 1
			if sort > 2:
				sort = 0
		return '%d.%d' % (sort, reverse)

	def setReverse(self, list, setDirs=False):
		sortDirs, sortFiles = list.getSortBy().split(',')
		if setDirs:
			sort, reverse = [int(x) for x in sortDirs.split('.')]
		else:
			sort, reverse = [int(x) for x in sortFiles.split('.')]
		reverse += 1
		if reverse > 1:
			reverse = 0
		return '%d.%d' % (sort, reverse)

# ## sorting files left ###
	def goRedLong(self):
		if self.disableActions_Timer.isActive():
			return
		self["list_left"].setSortBy(self.setSort(self["list_left"]))
		self.doRefresh()

# ## reverse sorting files left ###
	def goGreenLong(self):
		if self.disableActions_Timer.isActive():
			return
		self["list_left"].setSortBy(self.setReverse(self["list_left"]))
		self.doRefresh()

# ## reverse sorting files right ###
	def goYellowLong(self):
		if self.disableActions_Timer.isActive():
			return
		self["list_right"].setSortBy(self.setReverse(self["list_right"]))
		self.doRefresh()

# ## sorting files right ###
	def goBlueLong(self):
		if self.disableActions_Timer.isActive():
			return
		self["list_right"].setSortBy(self.setSort(self["list_right"]))
		self.doRefresh()

# ## convert subtitles
	def convertSubtitles(self):
		if self.disableActions_Timer.isActive():
			return
		filename = self.SOURCELIST.getFilename()
		if (filename):
			sourceDir = self.SOURCELIST.getCurrentDirectory()
			if sourceDir not in filename:
				name = sourceDir + filename
				try:
					os.rename(name, name + ".tmp")
				except Exception as error:
					self.session.open(MessageBox, "%s" % error, MessageBox.TYPE_ERROR, timeout=3)
				else:
					fi = open(name + ".tmp", "rt")
					fo = open(name, "wt")
					try:
						for line in fi:
							fo.write(line.decode(cfg.cp.value).encode('utf-8', 'ignore'))
					except Exception as error:
						self.session.open(MessageBox, "%s" % error, MessageBox.TYPE_ERROR, timeout=3)
						target = name
					else:
						target = name + ".orig"
					fo.close()
					fi.close()
					os.rename(name + ".tmp", target)
				self.doRefresh()

# ## copy ###
	def goYellow(self):
		# commented out
		#if InfoBar.instance and InfoBar.instance.LongButtonPressed or self.disableActions_Timer.isActive():
		#	return
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		targetDir = self.TARGETLIST.getCurrentDirectory()
		if (filename is None) or (sourceDir is None) or (targetDir is None) or not self.SOURCELIST.getSelectionID():
			return
		warntxt = ""
		if sourceDir not in filename:
			if os.path.exists(targetDir + filename):
				warntxt = _(" - file exist! Overwrite")
			copytext = _("Copy file") + warntxt
		else:
			if os.path.exists(targetDir + filename.split('/')[-2]):
				warntxt = _(" - folder exist! Overwrite")
			copytext = _("Copy folder") + warntxt
		self.session.openWithCallback(self.doCopy, MessageBox, copytext + "?\n\n%s\n\n%s\n%s\n%s\n%s" % (filename.rstrip('/').split('/')[-1], _("from dir"), sourceDir, _("to dir"), targetDir), default=True, simple=True)

	def doCopy(self, result=True):
		if result:
			filename = self.SOURCELIST.getFilename()
			sourceDir = self.SOURCELIST.getCurrentDirectory()
			targetDir = self.TARGETLIST.getCurrentDirectory()
			updateDirs = [targetDir]
			dst_file = targetDir
			if dst_file.endswith("/") and dst_file != "/":
				targetDir = dst_file[:-1]
			if sourceDir not in filename:
				self.addJob(FileTransferJob(sourceDir + filename, targetDir, False, True, "%s : %s" % (_("copy file"), sourceDir + filename)), updateDirs)
			else:
				self.addJob(FileTransferJob(filename, targetDir, True, True, "%s : %s" % (_("copy folder"), filename)), updateDirs)

# ## delete ###
	def goRed(self):
		# commented out
		#if  InfoBar.instance and InfoBar.instance.LongButtonPressed or self.disableActions_Timer.isActive():
		#	return
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		if (filename is None) or (sourceDir is None) or not self.SOURCELIST.getSelectionID():
			return
		if sourceDir not in filename:
			deltext = _("Delete file")
		else:
			deltext = _("Delete folder")
		self.session.openWithCallback(self.doDelete, MessageBox, deltext + "?\n\n%s\n\n%s\n%s" % (filename.rstrip('/').split('/')[-1], _("from dir"), sourceDir), type=MessageBox.TYPE_YESNO, default=False, simple=True)

	def doDelete(self, result=False):
		if result:
			filename = self.SOURCELIST.getFilename()
			sourceDir = self.SOURCELIST.getCurrentDirectory()
			if sourceDir is None:
				return
			if sourceDir not in filename:
				os.remove(sourceDir + filename)
				self.doRefresh()
			else:
				self.addJob([filename], [sourceDir])

# ## move ###
	def goGreen(self):
		# commented out
		#if  InfoBar.instance and InfoBar.instance.LongButtonPressed or self.disableActions_Timer.isActive():
		#	return
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		targetDir = self.TARGETLIST.getCurrentDirectory()
		if (filename is None) or (sourceDir is None) or (targetDir is None) or not self.SOURCELIST.getSelectionID():
			return
		warntxt = ""
		if sourceDir not in filename:
			if os.path.exists(targetDir + filename):
				warntxt = _(" - file exist! Overwrite")
			movetext = _("Move file") + warntxt
		else:
			if os.path.exists(targetDir + filename.split('/')[-2]):
				warntxt = _(" - folder exist! Overwrite")
			movetext = _("Move folder") + warntxt
		self.session.openWithCallback(self.doMove, MessageBox, movetext + "?\n\n%s\n\n%s\n%s\n%s\n%s" % (filename.rstrip('/').split('/')[-1], _("from dir"), sourceDir, _("to dir"), targetDir), type=MessageBox.TYPE_YESNO, default=True, simple=True)

	def doMove(self, result=False):
		if result:
			filename = self.SOURCELIST.getFilename()
			sourceDir = self.SOURCELIST.getCurrentDirectory()
			targetDir = self.TARGETLIST.getCurrentDirectory()
			if (filename is None) or (sourceDir is None) or (targetDir is None):
				return
			updateDirs = [sourceDir, targetDir]
			dst_file = targetDir
			if dst_file.endswith("/") and dst_file != "/":
				targetDir = dst_file[:-1]
			if sourceDir not in filename:
				self.addJob(FileTransferJob(sourceDir + filename, targetDir, False, False, "%s : %s" % (_("move file"), sourceDir + filename)), updateDirs)
			else:
				self.addJob(FileTransferJob(filename, targetDir, True, False, "%s : %s" % (_("move folder"), filename)), updateDirs)

# ## rename ###
	def goBlue(self):
		# commented out
		#if  InfoBar.instance and InfoBar.instance.LongButtonPressed or self.disableActions_Timer.isActive():
		#	return
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		if (filename is None) or (sourceDir is None) or not self.SOURCELIST.getSelectionID():
			return
		filename = os.path.basename(os.path.normpath(filename))
		if not filename:
			self.session.open(MessageBox, _("It's not possible to rename the filesystem root."), type=MessageBox.TYPE_ERROR, simple=True)
			return
		fname = _("Please enter the new file name")
		if sourceDir in filename:
			fname = _("Please enter the new directory name")
		#length = cfg.input_length.value
		#self.session.openWithCallback(self.doRename, InputBox, text=filename, visible_width=length, overwrite=False, firstpos_end=True, allmarked=False, title=_("Please enter file/folder name"), windowTitle=_("Rename file"))
		# overwrite : False = insert mode (not overwrite) when InputBox is created
		# firstpos_end : True = cursor at end of text on InputBox creation - False = cursor at start of text on InputBox creation
		# visible_width : if this width is smaller than the skin width, the text will be scrolled if it is too long
		# allmarked : text all selected at InputBox creation or not
		self.session.openWithCallback(self.doRename, VirtualKeyBoard, title=fname, text=filename, visible_width=48)

	def doRename(self, newname):
		if newname:
			filename = self.SOURCELIST.getFilename()
			sourceDir = self.SOURCELIST.getCurrentDirectory()
			if (filename is None) or (sourceDir is None) or newname == filename:
				return
			try:
				if sourceDir not in filename:
					os.rename(sourceDir + filename, sourceDir + newname)
					movie, ext = os.path.splitext(filename)
					newmovie, newext = os.path.splitext(newname)
					if ext in ALL_MOVIE_EXTENSIONS and newext in ALL_MOVIE_EXTENSIONS:
						for ext in MOVIEEXTENSIONS:
							try:
								if ext == "eit":
									os.rename(sourceDir + movie + ".eit", sourceDir + newmovie + ".eit")
								else:
									os.rename(sourceDir + filename + "." + ext, sourceDir + newname + "." + ext)
							except:
								pass
				else:
					os.rename(filename, sourceDir + newname)
			except OSError as oe:
				self.session.open(MessageBox, _("Error renaming %s to %s:\n%s") % (filename, newname, oe.strerror), type=MessageBox.TYPE_ERROR, simple=True)
			self.doRefresh()

	def doRenameCB(self):
		self.doRefresh()

# ## symlink by name ###
	def gomakeSym(self):
		if self.disableActions_Timer.isActive():
			return
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		targetDir = self.TARGETLIST.getCurrentDirectory()
		if targetDir is None or filename is None or not self.SOURCELIST.getSelectionID():
			return
		if filename.startswith("/"):
			if filename == "/":
				filename = "root"
			else:
				filename = os.path.basename(os.path.normpath(filename))
		elif sourceDir is None:
			return
		#self.session.openWithCallback(self.doMakesym, InputBox, text=filename, title=_("Please enter name of the new symlink"), windowTitle=_("New symlink"))
		self.session.openWithCallback(self.doMakesym, VirtualKeyBoard, title=_("Please enter name of the new symlink"), text=filename)

	def doMakesym(self, newname):
		if newname:
			oldname = self.SOURCELIST.getFilename()
			sourceDir = self.SOURCELIST.getCurrentDirectory()
			targetDir = self.TARGETLIST.getCurrentDirectory()
			if targetDir is None or oldname is None:
				return
			if oldname.startswith("/"):
				oldpath = oldname
			elif sourceDir is not None:
				oldpath = os.path.join(sourceDir, oldname)
			else:
				return
			newpath = os.path.join(targetDir, newname)
			try:
				os.symlink(oldpath, newpath)
			except OSError as oe:
				self.session.open(MessageBox, _("Error linking %s to %s:\n%s") % (oldpath, newpath, oe.strerror), type=MessageBox.TYPE_ERROR, simple=True)
			self.doRefresh()

# ## File/directory information
	def gofileStatInfo(self):
		if self.disableActions_Timer.isActive():
			return
		self.session.open(FileCommanderFileStatInfo, self.SOURCELIST)

# ## symlink by folder ###
	def gomakeSymlink(self):
		if self.disableActions_Timer.isActive():
			return
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		targetDir = self.TARGETLIST.getCurrentDirectory()
		if (filename is None) or (sourceDir is None) or (targetDir is None):
			return
		if sourceDir not in filename:
			movetext = _("Create symlink to file")
		else:
			movetext = _("Symlink to ")
		testfile = filename[:-1]
		if (filename is None) or (sourceDir is None):
			return
		if path.islink(testfile):
			return
		self.session.openWithCallback(self.domakeSymlink, MessageBox, movetext + " %s in %s" % (filename, targetDir), type=MessageBox.TYPE_YESNO, default=True, simple=True)

	def domakeSymlink(self, result=False):
		if result:
			filename = self.SOURCELIST.getFilename()
			sourceDir = self.SOURCELIST.getCurrentDirectory()
			targetDir = self.TARGETLIST.getCurrentDirectory()
			if (filename is None) or (sourceDir is None) or (targetDir is None):
				return
			if sourceDir in filename:
				self.session.openWithCallback(self.doRenameCB, Console, title=_("create symlink ..."), cmdlist=(("ln", "-s", filename, targetDir),))

# ## new file ###
	def gomakeFile(self):
		if self.disableActions_Timer.isActive():
			return
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		if sourceDir is None:
			self.session.open(MessageBox, _("File cannot be created on\n<List of Storage Devices> or <Receiver>.\nChange directory, please."), type=MessageBox.TYPE_WARNING, simple=True)
			return
		self.session.openWithCallback(self.doMakefile, VirtualKeyBoard, title=_("Type the name for the new file"), text=_('new.txt'))

	def doMakefile(self, newname):
		if newname:
			sourceDir = self.SOURCELIST.getCurrentDirectory()
			if sourceDir is None:
				return
			try:
				if not os.path.exists(sourceDir + newname):
					open(sourceDir + newname, "wt").close()
				self.session.open(vEditor, sourceDir + newname)
				self.onFileActionCB(True)
			except OSError as oe:
				self.session.open(MessageBox, _("Error creating file %s:\n%s") % (sourceDir + newname, oe.strerror), type=MessageBox.TYPE_ERROR, simple=True)
			self.doRefresh()

# ## new folder ###
	def gomakeDir(self):
		if self.disableActions_Timer.isActive():
			return
		filename = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		if (filename is None) or (sourceDir is None):
			self.session.open(MessageBox, _("Directory cannot be created here on\n<List of Storage Devices> or <Receiver>.\nMove selector one line below or change directory."), type=MessageBox.TYPE_WARNING, simple=True)
			return
		self.session.openWithCallback(self.doMakedir, VirtualKeyBoard, title=_("Please enter name of the new directory"), text=_('New folder'))

	def doMakedir(self, newname):
		if newname:
			sourceDir = self.SOURCELIST.getCurrentDirectory()
			if sourceDir is None:
				return
			try:
				os.mkdir(sourceDir + newname)
			except OSError as oe:
				self.session.open(MessageBox, _("Error creating directory %s:\n%s") % (sourceDir + newname, oe.strerror), type=MessageBox.TYPE_ERROR, simple=True)
			self.doRefresh()

# ## download subtitles ###
	def downloadSubtitles(self):
		if self.disableActions_Timer.isActive():
			return
		testFileName = self.SOURCELIST.getFilename()
		sourceDir = self.SOURCELIST.getCurrentDirectory()
		if (testFileName is None) or (sourceDir is None):
			return
		subFile = sourceDir + testFileName
		if (testFileName.endswith(".mpg")) or (testFileName.endswith(".mpeg")) or (testFileName.endswith(".mkv")) or (testFileName.endswith(".m2ts")) or (testFileName.endswith(".vob")) or (testFileName.endswith(".mod")) or (testFileName.endswith(".avi")) or (testFileName.endswith(".mp4")) or (testFileName.endswith(".divx")) or (testFileName.endswith(".mkv")) or (testFileName.endswith(".wmv")) or (testFileName.endswith(".mov")) or (testFileName.endswith(".flv")) or (testFileName.endswith(".3gp")):
			print "[FileCommander] Downloading subtitle for: ", subFile
			# For Future USE

	def subCallback(self, answer=False):
		self.doRefresh()

# ## basic functions ###
	def updateHead(self):
		for side in ("list_left", "list_right"):
			dir = self[side].getCurrentDirectory()
			filename = self[side].getFilename()
			if dir is not None:
				self[side + "_head1"].text = cutLargePath(dir, self[side + "_head1"])
				self[side + "_head2"].updateList(self.statInfo(self[side]))
				self[side + "_free"].text = "%s" % freeDiskSpace(dir) + self.walkdirflag
			elif not dir and filename:
				self[side + "_head1"].text = cutLargePath(_("<Receiver>"), self[side + "_head1"])
			else:
				self[side + "_head1"].text = ""
				self[side + "_head2"].updateList(())
				self[side + "_free"].text = ""
			self[side + "_filename"].text = os.path.basename(os.path.normpath(filename)) if cfg.filename_header.value and filename else ""

		self["VKeyIcon"].boolean = self.viewable_file() is not None

	def doRefreshDir(self, jobs, updateDirs):
		if jobs:
			for job in jobs:
				self.addJob(job, updateDirs)
		self["list_left"].changeDir(cfg.path_left_tmp.value or None)
		self["list_right"].changeDir(cfg.path_right_tmp.value or None)
		if self.SOURCELIST == self["list_left"]:
			self["list_left"].selectionEnabled(1)
			self["list_right"].selectionEnabled(0)
		else:
			self["list_left"].selectionEnabled(0)
			self["list_right"].selectionEnabled(1)
		self.updateHead()

	def doRefresh(self):
		if self.disableActions_Timer.isActive():
			return
		sortDirsLeft, sortFilesLeft = self["list_left"].getSortBy().split(',')
		sortDirsRight, sortFilesRight = self["list_right"].getSortBy().split(',')
		sortLeft = formatSortingTyp(sortDirsLeft, sortFilesLeft)
		sortRight = formatSortingTyp(sortDirsRight, sortFilesRight)
		self["sort_left"].setText(sortLeft)
		self["sort_right"].setText(sortRight)

		self.SOURCELIST.refresh()
		self.TARGETLIST.refresh()
		self.updateHead()

	def listRightB(self):
		if self.disableActions_Timer.isActive():
			return
		if cfg.change_navbutton.value == 'yes':
			self.goLeft()
		elif cfg.change_navbutton.value == 'always' and self.SOURCELIST == self["list_right"]:
			self.listLeft()
		else:
			self.listRight()

	def listLeftB(self):
		if self.disableActions_Timer.isActive():
			return
		if cfg.change_navbutton.value == 'yes':
			self.goRight()
		elif cfg.change_navbutton.value == 'always' and self.SOURCELIST == self["list_left"]:
			self.listRight()
		else:
			self.listLeft()

	def listRightStart(self):
		self.listRight()
		if cfg.cursorposition.value:
			self.SOURCELIST.moveToIndex(cfg.lastcursorposition.value)
			self.updateHead()

	def listLeftStart(self):
		self.listLeft()
		if cfg.cursorposition.value:
			self.SOURCELIST.moveToIndex(cfg.lastcursorposition.value)
			self.updateHead()

	def listRight(self):
		if self.disableActions_Timer.isActive():
			return
		self["list_left"].selectionEnabled(0)
		self["list_right"].selectionEnabled(1)
		self.SOURCELIST = self["list_right"]
		self.TARGETLIST = self["list_left"]
		self.updateHead()

	def listLeft(self):
		if self.disableActions_Timer.isActive():
			return
		self["list_left"].selectionEnabled(1)
		self["list_right"].selectionEnabled(0)
		self.SOURCELIST = self["list_left"]
		self.TARGETLIST = self["list_right"]
		self.updateHead()

	def call_change_mode(self):
		if self.disableActions_Timer.isActive():
			return
		self.change_mod(self.SOURCELIST)

# 	def call_onFileAction(self):
# 		self.onFileAction(self.SOURCELIST, self.TARGETLIST)

# ####################
# ## Config MultiSelectionScreen ###
# ####################


class MultiSelectionSetup(ConfigListScreen, Screen):
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)

		self.skinName = ["FileCommanderSetup", "Setup"]

#		self["help"] = Label(_("Select your personal settings:"))
		self["description"] = Label()
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["Actions"] = ActionMap(["ColorActions", "SetupActions"],
		{
			"green": self.save,
			"red": self.cancel,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.ok,
		}, -2)
		self.list = []
		self.onChangedEntry = []
		ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changedEntry)
		self.loadMenu()
		self.onLayoutFinish.append(self.onLayout)

	def loadMenu(self):
		self.list = []
		self.search = _("Search in group selection by")
		self.list.append(getConfigListEntry(self.search, cfg.search, _("You can set what will group selection use - start of title, end of title or contains in title.")))
		if cfg.search.value == "begin":
			self.list.append(getConfigListEntry(_("Pre-fill first 'n' filename chars to virtual keyboard"), cfg.length, _("You can set the number of letters from the beginning of the current file name as the text pre-filled into virtual keyboard for easier input via group selection.")))
		elif cfg.search.value == "end":
			self.list.append(getConfigListEntry(_("Pre-fill last 'n' filename chars to virtual keyboard"), cfg.endlength, _("You can set the number of letters from the end of the current file name as the text pre-filled into virtual keyboard for easier input via group selection.")))
		self.list.append(getConfigListEntry(_("Compare case sensitive"), cfg.sensitive, _("Sets whether to distinguish between uper case and lower case for searching.")))
		#duplicity from main setting:
		self.list.append(getConfigListEntry(_("Filenames in header"), cfg.filename_header, _("Display filenames in header. It is useful for filenames that are too long.")))
		self.list.append(getConfigListEntry(_("Directories to group selections"), cfg.select_across_dirs, _("'Group selection' and 'Invert selection' in Multiselection mode can work with directories too.")))
		self.list.append(getConfigListEntry(_("Move selector to next item"), cfg.move_selector, _("In multi-selection mode moves cursor to next item after marking.") + "\n\n" + _("Note - for switching this option in multi-selection mode you can use key '6' too.")))
		self.list.append(getConfigListEntry(_("All movie extensions"), cfg.all_movie_ext, _("All files in the directory with the same name as the selected movie will be copied or moved too.")))

		self["config"].list = self.list

	def changedEntry(self):
		if self["config"].getCurrent():
			if self["config"].getCurrent()[0] == self.search:
				self.loadMenu()

	def getCurrentEntry(self):
		x = self["config"].getCurrent()
		if x:
			text = x[2] if len(x) == 3 else ""
			self["description"].setText(text)

	def onLayout(self):
		self.setTitle(pname + " - " + _("MultiSelection Settings"))

	def ok(self):
		self.save()

	def save(self):
		self.keySave()

	def cancel(self):
		self.keyCancel()

#####################
# ## Select Screen ###
#####################


def NAME(item):
	return item[0][4]


def SELECTED(item):
	return item[0][3]


class FileCommanderScreenFileSelect(Screen, HelpableScreen, key_actions):
	def __init__(self, session, parent, leftactive, selectedid):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		self.skin = FileCommanderScreen.skin

		self.parent = parent
		self.selectedFiles = []
		self.selectedid = selectedid

		path_left = cfg.path_left_tmp.value or None
		path_right = cfg.path_right_tmp.value or None

		# set sorting
		sortDirsLeft, sortFilesLeft = cfg.sortingLeft_tmp.value.split(',')
		sortDirsRight, sortFilesRight = cfg.sortingRight_tmp.value.split(',')
		firstDirs = cfg.firstDirs.value

		sortLeft = formatSortingTyp(sortDirsLeft, sortFilesLeft)
		sortRight = formatSortingTyp(sortDirsRight, sortFilesRight)
		self["sort_left"] = Label(sortLeft)
		self["sort_right"] = Label(sortRight)

		# set filter
		filter = self.fileFilter()

		# set current folder
		self["list_left_head1"] = Label(path_left)
		self["list_left_head2"] = List()
		self["list_left_select"] = Label()
		self["list_left_filename"] = Label()
		self["list_left_free"] = Label()

		self["list_right_head1"] = Label(path_right)
		self["list_right_head2"] = List()
		self["list_right_select"] = Label()
		self["list_right_filename"] = Label()
		self["list_right_free"] = Label()

		if leftactive:
			self["list_left"] = MultiFileSelectList(self.selectedFiles, path_left, matchingPattern=filter, sortDirs=sortDirsLeft, sortFiles=sortFilesLeft, firstDirs=firstDirs)
			self["list_right"] = FileList(path_right, matchingPattern=filter, sortDirs=sortDirsRight, sortFiles=sortFilesRight, firstDirs=firstDirs)
			self.SOURCELIST = self["list_left"]
			self.TARGETLIST = self["list_right"]
			self.onLayoutFinish.append(self.listLeft)
		else:
			self["list_left"] = FileList(path_left, matchingPattern=filter, sortDirs=sortDirsLeft, sortFiles=sortFilesLeft, firstDirs=firstDirs)
			self["list_right"] = MultiFileSelectList(self.selectedFiles, path_right, matchingPattern=filter, sortDirs=sortDirsRight, sortFiles=sortFilesRight, firstDirs=firstDirs)
			self.SOURCELIST = self["list_right"]
			self.TARGETLIST = self["list_left"]
			self.onLayoutFinish.append(self.listRight)

		self["key_red"] = StaticText(_("Delete"))
		self["key_green"] = StaticText(_("Move"))
		self["key_yellow"] = StaticText(_("Copy"))
		self["key_blue"] = StaticText(_("Invert selection"))

		self["actions"] = HelpableActionMap(self, ["ChannelSelectBaseActions", "WizardActions", "NumberActions", "ColorActions", "InfobarActions", "EPGSelectActions"], {
			"menu": (self.selectAction, _("Open actions menu")),
			"ok": (self.ok, _("Select (source list) or enter directory (target list)")),
			"back": (self.exit, _("Leave multi-select mode")),
			"nextMarker": (self.listRight, _("Activate right-hand file list as multi-select source")),
			"prevMarker": (self.listLeft, _("Activate left-hand file list as multi-select source")),
			"nextBouquet": (self.listRightB, _("Activate right-hand file list as multi-select source")),
			"prevBouquet": (self.listLeftB, _("Activate left-hand file list as multi-select source")),
			"up": (self.goUp, _("Move up list")),
			"down": (self.goDown, _("Move down list")),
			"left": (self.goLeftB, _("Page up list")),
			"right": (self.goRightB, _("Page down list")),
			"red": (self.goRed, _("Delete the selected files or directories")),
			"green": (self.goGreen, _("Move files/directories to target directory")),
			"yellow": (self.goYellow, _("Copy files/directories to target directory")),
			"blue": (self.invertSelection, _("Invert selection")),
			"info": (self.gofileStatInfo, _("File/Directory Status Information")),
			"0": (self.doRefresh, _("Refresh screen")),
			"1": (self.dirSizeWalk, _("Counting directory content size while walking (on/off)")),
			"2": (boundFunction(self.selectGroup, True), _("Select group")),
			"5": (boundFunction(self.selectGroup, False), _("Deselect group")),
			"6": (self.moveSelector, _("Move selector to next item (on/off)")),
			"8": (self.openTasklist, _("Show task list")),
			"keyRecord": (self.goBlue, _("Leave multi-select mode")),
			"showMovies": (self.goBlue, _("Leave multi-select mode")),
		}, -1)
		self.selItems = 0
		self.selSize = 0
		self.setMovieSelectorFlag()
		self.onLayoutFinish.append(self.onLayout)

	def onLayout(self):
		if cfg.extension.value == "^.*":
			filtered = ""
		else:
			filtered = "(*)"
		self.setTitle(pname + " " + filtered + " " + _("(Selectmode)"))
		self.SOURCELIST.moveToIndex(self.selectedid)
		self.updateHead()

	def changeSelectionState(self):
		if self.ACTIVELIST == self.SOURCELIST:
			self.ACTIVELIST.changeSelectionState()
			self.selectedFiles = self.ACTIVELIST.getSelectedList()
			self.getSelectedFilesInfos(self.selectedFiles)
#			print "[FileCommander] selectedFiles:", self.selectedFiles
			if cfg.move_selector.value:
				self.goDown()
			else:
				self.updateHead()

	def getSelectedFilesInfos(self, selected):
		size = 0
		for file in selected:
			size += os.path.getsize(file) if os.path.isfile(file) else 0
		self.selSize = size
		self.selItems = len(selected)

	def invertSelection(self):
		if self.ACTIVELIST == self.SOURCELIST:
			self.ACTIVELIST.toggleAllSelection()
			self.getSelectedFilesInfos(self.selectedFiles)
			self.updateHead()

	def deselectAll(self):
		if self.ACTIVELIST == self.SOURCELIST:
			self.ACTIVELIST.deselectAllSelection()
			self.getSelectedFilesInfos(self.selectedFiles)
			self.updateHead()

	def selectAll(self):
		if self.ACTIVELIST == self.SOURCELIST:
			self.ACTIVELIST.selectAllSelection()
			self.getSelectedFilesInfos(self.selectedFiles)
			self.updateHead()

	def selectAction(self):
		menu = []
		menu.append((_("Select group..."), boundFunction(self.selectGroup, True)))						#2
		menu.append((_("Deselect group..."), boundFunction(self.selectGroup, False)))						#5
		menu.append((_("Select All"), self.selectAll))									        #""
		menu.append((_("Deselect All"), self.deselectAll))									#""
		menu.append((_("Create directory in 'Target' panel"), self.gomakeDir))							#7
		menu.append((_("Invert Selection"), self.invertSelection))								#blue
		menu.append((_("Settings..."), boundFunction(self.session.openWithCallback, self.runBacktoMenu, MultiSelectionSetup)))	#menu
		keys = ["2", "5", "", "", "7", "blue", "menu"]
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_("Select operation:"), list=menu, keys=["dummy" if key == "" else key for key in keys], skin_name="ChoiceBox")

	def menuCallback(self, choice):
		if choice is None:
			return
		if choice[1]:
			choice[1]()

	def runBacktoMenu(self, dummy=False):
		self.setMovieSelectorFlag()
		self.updateHead()
		self.selectAction()

	def selectGroup(self, mark=True):
		if self.ACTIVELIST != self.SOURCELIST:
			return

		def getSubstring(value):
			if value == "begin":
				return _("starts with...")
			elif value == "end":
				return _("ends with...")
			else:
				return _("contains...")
		if mark:
			txt = _("Add to selection (%s)") % getSubstring(cfg.search.value)
		else:
			txt = _("Remove from selection (%s)") % getSubstring(cfg.search.value)

		item = self.SOURCELIST.l.getCurrentSelection()
		length = int(cfg.length.value)
		endlength = int(cfg.endlength.value)
		name = ""
		if item:
			if cfg.search.value == "begin" and length:
				name = NAME(item).decode('UTF-8', 'replace')[0:length]
				txt += 10 * " " + "%s" % length
			elif cfg.search.value == "end" and endlength:
				name = NAME(item).decode('UTF-8', 'replace')[-endlength:]
				txt += 10 * " " + "%s" % endlength
		self.session.openWithCallback(boundFunction(self.changeItems, mark), VirtualKeyBoard, title=txt, text=name)

	def changeItems(self, mark, searchString=None):
		if searchString:
			searchString = searchString.decode('UTF-8', 'replace')
			if not cfg.sensitive.value:
				searchString = searchString.lower()
			for item in self.SOURCELIST.list:
				if cfg.sensitive.value:
					if cfg.search.value == "begin":
						exist = NAME(item).decode('UTF-8', 'replace').startswith(searchString)
					elif cfg.search.value == "end":
						exist = NAME(item).decode('UTF-8', 'replace').endswith(searchString)
					else:
						exist = False if NAME(item).decode('UTF-8', 'replace').find(searchString) == -1 else True
				else:
					if cfg.search.value == "begin":
						exist = NAME(item).decode('UTF-8', 'replace').lower().startswith(searchString)
					elif cfg.search.value == "end":
						exist = NAME(item).decode('UTF-8', 'replace').lower().endswith(searchString)
					else:
						exist = False if NAME(item).decode('UTF-8', 'replace').lower().find(searchString) == -1 else True
				if exist:
					if mark:
						if not SELECTED(item):
							self.ACTIVELIST.toggleItemSelection(item)
					else:
						if SELECTED(item):
							self.ACTIVELIST.toggleItemSelection(item)
		self.getSelectedFilesInfos(self.selectedFiles)
		self.updateHead()

	def exit(self, jobs=None, updateDirs=None):
		cfg.path_left_tmp.value = self["list_left"].getCurrentDirectory() or ""
		cfg.path_right_tmp.value = self["list_right"].getCurrentDirectory() or ""
		self.close(jobs, updateDirs)

	def gofileStatInfo(self):
		self.session.open(FileCommanderFileStatInfo, self.SOURCELIST)

	def ok(self):
		if self.ACTIVELIST == self.SOURCELIST:
			self.changeSelectionState()
		else:
			if self.ACTIVELIST.canDescent():  # isDir
				self.ACTIVELIST.descent()
			self.updateHead()

	def goParentfolder(self):
		if self.ACTIVELIST == self.SOURCELIST:
			return
		if self.ACTIVELIST.getParentDirectory() != False:
			self.ACTIVELIST.changeDir(self.ACTIVELIST.getParentDirectory())
			self.updateHead()

	def goLeftB(self):
		if cfg.change_navbutton.value == 'yes':
			self.listLeft()
		else:
			self.goLeft()

	def goRightB(self):
		if cfg.change_navbutton.value == 'yes':
			self.listRight()
		else:
			self.goRight()

	def goLeft(self):
		self.ACTIVELIST.pageUp()
		self.updateHead()

	def goRight(self):
		self.ACTIVELIST.pageDown()
		self.updateHead()

	def goUp(self):
		self.ACTIVELIST.up()
		self.updateHead()

	def goDown(self):
		self.ACTIVELIST.down()
		self.updateHead()

	def openTasklist(self):
		self.tasklist = []
		for job in job_manager.getPendingJobs():
			#self.tasklist.append((job, job.name, job.getStatustext(), int(100 * job.progress / float(job.end)), str(100 * job.progress / float(job.end)) + "%"))
			progress = job.getProgress()
			self.tasklist.append((job, job.name, job.getStatustext(), progress, str(progress) + " %"))
		self.session.open(TaskListScreen, self.tasklist)

	def dirSizeWalk(self):
		self.parent.setWalkdir()
		self.updateHead()

	def moveSelector(self):
		cfg.move_selector.value = not cfg.move_selector.value
		self.setMovieSelectorFlag()
		self.updateHead()

	def setMovieSelectorFlag(self):
		self.moveselectorflag = ' _' if cfg.move_selector.value else ''


# ## new folder in !Target! ###


	def gomakeDir(self):
		filename = self.TARGETLIST.getFilename()
		sourceDir = self.TARGETLIST.getCurrentDirectory()
		if (filename is None) or (sourceDir is None):
			self.session.open(MessageBox, _("Directory cannot be created here on\n<List of Storage Devices> or <Receiver>.\nMove selector one line below or change directory."), type=MessageBox.TYPE_WARNING, simple=True)
			return
		self.session.openWithCallback(self.doMakedir, VirtualKeyBoard, title=_("Please enter name of the new directory"), text=_('New folder'))

	def doMakedir(self, newname):
		if newname:
			targetDir = self.TARGETLIST.getCurrentDirectory()
			if targetDir is None:
				return
			try:
				os.mkdir(targetDir + newname)
			except OSError as oe:
				self.session.open(MessageBox, _("Error creating directory %s:\n%s") % (targetDir + newname, oe.strerror), type=MessageBox.TYPE_ERROR, simple=True)
			self.doRefresh()

# ## delete select ###
	def goRed(self):
		if not len(self.selectedFiles):
			return
		sourceDir = self.SOURCELIST.getCurrentDirectory()

		cnt = 0
		filename = ""
		self.delete_dirs = []
		self.delete_files = []
		self.delete_updateDirs = [self.SOURCELIST.getCurrentDirectory()]
		for file in self.selectedFiles:
			fn = file.rstrip('/').split('/')[-1]
			filename += '%s' % fn if not cnt else ', %s' % fn if cnt < 5 else ', ...' if cnt < 6 else ''
			cnt += 1
			if os.path.isdir(file):
				self.delete_dirs.append(file)
			else:
				self.delete_files.append(file)
		deltext = ngettext("Delete %d element", "Delete %d elements", len(self.selectedFiles)) % len(self.selectedFiles)
		self.session.openWithCallback(self.doDelete, MessageBox, deltext + "?\n\n%s\n\n%s\n%s" % (filename, _("from dir"), sourceDir), type=MessageBox.TYPE_YESNO, default=False, simple=True)

	def doDelete(self, result=False):
		if result:
			for file in self.delete_files:
				print 'delete:', file
				os.remove(file)
			self.exit([self.delete_dirs], self.delete_updateDirs)

# ## move select ###
	def goGreen(self):
		targetDir = self.TARGETLIST.getCurrentDirectory()
		if targetDir is None or not len(self.selectedFiles):
			return
		sourceDir = self.SOURCELIST.getCurrentDirectory()

		cnt = 0
		warncnt = 0
		warntxt = ""
		filename = ""
		self.cleanList()
		self.move_updateDirs = [targetDir, self.SOURCELIST.getCurrentDirectory()]
		self.move_jobs = []
		for file in self.selectedFiles:
			fn = file.rstrip('/').split('/')[-1]
			filename += '%s' % fn if not cnt else ', %s' % fn if cnt < 3 else ', ...' if cnt < 4 else ''
			cnt += 1
			if os.path.exists(targetDir + '/' + file.rstrip('/').split('/')[-1]):
				warncnt += 1
			dst_file = targetDir
			if dst_file.endswith("/") and dst_file != "/":
				targetDir = dst_file[:-1]
			self.move_jobs.append(FileTransferJob(file, targetDir, False, False, "%s : %s" % (_("move file"), file)))
		warntxt = ngettext(" - %d element exist! Overwrite", " - %d elements exist! Overwrite", warncnt) % warncnt if warncnt else ''
		movetext = ngettext("Move %d element", "Move %d elements", len(self.selectedFiles)) % len(self.selectedFiles) + warntxt
		self.session.openWithCallback(self.doMove, MessageBox, movetext + "?\n\n%s\n\n%s\n%s\n%s\n%s" % (filename, _("from dir"), sourceDir, _("to dir"), targetDir), type=MessageBox.TYPE_YESNO, default=True, simple=True)

	def doMove(self, result=False):
		if result:
			self.exit(self.move_jobs, self.move_updateDirs)

# ## copy select ###
	def goYellow(self):
		targetDir = self.TARGETLIST.getCurrentDirectory()
		if targetDir is None or not len(self.selectedFiles):
			return
		sourceDir = self.SOURCELIST.getCurrentDirectory()

		cnt = 0
		warncnt = 0
		warntxt = ""
		filename = ""
		self.cleanList()
		self.copy_updateDirs = [targetDir]
		self.copy_jobs = []
		for file in self.selectedFiles:
			fn = file.rstrip('/').split('/')[-1]
			filename += '%s' % fn if not cnt else ', %s' % fn if cnt < 3 else ', ...' if cnt < 4 else ''
			cnt += 1
			if os.path.exists(targetDir + '/' + file.rstrip('/').split('/')[-1]):
				warncnt += 1
			dst_file = targetDir
			if dst_file.endswith("/") and dst_file != "/":
				targetDir = dst_file[:-1]
			if file.endswith("/"):
				self.copy_jobs.append(FileTransferJob(file, targetDir, True, True, "%s : %s" % (_("copy folder"), file)))
			else:
				self.copy_jobs.append(FileTransferJob(file, targetDir, False, True, "%s : %s" % (_("copy file"), file)))
		warntxt = ngettext(" - %d element exist! Overwrite", " - %d elements exist! Overwrite", warncnt) % warncnt if warncnt else ''
		copytext = ngettext("Copy %d element", "Copy %d elements", len(self.selectedFiles)) % len(self.selectedFiles) + warntxt
		self.session.openWithCallback(self.doCopy, MessageBox, copytext + "?\n\n%s\n\n%s\n%s\n%s\n%s" % (filename, _("from dir"), sourceDir, _("to dir"), targetDir), type=MessageBox.TYPE_YESNO, default=True, simple=True)

	def doCopy(self, result=False):
		if result:
			self.exit(self.copy_jobs, self.copy_updateDirs)

	def goBlue(self):
		self.exit()

# ## basic functions ###
	def updateHead(self):
		for side in ("list_left", "list_right"):
			dir = self[side].getCurrentDirectory()
			filename = self[side].getFilename()
			if dir is not None:
				self[side + "_head1"].text = cutLargePath(dir, self[side + "_head1"])
				self[side + "_free"].text = "%s" % freeDiskSpace(dir) + self.parent.walkdirflag + self.moveselectorflag
				if self.selItems and self.SOURCELIST == self[side]:
					self[side + "_head2"].updateList(())
					self[side + "_select"].text = self.selInfo(self.selItems, self.selSize)
				else:
					self[side + "_head2"].updateList(self.statInfo(self[side]))
					self[side + "_select"].text = ""
			elif not dir and filename:
				self[side + "_head1"].text = cutLargePath(_("<Receiver>"), self[side + "_head1"])
			else:
				self[side + "_head1"].text = ""
				self[side + "_head2"].updateList(())
				self[side + "_select"].text = ""
				self[side + "_free"].text = ""
			self[side + "_filename"].text = os.path.basename(os.path.normpath(filename)) if cfg.filename_header.value and filename else ""

	def doRefresh(self):
		print "[FileCommander] selectedFiles:", self.selectedFiles
		self.SOURCELIST.refresh()
		self.TARGETLIST.refresh()
		self.updateHead()

	def listRightB(self):
		if cfg.change_navbutton.value == 'yes':
			self.goLeft()
		elif cfg.change_navbutton.value == 'always' and self.ACTIVELIST == self["list_right"]:
			self.listLeft()
		else:
			self.listRight()

	def listLeftB(self):
		if cfg.change_navbutton.value == 'yes':
			self.goRight()
		elif cfg.change_navbutton.value == 'always' and self.ACTIVELIST == self["list_left"]:
			self.listRight()
		else:
			self.listLeft()

	def listRight(self):
		self["list_left"].selectionEnabled(0)
		self["list_right"].selectionEnabled(1)
		self.ACTIVELIST = self["list_right"]
		self.updateHead()

	def listLeft(self):
		self["list_left"].selectionEnabled(1)
		self["list_right"].selectionEnabled(0)
		self.ACTIVELIST = self["list_left"]
		self.updateHead()

	# remove movieparts if the movie is present
	def cleanList(self):
		for file in self.selectedFiles[:]:
			movie, extension = os.path.splitext(file)
			if extension[1:] in MOVIEEXTENSIONS:
				if extension == ".eit":
					extension = ".ts"
					movie += extension
				else:
					extension = os.path.splitext(movie)[1]
				if extension in ALL_MOVIE_EXTENSIONS and movie in self.selectedFiles:
					self.selectedFiles.remove(file)


class FileCommanderFileStatInfo(Screen, key_actions, stat_info):
	skin = """
		<screen name="FileCommanderFileStatInfo" position="center,center" size="545,370" title="File/Directory Status Information">
			<widget name="filename" position="10,0" size="525,46" font="Regular;20"/>
			<widget source="list" render="Listbox" position="10,60" size="525,300" scrollbarMode="showOnDemand" selectionDisabled="1" transparent="1" >
				<convert type="TemplatedMultiContent">
					{"template": [
						# 0   100 200 300 400 500
						# |   |   |   |   |   |
						# 00000000 1111111111111
						MultiContentEntryText(pos = (0, 0), size = (200, 25), font = 0, flags = RT_HALIGN_LEFT, text = 0), # index 0 is a label
						MultiContentEntryText(pos = (225, 0), size = (300, 25), font = 0, flags = RT_HALIGN_LEFT, text = 1), # index 1 is the information
						],
						"fonts": [gFont("Regular", 20)],
						"itemHeight": 25,
						"selectionEnabled": False
					}
				</convert>
			</widget>
		</screen>
	"""

	SIZESCALER = UnitScaler(scaleTable=UnitMultipliers.Jedec, maxNumLen=3, decimals=1)

	def __init__(self, session, source):
		Screen.__init__(self, session)
		stat_info.__init__(self)

		self.list = []

		self["list"] = List(self.list)
		self["filename"] = Label()
		self["link_sep"] = Label()
		self["link_label"] = Label()
		self["link_value"] = Label()

		self["link_sep"].hide()

		self["actions"] = ActionMap(
			["SetupActions", "DirectionActions", "EPGSelectActions"],
			{
				"cancel": self.close,
				"ok": self.close,
				"up": self.pageUp,
				"down": self.pageDown,
				"info": self.close,
			}, prio=-1)

		self.setTitle(_("File/Directory Status Information"))
		self.source = source

		self.onShown.append(self.fillList)

	def pageUp(self):
		if "list" in self:
			self["list"].pageUp()

	def pageDown(self):
		if "list" in self:
			self["list"].pageDown()

	def fillList(self):
		filename = self.source.getFilename()
		sourceDir = self.source.getCurrentDirectory()

		if filename is None:
			self.session.open(MessageBox, _("It is not possible to get the file status of <List of Storage Devices>"), type=MessageBox.TYPE_ERROR, simple=True)
			self.close()
			return

		dirname = filename if os.path.isdir(filename) else None

		if filename.endswith("/"):
			filepath = os.path.normpath(filename)
			if filepath == '/':
				filename = '/'
			else:
				filename = os.path.normpath(filename)
		else:
			filepath = os.path.join(sourceDir, filename)

		filename = os.path.basename(os.path.normpath(filename))
		self["filename"].text = filename
		self.list = []

		try:
			st = os.lstat(filepath)
		except OSError as oe:
			self.session.open(MessageBox, "%s: %s" % (filepath, oe.strerror), type=MessageBox.TYPE_ERROR, simple=True)
			self.close()
			return

		mode = st.st_mode
		perms = stat.S_IMODE(mode)
		self.list.append((_("Type:"), self.filetypeStr(mode)))
		self.list.append((_("Owner:"), "%s (%d)" % (self.username(st.st_uid), st.st_uid)))
		self.list.append((_("Group:"), "%s (%d)" % (self.groupname(st.st_gid), st.st_gid)))
		self.list.append((_("Permissions:"), _("%s (%04o)") % (self.fileModeStr(perms), perms)))
		if not (stat.S_ISCHR(mode) or stat.S_ISBLK(mode)):
			self.list.append((_("Size:"), "%s (%sB)" % ("{:n}".format(st.st_size), ' '.join(self.SIZESCALER.scale(st.st_size)))))
		self.list.append((_("Modified:"), self.formatTime(st.st_mtime)))
		self.list.append((_("Accessed:"), self.formatTime(st.st_atime)))
		self.list.append((_("Metadata changed:"), self.formatTime(st.st_ctime)))
		self.list.append((_("Links:"), "%d" % st.st_nlink))
		self.list.append((_("Inode:"), "%d" % st.st_ino))
		self.list.append((_("On device:"), "%d, %d" % ((st.st_dev >> 8) & 0xff, st.st_dev & 0xff)))
		if cfg.dir_size.value and dirname:
			self.list.append((_("Content size:"), "%s" % self.dirContentSize(dirname)))

		self["list"].updateList(self.list)

		if stat.S_ISLNK(mode):
			self["link_sep"].show()
			self["link_label"].text = _("Link target:")
			try:
				self["link_value"].text = os.readlink(filepath)
			except OSError as oe:
				self["link_value"].text = _("Can't read link contents: %s") % oe.strerror
		else:
			self["link_sep"].hide()
			self["link_label"].text = ""
			self["link_value"].text = ""
