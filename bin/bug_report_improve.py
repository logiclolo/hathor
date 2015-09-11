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
from copy import deepcopy
import subprocess

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
	'hi3516a': ['Hisilicon'],
	'rossini388': ['Rossini'],
}

base_platform_entrance = {
	'Rossini': ['Rossini ONE FW', 'VC8101-VVTK'],
        'Hisilicon': ['Hisilicon ONE FW', 'SD9363-EH-VVTK'] 
}

debug = False 

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
tmp_cache = {}
cache_path = os.path.join(os.getenv('HOME'), '.hathor', 'dqa_cache')
cache_updated = False
isonefw = False
g_cache_subproj = []
g_all_matching_products = []
g_cache_issues = [] 

g_total_camera_issue = []
g_parent_pkg = ''
g_previous_release_revision = 0

def help_msg():
	print "Usage: bug_report.py [-n <number of space>] [output file]"

def auth_setup():
	global username, password
        print 'Username:'
	username = raw_input()
	password = getpass.getpass()

	auth = urllib2.HTTPBasicAuthHandler()
	auth.add_password('Redmine API', base, username, password)
	opener = urllib2.build_opener(auth)
	urllib2.install_opener(opener)

	# test validation
	try:
		url = '%s/projects.json' % base
		urllib2.urlopen(url)
	except urllib2.HTTPError, e:
		if e.code == 401:
			print '\nWrong Username/Password. try again.'	
			auth_setup()
		
	except urllib2.URLError, e:
		print e.args
		
def get_obj(rel_path):
	url = '%s/%s' % (base, rel_path)
	if debug:
		print url
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

def match_pkg_version(issue):
	tmp = get_custom_field(issue, 165)

	if tmp:
		if tmp.has_key('value'): 
			if tmp['value'] == os.getenv('PRODUCTVER'):
				return True
			else:
				return False
		else:
			return False
	else:
		return False


def classify_issues(issues):
	issues.sort(issue_compare)
	if len(issues) > 0:
		bugid_max_width = len(str(issues[-1]['id']))

	for i in issues:
		# check 'PKG version for RD fix bug'
		if isonefw and not match_pkg_version(i):
			continue

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
        global g_cache_subproj
	proj_list = []
	data = {}
	if len(g_cache_subproj) > 0 and g_cache_subproj[0]:
		obj = g_cache_subproj[0]
	else:
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
		index = (offset / limit) - 1  
		#print 'index is %s' % index
		if len(g_cache_subproj) > index:
                        #print 'use cache'

                        # do it by copy-by-value!
			obj = deepcopy(g_cache_subproj[index]) 
		else:
                        #print 'real fetch'

			obj = get_obj('/projects.json?%s' % urllib.urlencode(data))
			g_cache_subproj.append(obj)

	return proj_list

def get_dqa_proj():
	proj = read_cache('dqa_proj')
	if proj:
		return proj

	proj = get_obj('/projects/dqa-test-1-bug.json')
	if proj:
		write_cache('dqa_proj', proj)

	return proj

def ask_user(name, model):
	while True:
		if re.search('common', model, re.IGNORECASE):
			print 'I found a model "%s" in Redmine. Onefw project has common bug issue, consider it? [Y/n]' % name
		else:
			print 'I found a model "%s" in Redmine. Is it correct for %s? [Y/n]' % (name, model)
		ans = raw_input()

		if ans.lower() == 'y' or ans == '':
			print 'Ok. I will cache your choice for next time.'
			return True
		elif ans.lower() == 'n':
			return False
		else:
			print 'Not a valid answer.'

	return False

def is_match_already(product):
	if len(g_all_matching_products) > 0:
		for p in g_all_matching_products:
			if product['name'] == p['name']:
				if debug:
					print '\t\t%s is already matched!' % product['name']	
				return True
	return False
def search_onefw_common_project(name, model):
	#if re.search('Hisilicon', model, re.IGNORECASE):
		## ex: 00. Hisilicon Standard Common bug
		#if re.search('common', model, re.IGNORECASE) and re.search(model.split(' ')[1], name, re.IGNORECASE): 
			#return True
	#else:
		#if re.search('common', model, re.IGNORECASE) and re.search('common', name, re.IGNORECASE): 
			#return True

	if re.search(model.split(' ')[0], name, re.IGNORECASE) and re.search('common', model, re.IGNORECASE) and re.search('common', name, re.IGNORECASE): 
		return True

	return False

