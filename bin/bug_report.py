#!/usr/local/bin/python

import json
import urllib2
import urllib
import getpass
import sys
import os
import getopt
import pickle
import re

username = None
password = None
base = 'http://dqa02.vivotek.tw'

severity_abbr_map = {
	'normal': 'NRML',
	'major': 'MJR',
	'minor': 'MNR',
	'suggestion': 'SGST',
	'unconfirmed': 'UNCM',
	'critical': 'CRIT',
}

plat_map = {
	'mozart325': ['Mozart325'],
	'mozart330': ['Mozart330 (V2)'],
	'mozart330o': ['Mozart330 (V2)'],
	'mozart330s': ['Mozart330s (V3)'],
	'mozart365': ['Mozart365'],
	'mozart370': ['Mozart370'],
	'mozart380': ['Mozart380'],
	'mozart385s': ['Mozart385s (V3)'],
	'dm365': ['Ti-DM365', 'Ti-DM368', 'Ti-DM369'],
	'dm385': ['Ti-DM385'],
	'xarina': ['Xarina'],
}

new_bugs = []
fixed_bugs = []
invalid_bugs = []
worksforme_bugs = []
suggestion_bugs = []
fixlater_bugs = []
wontfix_bugs = []
outfile = 'bug_summary.txt'
space_count = 0
cache = {}
cache_path = os.path.join(os.getenv('HOME'), '.hathor', 'dqa_cache')
cache_updated = False

def help_msg():
	print "Usage: bug_report.py [-n <number of space>] [output file]"

def auth_setup():
	global username, password
	username = raw_input('Username: ')
	password = getpass.getpass()

	auth = urllib2.HTTPBasicAuthHandler()
	auth.add_password('Redmine API', base, username, password)
	opener = urllib2.build_opener(auth)
	urllib2.install_opener(opener)

def get_obj(rel_path):
	url = '%s/%s' % (base, rel_path)
	r = urllib2.urlopen(url)

	return json.loads(r.read())

def get_custom_field(issue, id):
	fields = issue['custom_fields']

	for f in fields:
		if f['id'] == id:
			return f

	return None

def get_bug_id(issue):
	return issue['id']

def get_priority(issue):
	tmp = issue['priority']['name']
	if tmp == 'Unconfirmed':
		tmp = 'Un'

	return tmp

def get_severity(issue):
	tmp = get_custom_field(issue, 1)

	if tmp:
		return tmp['value'].lower()
	else:
		return None

def get_status(issue):
	return issue['status']['name']

def get_abbr(severity):
	return severity_abbr_map[severity]
#	return severity

def get_assignee(issue):
	if issue.has_key('assigned_to'):
		return issue['assigned_to']['name']

	return '<none>'

def issue_compare(x, y):
	if x['id'] > y['id']:
		return 1
	elif x['id'] < y['id']:
		return -1
	else:
		return 0

def classify_issues(issues):
	issues.sort(issue_compare)
	bugid_max_width = len(str(issues[-1]['id']))

	for i in issues:
		bugid = i['id']
		desc = i['subject']
		prio = get_priority(i)
		severity = get_severity(i)
		status = get_status(i)
		assignee = get_assignee(i)

		bug_str = u'[{0:{width}d}][{1:s}][{2:4s}] {3:15s} {4:s}\n'.format(bugid, prio, get_abbr(severity), assignee, desc, width = bugid_max_width)
#		bug_str = '%s   %s  %-10s         %-20s %s\n' % (bugid, prio, get_abbr(severity), assignee, desc)

		if status == 'NEW':
			if severity == 'suggestion':
				suggestion_bugs.append(bug_str)
			else:
				new_bugs.append(bug_str)
		elif status == 'FIXED':
			fixed_bugs.append(bug_str)
		elif status == 'INVALID':
			invalid_bugs.append(bug_str)
		elif status == 'WORK':
			worksforme_bugs.append(bug_str)
		elif status == 'WONTFIX':
			wontfix_bugs.append(bug_str)
		elif status == 'LATER':
			fixlater_bugs.append(bug_str)
		elif status == 'ASSIGNED':
			if severity == 'suggestion':
				suggestion_bugs.append(bug_str)
			else:
				new_bugs.append(bug_str)
		elif status == 'REOPENED':
			if severity == 'suggestion':
				suggestion_bugs.append(bug_str)
			else:
				new_bugs.append(bug_str)
		else:
			pass

