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
            keywords=[]
            countries=[]
            affiliations=[]
            for entity in db_response:
                entry={
                    "name":entity["name"],
                    "id":str(entity["_id"]),
                    "abbreviations":entity["abbreviations"],
                    "external_urls":entity["external_urls"]
                }
                entity_list.append(entry)
                if not entity["addresses"][0]["country_code"] in countries:
                    countries.append(entity["addresses"][0]["country_code"])
                for relation in entity["relations"]:
                    if relation["type"]=="university":
                        del(relation["type"])
                        del(relation["collection"])
                        if not relation in affiliations:
                            affiliations.append(relation)
                        
            return {"data":entity_list,
                    "filters":{"affiliations":affiliations,
                        "keywords":keywords,
                        "countries":countries
                    },
                    "count":len(entity_list)
                }
        else:
            return None

    def search_author(self,affiliation=None,max_results=100,page=1):
        """
        TODO:
            Code already with pagination, missing the queries that make use of them
            namely keyword and country, here in this function as well as in the endpoint function
        """
        self.db = self.dbclient["antioquia"]
        if affiliation:
            cursor=self.db['authors'].find({"affiliations.id":ObjectId(affiliation)})
            affiliations=[]
            for reg in self.db['authors'].find({"affiliations.id":ObjectId(affiliation)},{"affiliations":{"$slice":-1}}):
                if len(reg["affiliations"])==0:
                    continue
                if not reg["affiliations"][0] in affiliations:
                     affiliations.append(reg["affiliations"][0])
            
            pipeline=[
                {"$match":{"affiliations.id":ObjectId(affiliation)}},
                {"$lookup":{
                    "from":"institutions",
                    "localField":"affiliations.id",
                    "foreignField":"_id",
                    "as":"affiliations"
                    }
                },
                {"$project":{"affiliations.addresses.country_code":1,"_id":0}},
                {"$unwind":"$affiliations"}
            ]
            countries=[]
            for reg in self.db["authors"].aggregate(pipeline):
                country=reg["affiliations"]["addresses"][0]["country_code"]
                if not country in countries:
                    countries.append(country)
        else:
            cursor=self.db['authors'].find()
            affiliations=[]
            for reg in self.db['authors'].find({},{"affiliations":{"$slice":-1}}):
                if len(reg["affiliations"])==0:
                    continue
                if not reg["affiliations"][0] in affiliations:
                     affiliations.append(reg["affiliations"][0])
            pipeline=[
                {"$lookup":{
                    "from":"institutions",
                    "localField":"affiliations.id",
                    "foreignField":"_id",
                    "as":"affiliations"}
                },
                {"$project":{"affiliations.addresses.country_code":1,"_id":0}},
                {"$unwind":"$affiliations"}
            ]
            countries=[]
            for reg in self.db["authors"].aggregate(pipeline):
                country=reg["affiliations"]["addresses"][0]["country_code"]
                if not country in countries:
                    countries.append(country)

        total=cursor.count()
        if not page:
            page=1
        else:
            try:
                page=int(page)
            except:
                print("Could not convert end page to int")
                return None
        if not max_results:
            max_results=100
        else:
            try:
                max_results=int(max_results)
            except:
                print("Could not convert end max to int")
                return None
        cursor=cursor.skip(max_results*(page-1)).limit(max_results)

        if cursor:
            author_list=[]
            keywords=[]
            for author in cursor:
                entry={
                    "id":author["_id"],
                    "full_name":author["full_name"],
                    "affiliation":author["affiliations"][-1] if len(author["affiliations"])>0 else [],
                    "keywords":author["keywords"]
                }
                author_list.append(entry)
            return {"data":author_list,
                    "filters":{"affiliations":affiliations,
                        "keywords":keywords,
                        "countries":countries
                    },
                    "count":len(author_list),
                    "page":page,
                    "total_results":total
                }
        else:
            return None
        

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

        @apiSuccessExample {json} Success-Response (data=author):
            {
                "data": [
                    {
                    "id": "5fc59becb246cc0887190a5c",
                    "full_name": "Johann Hasler Perez",
                    "affiliation": {
                        "id": "60120afa4749273de6161883",
                        "name": "University of Antioquia"
                    },
                    "keywords": [
                        "elliptical orbits",
                        "history of ideas",
                        "history of science",
                        "johannes kepler",
                        "music of the spheres",
                        "planetary music",
                        "speculative music",
                        "alchemical meditation",
                        "atalanta fugiens",
                        "early multimedia",
                        "emblem books",
                        "historical instances of performance",
                        "michael maier"
                    ]
                    },
                    {
                    "id": "5fc59d6bb246cc0887190a5d",
                    "full_name": "Carolina Santamaria Delgado",
                    "affiliation": {
                        "id": "60120afa4749273de6161883",
                        "name": "University of Antioquia"
                    },
                    "keywords": [
                        "art in the university",
                        "artist-professor",
                        "intellectual production",
                        "music as an academic field",
                        "research-creation",
                        "the world of art"
                    ]
                    }
                ],
                "filters": {
                    "affiliations": [
                    {
                        "id": "60120afa4749273de6161883",
                        "name": "University of Antioquia"
                    }
                    ],
                    "keywords": [],
                    "countries": [
                    "CO"
                    ]
                },
                "count": 2,
                "page": 2,
                "total_results": 565
            }
        """
        data = self.request.args.get('data')
        if not self.valid_apikey():
            return self.apikey_error()
        if data=="faculty":
            if "affiliation" in self.request.args:
                iid = self.request.args.get('affiliation')
                result=self.search_branch("faculty",iid)
            else:
                result=self.search_branch("faculty")
        elif data=="department":
            if "affiliation" in self.request.args:
                iid = self.request.args.get('affiliation')
                result=self.search_branch("department",iid)
            else:
                result=self.search_branch("department")
        elif data=="group":
            if "affiliation" in self.request.args:
                iid = self.request.args.get('affiliation')
                result=self.search_branch("group",iid)
            else:
                result=self.search_branch("group")
        elif data=="author":
            max_results=self.request.args.get('max') if 'max' in self.request.args else 100
            page=self.request.args.get('page') if 'page' in self.request.args else 1
            iid = self.request.args.get('affiliation') if "affiliation" in self.request.args else None
                
            result=self.search_author(iid,max_results,page)
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