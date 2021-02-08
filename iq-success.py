
import requests
import datetime
import json
# import urllib


authorization = "admin:admin123"
iq_url = "http://localhost:8070"
output_json_file = "results_1.json"
app_filter = "__bad"
org_filter = "__bad"
target_category = 'Distributed'

#------------------------------
cred = authorization.split(":")
iq_session = requests.Session()
iq_session.auth = requests.auth.HTTPBasicAuth(cred[0], cred[1])
iq_session.cookies.set('CLM-CSRF-TOKEN', 'api')
iq_headers = {'X-CSRF-TOKEN': 'api'}
orgs, apps, tags, report, target, csv = {}, {}, {}, {}, [], []

#------------------------------
# last 3 month



def main():
	set_up()
	header = ['']+date_range
	new = "discoveredCounts"
	_open = "openCountsAtTimePeriodEnd"
	crit = "CRITICAL"
	high = "SEVERE"
	med = "MODERATE"

	# # of apps onboarded into platform
	_row(['apps on platform',f'{len(apps)}'])
	_row(devide())
	# header row
	_row(header)
	# # of apps scanned (build & release) in the last month (date range)
	dd = [f'{len(report[dd]["scanned"])}' for dd in date_range]
	_row(['apps scanned']+dd)
	# # of new apps onboarded in the last month (date range)
	dd = [f'{len(report[dd]["onboarded"])}' for dd in date_range]
	_row(['apps onboarded']+dd)
	_row(devide())

	# MTTR for root
	# MTTR for each sub

	_row(devide())
	_row('All applications')
	_row(devide())
	_row(header)
	_row(['new critical']+rep_data("all",new,crit))
	_row(['new high']+rep_data("all",new,high))
	_row(['new medium']+rep_data("all",new,med))
	_row(devide())
	_row(['open critical']+rep_data("all",_open,crit))
	_row(['open high']+rep_data("all",_open,high))
	_row(['open medium']+rep_data("all",_open,high))
	_row(devide())
	for org in orgs.values():
		name = org['name']
		_row(name)
		_row(devide())
		_row(header)
		# # open critical, root
		_row(['open critical']+rep_data(name,_open,crit))
		# # open high, root 
		_row(['open high']+rep_data(name,_open,high))
		# # open medium, root
		_row(['open medium']+rep_data(name,_open,med))
		_row(devide())

	_row('PCI Applications')
	_row(devide())
	_row(['new critical']+rep_data("target",new,crit))
	_row(['new high']+rep_data("target",new,high))
	_row(['new medium']+rep_data("target",new,med))
	_row(devide())
	_row(['open critical']+rep_data("target",_open,crit))
	_row(['open high']+rep_data("target",_open,high))
	_row(['open medium']+rep_data("target",_open,high))
	_row(devide())
	
	for org in orgs.values():
		name = "target_"+org['name']		
		_row("PCI in "+org['name'])
		_row(devide())
		_row(header)
		# # open critical, root
		_row(['open critical']+rep_data(name,_open,crit))
		# # open high, root 
		_row(['open high']+rep_data(name,_open,high))
		# # open medium, root
		_row(['open medium']+rep_data(name,_open,med))
		_row(devide())
	
	# ---
	# Average Total Risk score for root organization
	# Average Total Risk score for each sub-organization

	# ---
	# Top 15 apps with highest Total Risk
	# Top 15 components with the highest Total Risk score in the root
	# Top 15 components used across the most applications in the root

	# ---
	

	build_csv()
	print_results({'report': report, 'target': target, 'orgs': get_orgs(), 'apps': apps})
	# pp(report)

#------

def devide():
	return '-'*40

def _row(row):
	csv.append(row)

def pp(page):
    print(json.dumps(page, indent=4))

def build_csv():
	with open('results.csv', "w+") as file:
		for row in csv:
			if isinstance(row,list):
				row = ",".join(row)
			file.write(row + '\n')
	print(f"Results saved to results.csv")

def print_results(results, file_name = output_json_file):
	with open(file_name, "w+") as file:
		file.write(json.dumps(results, indent=4))
	print(f"Json results saved to -> {file_name}")

def milli_days(ms):
	return ms//1000//60//60//24

def short(dd):
	return dd.strftime("%Y-%m")

def get_month(offset):
	return short((today - datetime.timedelta(days=offset*30)).replace(day=1))

def c_eval(dt):
	return datetime.datetime.fromisoformat(dt)

def format_url(url):
	if url[0:4] != 'http': url = iq_url+url
	return url

def clean_dict(dictionary, remove_list):
    for e in remove_list: 
        dictionary.pop(e, None)

def prune_dict(dictionary, keep_list):
	dict_keys = list(dictionary.keys())
	dict_keys = [ii for ii in dict_keys if ii not in keep_list]
	for e in dict_keys: 
		dictionary.pop(e, None)

def post_url(url, payload):
	url = format_url(url)
	resp = iq_session.post(url, headers=iq_headers, json=payload)
	return resp.json()

def get_url(url):
	url = format_url(url)
	resp = iq_session.get(url, headers=iq_headers)
	return resp.json()

#-------------------
def set_up():
	global today, date_range
	today = datetime.date.today()
	date_range = [get_month(rr) for rr in reversed(range(4))]
	set_orgs()
	set_categories()
	set_applications()
	setup_report()