def matching(product, model):
	if debug:
		print ('############### ready to match {0:s} with {1:s} ###################'.format(model, product['name']))
	if product.has_key('cached_guessing') and product['cached_guessing'] == model:
		return True

	# product had already been matched before
	if is_match_already(product):
		return False

	# product name could be like this 01. IB836B.......
	# remove the number at the beginning
	name = product['name']
	name = re.sub('^[0-9]+\.\s', '', name)
	ori_name = name

	# Try to match 'XX Common bug' 
	if isonefw and search_onefw_common_project(name, model):
		if ask_user(name, model):
			product['cached_guessing'] = model
			return True

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
		if ask_user(name, model):
			product['cached_guessing'] = model
			return True

	# In onefw project, the name would be more complicated. (eg. 01. IB836B/FD8x6B-VVTK series)
        # So we need to fetch the key word
        if isonefw: 
		m = re.search('.*([A-Z][A-Z]\d*[xX].*)-.*', name)
		if m:
			name = m.group(1)

	# The followings are guessing
	# Requisite: the model type must be matched
        if re.match(mtype, name):
		# Guessing 1: try to match the number part except 'x' (eg. FD8x6B)
		m = re.match('.*[A-Z][A-Z]([A-Z0-9]+)[xX]([A-Z0-9]+)', name)
		if m:
			first_part = m.group(1)
			last_part = m.group(2)
                        #print number
                        #print first_part 
                        #print last_part 
			if number.find(first_part) >= 0 and number.find(last_part) >= 0:
				if ask_user(ori_name, model):
					product['cached_guessing'] = model
					return True

		# Guessing 2: try to match the last two digits of the model name
		m = re.match('.*(\d\d).*', name)
		if m:
			last_digits = m.group(1)
			if number.find(last_digits) > 0:
				if ask_user(ori_name, model):
					product['cached_guessing'] = model
					return True


		# Guessing 2: try to match the 'X' part in model name (eg. SD83X3)
		#m = re.match('.*([xX]\d).*', name)
                #print m
		#if m:
			#if ask_user(ori_name):
				#product['cached_guessing'] = model
				#return True

	return False

def sort_list(product_list):
	# make 'XX ONE FW' in the end of the list
        if re.search('ONE FW', product_list[0]['name']):
		return list(reversed(product_list))
	else:
		return product_list
		
def get_onefw_product_proj(plat_id, plat, product):
	if debug:
		print '\nin get_onefw_product_proj'

	if debug:
		print '------------ Match product from cache..... -------------------'
	cache_list = read_cache('onefw_product_proj')
	if cache_list: 
		# Search for "XX ONE FW" model 
		if re.search(plat, cache_list['name']) and re.search('ONE FW', cache_list['name']):
			return cache_list 

	if debug:
		print '------------ Match product from url..... -------------------'
	onefw_product_list = get_subproj(plat_id)
	for p in onefw_product_list:
		# Search for "XX ONE FW" model
		# e.g. "Hisilicon ONE FW" or "Rossini ONE FW"
		if re.search('ONE FW', p['name']):
			write_cache('onefw_product_proj', p) 
			return p

	return None

def is_in_list(products, product):
	if len(products) == 0:
		return False
	for p in products:
		if p['name'] == product['name']:
			return True
	return False

def handle_matching_products(product, source):
	# maintain a matching list to skip the dulplicate product
	global g_all_matching_products
	global cache_updated

	if not is_in_list(g_all_matching_products, product):
		g_all_matching_products.append(product)

		if source == 'url':
			cache_updated = True

	return

def convert_to_list(cache_list):
	# old script save the cache using dictionary type
	# make it list for backward compatible
	if isinstance(cache_list, dict):
		tmp = []
		tmp.append(cache_list)
		return tmp
	return cache_list

def get_product_proj(plat_id, product):
	if debug:
		print '\nin get_product_proj'

	if debug:
		print '------------ Match product from cache..... -------------------'
	cache_list = convert_to_list(read_cache('product_proj'))
	if cache_list:
		for p in cache_list:
			if matching(p, product):
				handle_matching_products(p, 'cache')	
				return p	

	if debug:
		print '------------ Match product from url..... -------------------'
	product_list = get_subproj(plat_id)
	for p in product_list:
		if not has_children(p) and matching(p, product):
			handle_matching_products(p, 'url')	
			return p	

		if isonefw and has_children(p): 
			if debug:
				print 'start finding sub project (recursive)'
			sub_project = get_product_proj(p['id'], product)	
			if sub_project != None:
				return sub_project	

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

