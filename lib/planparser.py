#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2010 Martin Thurau <martin.thurau@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import urllib2
import re
from datetime import date, timedelta
from time import strptime
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
from decimal import Decimal
from odf import table, text
from copy import deepcopy
from collections import defaultdict
from itertools import count, izip

import logging
log = logging.getLogger('mensaplan.parser')

# wochentag um von korrektem locale unabhängig zu sein
WEEKDAYS = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")

class Meal:
	'''Wrapper für eine Gericht. Enthält Name des Gerichtes, Typ und Preis (wenn vorhanden)
	
	Felder:
		type		Typ des Gerichtes (siehe Konstanten)
		meal		Name des Gerichts
		price		Preis des Gereicht (None wenn kein Preis verfügbar)
		
	Konstanten:
		E			"Eintopf"
		VEG			"Vegetarisch"
		H1			"Hauptgericht 1"
		H2			"Hautpgericht 2"
		B			"Beilagen"
		CAF			"Cafeteria" '''

	E = "Eintopf"
	VEG = "Vegetarisch"
	H1 = "Hauptgericht 1"
	H2 = "Hauptgericht 2"
	B = "Beilagen"
	CAF = "Cafeteria"

	def __init__(self, type, meal = None, price = None):
		self.type = type
		self.meal = meal
		self.price = price

	def __str__(self):
		if self.price:
			return unicode("%s: %s (%s)" % (self.type, self.meal, self.price)).encode("utf-8")
		else:
			return unicode("%s: %s" % (self.type, self.meal)).encode("utf-8")


class Day:
	'''Wrapper für einen Tag
	
	Felder:
		data		ein datetime.date Objekt für den entsprechenden tag
		meals		eine liste mit Meal-Objekten für den Tag'''

	def __init__(self, date):
		self.date = date
		self.meals = defaultdict()

	def __str__(self):
		return u"%s" % self.date.strftime("%a %d.%m.%Y")
	
	

class ParserException(Exception):
	pass

class MealfillerException(Exception):
	pass

def fill_meal_table(meals_table, days):
	'''Füllt eine Tabelle in einem OpenDocument ODT Dokument mit dem Mensaplan

	Parameter:
		meals_table		die Tabelle die gefüllt werden soll
		days			die Tage mit den Gerichten

	Exceptions:		
		MealfillerException		wenn das gegebene Dokument fehlerhaft ist

	Links:
		odfpy			http://opendocumentfellowship.com/projects/odfpy
	'''

	def cell_replace_text(cell, new_text):
		'''Hilfsmethode zum ersetzen einer Textzelle.
		Ersetzt den Inhalt einer Tabellenzelle mit neuem Text, behält dabei aber
		alle formatierenungen bei'''
		# altes textelement der zelle sichern
		old_content = cell.firstChild
		
		# neues textelement mit selbem style erzeugen
		new_content = text.P(text=new_text)
		new_content.attributes = deepcopy(old_content.attributes)
		
		# element ersetzen
		cell.removeChild(old_content)
		cell.addElement(new_content)

	def format_meal_cell(cell, meal):
		'''Hilfsmethode zum formatieren einer Zelle mit einem Gericht.
		Sofern das Gericht eine Beilage ist, wird kein Preis ausgegeben. 
		Wenn es ein normales Gericht ist, wird der Preis angegeben, und wenn dieser
		nicht vorhanden ist, wir der Text "Mensatipp" ausgeben'''
		cell_replace_text(cell, meal.meal)

		spacer = text.P()
		spacer.attributes = cell.firstChild.attributes
		cell.addElement(spacer)
		if meal.type == Meal.B:
			# beilagen bekommen keinen preis
			pass
		else:
			if meal.price and meal.meal:
				price_p = text.P(text=u"%s€" % str(meal.price).replace('.',','))
				price_p.attributes = cell.firstChild.attributes
			elif meal.meal:
				price_p = text.P(text=u"Mensatipp")
				price_p.attributes = {u'text:style-name': u'bold'}
			else:
				price_p = text.P(text=u"")
				price_p.attributes = cell.firstChild.attributes

			#print cell.firstChild.attributes
			cell.addElement(price_p)
	
	rows = meals_table.getElementsByType(table.TableRow)

	# beim durchlaufen lassen wir die erste zeile weg (Überschriften)
	for day, row in izip(days, rows[1:]):
		if day.meals == None:
			# wenn meals None ist, dann ist beim extrahieren des tages was schiefgegangen
			continue

		cells = row.getElementsByType(table.TableCell)

		# erste zelle ist datum
		date_str = WEEKDAYS[day.date.weekday()] + " " + day.date.strftime("%d.%m.%Y")
		cell_replace_text(cells[0], date_str)
		# restlichen Zellen in reihenfolge
		format_meal_cell(cells[1], day.meals[Meal.E])
		format_meal_cell(cells[2], day.meals[Meal.H1])
		format_meal_cell(cells[3], day.meals[Meal.H2])
		format_meal_cell(cells[4], day.meals[Meal.VEG])
		format_meal_cell(cells[5], day.meals[Meal.B])
		