#-------------------
def set_orgs():
	# build the orgs object of organizations.
	url = '/api/v2/organizations'
	resp = get_url(url)["organizations"]
	for o in resp:
		if not o['id'] == 'ROOT_ORGANIZATION_ID':
			orgs.update({ 
				o["id"] : {'name': o["name"],
				'apps':[], 'target':[]} 
			})

def add_org(orgId, publicId):
	orgs[orgId]['apps'].append(publicId)

def get_org_name(orgId):
	return orgs[orgId]['name']

def get_orgs():
	return orgs
#-------------------

def set_categories():
	# get categories that are set at the root org.	
	url = f'/api/v2/applicationCategories/organization/ROOT_ORGANIZATION_ID'
	resp = get_url(url)
	for t in resp:
		tags.update({t['id'] : t['name']})	

def add_target(app_tags, org_id, publicId):
	for app_tag in app_tags:
		tag_id =app_tag['tagId']
		if tags[tag_id] == target_category:
			target.append(publicId)
			orgs[org_id]['target'].append(publicId)

def rep_data(l1,l2,l3):
	return [f'{ report[dd][l1][l2][l3] }' for dd in date_range if l1 in report[dd]]

def setup_report():
	for date in date_range:
		report.update({
			date:{
				"onboarded":[],
				"scanned":[]
			}
		})

	for name, app in apps.items():

		dd = onboard_month(app['history'])
		if dd and dd in date_range:
			report[dd]["onboarded"].append(name)
		
		dd = last_scanned(app['history'])
		if dd and dd in date_range:
			report[dd]["scanned"].append(name)

		for nn, aa in app['metrics'].items():
			summation('all', aa)

	for name in target:
		for nn, aa in apps[name]['metrics'].items():
			summation('target', aa)
	
	for org in orgs.values():

		for name in org['apps']:
			for nn, aa in apps[name]['metrics'].items():
				summation(org['name'], aa)

	for org in orgs.values():
		for name in org['target']:
			for nn, aa in apps[name]['metrics'].items():
				summation('target_'+org['name'], aa)


def summation(group, metric):
	dd = metric["timePeriodStart"]
	if not group in report[dd]:
		report[dd].update({ group: get_blank_metric(metric)})

	for aa in list(metric.keys()):
		if aa.startswith('mttr') and metric[aa] is not None:
			report[dd][group][aa].append( metric[aa]) 

		elif isinstance(metric[aa], dict):
			for bb in list(metric[aa].keys()):
				report[dd][group][aa][bb] += metric[aa][bb]


def get_blank_metric(metric):
	cc = {}
	for aa in list(metric.keys()):
		if aa.startswith('mttr'):
			cc.update({aa: []})

		elif isinstance(metric[aa], dict):
			dd = {}
			for bb in list(metric[aa].keys()):
				dd.update({bb: 0})
			cc.update({aa: dd})
	return cc

#-------------------		
def set_applications():
	#get the applications
	url = '/api/v2/applications'
	resp = get_url(url)["applications"]

	# prune apps that should be filtered out: prune_app()
	resp = [aa for aa in resp if not prune_app(aa)]

	for app in resp:
		_id, publicId = app['id'], app["publicId"]

		add_org( app['organizationId'] , publicId)
		add_target( app['applicationTags'] , app['organizationId'], publicId)
		app = {
			'id': _id,
			'history': get_app_history(_id),
			'metrics': get_app_metrics(_id)
		}
		apps.update({ publicId : app })


def prune_app(app, prune = False):
	# prune if app and starts with filter
	if "app_filter" in globals(): 
		prune = app['name'].startswith(app_filter)

	# prune if org name starts with filter
	if "org_filter" in globals() and not prune:
		org_name = get_org_name(app['organizationId'])
		prune = org_name.startswith(org_filter)

	return prune
#-------------------


def get_app_metrics(appId):
	resp = get_metrics( date_range[0], date_range[-1], [appId])
	metrics = {}
	if resp:
		app_metrics = resp[0]["aggregations"]
		for period in app_metrics:
			handle_data(period)
			metrics.update({period["timePeriodStart"]: period})
	return metrics


def get_app_history(appId):
	url = f'/api/v2/reports/applications/{appId}/history'
	reponse = get_url(url)
	reports =reponse['reports']
	# remove CM scans from history.
	reports = [rr for rr in reports \
		if rr['isForMonitoring'] == False]

	for report in reports:
		keep = ["stage", "evaluationDate", 
				"policyEvaluationId", "scanId"]
		prune_dict(report, keep)
	return reports


def handle_data(data):
	# formatting period to year and month
	name = "timePeriodStart"
	data[name] = data[name][:7]

	for name, field in data.items():

		# convert mttr from milliseconds to days.
		if name.startswith('mttr') and field:
			data[name] = milli_days(field)

		# just need SECURITY data
		if type(field) is dict:
			field["SECURITY"].pop("LOW", None)
			data[name] = field["SECURITY"]


def get_metrics(start, end, appId=[], orgId=[] ):
	url = '/api/v2/reports/metrics'
	payload = { "timePeriod": "MONTH", 
		"firstTimePeriod": start, "lastTimePeriod": end,
		"applicationIds": appId, "organizationIds": orgId
	}
	resp = post_url(url, payload)
	return resp

def last_scanned(history):
	return None if not history else short(c_eval(history[0]['evaluationDate']))

def onboard_month(history):
	return None if not history else short(c_eval(history[-1]['evaluationDate']))







if __name__ == "__main__":
    main()




