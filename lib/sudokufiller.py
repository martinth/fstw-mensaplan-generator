# -*- coding: utf-8 -*-
# Copyright (c) 2010 Martin Thurau <martin.thurau@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from copy import deepcopy
from hashlib import md5
from odf import table, text
from sudoku import Sudoku, Board

tmp = None

class SudokufillerException(Exception):
	pass

class SudokuFiller:
	'''Füllt eine Tabelle in einem  OpenDocument ODT Dokument mit einem Sudoku.
	Die Klasse verwendet dazu odfpy und einen teil von pythonsudoku.

	Links:
		odfpy						http://opendocumentfellowship.com/projects/odfpy
		pythonsudoku		http://pythonsudoku.sourceforge.net/'''
	
	def __init__(self, doc, table_name="Sudoku"):
		'''Erzeugt ein neue SudokuFiller Objekt mit einen gegeben ODT-Dokument.

		Parameter:
			doc						das ODT Dokument das gefüllt wird
			table_name		(optional) der name der Tabelle die gefüllt werden soll'''

		self.doc = doc
		self.table_name = table_name

	def fill(self, numbers):
		'''Füllt das im Konstruktor gegebene odfpy Dokument mit dem gegebene Sudoku.

		Parameter:
			numbers			eine Liste mit 9 Listen mit je 9 Zahlen (reihen und spalten) 

		Rückgabe:			das gefüllt Dokument
		
		Exceptions:		
			SudokufillerException		wenn das gegebene Dokument fehlerhaft ist'''

		# die richtig tabelle suchen und exception werfen, wenn nicht gefunden
		sudoku_table = None
		for t in self.doc.getElementsByType(table.Table):
			if t.getAttribute("name") == self.table_name:
				sudoku_table = t
				break
		if not sudoku_table:
			raise SudokufillerException(
				"Das Dokument muss eine Tabelle namens '%s' enthalten" % self.table_name)

		# die tabelle muss 9 zeilen haben
		rows = sudoku_table.getElementsByType(table.TableRow)
		if len(rows) != 9:
			raise SudokufillerException("Tabelle '%s' hat nicht 9 Zeilen" % 
				self.table_name)

		row_idx = 0
		for row in rows:
			cells = row.getElementsByType(table.TableCell)

			# jede zeile soll 9 zellen haben
			if len(cells) != 9:
				raise SudokufillerException("Zeile %d hat nicht 9 Zellen" % row_idx)
			
			col_idx = 0
			for cell in cells:
				
				# altes textelement der zelle sichern
				old_content = cell.firstChild
				
				# neues textelement mit selbem style erzeugen
				new_content = text.P(text=numbers[row_idx][col_idx])
				new_content.attributes = deepcopy(old_content.attributes)
				
				# element ersetzen
				cell.removeChild(old_content)
				cell.addElement(new_content)
			
				col_idx += 1
			row_idx += 1

		return self.doc

class MySudoku(object):
	'''Erzeugt ein zufälliges Sudoku samt Lösung'''

	def __init__(self):
		# sudoku erzeugen
		sudoku = Sudoku(Board(3))
		sudoku.create()
		board = sudoku.to_board()
		self.sudoku = deepcopy(board.numbers)

		# lösung erzeugen
		solved = Sudoku(board)
		solved.solve()
		self.solution = deepcopy(solved.to_board().numbers)

		# hash des boards berechnen
		m = md5()
		for row in self.sudoku:
				for num in row:
						m.update(str(num))
		self.hash = m.hexdigest()
				

def fill_sudoku_table(sudoku_table, numbers):
	'''Füllt eine Tabelle in einem OpenDocument ODT Dokument mit einem Sudoku.

	Parameter:
			sudoku_table		die Tabelle die gefüllt werden soll
			numbers			eine Liste mit 9 Listen mit je 9 Zahlen (reihen und spalten)

		Exceptions:		
			SudokufillerException		wenn das gegebene Dokument fehlerhaft ist

	Links:
		odfpy						http://opendocumentfellowship.com/projects/odfpy
		pythonsudoku		http://pythonsudoku.sourceforge.net/
	'''

	# die tabelle muss 9 zeilen haben
	rows = sudoku_table.getElementsByType(table.TableRow)
	if len(rows) != 9:
		raise SudokufillerException("Tabelle '%s' hat nicht 9 Zeilen" % 
			self.table_name)

	row_idx = 0
	for row in rows:
		cells = row.getElementsByType(table.TableCell)

		# jede zeile soll 9 zellen haben
		if len(cells) != 9:
			raise SudokufillerException("Zeile %d hat nicht 9 Zellen" % row_idx)
		
		col_idx = 0
		for cell in cells:
			
			# altes textelement der zelle sichern
			old_content = cell.firstChild
			
			# neues textelement mit selbem style erzeugen
			new_content = text.P(text=numbers[row_idx][col_idx])
			new_content.attributes = deepcopy(old_content.attributes)
			
			# element ersetzen
			cell.removeChild(old_content)
			cell.addElement(new_content)
		
			col_idx += 1
		row_idx += 1
