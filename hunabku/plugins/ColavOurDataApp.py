from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId
from pymongo import ASCENDING,DESCENDING

class ColavOurDataApp(HunabkuPluginBase):
    def __init__(self, hunabku):
        super().__init__(hunabku)

    def get_our_data(self):
        entry={
            "documents":self.colav_db["documents"].count_documents({}),
            "authors":self.colav_db["authors"].count_documents({}),
            "institutions":self.colav_db["institutions"].count_documents({}),
            "sources":self.colav_db["sources"].count_documents({})
        }
        return entry

    @endpoint('/app/ourdata', methods=['GET'])
    def app_ourdata(self):
        """
        
        """
        data = self.request.args.get('data')
        if not self.valid_apikey():
            return self.apikey_error()
        result=self.get_our_data()
        print("Endpoint ourdata returning:\n\t",result)
        if result:
            response = self.app.response_class(
            response=self.json.dumps(result),
            status=200,
            mimetype='application/json'
            )
        else:
            response = self.app.response_class(
            response=self.json.dumps({}),
            status=204,
            mimetype='application/json'
            )
        
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response