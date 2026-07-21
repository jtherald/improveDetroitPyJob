# improveDetroitPyJob
Python script to be ran in GCP Cloud Run Job to pull Improve Detroit (SeeClickFix) data. For GCP Cloud Run Jobs tutorial read https://docs.cloud.google.com/run/docs/quickstarts/jobs/build-create-python

### Files:
`improvedetroitpyjob.py`
  - getIssues(): REST call to seeclickfix api for data and loops over first 25 pages
  - getLatestTimestamp(): Queries BigQuery table for latest entry in database, returns empty or latest date 
  - writeDataToBQ(): Inserts json response objects into BigQuery table

`Procfile`
  - defines python file for job to execute

### Run Locally
- log in to GCP in the shell using `gcloud auth application-default login`
- run `python improvedetroitpyjob.py`
  
### Deploy and Run in GCP
Create the job (navigate to project root):
`gcloud run jobs deploy improve-detroit-import --source . --tasks 1 --region {YOUR_GCP_REGION} --project={YOUR_GCP_PROJECT}`

GCP CLI command to run the job:
`gcloud run jobs execute improve-detroit-import`


### Notes:
This builds off my [previous code that was written in Java](https://github.com/jtherald/improveDetroitData), more background information is available there. SeeClickFix has changed their API limits, from 100 per page to 20 and also limiting to 25 pages. Each run of this job will only get 500 issues at a time. If this changes you can remove or adjust the `if(next_page > 25)` code and the API call parameter "`per_page":"20"`. This can be scheduled using the GCP Web UI under Jobs->Triggers page
