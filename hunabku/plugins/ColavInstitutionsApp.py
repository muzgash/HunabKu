from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId

class ColavInstitutionsApp(HunabkuPluginBase):
    def __init__(self, hunabku):
        super().__init__(hunabku)

    def get_info(self,idx):
        self.db = self.dbclient["antioquia"]
        institution = self.db['institutions'].find_one({"_id":ObjectId(idx)})
        if institution:
            entry={"id":institution["_id"],
                "name":institution["name"],
                "external_urls":institution["external_urls"],
                "departments":[],
                "faculties":[],
                "area_groups":[],
                "logo":""
            }

            for dep in self.db['branches'].find({"type":"department","relations.id":ObjectId(idx)}):
                dep_entry={
                    "name":dep["name"],
                    "id":str(dep["_id"])
                }
                entry["departments"].append(dep_entry)
            
            for fac in self.db['branches'].find({"type":"faculty","relations.id":ObjectId(idx)}):
                fac_entry={
                    "name":fac["name"],
                    "id":str(fac["_id"])
                }
                entry["faculties"].append(fac_entry)
            
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
                cursor=self.db['documents'].find({"year_published":{"$gte":start_year},"authors.affiliations._id":ObjectId(idx)})
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","year_published":{"$gte":start_year},"authors.affiliations._id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","year_published":{"$gte":start_year},"authors.affiliations._id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","year_published":{"$gte":start_year},"authors.affiliations._id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","year_published":{"$gte":start_year},"authors.affiliations._id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","year_published":{"$gte":start_year},"authors.affiliations._id":ObjectId(idx)})}
            elif end_year and not start_year:
                cursor=self.db['documents'].find({"year_published":{"$lte":end_year},"authors.affiliations._id":ObjectId(idx)})
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","year_published":{"$lte":end_year},"authors.affiliations._id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","year_published":{"$lte":end_year},"authors.affiliations._id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","year_published":{"$lte":end_year},"authors.affiliations._id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","year_published":{"$lte":end_year},"authors.affiliations._id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","year_published":{"$lte":end_year},"authors.affiliations._id":ObjectId(idx)})}
            elif start_year and end_year:
                cursor=self.db['documents'].find({"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations._id":ObjectId(idx)})
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations._id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations._id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations._id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations._id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations._id":ObjectId(idx)})}
            else:
                cursor=self.db['documents'].find({"authors.affiliations._id":ObjectId(idx)})
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","authors.affiliations._id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","authors.affiliations._id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","authors.affiliations._id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","authors.affiliations._id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","authors.affiliations._id":ObjectId(idx)})}
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
            cursor.sort({"citations_count":pymongo.ASCENDING})
        if sort=="citations" and direction=="descending":
            cursor.sort({"citations_count":pymongo.DESCENDING})
        if sort=="year" and direction=="ascending":
            cursor.sort({"year_published":pymongo.ASCENDING})
        if sort=="year" and direction=="descending":
            cursor.sort({"year_published":pymongo.DESCENDING})

        for paper in cursor:
            entry={
                "_id":paper["_id"],
                "title":paper["titles"][0]["title"],
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
        return {
            "data":papers,
            "count":len(papers),
            "page":page,
            "total_results":total,
            "initial_year":initial_year,
            "final_year":final_year,
            "open_access":open_access,
            "venn_source":venn_source}

    @endpoint('/app/institutions', methods=['GET'])
    def app_institutions(self):
        """
        @api {get} /app/institutions Institutions
        @apiName app
        @apiGroup CoLav app
        @apiDescription Responds with information about the institutions

        @apiParam {String} apikey Credential for authentication
        @apiParam {String} data (info,production) Whether is the general information or the production
        @apiParam {Object} id The mongodb id of the institution requested
        @apiParam {Int} start_year Retrieves result starting on this year
        @apiParam {Int} end_year Retrieves results up to this year
        @apiParam {Int} max Maximum results per page
        @apiParam {Int} page Number of the page
        @apiParam {String} sort (citations,year) Sorts the results by key in descending order

        @apiError (Error 401) msg  The HTTP 401 Unauthorized invalid authentication apikey for the target resource.
        @apiError (Error 204) msg  The HTTP 204 No Content.
        @apiError (Error 200) msg  The HTTP 200 OK.

        @apiSuccessExample {json} Success-Response (data=info):
        {
            "id": "60120afa4749273de6161883",
            "name": "University of Antioquia",
            "external_urls": [
                {
                "source": "wikipedia",
                "url": "http://en.wikipedia.org/wiki/University_of_Antioquia"
                },
                {
                "source": "site",
                "url": "http://www.udea.edu.co/portal/page/portal/EnglishPortal/EnglishPortal"
                }
            ],
            "departments": [
                {
                "name": "Departamento de artes visuales",
                "id": "602c50f9fd74967db0663854"
                },
                {
                "name": "Departamento de música",
                "id": "602c50f9fd74967db0663855"
                },
                {
                "name": "Departamento de teatro",
                "id": "602c50f9fd74967db0663856"
                },
                {
                "name": "Decanatura facultad de artes",
                "id": "602c50f9fd74967db0663857"
                },
                {
                "name": "Instituto de matemáticas",
                "id": "602c50f9fd74967db0663858"
                },
                {
                "name": "Instituto de física",
                "id": "602c50f9fd74967db0663859"
                },
                {
                "name": "Instituto de biología",
                "id": "602c50f9fd74967db066385a"
                },
                {
                "name": "Instituto de química",
                "id": "602c50f9fd74967db066385b"
                },
                {
                "name": "Departamento de bioquímica",
                "id": "602c50f9fd74967db0663891"
                },
                {
                "name": "Departamento de farmacología y toxicología",
                "id": "602c50f9fd74967db0663892"
                },
                {
                "name": "Departamento de patología",
                "id": "602c50f9fd74967db0663893"
                },
                {
                "name": "Departamento de microbiología y parasitología",
                "id": "602c50f9fd74967db0663894"
                },
                {
                "name": "Departamento de medicina interna",
                "id": "602c50f9fd74967db0663895"
                },
                {
                "name": "Departamento de cirugía",
                "id": "602c50f9fd74967db0663896"
                }
            ],
            "faculties": [
                {
                "name": "Facultad de artes",
                "id": "602c50d1fd74967db0663830"
                },
                {
                "name": "Facultad de ciencias agrarias",
                "id": "602c50d1fd74967db0663831"
                },
                {
                "name": "Facultad de ciencias económicas",
                "id": "602c50d1fd74967db0663832"
                },
                {
                "name": "Facultad de ciencias exactas y naturales",
                "id": "602c50d1fd74967db0663833"
                },
                {
                "name": "Facultad de ciencias farmacéuticas y alimentarias",
                "id": "602c50d1fd74967db0663834"
                },
                {
                "name": "Facultad de ciencias sociales y humanas",
                "id": "602c50d1fd74967db0663835"
                },
                {
                "name": "Facultad de comunicaciones y filología",
                "id": "602c50d1fd74967db0663836"
                },
                {
                "name": "Facultad de derecho y ciencias políticas",
                "id": "602c50d1fd74967db0663837"
                },
                {
                "name": "Facultad de educación",
                "id": "602c50d1fd74967db0663838"
                },
                {
                "name": "Facultad de enfermería",
                "id": "602c50d1fd74967db0663839"
                },
                {
                "name": "Facultad de ingeniería",
                "id": "602c50d1fd74967db066383a"
                },
                {
                "name": "Facultad de medicina",
                "id": "602c50d1fd74967db066383b"
                },
                {
                "name": "Facultad de odontología",
                "id": "602c50d1fd74967db066383c"
                },
                {
                "name": "Facultad de salud pública",
                "id": "602c50d1fd74967db066383d"
                },
                {
                "name": "Escuela de idiomas",
                "id": "602c50d1fd74967db066383e"
                },
                {
                "name": "Escuela interamericana de bibliotecología",
                "id": "602c50d1fd74967db066383f"
                },
                {
                "name": "Escuela de microbiología",
                "id": "602c50d1fd74967db0663840"
                },
                {
                "name": "Escuela de nutrición y dietética",
                "id": "602c50d1fd74967db0663841"
                },
                {
                "name": "Instituto de filosofía",
                "id": "602c50d1fd74967db0663842"
                },
                {
                "name": "Instituto universitario de educación física y deporte",
                "id": "602c50d1fd74967db0663843"
                },
                {
                "name": "Instituto de estudios políticos",
                "id": "602c50d1fd74967db0663844"
                },
                {
                "name": "Instituto de estudios regionales",
                "id": "602c50d1fd74967db0663845"
                },
                {
                "name": "Corporación académica ambiental",
                "id": "602c50d1fd74967db0663846"
                },
                {
                "name": "Corporación académica ciencias básicas biomédicas",
                "id": "602c50d1fd74967db0663847"
                },
                {
                "name": "Corporación académica para el estudio de patologías tropicales",
                "id": "602c50d1fd74967db0663848"
                }
            ],
            "area_groups": [],
            "logo": ""
        }
        @apiSuccessExample {json} Success-Response (data=production):
            {
                "data": [
                    {
                    "_id": "602ef788728ecc2d8e62d4f1",
                    "title": "Product and quotient of correlated beta variables",
                    "source": {
                        "name": "Applied Mathematics Letters",
                        "_id": "602ef788728ecc2d8e62d4ef"
                    },
                    "authors": [
                        {
                        "full_name": "Daya Krishna Nagar",
                        "_id": "5fc5b0a5b246cc0887190a69",
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
                                "name": "Instituto de matemáticas",
                                "type": "department",
                                "_id": "602c50f9fd74967db0663858"
                                },
                                {
                                "name": "Análisis multivariado",
                                "type": "group",
                                "_id": "602c510ffd74967db06638d6"
                                }
                            ]
                            }
                        ]
                        },
                        {
                        "full_name": "Johanna Marcela Orozco Castañeda",
                        "_id": "5fc5bebab246cc0887190a70",
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
                                "name": "Instituto de matemáticas",
                                "type": "department",
                                "_id": "602c50f9fd74967db0663858"
                                }
                            ]
                            }
                        ]
                        },
                        {
                        "full_name": "Daya Krishna Nagar",
                        "_id": "5fc5b0a5b246cc0887190a69",
                        "affiliations": [
                            {
                            "name": "Bowling Green State University",
                            "_id": "60120add4749273de616099f",
                            "branches": []
                            },
                            {
                            "name": "Univ Antioquia",
                            "_id": "602ef788728ecc2d8e62d4f0",
                            "branches": []
                            }
                        ]
                        }
                    ]
                    }
                ],
                "count": 73,
                "page": 1,
                "total_results": 73,
                "initial_year": 1995,
                "final_year": 2017,
                "open_access": {
                    "green": 9,
                    "gold": 17,
                    "bronze": 6,
                    "closed": 39,
                    "hybrid": 2
                },
                "venn_source": {
                    "scholar": 0,
                    "lens": 0,
                    "oadoi": 0,
                    "wos": 0,
                    "scopus": 0,
                    "lens_wos_scholar_scopus": 55,
                    "lens_scholar": 6,
                    "lens_scholar_scopus": 6,
                    "lens_wos_scholar": 6
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
