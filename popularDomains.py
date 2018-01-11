#!/usr/bin/python
''' Python script to read in the Cisco Umbrella Top 1M list and check against a file containing domains (1 domain per line)
    python popularDomains.py
    __author__ = James Condon
'''

import csv

# csv from http://s3-us-west-1.amazonaws.com/umbrella-static/index.html
umbrella_fname = "top-1m.csv"

# txt file containing the domains to check against
domain_fname = "domain_examples.txt"

print "Loading Cisco Umbrella Top 1M List..."
with open(umbrella_fname, 'rb') as f:
    reader = csv.reader(f)
    top_1m = map(tuple,reader)

print "Loading Domain List..."
with open(domain_fname) as f:
    domains = f.readlines()

domains = [x.strip() for x in domains]

found_domains = []
not_found_domains = []

print "Checking Domains..."
for domain in domains:
	found = False
	for ranking in top_1m:
		if domain == ranking[1]:
			found_domains.append(ranking)
			found = True
			break
	if found == False:
		not_found_domains.append(domain)

print "*** Domains Not Found in Top 1 Million ***"
for entry in not_found_domains:
	print entry

print "\n*** Domains Found in Top 1 Million ***\nRank - Domain"
for entry in sorted(found_domains, key=lambda tup: int(tup[0])):
	print "%s - %s" % (entry[0],entry[1])
