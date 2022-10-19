#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# Components
from __future__ import print_function
from Components.config import config
from Components.Label import Label
from Components.ActionMap import HelpableActionMap
from Components.MenuList import MenuList
from Components.AVSwitch import AVSwitch
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText

# Screens
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen
from Screens.InfoBar import MoviePlayer as Movie_Audio_Player

# Tools
from Tools.Directories import fileExists

# Various
from Plugins.Extensions.FileCommander.InputBox import InputBoxWide
from enigma import eTimer, ePicLoad, getDesktop, gFont, eSize

from Tools.TextBoundary import getTextBoundarySize

import skin

import os

# for locale (gettext)
from . import _

##################################

pname = _("File Commander - Addon Mediaplayer")
pdesc = _("play/show Files")
pversion = "1.0-r0"

# ### play with movieplayer ###


class MoviePlayer(Movie_Audio_Player):
	def __init__(self, session, service):
		self.session = session
		self.WithoutStopClose = False
		Movie_Audio_Player.__init__(self, self.session, service)

	def leavePlayer(self):
		self.is_closing = True
		self.session.openWithCallback(self.leavePlayerConfirmed, MessageBox, _("Exit movie player?"))

	def leavePlayerConfirmed(self, answer):
		if answer:
			self.close()

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing:
			return
		self.close()

	def showMovies(self):
		self.WithoutStopClose = True
		self.close()

	def movieSelected(self, service):
		self.leavePlayer(self.de_instance)

	def __onClose(self):
		if not(self.WithoutStopClose):
			self.session.nav.playService(self.lastservice)

# ### File viewer/line editor ###