def is_issues_already(proj_id):
	for i in g_cache_issues:
		if i == proj_id:
			return True
	return False

def get_issues(proj_id):
	global g_cache_issues
	data = {}
	issues = []

        if is_issues_already(proj_id):
		return None 

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

	g_cache_issues.append(proj_id)
	return issues

def print_bugs(fh, bugs):
	sz = len(bugs)
	space_comp = 0

	while sz > 0:
		space_comp += 1
		sz /= 10

	indent = space_comp
	mod = 10
	if bugs:
		for i in xrange(len(bugs)):
			if (i + 1) % mod == 0:
				space_comp -= 1
				mod *= 10

			total_space = space_count + space_comp

			if isonefw:
				# Indent the sub-line of the string
				# replace the '\n' in the middle of the string with '\n   '
				bugs[i] = re.sub('(.)\n(.)', r'\1\n%*s\2' % (indent + 3, ' '), bugs[i])
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

        if isonefw:
		outh.write('Fixed bugs:\n')
		print_bugs(outh, fixed_bugs)

		outh.write('\n')
	else:
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
                
	if isonefw:
		write_cache('product_proj', g_all_matching_products)
	else:
		write_cache('product_proj', g_all_matching_products[0])

	if debug:
		print 'in save_cache()'
		print cache

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
	global cache_updated, cache 
	cache[key] = obj
	cache_updated = True

def gen_bug_report2():
	global fixed_bugs
	global g_parent_pkg
	
	ret_path = os.getcwd()
	proj_path = os.getenv('PRODUCTDIR')
	os.chdir(proj_path)

	g_parent_pkg = get_parent_pkg()
	get_onefw_proj()
	os.chdir(ret_path)

def get_onefw_proj():

	if not os.getenv('SHARE_BASE'):
		#  one svn repo (eg. Rossini)
		url = get_svn_url('.')
		start = get_latest_rev(url)

		do_scan('.', start, None, 100, 50) 		
	else:
		# multiple svn repos (eg. Hisilicon)
                print 'It\'s going to scan svn repos ... please wait'
		start = get_latest_rev(os.getenv('SHARE_BASE'))

		path = os.path.join(os.getenv('PRODUCTDIR'), 'build', 'settings')
		url = get_svn_url(path)
		do_scan(url, start, None, 100, 50) 		

		if g_previous_release_revision != 0:
			dirs = subprocess.Popen('find -iname ".svn" -type d' , shell=True, stdout = subprocess.PIPE).stdout
			for d in dirs: 
				dirname = os.path.dirname(d)
				dirname_url = get_svn_url(dirname)
				do_scan(dirname_url, start, g_previous_release_revision, 100, 1)	
			

	if len(fixed_bugs) == 0:
		print 'No svn log is fetched. Make sure to follow the svn log format!'

def do_scan(path, start, end, stride, max_count):
		count = 0
		if end == None:
			end = start - stride
		while 1:
			if end > 0:
				p = subprocess.Popen('svn log -r %d:%d %s' % (start, end, path) , shell=True, stdout = subprocess.PIPE).stdout
				ret = scan_svn_log(p)
				if ret:
					return ret	

			start = end - 1
			end = start - stride
			count = count + 1
			if (count >= max_count):
				return ret	

def get_latest_rev(url):
	log = subprocess.Popen('svn info %s' % url , shell=True, stdout = subprocess.PIPE).stdout
	for line in log:
		m = re.match('Last\sChanged\sRev:\s([0-9]+)', line) 
		if m:
			return int(m.group(1))
	return 0 

def get_svn_url(path):
	log = subprocess.Popen('svn info %s' % path , shell=True, stdout = subprocess.PIPE).stdout
	for line in log:
		m = re.match('URL:\s(.+)', line) 
		if m:
			return m.group(1)
	return None 

def find_specific_svn_log(target, aim, first_line):
	# find the previous pkg version commit log and return the stop
	# eg. '========1.1a.a1.1.1=========='
	m = re.search('=+([0-9]+\.[a-z0-9]+\.[a-z0-9]+\.[0-9]+\.[0-9]+)=+', target)
	if m:
		if m.group(1) == g_parent_pkg:
			return 'stop'

		return 'skip'

	# find the specific log format 
	# eg. '[fixed:1.1a.a1.1.2]'
	if first_line == 1 and re.search('\[fixed:[0-9]+\.[a-z0-9]+\.[a-z0-9]+\.[0-9]+\.[0-9]+\]', target):
		return 'continue'

	return 'skip' 

