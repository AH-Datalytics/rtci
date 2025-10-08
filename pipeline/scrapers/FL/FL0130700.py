import json
import requests
import sys

sys.path.append("../../utils")
from super import Scraper


class FL0130700(Scraper):
    def __init__(self):
        super().__init__()
        self.url = "https://wabi-us-gov-virginia-api.analysis.usgovcloudapi.net/public/reports/caf9f6dc-8586-4796-b76a-78ec046c99ca/modelsAndExploration?preferReadOnlySession=true"
        self.api_url = (
            "https://wabi-us-gov-virginia-api.analysis.usgovcloudapi.net/public/reports/querydata?synchronous"
            "=true"
        )
        self.oris = ["FL0130700"]

    def scrape(self):
        r = requests.get(self.url)
        # import re
        #
        print(r.text)
        # print(re.match(r"\d{8}-\d{4}-\d{4}-\d{4}-\d{12}", r.text))

        # pay = json.loads(
        #     """
        # {"version":"1.0.0","queries":[{"Query":{"Commands":[{"SemanticQueryDataShapeCommand":{"Query":{"Version":2,"From":[{"Name":"v","Entity":"vwLeCase","Type":0},{"Name":"v1","Entity":"vwDates","Type":0}],"Select":[{"Measure":{"Expression":{"SourceRef":{"Source":"v"}},"Property":"11MajorCrimeCountPropertyPY$"},"Name":"vwLeCase.11MajorCrimeCountPY$Property","NativeReferenceName":"11MajorCrimeCountPropertyPY$"}],"Where":[{"Condition":{"In":{"Expressions":[{"Column":{"Expression":{"SourceRef":{"Source":"v1"}},"Property":"MonthRelative"}}],"Values":[[{"Literal":{"Value":"'Prior Month'"}}],[{"Literal":{"Value":"'2024-Nov'"}}]]}}},{"Condition":{"Comparison":{"ComparisonKind":2,"Left":{"Column":{"Expression":{"SourceRef":{"Source":"v1"}},"Property":"FullDate"}},"Right":{"DateSpan":{"Expression":{"Literal":{"Value":"datetime'2014-01-01T00:00:00'"}},"TimeUnit":5}}}}},{"Condition":{"Comparison":{"ComparisonKind":2,"Left":{"Column":{"Expression":{"SourceRef":{"Source":"v"}},"Property":"ReportedDate"}},"Right":{"DateSpan":{"Expression":{"Literal":{"Value":"datetime'2014-01-01T00:00:00'"}},"TimeUnit":5}}}}}]},"Binding":{"Primary":{"Groupings":[{"Projections":[0]}]},"DataReduction":{"DataVolume":3,"Primary":{"Top":{}}},"Version":1},"ExecutionMetricsKind":1}}]},"QueryId":"","ApplicationContext":{"DatasetId":"0382921d-a250-4066-a74a-67aeacdc4b5b","Sources":[{"ReportId":"b4042b29-c53c-42c9-a7dd-d7dbe3ac5938","VisualId":"c4772b08010062a06508"}]}}],"cancelQueries":[],"modelId":903044}
        # """
        # )
        # print(pay)
        # headers = {}
        # r = requests.post(self.url, data=pay, headers=headers)
        # # data = json.loads(r.text)
        #
        # print(r)


FL0130700().run()