URI = '''http://www.uni-kiel.de/stwsh/seiten_essen/plan_mensa_luebeck.html'''
from urllib import urlopen
import sys
from itertools import izip, count

raw_data = urlopen(URI).read()

class MensaplanParser:

	def __init__(self, raw_data):
		try:
			self.raw_table = BeautifulStoneSoup(BeautifulSoup(raw_data).find(id="essen").prettify(),
												convertEntities = BeautifulStoneSoup.HTML_ENTITIES)
		except AttributeError:
			# kann auftreten wenn die zurückgegebene seite nicht so aussschaut wie erwartet
			msg = "Fehler beim vorverarbeiten der Daten. Vielleicht hat der Server einen Fehler zurückgegeben."
			log.error(msg + "\nAusgabe des Servers:\n" + raw_data)
			raise ParserException(msg)

	def extract(self):
		'''Extrahiert die Daten und gibt eine Liste von Day-Objekten zurück'''

		def cleanString(node):
			"""Extrahiert den Text aus einer gegebene BeautifulSoup-Node und räumt ihn auf"""
			s = ' '.join(node.findAll(text = True))
			s = re.sub('\s{2,}', ' ', s)
			s = re.sub('- ', '-', s).strip()
			s = re.sub('-[SR/VA]+-$', '', s).strip()
			s = re.sub('\(\d\)$', '', s).strip()
			return s

		def priceFromRaw(rawPrice):
			"""Extrahiert den ersten Preis aus einem String und gibt ihn als Decimal zurück"""
			matches = [Decimal(m.replace(',','.')) for m in re.findall('\d+,\d+', rawPrice)]
			try:
				return matches[0]
			except IndexError:
				return None

		# alle TDs mit "schrift_gerichte" als Klasse enthalten die nötigen Daten
		cells = self.raw_table.findAll('td', {"class": "schrift_gerichte"})
		cells = [cleanString(node) for node in cells] 

		# days enthält später eine Liste von Day-Objekten
		days = []

		# extrahieren des Anfangsdatums der Woche aus dem HTML
		headerText = cleanString(self.raw_table.find("td", {"colspan": "5"}))
		dayMonthStr = re.search("(\d+\.\d+\.)", headerText).groups()[0]
		dateStr = "%s%s" % (dayMonthStr, date.today().year)
		dt = strptime(dateStr, "%d.%m.%Y")
		startDate = date(dt[0], dt[1], dt[2])

		# Füllen von days mit noch leeren Day-Objekten
		for dayString, offset in izip(WEEKDAYS[0:5], count()):
			day = Day(startDate + timedelta(days=offset))
			days.append(day)

		# die Zellen für die Wokstation werden entfernt, da sie uns nicht interessieren
		del(cells[40:50])
		# die Cafetaria hat keine Preisangaben, deswegen fügen wir einen Dummystring ein
		cells += ['Kein Preis']*5

		# für jeden Gericht-Type holen wir uns 10 Felder, wobei die ersten 5 immer den Namen des Gerichts
		# beinhalten und die letzten 5 den Preis
		for idx, mealType in izip(range(0,60,10), (Meal.E, Meal.H1, Meal.VEG, Meal.H2, Meal.B, Meal.CAF)):

			mealsForType = cells[idx:idx+10]
			mealTexts = mealsForType[0:5]
			rawPrices = mealsForType[5:]

			# die Gerichte werden in die jeweiligen Day-Objekte eingefügt
			for mealText, rawPrice, dayObj in izip(mealTexts, rawPrices, days):
				price = priceFromRaw(rawPrice) 
				dayObj.meals[mealType] = Meal(mealType, mealText, price)


		return days
				
