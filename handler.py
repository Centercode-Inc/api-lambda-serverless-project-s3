import datetime
import logging
import urllib3
import json
import boto3
import os
import cStringIO

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
s3 = boto3.resource("s3")
timestamp = (datetime.datetime.utcnow() - datetime.datetime(1970,1,1,0,0,0)).total_seconds()

def run(event, context):
    current_time = datetime.datetime.now().time()
    name = context.function_name
    logger.info("Your cron function " + name + " ran at " + str(current_time))

    # Global data collection for s3 bucket files
    commProjectJsonData = cStringIO.StringIO()

    # Community User Accounts
    parseAPICall(os.environ.get('DOMAIN_PATH') + 'userDataPackages/' + os.environ.get('COMMUNITY_USER_REPORT'), 'userAccountCommunity')

    currProjPage = 1
    TotalProjPages = 1
    while currProjPage <= TotalProjPages:
        commProjectDataPackage = DataPackage(os.environ.get('DOMAIN_PATH') + 'projectDataPackages/' + os.environ.get('COMMUNITY_PROJECT_REPORT'), os.environ.get('CENTERCODE_API_KEY'), currProjPage)
        currProjPage += 1
        if commProjectDataPackage.Status == 200:
            DPPaging = commProjectDataPackage.getPaging()
            TotalProjPages = DPPaging.TotalPages
            DPDataRows = commProjectDataPackage.getDataRows()

            commProjectJsonData.write(commProjectDataPackage.getJsonString())

            logger.info('commProjectDataPackage TotalPages:' + str(DPPaging.TotalPages) + ', CurrentPage:' + str(DPPaging.CurrentPage) + ', ResultsPerPage:' + str(DPPaging.ResultsPerPage) + ', TotalResults:' + str(DPPaging.TotalResults))

            for rows in DPDataRows:
                ProjectName = ''
                projRootDataPackageURL = ''
                for data in rows:
                    # logger.info('data - FieldOrdinal:' + str(data.FieldOrdinal) + ', DataType:' + data.DataType + ', ComputedValue:' + data.ComputedValue)

                    if data.FieldOrdinal == int(os.environ.get('COMMUNITY_PROJECT_REPORT_NAME_ORDINAL')):
                        ProjectName = data.ComputedValue

                    if data.FieldOrdinal == int(os.environ.get('COMMUNITY_PROJECT_REPORT_KEY_ORDINAL')):
                        projRootDataPackageURL = os.environ.get('DOMAIN_PATH') + 'projects/' + data.ComputedValue + '/'

                logger.info('Project [' + ProjectName + '] projIssueReportDataPackageURL:' + projRootDataPackageURL)

                if projRootDataPackageURL != '':
                    # Project User Accounts
                    parseAPICall(projRootDataPackageURL + os.environ.get('PROJECT_USER_REPORT'), 'userAccountProjects')

                    # Project Issue Reports
                    parseAPICall(projRootDataPackageURL + os.environ.get('PROJECT_ISSUE_REPORT'), 'issueReports')

                    # Project Feature Requests
                    parseAPICall(projRootDataPackageURL + os.environ.get('PROJECT_FEATURE_REQUEST'), 'featureRequests')

                    # Project General Discussions
                    parseAPICall(projRootDataPackageURL + os.environ.get('PROJECT_GENERAL_DISCUSSION'), 'generalDiscussions')

        else:
            logger.error('commProjectDataPackage [NOT FOUND]:' + os.environ.get('DOMAIN_PATH') + 'projectDataPackages/' + os.environ.get('COMMUNITY_PROJECT_REPORT') + ', CurrentPage:' + str(currProjPage))
            break

    # Finalize the Community Level project API calls and write to s3/close
    finalizeAPICall('projectCommunity', commProjectJsonData)

    # End of run function


