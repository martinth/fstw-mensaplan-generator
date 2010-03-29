# -*- coding: utf-8 -*-

import urllib2
import re
from datetime import date
from time import strptime
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
from decimal import Decimal
from odf import table, text
from copy import deepcopy
from collections import defaultdict
from itertools import count, izip

import logging
log = logging.getLogger('mensaplan.parser')

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

class MensaplanParser:

	def __init__(self, raw_data):
		try:
			self.raw_table = BeautifulStoneSoup(BeautifulSoup(raw_data).html.body.table.prettify(),
										    convertEntities = BeautifulStoneSoup.HTML_ENTITIES)
		except AttributeError:
			# kann auftreten wenn die zurückgegebene seite nicht so aussschaut wie erwartet
			msg = "Fehler beim vorverarbeiten der Daten. Vielleicht hat der Server einen Fehler zurückgegeben."
			log.error(msg + "\nAusgabe des Servers:\n" + raw_data)
			raise ParserException(msg)

	def _pre_sanitize(self):
		'''Räumt die rohe HTML-Seite ein wenig auf'''
		# aufraeumen 1: die ueberschriften entfernen (ersten beiden trs)
		header_rows = self.raw_table.findAll("tr")[0:2]
		[row.extract() for row in header_rows]

		# aufraeuman 2: werbung weg
		advertise_tds = self.raw_table.findAll("td", attrs = {"colspan": "6"})
		[td.parent.extract() for td in advertise_tds]
		log.debug("Vorverarbeitung erfolgreich")


	def extract(self):
		'''Extrahiert die Daten und gibt eine Liste von Day-Objekten zurück'''

		self._pre_sanitize()
		data_trs = self.raw_table.findAll("tr")
		days = []

		def cleanup(instr):
			'''Räumt Strings ein bischen auf'''
			s = re.sub('\s{2,}', ' ', instr)
			s = re.sub('- ', '-', s)
			s = s.strip()
			return s

		# durch die verbleibenden trs wird in dreierschritten gelaufen, denn ein tag
		# besteht aus je drei trs
		for idx in range(0, 15, 3):
			try:
				raw_caf = data_trs[idx]
				raw_meals = data_trs[idx + 1]
				raw_prices = data_trs[idx + 2]

				# Datum des Tages steht auch im ersten tr (bloed geschachtelt)
				date_str = cleanup(' '.join(raw_caf.td.findAll(text = True)))

				# date_str hat so ein formatformat "Fr 30.10.", daher schneiden wir 
				# erst den tag raus und wandeln es dann um
				date_str = date_str.split()[-1]
				date_str = "%s%s" % (date_str, date.today().year)
				dt = strptime(date_str, "%d.%m.%Y")
				date_obj = date(dt[0], dt[1], dt[2])

				day = Day(date_obj)

				# das Cafeteria Spezial ist das letzte <span> mit "special" class
				cafe = raw_caf.findAll("span", attrs = {"class": "special"})[-1].string
				cafe = cleanup(cafe).strip("-")
				#print cafe

				day.meals[Meal.CAF] = Meal(Meal.CAF, cafe)

				# die gerichte des tages stehen in eizelnen tds
				meals = []
				for td in raw_meals.findAll("td"):
					# in den tds sind u.U. mehre text-nodes, daher werden diese entweder 
					# zusammen gefasst, oder, falls nur eine vorhanden ist, diese genommen
					raw_meal = td.findAll(text = True)
					raw_meal = ' '.join(raw_meal)
					raw_meal = cleanup(raw_meal)
					raw_meal = re.sub('-[SRA]-$', '', raw_meal)
					meals.append(raw_meal)

				prices = []
				for td in raw_prices.findAll("td"):
					raw_price = td.findAll(text = True)
					raw_price = ' '.join(raw_price)
					raw_price = cleanup(raw_price)
					matches = [Decimal(m.replace(',','.')) for m in re.findall('\d+,\d+', raw_price)]
					try:
						stud_price = matches[0]
					except IndexError:
						stud_price = None
					prices.append(stud_price)

				# weil wir die sachen in umgekehrter reihenfolge in der liste haben, drehen
				# wir beide listen um
				meals.reverse()
				prices.reverse()

				# der reihe nach (wie auf der homepage) aus den listen ziehen und in objekte stopfen
				day.meals[Meal.E] = Meal(Meal.E, meals.pop(), prices.pop())      # eintopf
				day.meals[Meal.H1] = Meal(Meal.H1, meals.pop(), prices.pop())     # hautpgericht 1
				day.meals[Meal.H2] = Meal(Meal.H2, meals.pop(), prices.pop())     # hautpgereicht 2
				day.meals[Meal.VEG] = Meal(Meal.VEG, meals.pop(), prices.pop())    # wegetarisch
				day.meals[Meal.B] = Meal(Meal.B, meals.pop(), None)              # beilagen (ohne preis)

				log.debug("Tag '%s' gelesen" % day)

			except IndexError:
				# kann auftreten, wenn der tag aus irgendeinem grund der mansplan 
				# weniger spalten enthält als eigentlich da sein sollten
				day.meals = None
				print "FEHLER: TAG '%s' KONNTE NCHT EXTRAHIERT WERDEN - MANUELL EINGEBEN" % day
			# zuletzt den tag samt gerichten abspeichern
			finally:
				days.append(day)

		return days

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
		cell_replace_text(cells[0], day.date.strftime("%A %d.%m.%Y"))
		# restlichen Zellen in reihenfolge
		format_meal_cell(cells[1], day.meals[Meal.E])
		format_meal_cell(cells[2], day.meals[Meal.H1])
		format_meal_cell(cells[3], day.meals[Meal.H2])
		format_meal_cell(cells[4], day.meals[Meal.VEG])
		format_meal_cell(cells[5], day.meals[Meal.B])
		