class vEditor(Screen, HelpableScreen):

	skin = """
		<screen position="40,80" size="1200,600" title="">
			<widget name="list_head" position="10,10" size="1170,45" font="Regular;20" foregroundColor="#00fff000"/>
			<widget name="filedata"  scrollbarMode="showOnDemand" position="10,60" size="1160,500" itemHeight="25"/>
			<widget source="key_red" render="Label" position="100,570" size="260,25" transparent="1" font="Regular;20"/>
			<widget source="key_green" render="Label" position="395,570" size="260,25"  transparent="1" font="Regular;20"/>
			<widget source="key_yellow" render="Label" position="690,570" size="260,25" transparent="1" font="Regular;20"/>
			<widget source="key_blue" render="Label" position="985,570" size="260,25" transparent="1" font="Regular;20"/>
			<ePixmap position="70,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FileCommander/pic/button_red.png" transparent="1" alphatest="on"/>
			<ePixmap position="365,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FileCommander/pic/button_green.png" transparent="1" alphatest="on"/>
			<ePixmap position="660,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FileCommander/pic/button_yellow.png" transparent="1" alphatest="on"/>
			<ePixmap position="955,570" size="260,25" zPosition="0" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FileCommander/pic/button_blue.png" transparent="1" alphatest="on"/>
			### do not remove this line. Set x-size and font same as is set "input" in InputBoxWide screen ###
			<widget name="InputBoxWide_input" position="0,0" size="1080,0" font="Regular;22"/>
			###
		</screen>"""

	def __init__(self, session, file):
		pname = _("File Commander - Addon File-Viewer")
		self.skin = vEditor.skin
		Screen.__init__(self, session)
		self.session = session
		HelpableScreen.__init__(self)
		self.file_name = file
		self.list = []
		self["filedata"] = MenuList(self.list)
		self["actions"] = HelpableActionMap(self, ["WizardActions", "ColorActions", "InfobarChannelSelection"], {
			"ok": (self.editLine, _("Edit current line")),
			"green": (self.editLine, _("Edit current line")),
			"back": (self.exitEditor, _("Exit editor and write changes (if any)")),
			"red": (self.exitEditor, _("Exit editor and write changes (if any)")),
			"yellow": (self.del_Line, _("Delete current line")),
			"blue": (self.ins_Line, _("Insert line before current line")),
			"keyChannelUp": (self.posStart, _("Go to start of file")),
			"keyChannelDown": (self.posEnd, _("Go to end of file")),
		}, -1)
		self["list_head"] = Label(self.file_name)
		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Edit"))
		self["key_yellow"] = StaticText(_("Delete"))
		self["key_blue"] = StaticText(_("Insert"))

		# do not remove label "InputBoxWide_input".
		# it is used for get true length (in chars) for InputBoxWide
		# because InputBoxWide is opened later
		self["InputBoxWide_input"] = Label()
		#

		self.selLine = None
		self.oldLine = None
		self.isChanged = False
		self.skinName = "vEditorScreen"
		self.GetFileData(file)
		self.setTitle(pname)

	def exitEditor(self):
		if self.isChanged:
			warningtext = "\n" + (_("has been CHANGED! Do you want to save it?"))
			warningtext = warningtext + "\n\n" + (_("WARNING!"))
			warningtext = warningtext + "\n" + (_("The authors are NOT RESPONSIBLE"))
			warningtext = warningtext + "\n" + (_("for DATA LOSS OR DAMAGE !!!"))
			msg = self.session.openWithCallback(self.SaveFile, MessageBox, _(self.file_name + warningtext), MessageBox.TYPE_YESNO)
			msg.setTitle(_("File Commander"))
		else:
			self.close()

	def GetFileData(self, fx):
		try:
			flines = open(fx, "r")
			lineNo = 1
			for line in flines:
				self.list.append(str(lineNo).zfill(4) + ": " + line)
				lineNo += 1
			flines.close()
			self["list_head"] = Label(fx)
		except:
			pass

	def editLine(self):
		try:
			self.findtab = -1
			self.selLine = self["filedata"].getSelectionIndex()
			self.oldLine = self.list[self.selLine]
			my_editableText = self.list[self.selLine][:-1]
			editableText = my_editableText.partition(": ")[2]
			# os.system('echo %s %s >> /tmp/test.log' % ("oldline_a :", str(len(editableText))))
			if len(editableText) == 0:
				editableText = ""  # self.list[self.selLine][:-1]
			self.findtab = editableText.find("\t", 0, len(editableText))
			if self.findtab != -1:
				editableText = editableText.replace("\t", "        ")

			firstpos_end = config.plugins.filecommander.editposition_lineend.value

			# count position for InputBoxWide
			def getMaxPosition(text, label, end=False):
				try:
					def getStringSize(string, label):
						label.instance.setNoWrap(1)
						label.setText("%s" % string)
						return label.instance.calculateSize().width()

					w = label.instance.size().width()
					if w <= 0:
						return 100 # default value
					sw = getStringSize(text, label)

					if sw > w:
						if end: # editation from end
							l = len(text)
							for i, idx in enumerate(text):
								x = text[l - i:]
								print(x)
								if getStringSize(x, label) >= w:
									return i
							return i
						else:	# standard editation
							for i, idx in enumerate(text):
								x = text[:i]
								if getStringSize(x, label) >= w:
									return i
							return i
					return w // getStringSize("0", label) # approximate number of characters in label
				except:
					return 100 # default value, if missing label "InputBoxWide_input" in vEditor skin

			length = getMaxPosition(editableText, self["InputBoxWide_input"], end=firstpos_end) - 1

			self.session.openWithCallback(self.callbackEditLine, InputBoxWide, title="%s %s" % (_("Original:"), editableText), visible_width=length, overwrite=False, firstpos_end=firstpos_end, allmarked=False, windowTitle=_("Edit line ") + str(self.selLine + 1), text=editableText)
		except:
			msg = self.session.open(MessageBox, _("This line is not editable!"), MessageBox.TYPE_ERROR)
			msg.setTitle(_("Error..."))

	def callbackEditLine(self, newline):
		if newline is not None:
			k = 0
			for x in self.list:
				if x == self.oldLine:
					if k == self.selLine:
						self.isChanged = True
						if self.findtab != -1:
							newline = newline.replace("        ", "\t")
							self.findtab = -1
						my_line = self.oldLine.partition(": ")[0]
						if self.oldLine.find(": ") != -1:
							newline = my_line + ": " + newline
						else:
							newline = "0000" + ": " + newline
						self.list.remove(x)
						self.list.insert(self.selLine, newline + '\n')
				k += 1
		self.findtab = -1
		self.selLine = None
		self.oldLine = None

	def posStart(self):
		self.selLine = 0
		self["filedata"].moveToIndex(0)

	def posEnd(self):
		self.selLine = len(self.list)
		self["filedata"].moveToIndex(len(self.list) - 1)

	def del_Line(self):
		self.selLine = self["filedata"].getSelectionIndex()
		if len(self.list) > 1:
			self.isChanged = True
			del self.list[self.selLine]
			self.refreshList()

	def ins_Line(self):
		self.selLine = self["filedata"].getSelectionIndex()
		self.list.insert(self.selLine, "0000: " + "" + '\n')
		self.isChanged = True
		self.refreshList()

	def refreshList(self):
		lineno = 1
		for x in self.list:
			my_x = x.partition(": ")[2]
			self.list.remove(x)
			self.list.insert(lineno - 1, str(lineno).zfill(4) + ": " + my_x)  # '\n')
			lineno += 1
		self["filedata"].setList(self.list)

	def SaveFile(self, answer):
		if answer is True:
			try:
				if fileExists(self.file_name):
					os.system("cp " + self.file_name + " " + self.file_name + ".bak")
				eFile = open(self.file_name, "w")
				for x in self.list:
					my_x = x.partition(": ")[2]
					eFile.writelines(my_x)
				eFile.close()
			except:
				pass
			self.close()
		else:
			self.close()


