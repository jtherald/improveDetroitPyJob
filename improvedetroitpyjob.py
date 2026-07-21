from google.cloud import bigquery
import requests
import pandas as pd
import os, json
import time

project_id = 'YOUR_GCP_PROJECT'
dataset_id = 'YOUR_BQ_DATASET'
table_id = 'YOUR_TABLE'
client = bigquery.Client(project = project_id)
dataset = client.dataset(dataset_id)
table = dataset.table(table_id)

def getIssues():
    afterDate = getLatestTimestamp()
    seeclickfixURL="https://seeclickfix.com/api/v2/issues"
    results = []
    next_page = 1
    while(next_page != None):
        print(next_page)
        #I need the details and are limited to 20 issues per page
        #without details max is 100 per page
        #adjust request_types for your city and needs
        payload = {"place_url":"detroit",
                   "per_page":"20",
                   "page": next_page,
                   "sort_direction":"ASC",
                   "sort":"created_at",
                   "after":afterDate,
                   "status":"open,acknowledged,closed,archived",
                   "details":"true",
                   "request_types":"7047,22880",
                   "fields[issue]":"id,status,summary,description,lat,lng,created_at,acknowledged_at,closed_at,request_type,questions,reporter",
                   }
        headers = {"Content-Type": "application/json"}
        response = requests.get(seeclickfixURL, params=payload)
        results.extend(response.json()['issues'])
        next_page = response.json()['metadata']['pagination']['next_page']

        #new seeclickfix api does not allow you to get pages 26+
        if(next_page > 25):
            print("inserting to bq")
            writeDataToBQ(results)
            break
    return results;

project_id+"."+dataset_id+"."+"."table_id


def getLatestTimestamp():
    #add one second because the AFTER is inclusive and would add a duplicate
    query = ('select FORMAT_TIMESTAMP("%Y-%m-%dT%H:%M:%E*SZ", '
             'TIMESTAMP_ADD(created_at, INTERVAL 1 SECOND)) as created_at '
             'from '+project_id+"."+dataset_id+"."+table_id+' '
             'order by created_at desc limit 1;')
    query_job = client.query(query)
    try:
        result = query_job.result()

    #first time the table might not exist and throw error
    except Exception as e:
        print('starting from the beginning')
        return ""
   
    if result.total_rows > 0:
        latest_date = next(query_job.result())
        print('starting at date: ', latest_date['created_at'])
        return latest_date['created_at']
    return ""


def writeDataToBQ(data):
    job_config = bigquery.LoadJobConfig(autodetect=True, source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON)
    job = client.load_table_from_json(data, table, job_config = job_config)

print("starting")
start = time.time()
x = getIssues()
end = time.time()
print("inserted: ",len(x))
print("done in", end - start)
