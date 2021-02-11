from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId

class ColavApp(HunabkuPluginBase):
    def __init__(self, hunabku):
        super().__init__(hunabku)

    @endpoint('/app/faculty', methods=['GET'])
    def app_faculty(self):
        """
        @api {get} /app/faculty Requests faculty general information or the list of papers
        @apiName app
        @apiGroup CoLav app
        @apiDescription Responds with information about the faculty

        @apiParam {String} data Wether is the general information or the list of papers
        @apiParam {Object} id the id of the faculty requested in mongodb
        @apiParam {String} apikey  Credential for authentication

        @apiError (Error 401) msg  The HTTP 401 Unauthorized invalid authentication apikey for the target resource.
        @apiError (Error 204) msg  The HTTP 204 No Content.
        @apiError (Error 401) msg  The HTTP 200 OK.
        """
        data = self.request.args.get('data')
        if not self.valid_apikey():
            return self.apikey_error()
        if data=="info":
            self.db = self.dbclient["antioquia"]
            faculty = self.db['branches'].find_one({"type":"faculty","_id":ObjectId("602599029e9b96dff8bf00ab")})
            if faculty:
                entry={"id":faculty["_id"],
                    "name":faculty["name"],
                    "type":faculty["type"],
                    "external_urls":faculty["external_urls"],
                    "departments":[],
                    "groups":[],
                    "authors":[],
                    "institution":[]
                }
                inst_id=""

                if inst_id:
                    inst=self.db['institutions'].find_one({"_id":inst_id})
                    if inst:
                        entry["institution"]=[{"name":inst["name"],"id":inst_id}]#,"logo":inst["logo"]}]

                for dep in self.db['branches'].find({"type":"department","relations.id":faculty["_id"]}):
                    dep_entry={
                        "name":dep["name"],
                        "id":str(dep["_id"])
                    }
                    entry["departments"].append(dep_entry)
                for author in self.db['authors'].find({"branches.id":faculty["_id"]}):
                    author_entry={
                        "full_name":author["full_name"],
                        "id":str(author["_id"])
                    }
                    entry["authors"].append(author_entry)
                    for branch in author["branches"]:
                        if branch["type"]=="group":
                            branch_db=self.db["branches"].find_one({"_id":ObjectId(branch["id"])})
                            entry_group={
                                "id":branch["id"],
                                "name":branch_db["name"]
                            }
                            entry["groups"].append(entry_group)
                
                response = self.app.response_class(
                response=self.json.dumps(entry),
                status=200,
                mimetype='application/json'
            )
            else:
                response = self.app.response_class(
                response=self.json.dumps({"status":"Request returned empty"}),
                status=204,
                mimetype='application/json'
            )
        elif data=="paper":
            pass
        else:
            response = self.app.response_class(
                response=self.json.dumps({}),
                status=400,
                mimetype='application/json'
            )
        
        return response

    @endpoint('/api/faculty', methods=['GET'])
    def api_faculty(self):
        """
        @api {get} /api/faculty Requests faculty general information or the list of papers
        @apiName api
        @apiGroup CoLav api
        @apiDescription Responds with information about the faculty

        @apiParam {String} data Wether is the general information or the list of papers
        @apiParam {Object} id the id of the faculty requested in mongodb
        @apiParam {String} apikey  Credential for authentication

        @apiError (Error 401) msg  The HTTP 401 Unauthorized invalid authentication apikey for the target resource.
        @apiError (Error 204) msg  The HTTP 204 No Content.
        @apiError (Error 401) msg  The HTTP 200 OK.
        """
        data = self.request.args.get('data')
        if not self.valid_apikey():
            return self.apikey_error()
        if data=="info":
            self.db = self.dbclient["antioquia"]
            faculty = self.db['branches'].find_one({"type":"faculty","_id":ObjectId("602599029e9b96dff8bf00ab")})
            if faculty:
                entry={"id":faculty["_id"],
                    "name":faculty["name"],
                    "type":faculty["type"],
                    "external_urls":faculty["external_urls"],
                    "departments":[],
                    "groups":[],
                    "authors":[],
                    "institution":[]
                }
                inst_id=""

                if inst_id:
                    inst=self.db['institutions'].find_one({"_id":inst_id})
                    if inst:
                        entry["institution"]=[{"name":inst["name"],"id":inst_id}]#,"logo":inst["logo"]}]

                for dep in self.db['branches'].find({"type":"department","relations.id":faculty["_id"]}):
                    dep_entry={
                        "name":dep["name"],
                        "id":str(dep["_id"])
                    }
                    entry["departments"].append(dep_entry)
                for author in self.db['authors'].find({"branches.id":faculty["_id"]}):
                    author_entry={
                        "full_name":author["full_name"],
                        "id":str(author["_id"])
                    }
                    entry["authors"].append(author_entry)
                    for branch in author["branches"]:
                        if branch["type"]=="group":
                            branch_db=self.db["branches"].find_one({"_id":ObjectId(branch["id"])})
                            entry_group={
                                "id":branch["id"],
                                "name":branch_db["name"]
                            }
                            entry["groups"].append(entry_group)
                
                response = self.app.response_class(
                response=self.json.dumps(entry),
                status=200,
                mimetype='application/json'
            )
            else:
                response = self.app.response_class(
                response=self.json.dumps({"status":"Request returned empty"}),
                status=204,
                mimetype='application/json'
            )
        elif data=="paper":
            pass
        else:
            response = self.app.response_class(
                response=self.json.dumps({}),
                status=400,
                mimetype='application/json'
            )
        
        return response

