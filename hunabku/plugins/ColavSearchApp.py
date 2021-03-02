from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId

class ColavSearchApp(HunabkuPluginBase):
    def __init__(self, hunabku):
        super().__init__(hunabku)

    def search_branch(self,branch,iid=None):
        self.db = self.dbclient["antioquia"]
        if iid:
            db_response=self.db['branches'].find({"type":branch,"relations.id":ObjectId(iid)})
        else:
            db_response=self.db['branches'].find({"type":branch})
        if db_response:
            entity_list=[]
            for entity in db_response:
                entry={
                    "name":entity["name"],
                    "id":str(entity["_id"]),
                    "abbreviations":entity["abbreviations"],
                    "external_urls":entity["external_urls"]
                }
                entity_list.append(entry)
        return entity_list

    @endpoint('/app/search', methods=['GET'])
    def app_search(self):
        """
        @api {get} /app/search Search
        @apiName app
        @apiGroup CoLav app
        @apiDescription Requests search of different entities in the CoLav database

        @apiParam {String} data Specifies the type of entity (or list of entities) to return, namely paper, institution, faculty, department, author
        @apiParam {String} affiliation The mongo if of the related affiliation of the entity to return
        @apiParam {String} apikey  Credential for authentication

        @apiError (Error 401) msg  The HTTP 401 Unauthorized invalid authentication apikey for the target resource.
        @apiError (Error 204) msg  The HTTP 204 No Content.
        @apiError (Error 200) msg  The HTTP 200 OK.

        @apiSuccessExample {json} Success-Response (data=faculty):
        [
            {
                "name": "Facultad de artes",
                "id": "602c50d1fd74967db0663830",
                "abbreviations": [],
                "external_urls": [
                {
                    "source": "website",
                    "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/institucional/unidades-academicas/facultades/artes"
                }
                ]
            },
            {
                "name": "Facultad de ciencias agrarias",
                "id": "602c50d1fd74967db0663831",
                "abbreviations": [],
                "external_urls": [
                {
                    "source": "website",
                    "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/unidades-academicas/ciencias-agrarias"
                }
                ]
            },
            {
                "name": "Facultad de ciencias económicas",
                "id": "602c50d1fd74967db0663832",
                "abbreviations": [
                "FCE"
                ],
                "external_urls": [
                {
                    "source": "website",
                    "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/institucional/unidades-academicas/facultades/ciencias-economicas"
                }
                ]
            },
            {
                "name": "Facultad de ciencias exactas y naturales",
                "id": "602c50d1fd74967db0663833",
                "abbreviations": [
                "FCEN"
                ],
                "external_urls": [
                {
                    "source": "website",
                    "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/unidades-academicas/ciencias-exactas-naturales"
                }
                ]
            }
            ]
        """
        data = self.request.args.get('data')
        if not self.valid_apikey():
            return self.apikey_error()
        if data=="faculty":
            if "id" in self.request.args:
                iid = self.request.args.get('id')
                result=self.search_branch("faculty",iid)
            else:
                result=self.search_branch("faculty")
        elif data=="department":
            if "id" in self.request.args:
                iid = self.request.args.get('id')
                result=self.search_branch("department",iid)
            else:
                result=self.search_branch("department")
        elif data=="group":
            if "id" in self.request.args:
                iid = self.request.args.get('id')
                result=self.search_branch("group",iid)
            else:
                result=self.search_branch("group")
        else:
            result=None
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