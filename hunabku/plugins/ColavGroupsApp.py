from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId
from pymongo import ASCENDING,DESCENDING

class ColavGroupsApp(HunabkuPluginBase):
    def __init__(self, hunabku):
        super().__init__(hunabku)

    def get_info(self,idx):
        self.db = self.dbclient["antioquia"]
        group = self.db['branches'].find_one({"type":"group","_id":ObjectId(idx)})
        if group:
            entry={"id":group["_id"],
                "name":group["name"],
                "type":group["type"],
                "abbreviations":"",
                "external_urls":group["external_urls"],
                "departments":[],
                "groups":[],
                "authors":[],
                "institution":[]
            }
            if len(group["abbreviations"])>0:
                entry["abbreviations"]=group["abbreviations"][0]
            inst_id=""
            for rel in group["relations"]:
                if rel["type"]=="university":
                    inst_id=rel["id"]
                    break
            if inst_id:
                inst=self.db['institutions'].find_one({"_id":inst_id})
                if inst:
                    entry["institution"]=[{"name":inst["name"],"id":inst_id,"logo":""}]

            for author in self.db['authors'].find({"branches.id":group["_id"]}):
                author_entry={
                    "full_name":author["full_name"],
                    "id":str(author["_id"])
                }
                entry["authors"].append(author_entry)
            return entry
        else:
            return None

    def get_production(self,idx=None,max_results=100,page=1,start_year=None,end_year=None,sort=None,direction=None):
        self.db = self.dbclient["antioquia"]
        papers=[]
        initial_year=9999
        final_year=0
        total=0
        open_access={}
        venn_source={"scholar":0,"lens":0,"oadoi":0,"wos":0,"scopus":0}
        if start_year:
            try:
                start_year=int(start_year)
            except:
                print("Could not convert start year to int")
                return None
        if end_year:
            try:
                end_year=int(end_year)
            except:
                print("Could not convert end year to int")
                return None
        if idx:
            if start_year and not end_year:
                cursor=self.db['documents'].find({"year_published":{"$gte":start_year},"authors.affiliations.branches._id":ObjectId(idx)})
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","year_published":{"$gte":start_year},"authors.affiliations.branches._id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","year_published":{"$gte":start_year},"authors.affiliations.branches._id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","year_published":{"$gte":start_year},"authors.affiliations.branches._id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","year_published":{"$gte":start_year},"authors.affiliations.branches._id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","year_published":{"$gte":start_year},"authors.affiliations.branches._id":ObjectId(idx)})}
            elif end_year and not start_year:
                cursor=self.db['documents'].find({"year_published":{"$lte":end_year},"authors.affiliations.branches._id":ObjectId(idx)})
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","year_published":{"$lte":end_year},"authors.affiliations.branches._id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","year_published":{"$lte":end_year},"authors.affiliations.branches._id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","year_published":{"$lte":end_year},"authors.affiliations.branches._id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","year_published":{"$lte":end_year},"authors.affiliations.branches._id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","year_published":{"$lte":end_year},"authors.affiliations.branches._id":ObjectId(idx)})}
            elif start_year and end_year:
                cursor=self.db['documents'].find({"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches._id":ObjectId(idx)})
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches._id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches._id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches._id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches._id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches._id":ObjectId(idx)})}
            else:
                cursor=self.db['documents'].find({"authors.affiliations.branches._id":ObjectId(idx)})
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","authors.affiliations.branches._id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","authors.affiliations.branches._id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","authors.affiliations.branches._id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","authors.affiliations.branches._id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","authors.affiliations.branches._id":ObjectId(idx)})}
        else:
            cursor=self.db['documents'].find()
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

        if sort=="citations" and direction=="ascending":
            cursor.sort([("citations_count",ASCENDING)])
        if sort=="citations" and direction=="descending":
            cursor.sort([("citations_count",DESCENDING)])
        if sort=="year" and direction=="ascending":
            cursor.sort([("year_published",ASCENDING)])
        if sort=="year" and direction=="descending":
            cursor.sort([("year_published",DESCENDING)])

        for paper in cursor:
            entry={
                "id":paper["_id"],
                "title":paper["titles"][0]["title"],
                "citations_count":paper["citations_count"],
                "year_published":paper["year_published"]
            }

            if paper["year_published"]<initial_year:
                initial_year=paper["year_published"]
            if paper["year_published"]>final_year:
                final_year=paper["year_published"]

            sources_checked=[]
            for source in paper["source_checked"]:
                if not source["source"] in sources_checked:
                    sources_checked.append(source["source"])
            if "_".join(sources_checked) in venn_source.keys():
                venn_source["_".join(sources_checked)]+=1
            else:
                venn_source["_".join(sources_checked)]=1

            source=self.db["sources"].find_one({"_id":paper["source"]["_id"]})
            if source:
                entry["source"]={"name":source["title"],"_id":str(source["_id"])}
            authors=[]
            for author in paper["authors"]:
                au_entry={}
                author_db=self.db["authors"].find_one({"_id":author["_id"]})
                if author_db:
                    au_entry={"full_name":author_db["full_name"],"_id":author_db["_id"]}
                affiliations=[]
                for aff in author["affiliations"]:
                    aff_entry={}
                    aff_db=self.db["institutions"].find_one({"_id":aff["_id"]})
                    if aff_db:
                        aff_entry={"name":aff_db["name"],"_id":aff_db["_id"]}
                    branches=[]
                    if "branches" in aff.keys():
                        for branch in aff["branches"]:
                            branch_db=self.db["branches"].find_one({"_id":branch["_id"]})
                            if branch_db:
                                branches.append({"name":branch_db["name"],"type":branch_db["type"],"_id":branch_db["_id"]})
                    aff_entry["branches"]=branches
                    affiliations.append(aff_entry)
                au_entry["affiliations"]=affiliations
                authors.append(au_entry)
            entry["authors"]=authors
            papers.append(entry)
        if initial_year==9999:
            initial_year=0
        return {
            "data":papers,
            "count":len(papers),
            "page":page,
            "total_results":total,
            "filters":{
                "initial_year":initial_year,
                "final_year":final_year,
                "open_access":open_access,
                "venn_source":venn_source
                }
            }

    @endpoint('/app/groups', methods=['GET'])
    def app_groups(self):
        """
        @api {get} /app/groups Groups
        @apiName app
        @apiGroup CoLav app
        @apiDescription Responds with information about a group

        @apiParam {String} apikey Credential for authentication
        @apiParam {String} data (info,production) Whether is the general information or the production
        @apiParam {Object} id The mongodb id of the group requested
        @apiParam {Int} start_year Retrieves result starting on this year
        @apiParam {Int} end_year Retrieves results up to this year
        @apiParam {Int} max Maximum results per page
        @apiParam {Int} page Number of the page
        @apiParam {String} sort (citations,year) Sorts the results by key in descending order

        @apiError (Error 401) msg  The HTTP 401 Unauthorized invalid authentication apikey for the target resource.
        @apiError (Error 204) msg  The HTTP 204 No Content.
        @apiError (Error 200) msg  The HTTP 200 OK.

        @apiSuccessExample {json} Success-Response (data=info):
            HTTP/1.1 200 OK
            {
                "id": "602c50d1fd74967db0663833",
                "name": "Facultad de ciencias exactas y naturales",
                "type": "faculty",
                "external_urls": [
                    {
                    "source": "website",
                    "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/unidades-academicas/ciencias-exactas-naturales"
                    }
                ],
                "departments": [
                    {
                    "id": "602c50f9fd74967db0663858",
                    "name": "Instituto de matemáticas"
                    }
                ],
                "groups": [
                    {
                    "id": "602c510ffd74967db06639a7",
                    "name": "Modelación con ecuaciones diferenciales"
                    },
                    {
                    "id": "602c510ffd74967db06639ad",
                    "name": "álgebra u de a"
                    }
                ],
                "authors": [
                    {
                    "full_name": "Roberto Cruz Rodes",
                    "id": "5fc5a419b246cc0887190a64"
                    },
                    {
                    "full_name": "Jairo Eloy Castellanos Ramos",
                    "id": "5fc5a4b7b246cc0887190a65"
                    }
                ],
                "institution": [
                    {
                    "name": "University of Antioquia",
                    "id": "60120afa4749273de6161883"
                    }
                ]
                }
        @apiSuccessExample {json} Success-Response (data=production):
            HTTP/1.1 200 OK
            {
                "data": [
                    {
                    "_id": "602ef9dd728ecc2d8e62e030",
                    "title": "Comments on the Riemann conjecture and index theory on Cantorian fractal space-time",
                    "source": {
                        "name": "Chaos Solitons & Fractals",
                        "_id": "602ef9dd728ecc2d8e62e02d"
                    },
                    "authors": [
                        {
                        "full_name": "Carlos Castro",
                        "_id": "602ef9dd728ecc2d8e62e02f",
                        "affiliations": [
                            {
                            "name": "Center for Theoretical Studies, University of Miami",
                            "_id": "602ef9dd728ecc2d8e62e02e",
                            "branches": []
                            }
                        ]
                        },
                        {
                        "full_name": "Jorge Eduardo Mahecha Gomez",
                        "_id": "5fc65863b246cc0887190a9f",
                        "affiliations": [
                            {
                            "name": "University of Antioquia",
                            "_id": "60120afa4749273de6161883",
                            "branches": [
                                {
                                "name": "Facultad de ciencias exactas y naturales",
                                "type": "faculty",
                                "_id": "602c50d1fd74967db0663833"
                                },
                                {
                                "name": "Instituto de física",
                                "type": "department",
                                "_id": "602c50f9fd74967db0663859"
                                },
                                {
                                "name": "Grupo de física atómica y molecular",
                                "type": "group",
                                "_id": "602c510ffd74967db06638fb"
                                }
                            ]
                            }
                        ]
                        }
                    ]
                    }
                ],
                "count": 3,
                "page": 1,
                "total_results": 3,
                "initial_year": 2002,
                "final_year": 2014,
                "open_access": {
                    "green": 2,
                    "gold": 0,
                    "bronze": 1,
                    "closed": 0,
                    "hybrid": 0
                },
                "venn_source": {
                    "scholar": 0,
                    "lens": 0,
                    "oadoi": 0,
                    "wos": 0,
                    "scopus": 0,
                    "lens_wos_scholar_scopus": 3
                }
                }
        """
        data = self.request.args.get('data')
        if not self.valid_apikey():
            return self.apikey_error()
        if data=="info":
            idx = self.request.args.get('id')
            info = self.get_info(idx)
            if info:    
                response = self.app.response_class(
                response=self.json.dumps(info),
                status=200,
                mimetype='application/json'
                )
            else:
                response = self.app.response_class(
                response=self.json.dumps({"status":"Request returned empty"}),
                status=204,
                mimetype='application/json'
            )
        elif data=="production":
            idx = self.request.args.get('id')
            max_results=self.request.args.get('max')
            page=self.request.args.get('page')
            start_year=self.request.args.get('start_year')
            end_year=self.request.args.get('end_year')
            sort=self.request.args.get('sort')
            production=self.get_production(idx,max_results,page,start_year,end_year,sort,"descending")
            if production:
                response = self.app.response_class(
                response=self.json.dumps(production),
                status=200,
                mimetype='application/json'
                )
            else:
                response = self.app.response_class(
                response=self.json.dumps({"status":"Request returned empty"}),
                status=204,
                mimetype='application/json'
                )
        else:
            response = self.app.response_class(
                response=self.json.dumps({}),
                status=400,
                mimetype='application/json'
            )

        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
