<!--
title: 'Centercode API Enpoint Iteration'
description: 'This will grab a community level project list API endpoint and loop through all of the projects and output the endpoints to json files.'
platform: AWS
language: Python
-->
# AWS Python Scheduled Centercode API Endpoint Iteration

This is an example iteration through Centercode Platform API endpoints based off a Community level project API Endpoint. It loops through all Projects and their endpoints and writes the data to json files into s3 bucket.

This code uses the Serverless Framework for deployment (https://www.serverless.com/framework/docs/getting-started/). Please follow the installation directions to get it setup on your system.

## Customizable Environment Variables

* S3_BUCKET: "s3bucket-name"
* DOMAIN_PATH: "https://sub.domain.com/api/v1/"
* CENTERCODE_API_KEY: "CENTERCODEAPIKEY"
* COMMUNITY_PROJECT_REPORT: "activeProjects"
* COMMUNITY_USER_REPORT: "activeUsers"
* COMMUNITY_PROJECT_REPORT_NAME_ORDINAL: 0
* COMMUNITY_PROJECT_REPORT_KEY_ORDINAL: 1
* PROJECT_USER_REPORT: "userDataPackages/userAccounts"
* PROJECT_ISSUE_REPORT: "feedbackDataPackages/issueReports"
* PROJECT_FEATURE_REQUEST: "feedbackDataPackages/featureRequests"
* PROJECT_GENERAL_DISCUSSION: "feedbackDataPackages/generalDiscussions"

## Event Schedule Rate syntax

```pseudo
rate(value unit)
```

`value` - A positive number

`unit` - The unit of time. ( minute | minutes | hour | hours | day | days )

**Example** `rate(5 minutes)`

For more [information on the rate syntax see the AWS docs](http://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html#RateExpressions)

## Deploy

In order to deploy the endpoint you simply run

```bash
serverless deploy
```

The expected result should be similar to:

```bash
Serverless: Packaging service...
Serverless: Uploading CloudFormation file to S3...
Serverless: Uploading service .zip file to S3 (24.84 KB)...
Serverless: Updating Stack...
Serverless: Checking Stack update progress...
..............
Serverless: Stack update finished...

Service Information
service: centercode-api-cron
stage: dev
region: us-west-2
stack: centercode-api-cron-dev
resources: 6
api keys:
  None
endpoints:
  None
functions:
  cron: centercode-api-cron-dev-cron
layers:
  None
Serverless: Removing old service artifacts from S3...
```

There is no additional step required. Your defined schedule becomes active right away after deployment.

## Testing the function

If you have not yet enabled the cron scheduler and want to test the function call, you can simply run

```bash
serverless invoke -f cron
```

## Cloudwatch Results

The expected result should be similar to:

```bash
START RequestId: eddf3fbe0a-11e6-8d73bdd3836e44 Version: $LATEST
Invalid date	2009T12:28:03.214Z	eddf3fbe0a-11e6-8d73bdd3836e44	Your cron function centercode-api-cron-dev-cron ran at 12:28:03.214844
END RequestId: eddf3fbe0a-11e6-8d73bdd3836e44
REPORT RequestId: eddf3fbe0a-11e6-8d73bdd3836e44	Duration: 0.40 ms	Billed Duration: 100 ms 	Memory Size: 1024 MB	Max Memory Used: 16 MB

START RequestId: af2da2ba-be0b-11e6-a2e2-05f86a84b0e4 Version: $LATEST
Invalid date	2009T12:33:27.715Z	af2da2ba-be0b-11e6-a2e2-05f86a84b0e4	Your cron function centercode-api-cron-dev-cron ran at 12:33:27.715374
END RequestId: af2da2ba-be0b-11e6-a2e2-05f86a84b0e4
REPORT RequestId: af2da2ba-be0b-11e6-a2e2-05f86a84b0e4	Duration: 0.32 ms	Billed Duration: 100 ms 	Memory Size: 1024 MB	Max Memory Used: 15 MB
```
