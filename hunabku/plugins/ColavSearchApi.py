from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId

class ColavSearchApi(HunabkuPluginBase):
    def __init__(self, hunabku):
        super().__init__(hunabku)

    @endpoint('/api/search', methods=['GET'])
    def api_search(self):
        """
        @api {get} /api/search Search
        @apiName api
        @apiGroup CoLav api
        @apiDescription Requests search of different entities in the CoLav database

        @apiParam {String} data Specifies the type of entity (or list of entities) to return, namely paper, institution, faculty, department, author
        @apiParam {String} affiliation The mongo if of the related affiliation of the entity to return
        @apiParam {String} apikey  Credential for authentication

        @apiError (Error 401) msg  The HTTP 401 Unauthorized invalid authentication apikey for the target resource.
        @apiError (Error 204) msg  The HTTP 204 No Content.
        @apiError (Error 200) msg  The HTTP 200 OK.
        """
        response = self.app.response_class(
            response=self.json.dumps({}),
            status=204,
            mimetype='application/json'
            )
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response