def add_svn_log_to_fixed_bugs(content):
	if len(fixed_bugs) == 0:
		fixed_bugs.append(content)
	else:
		for info in fixed_bugs:
			if content != info:
				fixed_bugs.append(content)	
def scan_svn_log(log):
	global g_previous_release_revision
	
	# fetch last onefw version 
	ver = find_version(os.getenv('PRODUCTVER'))

	content = ''
	first_line = 1 
	for line in log:
		#print repr(line) 

		# type of line is 'str'
		# make it 'unicode' 
		line = line.decode('utf-8')

		if re.match('\n', line):
			continue

		# match split 
		if re.match('------------------------------------------------------------------------+$', line):
			#print 'match split'
			if content != '':
				add_svn_log_to_fixed_bugs(content)
			content = '' 
			first_line = 1 
			continue	

		# match svn log header
		m = re.match('r([0-9]*)\s\|.*\|.*\|.*', line)
		if m:
			#print 'match svn header'
			revision = m.group(1)
			continue

		# time to stop ?
		val = find_specific_svn_log(line, ver, first_line)
		if val == 'skip':
			continue
		elif val == 'stop':
			g_previous_release_revision = int(revision)
			return True

		content = content + line
                first_line = 0

	return False

def find_version(pkgversion):
	m = re.search('[0-9]+\.[a-z0-9]+\.[a-z0-9]+\.[0-9]+\.([0-9]+)', pkgversion)
	if m:
		#print 'version is %s' % m.group(1)
		return m.group(1)

	return None

def gen_bug_report(model, vendor, plat):
	product_proj = []

	proj = get_dqa_proj()
	if debug:
		print 'Project id: %s' % proj['project']['id']
		print 'Project name: %s' % proj['project']['name'] 

	vendor_proj = get_vendor_proj(proj['project']['id'], vendor)
	if debug:
		print 'sub proj name: %s' % vendor_proj['name']
		print 'sub proj identifier: %s' % vendor_proj['identifier']
		print 'sub proj id: %s' % vendor_proj['id']

	if not isonefw:
		if vendor_proj['name'] != 'VVTK':
			product_proj = get_product_proj(vendor_proj['id'], model)
		else:

			platform_proj = get_platform_proj(vendor_proj['id'], plat)

			if debug:
				print 'platform name: %s' % platform_proj['name']
				print 'platform identifier: %s' % platform_proj['identifier']
				print 'platform id: %s' % platform_proj['id']
			product_proj = get_product_proj(platform_proj['id'], model)
	else:
		if vendor_proj['name'] != 'VVTK':
			product_proj = get_product_proj(vendor_proj['id'], model)
		else:

			platform_proj = get_platform_proj(vendor_proj['id'], plat)

			if debug:
				print 'platform name: %s' % platform_proj['name']
				print 'platform identifier: %s' % platform_proj['identifier']
				print 'platform id: %s' % platform_proj['id']

			onefw_product_proj = get_onefw_product_proj(platform_proj['id'], plat, model)

			if has_children(onefw_product_proj):
				if debug:
					print 'onefw product name: %s' % onefw_product_proj['name']
				product_proj = get_product_proj(onefw_product_proj['id'], model)
			else:
				product_proj = onefw_product_proj

	if product_proj != None:
		if debug:
			print 'product name: %s' % product_proj['name']
			print 'product identifier: %s' % product_proj['identifier']
			print 'product id: %s' % product_proj['id']

		issues = get_issues(product_proj['id'])
		#issues = None 
		if issues != None:
			classify_issues(issues)
			if not is_onefw:
				print 'Total %d bugs' % len(issues)
			g_total_camera_issue.append(product_proj['name'])
	else:
		if len(g_all_matching_products) == 0:
			print 'Project not find.'
			return False

		return True

def has_children(product):
	if isinstance(product, dict):
		if product != None:
			product_list = get_subproj(product['id'])
                	if len(product_list) > 0:
				return True
	elif isinstance(product, list):
		if product and len(product) > 0:
			product_list = get_subproj(product[0]['id'])
                	if len(product_list) > 0:
				return True
	return False
	
def get_plat(env):
	if plat_map.has_key(env):
		return plat_map[env]

	return None

