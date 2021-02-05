
import requests
import datetime
import json
# import urllib


authorization = "admin:admin123"
iq_url = "http://localhost:8070"
output_json_file = "results_1.json"

#------------------------------
cred = authorization.split(":")
iq_session = requests.Session()
iq_session.auth = requests.auth.HTTPBasicAuth(cred[0], cred[1])
iq_session.cookies.set('CLM-CSRF-TOKEN', 'api')
iq_headers = {'X-CSRF-TOKEN': 'api'}
orgs,apps,tags,report = {},{},{},[]
#------------------------------

def main():
	set_up()
	# pp(tags)
	# pp(apps)

	# Requirements - output from tool should be in CSV format

	# # of apps scanned (build & release) in the last month (date range)
	report.append(f'scanned_last_month, {scanned_last_month()}' )

	# # of new apps onboarded in the last month (date range)

	# # of apps onboarded into platform

	# ---
	# # new open critical, last month 
	# # new open high, last month
	# # new open medium, last month
	# ---
	# # open critical, root
	# # open high, root 
	# # open medium, root
	# ---
	# # open critical, sub
	# # open high, sub
	# # open medium, sub
	# ---
	# # new open, critical, last month, category = PCI
	# # new open, high, last month, category = PCI
	# # new open, medium, last month, category = PCI
	# ---
	# # open critical, root, category = PCI
	# # open high, root, category = PCI
	# # open medium, root, category = PCI
	# ---
	# # open critical, sub, category = PCI
	# # open high, sub, category = PCI
	# # open medium, sub, category = PCI
	# ---
	# Average Total Risk score for root organization
	# Average Total Risk score for each sub-organization
	# ---
	# Top 15 apps with highest Total Risk, minus any app name beginning with “z-“
	# Top 15 components with the highest Total Risk score in the root
	# Top 15 components used across the most applications in the root
	# ---
	# MTTR for root
	# MTTR for each sub

	print_results(apps)
	pp(report)

#------
def pp(page):
    print(json.dumps(page, indent=4))

def print_results(results, file_name = output_json_file):
	with open(file_name, "w+") as file:
		file.write(json.dumps(results, indent=4))
	print(f"Json results saved to -> {file_name}")

def format_url(url):
	if url[0:4] != 'http': 
		url = iq_url+url
	return url

def post_url(url, payload):
	reponse = iq_session.post(format_url(url), headers=iq_headers, json=payload)
	return reponse.json()

def get_url(url):
	reponse = iq_session.get(format_url(url), headers=iq_headers)
	return reponse.json()

def set_up():
	# get the organizations
	url = '/api/v2/organizations'
	reponse = get_url(url)["organizations"]
	for o in reponse:
		orgs.update({ o["id"] : o["name"] })
	# ----
	# get the categories
	root = 'ROOT_ORGANIZATION_ID'
	url = f'/api/v2/applicationCategories/organization/{root}'
	reponse = get_url(url)
	for t in get_url(url):
		tags.update({t["id"] : t})	
	# ----
	#get the applications
	url = '/api/v2/applications'
	for o in get_url(url)["applications"]:
		_id = o['id']
		o['organization'] = orgs[o['organizationId']]
		o["categories"] = []
		for t in o['applicationTags']:
			t.update(tags[t['tagId']])
			o["categories"].append(t['name'])
		o['history'] = get_history(_id)
		o['metrics'] = get_metrics([_id])
		apps.update({ o["publicId"] : o })

def milli_days(ms):
	return ms//1000//60//60//24

def prior_month(dt):
	return (dt.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)

def get_today():
	return datetime.date.today()

def get_last_month():
	return prior_month(get_today()).strftime("%Y-%m")

def get_this_month():
	return get_today().replace(day=1).strftime("%Y-%m")

def c_eval_date(dt):
	return datetime.datetime.fromisoformat(dt)

def clean_dict(dictionary, remove_list):
    for e in remove_list: 
        dictionary.pop(e, None)

def get_history(applicationInternalId):
	url = f'/api/v2/reports/applications/{applicationInternalId}/history'
	reponse = get_url(url)

	dt = get_today()
	ls = ""
	for rr in reponse['reports']:
		clean_dict(rr, ['policyEvaluationResult','commitHash','reportHtmlUrl','reportDataUrl','applicationId','latestReportHtmlUrl','embeddableReportHtmlUrl','reportPdfUrl'])
		ds = c_eval_date(rr['evaluationDate']).date()
		if not ls:
			ls = ds
		if dt > ds: dt = ds
	reponse['onboarded'] = dt.isoformat()
	reponse['last_scanned'] = ls.isoformat()
	return reponse

def handle_metrics(metrics): # removing everything except security
	for app in metrics: # metrics is list of applications.
		for period in app["aggregations"]: # there may be multiple periods for a given app.
			for data in period:
				if data.startswith('mttr') and period[data]:
					period[data] = milli_days(period[data])
				if type(period[data]) is dict:
					for name in list(period[data].keys()):
						if name in ['LICENSE','QUALITY','OTHER']:
							del period[data][name]
	return metrics

def get_metrics(applicationInternalId=[], organizationId=[]):
	url = '/api/v2/reports/metrics'
	payload = { 
		"timePeriod": "MONTH", 
		"firstTimePeriod": get_last_month(), 
		"lastTimePeriod": get_this_month(),
		"applicationIds": applicationInternalId,
		"organizationIds": organizationId
	}
	rr = post_url(url, payload)
	return handle_metrics(rr)

def scanned_last_month():
	scan_count = 0
	for app in apps.values():
		for aa in app['metrics']:
			for agg in aa['aggregations']:
				if agg['timePeriodStart'].startswith(get_last_month()):
					scan_count += agg['evaluationCount']
	return scan_count



if __name__ == "__main__":
    main()