def get_subproj(parent_id):
	proj_list = []
	data = {}
	obj = get_obj('/projects.json')

	total = obj['total_count']
	limit = obj['limit']
	offset = 0

	while total > 0:
		for tmp in obj['projects']:
			if tmp.has_key('parent') and tmp['parent']['id'] == parent_id:
				proj_list.append(tmp)

		total -= limit
		offset += limit
		data['offset'] = offset
		obj = get_obj('/projects.json?%s' % urllib.urlencode(data))

	return proj_list

def get_dqa_proj():
	proj = read_cache('dqa_proj')
	if proj:
		return proj

	proj = get_obj('/projects/dqa-test-1-bug.json')
	if proj:
		write_cache('dqa_proj', proj)

	return proj

def ask_user(name):
	while True:
		print 'I found a model "%s" in Redmine. Is it correct? [Y/n]' % name,
		ans = raw_input()

		if ans.lower() == 'y' or ans == '':
			print 'Ok. I will cache your choice for next time.'
			return True
		elif ans.lower() == 'n':
			return False
		else:
			print 'Not a valid answer.'

	return False

def matching(product, model):
	if product.has_key('cached_guessing') and product['cached_guessing'] == model:
		return True

	name = product['name']
	# Try to match the whole string
	if name == model:
		return True

	# Try to match the first part (eg. IPXXXX)
	first = model.split('-')[0]
	if re.match(first, name):
		return True

	# Try to match the saperated type & number part (eg. FD8163/8363)
	mtype = first[:2]
	number = first[2:]
	if re.search(mtype, name) and re.search(number, name):
		if ask_user(name):
			product['cached_guessing'] = model
			return True

	# The followings are guessing
	# Requisite: the model type must be matched
	if re.match(mtype, name):
		# Guessing 1: try to match the last two digits of the model name
		m = re.match('.*(\d\d).*', name)
		if m:
			last_digits = m.group(1)
			if number.find(last_digits) > 0:
				if ask_user(name):
					product['cached_guessing'] = model
					return True

		# Guessing 2: try to match the 'X' part in model name (eg. SD83X3)
		m = re.match('.*([xX]\d).*', name)
		if m:
			if ask_user(name):
				product['cached_guessing'] = model
				return True

	return False
		

def get_product_proj(plat_id, product):
	p = read_cache('product_proj')
	if p and matching(p, product):
		return p

	product_list = get_subproj(plat_id)
	for p in product_list:
		if matching(p, product):
			write_cache('product_proj', p)
			return p

	return None


def get_platform_proj(vendor_id, platform):
	p = read_cache('platform_proj')
	if p and p['name'] == platform:
		return p

	platform_list = get_subproj(vendor_id)
	for p in platform_list:
		if p['name'] == platform:
			write_cache('platform_proj', p)
			return p

	return None

def get_vendor_proj(proj_id, vendor):
	v = read_cache('vendor_proj')
	if v and v['name'] == vendor:
		return v

	vendor_list = get_subproj(proj_id)
	for v in vendor_list:
		if v['name'] == vendor:
			write_cache('vendor_proj', v)
			return v

	return None

def get_issues(proj_id):
	data = {}
	issues = []

	data['project_id'] = proj_id
	obj = get_obj('/issues.json?%s' % urllib.urlencode(data))

	total = obj['total_count']
	limit = obj['limit']
	offset = 0

	while total > 0:
		issues += obj['issues']

		total -= limit
		offset += limit
		data['offset'] = offset
		obj = get_obj('/issues.json?%s' % urllib.urlencode(data))

	return issues

def print_bugs(fh, bugs):
	sz = len(bugs)
	space_comp = 0

	while sz > 0:
		space_comp += 1
		sz /= 10

	mod = 10
	if bugs:
		for i in xrange(len(bugs)):
			if (i + 1) % mod == 0:
				space_comp -= 1
				mod *= 10

			total_space = space_count + space_comp
			fh.write('%*s%d) %s' % (total_space, ' ', i + 1, bugs[i].encode('utf-8')))
	else:
		fh.write('<NONE>\n')