# Write to S3 and close the string wirter
def parseAPICall(dataPackageURL, fileName):
    stringWriter = cStringIO.StringIO()
    currReportPage = 1
    TotalReportPages = 1
    while currReportPage <= TotalReportPages:
        currDataPackage = DataPackage(dataPackageURL, os.environ.get('CENTERCODE_API_KEY'), currReportPage)
        if currDataPackage.Status == 200:
            URPaging = currDataPackage.getPaging()
            TotalReportPages = URPaging.TotalPages
            stringWriter.write(currDataPackage.getJsonString())
            logger.info(fileName+' TotalPages:' + str(URPaging.TotalPages) + ', CurrentPage:' + str(URPaging.CurrentPage) + ', ResultsPerPage:' + str(URPaging.ResultsPerPage) + ', TotalResults:' + str(URPaging.TotalResults))
            currReportPage += 1
        else:
            logger.error(fileName+' [NOT FOUND]:' + dataPackageURL + ', CurrentPage:' + str(currReportPage))
            break

    finalizeAPICall(fileName, stringWriter)

def finalizeAPICall(fileName, stringWriter):
    s3.Bucket(os.environ.get('S3_BUCKET')).put_object(Key=fileName+'-'+str(timestamp)+'.json', Body=stringWriter.getvalue())
    stringWriter.close()

# Defines the API Datapackage container
# Populates the Paging, Fields, and Data
class DataPackage:
    _json_data = None
    _json_object = None
    Status = -1

    def __init__(self, url, apiKey, currPage):
        logger.info('DataPackage url:' + url)
        http = urllib3.PoolManager()
        r = http.request('GET', url + '?page='+str(currPage)+'&apiKey='+apiKey)  # result is now a dict
        self.Status = r.status
        if self.Status == 200:
            self._json_data = r.data.decode('utf-8')
            self._json_object = json.loads(self._json_data)
        else:
            # This means something went wrong.
            logger.error('invokeAPI (' + url + ') status:' + str(self.Status))


    def getPaging(self):
        return Paging(self._json_object['paging'])

    def getFields(self):
        return Fields(self._json_object['fields'])

    def getDataRows(self):
        return DataRows(self._json_object['data'])

    def getJsonString(self):
        return json.dumps(self._json_object)

    def getJsonData(self):
        return json.dumps(self._json_data)        

# Define the paging for this particular API endpoint
class Paging:
    TotalPages = 0
    CurrentPage = 0
    ResultsPerPage = 0
    TotalResults = 0

    def __init__(self, paging):
        self.TotalPages = int(paging['totalPages'])
        self.CurrentPage = int(paging['currentPage'])
        self.ResultsPerPage = int(paging['resultsPerPage'])
        self.TotalResults = int(paging['totalResults'])

# Define the View Fields defined in the Data Package
class Fields:
    Ordinal = -1

    def __init__(self, fields):
        self._fields = []
        for field in fields:
            self.Ordinal += 1
            self._fields.append(Field(self.Ordinal, field))

    def __len__(self):
        return len(self._fields)

    def __iter__(self):
        return iter(self._fields)

#Define the individual Field of the Fields return
class Field:
    Ordinal = -1
    DataType = ""
    Name = ""

    def __init__(self, ordinal, field):
        self.Ordinal = ordinal
        self.DataType = str(field['dataType'])
        self.Name = str(field['name'])

# Gather all of the returned data rows from this endpoint
class DataRows:
    Ordinal = -1

    def __init__(self, datarows):
        self._datarows = []
        for datarow in datarows:
            self.Ordinal += 1
            self._datarows.append(DataRow(datarow))

    def __len__(self):
        return len(self._datarows)

    def __iter__(self):
        return iter(self._datarows)

# Populate individual data row
class DataRow:
    Data = []

    def __init__(self, datarow):
        self._datarow = []
        for data in datarow:
            self._datarow.append(Data(data))

    def __len__(self):
        return len(self._datarow)

    def __iter__(self):
        return iter(self._datarow)

# Define the data for the row
class Data:
    DataType = ""
    ComputedValue = ""
    FieldOrdinal = 0
    Values = []

    def __init__(self, data):
        self.DataType = str(data['dataType'])
        self.ComputedValue = str(data['computedValue'])
        self.FieldOrdinal = int(data['fieldOrdinal'])
        self.Values = DataValues(data['values'])

# Define the Data Value Array for the row
class DataValues:
    Ordinal = -1

    def __init__(self, dataValues):
        self._datavalues = []
        for dataValue in dataValues:
            self.Ordinal += 1
            self._datavalues.append(dataValue)

    def __len__(self):
        return len(self._datavalues)

    def __iter__(self):
        return iter(self._datavalues)