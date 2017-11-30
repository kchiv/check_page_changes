import sqlite3
from page_class import Page

from urllib2 import urlopen
from bs4 import BeautifulSoup
import sys
import os.path
import datetime

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

import config

conn = sqlite3.connect('ll_meta_elements.db')

c = conn.cursor()

# creates new table

# c.execute('''CREATE TABLE meta_elements (
# 				date_time text,
# 				url text,
# 				status_code integer,
# 				title text,
# 				meta_description text,
# 				canonical text,
# 				canonical_match integer,
# 				header_one text,
# 				header_two text
# 	)''')

def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d


def scrape_url(urls):
	# function for scraping page elements

	# gets current year, month, day
	time_now = datetime.datetime.now()
	standard_time = time_now.strftime("%Y-%m-%d")

	# strips /n from URL
	url = urls.rstrip()
	# handles url opening, closing
	uClient = urlopen(url)
	page_html = uClient.read()
	uClient.close()
	# gets server status code - need to update
	server_status = uClient.getcode()
	# parse page
	page_soup = BeautifulSoup(page_html, 'html.parser')
	# title parse
	title_parse = page_soup.find('title').text
	# meta description parse
	meta_description_tag = page_soup.find('meta', {'name':'description'})
	meta_description = meta_description_tag['content']
	# rel=canonical parse
	canonical_tag = page_soup.find('link', {'rel':'canonical'})
	canonical = canonical_tag['href']
	# h1 parse
	header_one = page_soup.find('h1').text.strip()
	# h2 parse
	header_two = page_soup.find('h2').text.strip()

	# conditional that checks if canonical matches
	if canonical != url:
		canonical_match = 0
	else:
		canonical_match = 1

	# return dictionary with parsed elements
	return {'standard_time': standard_time,
			'url': url,
			'server_status': server_status,
			'title_parse': title_parse,
			'meta_description': meta_description,
			'canonical': canonical,
			'canonical_match': canonical_match,
			'header_one': header_one,
			'header_two': header_two}


def second_latest(urls):
	# strips /n from URL
	url = urls.rstrip()
	conn.row_factory = dict_factory
	cur = conn.cursor()
	cur.execute('''SELECT * FROM 
				(SELECT * FROM meta_elements
				WHERE url = ?
				ORDER BY date_time DESC LIMIT 2) AS comp_url
				ORDER BY date_time LIMIT 1''', (url,))
	return cur.fetchone()


fdir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(fdir,'urllist.txt'), 'r') as urllist:
	body_str = ''
	for url in urllist:
		# initiates scraper function
		scraped_page = scrape_url(url)
		# creates object from scraped data
		new_page = Page(scraped_page['standard_time'], 
						scraped_page['url'],
						scraped_page['server_status'],
						scraped_page['title_parse'],
						scraped_page['meta_description'],
						scraped_page['canonical'],
						scraped_page['canonical_match'],
						scraped_page['header_one'],
						scraped_page['header_two'])
		c.execute('''INSERT INTO meta_elements VALUES (:time_stamp,
													:url,
													:status_code,
													:title, :meta_desc, :canonical, :canon_match, :h1, :h2)''',
													{'time_stamp': new_page.date,
													'url': new_page.url,
													'status_code': new_page.status_code,
													'title': new_page.title,
													'meta_desc': new_page.meta_desc,
													'canonical': new_page.canonical,
													'canon_match': new_page.canon_match,
													'h1': new_page.h1,
													'h2': new_page.h2})
		conn.commit()
		meta_compare = second_latest(url)

		url_str = 'URL: ' + url + '\n'

		body_change = ''

		if meta_compare['status_code'] != new_page.status_code:
			body_change += 'Server status code changed from: %s to %s \n' % (meta_compare['status_code'], new_page.status_code)
		if meta_compare['title'] != new_page.title:
			body_change += "Title tag changed from: '%s' to '%s' \n" % (meta_compare['title'], new_page.title)
		if meta_compare['meta_description'] != new_page.meta_desc:
			body_change += "Meta description changed from: '%s' to '%s' \n" % (meta_compare['meta_description'], new_page.meta_desc)
		if meta_compare['canonical'] != new_page.canonical:
			body_change += 'Canonical changed from: %s to %s \n' % (meta_compare['canonical'], new_page.canonical)
		if meta_compare['header_one'] != new_page.h1:
			body_change += "H1 changed from: '%s' to '%s' \n" % (meta_compare['header_one'], new_page.h1)
		if meta_compare['header_two'] != new_page.h2:
			body_change += "H2 changed from: '%s' to '%s' \n" % (meta_compare['header_two'], new_page.h2)

		if body_change != '':
			body_str += url_str + body_change + '\n'
conn.close()








# email data
fromaddr = config.from_email
toaddr = config.to_email
msg = MIMEMultipart()
msg['From'] = fromaddr
msg['To'] = toaddr
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(fromaddr, config.email_password)

if body_str != '':
	msg['Subject'] = "PYSCRIPT: An Element Changed"
	body = 'There were changes on the following pages:\n' + body_str
else:
	msg['Subject'] = "PYSCRIPT: No Changes Found"
	body = "There weren't any changes today!"

# send email
msg.attach(MIMEText(body.encode('utf-8'), 'plain', 'utf-8'))
text = msg.as_string()
server.sendmail(fromaddr, toaddr, text)
server.quit()