class ImageViewer(Screen, HelpableScreen):
	s, w, h = 30, getDesktop(0).size().width(), getDesktop(0).size().height()
	skin = """
		<screen position="0,0" size="%d,%d" flags="wfNoBorder">
			<eLabel position="0,0" zPosition="0" size="%d,%d" backgroundColor="#00000000" />
			<widget name="image" position="%d,%d" size="%d,%d" zPosition="1" alphatest="on" />
			<widget name="status" position="%d,%d" size="20,20" zPosition="2" pixmap="icons/record.png" alphatest="on" />
			<widget name="icon" position="%d,%d" size="20,20" zPosition="2" pixmap="icons/ico_mp_play.png"  alphatest="on" />
			<widget source="message" render="Label" position="%d,%d" size="%d,25" font="Regular;20" halign="left" foregroundColor="#0038FF48" zPosition="2" noWrap="1" transparent="1" />
		</screen>
		""" % (w, h, w, h, s, s, w - (s * 2), h - (s * 2), s + 5, s + 2, s + 25, s + 2, s + 45, s, w - (s * 2) - 50)

	def __init__(self, session, fileList, index, path, filename):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		self["actions"] = HelpableActionMap(self, ["OkCancelActions", "ColorActions", "DirectionActions"], {
			"cancel": (self.keyCancel, _("Exit picture viewer")),
			"left": (self.keyLeft, _("Show previous picture")),
			"right": (self.keyRight, _("Show next picture")),
			"blue": (self.keyBlue, _("Start/stop slide show")),
			"yellow": (self.keyYellow, _("Show image information")),
		}, -1)

		self["icon"] = Pixmap()
		self["image"] = Pixmap()
		self["status"] = Pixmap()
		self["message"] = StaticText(_("Please wait, Loading image."))

		self.fileList = []
		self.currentImage = []

		self.lsatIndex = index
		self.startIndex = index
		self.filename = filename
		self.fileListLen = 0
		self.currentIndex = 0
		self.directoryCount = 0

		self.displayNow = True

		self.makeFileList(fileList, path)

		self.pictureLoad = ePicLoad()
		self.pictureLoad.PictureData.get().append(self.finishDecode)

		self.slideShowTimer = eTimer()
		self.slideShowTimer.callback.append(self.cbSlideShow)

		self.onFirstExecBegin.append(self.firstExecBegin)

	def firstExecBegin(self):
		# Ensure that Plugins.Extensions.PicturePlayer exists and
		# that the config.pic config variables have been initialised.
		try:
			import Plugins.Extensions.PicturePlayer.ui
		except:
			self.session.open(MessageBox, _("The Image Viewer component of the File Commander requires the PicturePlayer extension. Install PicturePlayer to enable this operation."), MessageBox.TYPE_ERROR)
			self.close()
			return

		if self.fileListLen >= 0:
			self.setPictureLoadPara()

	def keyLeft(self):
		self.currentImage = []
		self.currentIndex = self.lsatIndex
		self.currentIndex -= 1
		if self.currentIndex < 0:
			self.currentIndex = self.fileListLen
		self.startDecode()
		self.displayNow = True

	def keyRight(self):
		self.displayNow = True
		self.showPicture()

	def keyYellow(self):
		if self.fileListLen < 0:
			return
		from Plugins.Extensions.PicturePlayer.ui import Pic_Exif
		self.session.open(Pic_Exif, self.pictureLoad.getInfo(self.fileList[self.lsatIndex]))

	def keyBlue(self):
		if self.slideShowTimer.isActive():
			self.slideShowTimer.stop()
			self["icon"].hide()
		else:
			CONFIG_SLIDESHOW = config.plugins.filecommander.diashow.value
			self.slideShowTimer.start(CONFIG_SLIDESHOW)
			self["icon"].show()
			self.keyRight()

	def keyCancel(self):
		del self.pictureLoad
		self.close(self.startIndex)

	def setPictureLoadPara(self):
		sc = AVSwitch().getFramebufferScale()
		self.pictureLoad.setPara([
			self["image"].instance.size().width(),
			self["image"].instance.size().height(),
			sc[0],
			sc[1],
			0,
			int(config.pic.resize.value),
			'#00000000'
		])
		self["icon"].hide()
		if not config.pic.infoline.value:
			self["message"].setText("")
		self.startDecode()

	def makeFileList(self, fileList, path):
		i = 0
		start_pic = -1
		for x in fileList:
			l = len(fileList[0])
			if x[0][0] is not None:
				testfilename = x[0][0].lower()
			else:
				testfilename = x[0][0]  # "empty"
			if l == 3 or l == 2:
				if not x[0][1] and ((testfilename.endswith(".jpg")) or (testfilename.endswith(".jpeg")) or (testfilename.endswith(".jpe")) or (testfilename.endswith(".png")) or (testfilename.endswith(".bmp"))):
					if self.filename == x[0][0]:
						start_pic = i
					i += 1
					self.fileList.append(path + x[0][0])
				else:
					self.directoryCount += 1
			else:
				testfilename = x[4].lower()
				if (testfilename.endswith(".jpg")) or (testfilename.endswith(".jpeg")) or (testfilename.endswith(".jpe")) or (testfilename.endswith(".png")) or (testfilename.endswith(".bmp")):
					if self.filename == x[0][0]:
						start_pic = i
					i += 1
					self.fileList.append(x[4])
		self.currentIndex = start_pic
		if self.currentIndex < 0 or start_pic < 0:
			self.currentIndex = 0
		self.fileListLen = len(self.fileList) - 1

	def showPicture(self):
		if self.displayNow and len(self.currentImage):
			self.displayNow = False
			self["message"].setText(self.currentImage[0])
			self.setTitle(self.currentImage[0])
			self.lsatIndex = self.currentImage[1]
			self["image"].instance.setPixmap(self.currentImage[2].__deref__())
			self.currentImage = []

			self.currentIndex += 1

			if self.currentIndex > self.fileListLen:
				self.currentIndex = 0
			self.startDecode()

	def finishDecode(self, picInfo=""):
		self["status"].hide()
		ptr = self.pictureLoad.getData()
		if ptr is not None:
			text = ""
			try:
				text = picInfo.split('\n', 1)
				text = "(" + str(self.currentIndex + 1) + "/" + str(self.fileListLen + 1) + ") " + text[0].split('/')[-1]
			except:
				pass
			self.currentImage = []
			self.currentImage.append(text)
			self.currentImage.append(self.currentIndex)
			self.currentImage.append(ptr)
			self.showPicture()

	def startDecode(self):
		if len(self.fileList) == 0:
			self.currentIndex = 0
		self.pictureLoad.startDecode(self.fileList[self.currentIndex])
		self["status"].show()

	def cbSlideShow(self):
		print("slide to next Picture index=" + str(self.lsatIndex))
		if not config.pic.loop.value and self.lsatIndex == self.fileListLen:
			self.PlayPause()
		self.displayNow = True
		self.showPicture()