def output():
	try:
		print 'Output %s ...' % outfile
		outh = open(outfile, 'w')
	except IOError, e:
		print e
		sys.exit(1)

	outh.write('Fixed bugs:\n')
	print_bugs(outh, fixed_bugs)

	outh.write('\n')

	outh.write('Unfixed bugs:\n')
	print_bugs(outh, new_bugs)

	outh.write('\n')

	outh.write('Invalid bugs:\n')
	print_bugs(outh, invalid_bugs)

	outh.write('\n')

	outh.write('Worksforme bugs:\n')
	print_bugs(outh, worksforme_bugs)

	outh.write('\n')

	outh.write('Suggestion bugs:\n')
	print_bugs(outh, suggestion_bugs)

	outh.write('\n')

	outh.write("Won't fix bugs:\n")
	print_bugs(outh, wontfix_bugs)

	outh.write('\n')

	outh.write('Fix later bugs:\n')
	print_bugs(outh, fixlater_bugs)

def save_cache():
	if not cache_updated:
		return

	try:
		h = open(cache_path, 'w')
		pickle.dump(cache, h)
		h.close()
	except IOError as e:
		print str(e)
	except pickle.PicklingError as e:
		print str(e)

def load_cache():
	global cache
	try:
		h = open(cache_path)
		cache = pickle.load(h)
		h.close()
	except IOError as e:
		print '%s not found. Will try to create one before exiting.' % cache_path
	except pickle.UnpicklingError as e:
		print str(e)

def read_cache(key):
	if cache.has_key(key):
		return cache[key]

	return None

def write_cache(key, obj):
	global cache_updated
	cache[key] = obj
	cache_updated = True

def gen_bug_report(model, vendor, plat):
	proj = get_dqa_proj()
#	print 'Project id: %s' % proj['project']['id']
#	print 'Project name: %s' % proj['project']['name'] 

	vendor_proj = get_vendor_proj(proj['project']['id'], vendor)

#	print 'sub proj name: %s' % vendor_proj['name']
#	print 'sub proj identifier: %s' % vendor_proj['identifier']
#	print 'sub proj id: %s' % vendor_proj['id']

	if vendor_proj['name'] != 'VVTK':
		product_proj = get_product_proj(vendor_proj['id'], model)

	else:
		platform_proj = get_platform_proj(vendor_proj['id'], plat)

#		print 'platform name: %s' % platform_proj['name']
#		print 'platform identifier: %s' % platform_proj['identifier']
#		print 'platform id: %s' % platform_proj['id']

		product_proj = get_product_proj(platform_proj['id'], model)

	if product_proj != None:
		print 'product name: %s' % product_proj['name']
#	print 'product identifier: %s' % product_proj['identifier']
		print 'product id: %s' % product_proj['id']

		issues = get_issues(product_proj['id'])
		classify_issues(issues)

		output()
		print 'Total %d bugs' % len(issues)

		return True
	else:
		print 'Project not find.'
		return False

def get_plat(env):
	if plat_map.has_key(env):
		return plat_map[env]

	return None

def get_info_from_envs():
	fmver = os.getenv('PRODUCTVER')
	(model, vendor, ver) = fmver.split('-')

	plat = get_plat(os.getenv('OSEXTENSION'))

	tmp = []
	for p in plat:
		tmp.append(('%s-%s' % (model, vendor), vendor, p))

	return tmp

def check_envs():
	if not os.getenv('PRODUCTVER') or not os.getenv('OSEXTENSION'):
		return False

	return True

if __name__ == '__main__':
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'n:h')
	except getopt.GetoptError, e:
		print str(e)
		help_msg()
		sys.exit(1)
	
	for opt, val in opts:
		if opt == '-n':
			space_count = int(val)
		elif opt == '-h':
			help_msg()
			sys.exit(0)

	if len(args) > 0:
		outfile = args[0]

	if not check_envs():
		print 'Have you source the project devel file?'
		sys.exit(1)

	infos = get_info_from_envs()
#	print '%s:%s:%s' % (model, vendor, plat)

#	auth_setup()
	load_cache()
	for i in infos:
		(model, vendor, plat) = i[:]
		if gen_bug_report(model, vendor, plat):
			save_cache()
			break