def is_onefw():
	global isonefw
	global cache_path 
        version = os.getenv('PRODUCTVER') 
	if re.search('[a-z0-9]+\.[a-z0-9]+\.[a-z0-9]+\.[a-z0-9]+\.[a-z0-9]+', version):
		print 'It\'s onefw model.'
		isonefw = True
		cache_path = os.path.join(os.getenv('HOME'), '.hathor', 'dqa_cache_onefw')
	else:
		print 'It is not onefw model.'
		isonefw = False

	return isonefw
    

def is_test_models(target, aim):
	if len(target) < 0:
		return True 

	# not test models
	if re.match('[^_]+_[^_]+', aim):
		return False

	# whether in the list already
	for t in target:
		if re.split('-', t)[0] == re.split('-', aim)[0]:	
			return False 
	return True 

def fetch_releaselist(path):
    try: 
        fh = open(path)
        line = fh.readline()
        
        all_models = []
        while line:
            tmp = re.sub('[\r\n$()]', '', line)
            tmpmodname = re.split('\s+', tmp)[1]
            if is_test_models(all_models, tmpmodname):
                all_models.append(tmpmodname)
            line = fh.readline()
    except IOError as e:
        print e
    fh.close()
    return all_models

def get_onefw_models():
	model_path = os.path.join(os.getenv('PRODUCTDIR'), 'build', 'settings', os.getenv('PRODUCTVER'), 'release-list')
	model_path2 = os.path.join(os.getenv('PRODUCTDIR'), 'build', 'release-list')

	if os.path.exists(model_path):
		return fetch_releaselist(model_path)
	elif os.path.exists(model_path2):
		return fetch_releaselist(model_path2)

	return None

def get_info_from_envs():
    models = []
    if isonefw:
        models = get_onefw_models()
    else:
        models.append(os.getenv('PRODUCTVER')) 

    if not models:
    	print 'No release-list or No test models'
        sys.exit(0)

    plat = get_plat(os.getenv('OSEXTENSION'))

    tmp = []
	
    # onefw project has 'XX common bug' project and we must consider it
    if isonefw:
        devel_file = os.getenv('DEVELFILE')
        if devel_file == None:
            type_tmp = 'standard'
        else:
            devel_tmp = devel_file.split('_')[2]
            if devel_tmp == 'speeddome': 
                type_tmp = 'SD' 
            else:
                type_tmp = devel_tmp 
 
        tmp.append(('%s %s common' % (plat[0], type_tmp) , models[0].split('-')[1], plat[0]))

    for p in plat:
        for m in models:
            (model, vendor, ver) = m.split('-')
            tmp.append(('%s-%s' % (model, vendor), vendor, p))

    if debug:
        print tmp
    return tmp

def check_envs():
	if not os.getenv('PRODUCTVER') or not os.getenv('OSEXTENSION'):
		return False

	return True

def get_parent_pkg():
	line = ''
	try:
		if os.getenv('HATHOR'):
			path = os.path.join(os.getenv('HATHOR'), 'temp', os.getenv('PRODUCTVER'), 'parent_pkg')
			if os.path.exists(path):
				fh = open(path)
				line = fh.readline()
				line = re.sub('\n', '', line)
			else:
				print 'The current release pkg version is %s' % os.getenv('PRODUCTVER')	
				print 'What is the \'previous\' release pkg version ?'	
				line = raw_input()
		else:

			print 'The current release pkg version is %s' % os.getenv('PRODUCTVER')	
			print 'What is the \'previous\' release pkg version ?'	
			line = raw_input()

	except IOError as e:
		print e
		sys.exit(1)

	return line 

def check_bug_info_source():
	if os.getenv('HATHOR_BUGINFO_SOURCE') == 'svnlog':
		return 2 
	elif os.getenv('HATHOR_BUGINFO_SOURCE') == 'redmine':
		return 1 
	return 1 

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

	is_onefw()

	print 'Get bug list from svn log...'
	gen_bug_report2()

	print 'Total %d svn log found' % len(fixed_bugs)

	print '\nGet bug list from redmine (http://dqa02.vivotek.tw/redmine/)...'
	infos = get_info_from_envs()

	auth_setup()
	load_cache()
	for i in infos:
		(model, vendor, plat) = i[:]
		print '#####################################'
		print ' model is : %s' % model
		print '#####################################'
		gen_bug_report(model, vendor, plat)

	save_cache()
	if is_onefw and len(fixed_bugs) > 0:
		print 'Total %d bugs' % len(fixed_bugs)
	if debug:
		print 'total camera project which have isseus:'
		print g_total_camera_issue


	output()

	if debug and isonefw:
		print 'All matching products:'
		for p in g_all_matching_products:
			print p['name']

