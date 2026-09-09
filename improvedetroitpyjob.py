from google.cloud import bigquery
import requests
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
    while (next_page is not None) and (next_page <= 25):
        print(next_page)
        #We need the details and are limited to 20 issues per page
        #without details max is 100 per page
        #adjust request_types for your city and needs
        #new seeclickfix api does not allow you to get pages 26+
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
        response = requests.get(seeclickfixURL, params=payload)
        results.extend(response.json()['issues'])
        next_page = response.json()['metadata']['pagination']['next_page']

    #remove extra fields to save database space
    #TODO: a more efficient way to drop these columns
    for i in results:
        del i["reporter"]["civic_points"]
        del i["reporter"]["avatar"]
        del i["reporter"]["role"]
        del i["reporter"]["witty_title"]
        del i["reporter"]["html_url"]
        del i["request_type"]["related_issues_url"]
        del i["request_type"]["organization"]
        del i["request_type"]["url"]
        del i["request_type"]["title"]
        del i["url"]

    #only schema detect on the very first insert, saves time and prevents errors with new data
    if afterDate == "":
        writeDataToBQ(results, True)
    else:
        writeDataToBQ(results, False)

    return results

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


def writeDataToBQ(data, isAutoDetect):
    print("inserting to bq")
    job_config = bigquery.LoadJobConfig(autodetect=isAutoDetect, source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON)
    job = client.load_table_from_json(data, table, job_config = job_config)

print("starting")
start = time.time()
x = getIssues()
end = time.time()
print("inserted: ",len(x))
print("done in", end - start)
