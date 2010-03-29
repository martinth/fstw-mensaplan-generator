#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2010 Martin Thurau <martin.thurau@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys, os
from os.path import abspath, dirname, join
from time import sleep
from datetime import date
from urllib import urlopen
from optparse import OptionParser
import subprocess
import logging

from Tkinter import * 
import tkFileDialog, tkMessageBox

# insert "lib" dir to the module search path
if __file__:
	appDir = dirname(abspath(__file__))
	libDir = join(appDir, 'lib')
	sys.path.insert(1, libDir)

from odf.opendocument import load
from odf import table
from planparser import MensaplanParser, fill_meal_table
from sudokufiller import MySudoku, fill_sudoku_table
import locale

try:
	locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
except:
	pass


# Url von der die Daten gelanden werden sollen
URI = '''http://www.uni-kiel.de/stwsh/seiten_essen/plan_mensa_luebeck.html'''
# Vorlage für den Mensaplan
TEMPLATE = join(appDir, 'mensaplan.odt')


class Main(Frame):
	
	def __init__(self, master=None):

		parser = OptionParser()
		parser.add_option('-d', '--debug', action='store_true', dest='debug')
		parser.add_option('-f', '--from-file', action='store', dest='file')
		
		self.options, self.args = parser.parse_args()

		if self.options.debug:
			logging.basicConfig(level=logging.DEBUG)
			logging.info("Loglevel auf DEBUG gesetzt")

		# tk initialisieren
		Frame.__init__(self, master)   
		self.grid()                    
		self.createWidgets()
	
	def createWidgets(self):
		self.textField = Text(self, height=15, width=70)
		self.textField.grid()
		self.saveButton = Button (self, text='Mensaplan erzeugen', command=self.save_odt )        
		self.saveButton.grid() 
	
	def msg(self, message):
		self.textField.insert(END, message + "\n")
		self.update_idletasks()
	
	def save_odt(self):
		'''Signalhandler für den "Starten" Knopf. Fragt nach dem Speicherort und startet
		anschließend den Workerthread'''
		
		t = date.today()
		new_file = 'mensaplan_%02d_%02d_%d.odt' % (	t.day, t.month, t.year)

		file = tkFileDialog.asksaveasfile(
							parent=self, mode='w', title="Speicherort wählen",
							filetypes=[('Openoffice Dateien','*.odt'),],
							initialfile=new_file)
		if not file:
			return
		
		self.filename = file.name
		file.close()
		os.remove(self.filename)

		if not self.filename.lower().endswith('.odt'):
			self.filename += '.odt'
		
		if not os.path.exists(TEMPLATE):
			tkMessageBox.showerror("Vorlage nicht gefunden",
								"Konnte die Datei '%s' nicht finden" % TEMPLATE)
		
		self.saveButton.configure(state = DISABLED)
		
		if self.options.file:
			logging.info("Lade Daten aus Datei ''")
			data = open(self.options.file).read()
		else:
			self.msg("Lade Daten von '%s'" % URI)
			data = urlopen(URI).read()
		parser = MensaplanParser(data)
		days = parser.extract()

		self.msg("Lade Vorlage aus '%s'" % TEMPLATE)
		odt_doc = load(TEMPLATE)

		for t in odt_doc.getElementsByType(table.Table):
			table_name = t.getAttribute("name")
			if table_name == "Mensaplan":
				fill_meal_table(t, days)	
				self.msg("Schreibe Mensaplan in Tabelle 'Mensaplan'")
			
			if table_name.startswith("Sudoku"):
				s = MySudoku()
				fill_sudoku_table(t, s.sudoku)
				self.msg("Schreibe Sudoku in Tabelle '%s'" % table_name)
		
		odt_doc.save(str(self.filename))
		self.msg("Fertig! Datei in '%s' gespeichert" % self.filename)
		self.saveButton.configure(state = NORMAL)
		self.msg("Starte OpenOffice")
		if sys.platform == 'win32':
			os.startfile(self.filename)
		elif sys.platform == 'darwin':
			command = ['open',]
		else:
			command = ['xdg-open',]
		command.append(self.filename)
		subprocess.call(command)

if __name__ == "__main__":
	app = Main()                    
	app.master.title("Mensaplan erzeugen") 
	#app.master.wm_iconbitmap(join(appDir, 'gui', 'icon.png'))
	app.mainloop()    
