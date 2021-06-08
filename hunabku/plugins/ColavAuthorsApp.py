from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId
from pymongo import ASCENDING,DESCENDING
from pickle import load
from math import log

class ColavAuthorsApp(HunabkuPluginBase):
    def __init__(self, hunabku):
        super().__init__(hunabku)

    def get_info(self,idx):
        self.db = self.dbclient["antioquia"]
        author = self.db['authors'].find_one({"_id":ObjectId(idx)})
        if author:
            entry={"id":author["_id"],
                "full_name":author["full_name"],
                "type":"author",
                "affiliation":[],
                "country":"",
                "country_code":"",
                "faculty":{},
                "department":{},
                "group":{},
                "external_urls":[],
            }
            if "affiliations" in author.keys():
                if len(author["affiliations"]):
                    entry["affiliation"]=author["affiliations"][-1]
            if entry["affiliation"]:
                inst_db=self.db["institutions"].find_one({"_id":ObjectId(entry["affiliation"]["id"])})
                if inst_db:
                    entry["country_code"]=inst_db["addresses"][0]["country_code"]
                    entry["country"]=inst_db["addresses"][0]["country"]
                    entry["logo"]=inst_db["logo_url"]
            sources=[]
            for ext in author["external_ids"]:
                if ext["source"]=="researchid" and not "researcherid" in sources:
                    sources.append("researcherid")
                    entry["external_urls"].append({
                        "source":"researcherid",
                        "url":"https://publons.com/researcher/"+ext["value"]})
                if ext["source"]=="scopus" and not "scopus" in sources:
                    sources.append("scopus")
                    entry["external_urls"].append({
                        "source":"scopus",
                        "url":"https://www.scopus.com/authid/detail.uri?authorId="+ext["value"]})
                if ext["source"]=="scholar" and not "scholar" in sources:
                    sources.append("scholar")
                    entry["external_urls"].append({
                        "source":"scholar",
                        "url":"https://scholar.google.com.co/citations?user="+ext["value"]})
                if ext["source"]=="orcid" and not "orcid" in sources:
                    sources.append("orcid")
                    entry["external_urls"].append({
                        "source":"orcid",
                        "url":"https://orcid.org/"+ext["value"]})

            for branch in author["branches"]:
                if branch["type"]=="faculty":
                    entry["faculty"]=branch
                elif branch["type"]=="department":
                    entry["department"]=branch
                elif branch["type"]=="group":
                    entry["group"]=branch

            return entry
        else:
            return None

    def hindex(self,citation_list):
        return sum(x >= i + 1 for i, x in enumerate(sorted(list(citation_list), reverse=True)))
    
    def get_citations(self,idx=None,start_year=None,end_year=None):
        self.db = self.dbclient["antioquia"]
        initial_year=0
        final_year=0

        entry={
            "citations":0,
            "H5":0,
            "H":0,
            "yearly_citations":{}
        }

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
            result=self.db['documents'].find({"authors.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]

            pipeline=[
                    {"$match":{"authors.id":ObjectId(idx)}}
            ]
            if start_year and not end_year:
                cites_pipeline=[
                    {"$match":{"year_published":{"$gte":start_year},"authors.id":ObjectId(idx)}}
                ]
            elif end_year and not start_year:
                cites_pipeline=[
                    {"$match":{"year_published":{"$lte":end_year},"authors.id":ObjectId(idx)}}
                ]
            elif start_year and end_year:
                cites_pipeline=[
                    {"$match":{"year_published":{"$gte":start_year,"$lte":end_year},"authors.id":ObjectId(idx)}}
                ]
            else:
                cites_pipeline=[
                    {"$match":{"authors.id":ObjectId(idx)}}
                ]
        
        else:
            pipeline=[]
            cites_pipeline=[]
            result=self.db['documents'].find({},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]

        pipeline.extend([
            {"$project":{
                "_id":0,"year_published":1,"citations_count":1
            }}
        ])

        cites5_list=[]
        cites_list=[]
        now=date.today()
        for idx,reg in enumerate(self.db["documents"].aggregate(pipeline)):
            if reg["year_published"]<now.year:
                cites_list.append(reg["citations_count"])
                if reg["year_published"]>now.year-5:
                    cites5_list.append(reg["citations_count"])
        entry["H5"]=self.hindex(cites5_list)
        entry["H"]=self.hindex(cites_list)

        cites_pipeline.extend([
            {"$unwind":"$citations"},
            {"$lookup":{
                "from":"documents",
                "localField":"citations",
                "foreignField":"_id",
                "as":"citation"}
            },
            {"$unwind":"$citation"},
            {"$project":{"citation.year_published":1}},
            {"$group":{
                "_id":"$citation.year_published","count":{"$sum":1}}
            },
            {"$sort":{
                "_id":-1
            }}
        ])

        for idx,reg in enumerate(self.db["documents"].aggregate(cites_pipeline)):
            entry["citations"]+=reg["count"]
            entry["yearly_citations"][reg["_id"]]=reg["count"]

        filters={
            "start_year":initial_year,
            "end_year":final_year
        }
        return {"data":entry,"filters":filters}

    def get_coauthors(self,idx=None,start_year=None,end_year=None):
        self.db = self.dbclient["antioquia"]
        initial_year=0
        final_year=0

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
            pipeline=[
                {"$match":{"authors.id":ObjectId(idx)}}
            ]
            result=self.db['documents'].find({"authors.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]
            if start_year and not end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year},"authors.id":ObjectId(idx)}}
                ]
            elif end_year and not start_year:
                pipeline=[
                    {"$match":{"year_published":{"$lte":end_year},"authors.id":ObjectId(idx)}}
                ]
            elif start_year and end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year,"$lte":end_year},"authors.id":ObjectId(idx)}}
                ]
                
        else:
            pipeline=[]
            result=self.db['documents'].find({},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]

        pipeline.extend([
            {"$unwind":"$authors"},
            {"$unwind":"$authors.affiliations"},
            {"$group":{"_id":"$authors.id","count":{"$sum":1}}},
            {"$sort":{"count":-1}},
            {"$lookup":{"from":"authors","localField":"_id","foreignField":"_id","as":"author"}},
            {"$project":{"count":1,"author.full_name":1}},
            {"$unwind":"$author"}
        ])

        entry={
            "coauthors":[],
            "geo":[],
            "coauthors_network":{"nodes":load(open("./nodes.p","rb")),"edges":load(open("./edges.p","rb"))},
            "institution_network":{"nodes":load(open("./nodes.p","rb")),"edges":load(open("./edges.p","rb"))}
        }

        entry["coauthors"]=[
            {"id":reg["_id"],"full_name":reg["author"]["full_name"],"count":reg["count"]} for reg in self.db["documents"].aggregate(pipeline) if reg["_id"] != ObjectId(idx)
        ]

        countries=[]
        country_list=[]
        pipeline=[pipeline[0]]
        pipeline.extend([
            {"$unwind":"$authors"},
            {"$group":{"_id":"$authors.affiliations.id","count":{"$sum":1}}},
            {"$unwind":"$_id"},
            {"$lookup":{"from":"institutions","localField":"_id","foreignField":"_id","as":"affiliation"}},
            {"$project":{"count":1,"affiliation.addresses.country_code":1,"affiliation.addresses.country":1}},
            {"$unwind":"$affiliation"},
            {"$unwind":"$affiliation.addresses"},
            {"$sort":{"count":-1}}
        ])
        for reg in self.db["documents"].aggregate(pipeline):
            #print(reg)
            if str(reg["_id"])==idx:
                continue
            if not "country_code" in reg["affiliation"]["addresses"].keys():
                continue
            if reg["affiliation"]["addresses"]["country_code"] and reg["affiliation"]["addresses"]["country"]:
                if reg["affiliation"]["addresses"]["country_code"] in country_list:
                    i=country_list.index(reg["affiliation"]["addresses"]["country_code"])
                    countries[i]["count"]+=reg["count"]
                else:
                    country_list.append(reg["affiliation"]["addresses"]["country_code"])
                    countries.append({
                        "country":reg["affiliation"]["addresses"]["country"],
                        "country_code":reg["affiliation"]["addresses"]["country_code"],
                        "count":reg["count"]
                    })
        sorted_geo=sorted(countries,key=lambda x:x["count"],reverse=True)
        countries=sorted_geo
        for item in countries:
            item["log_count"]=log(item["count"])
        entry["geo"]=countries
                        
        filters={
            "start_year":initial_year,
            "end_year":final_year
        }

        return {"data":entry,"filters":filters}

    def get_venn(self,venn_query):
        venn_source={
            "scholar":0,"lens":0,"scielo":0,"scopus":0,
            "scholar_lens":0,"scholar_scielo":0,"scholar_scopus":0,"lens_scielo":0,"lens_scopus":0,"scielo_scopus":0,
            "scholar_lens_scielo":0,"scholar_scielo_scopus":0,"scholar_lens_scopus":0,"lens_scielo_scopus":0,
            "scholar_lens_scielo_scopus":0
        }
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":{"$ne":"lens"}},
                {"source_checked.source":{"$ne":"scielo"}},
                {"source_checked.source":{"$ne":"scopus"}}]
        venn_source["scholar"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":{"$ne":"scholar"}},
                {"source_checked.source":"lens"},
                {"source_checked.source":{"$ne":"scielo"}},
                {"source_checked.source":{"$ne":"scopus"}}]
        venn_source["lens"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":{"$ne":"scholar"}},
                {"source_checked.source":{"$ne":"lens"}},
                {"source_checked.source":"scielo"},
                {"source_checked.source":{"$ne":"scopus"}}]
        venn_source["scielo"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":{"$ne":"scholar"}},
                {"source_checked.source":{"$ne":"lens"}},
                {"source_checked.source":{"$ne":"scielo"}},
                {"source_checked.source":"scopus"}]
        venn_source["scopus"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":"lens"},
                {"source_checked.source":{"$ne":"scielo"}},
                {"source_checked.source":{"$ne":"scopus"}}]
        venn_source["scholar_lens"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":{"$ne":"lens"}},
                {"source_checked.source":"scielo"},
                {"source_checked.source":{"$ne":"scopus"}}]
        venn_source["scholar_scielo"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":{"$ne":"lens"}},
                {"source_checked.source":{"$ne":"scielo"}},
                {"source_checked.source":"scopus"}]
        venn_source["scholar_scopus"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":{"$ne":"scholar"}},
                {"source_checked.source":"lens"},
                {"source_checked.source":"scielo"},
                {"source_checked.source":{"$ne":"scopus"}}]
        venn_source["lens_scielo"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":{"$ne":"scholar"}},
                {"source_checked.source":"lens"},
                {"source_checked.source":{"$ne":"scielo"}},
                {"source_checked.source":"scopus"}]
        venn_source["lens_scopus"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":{"$ne":"scholar"}},
                {"source_checked.source":{"$ne":"lens"}},
                {"source_checked.source":"scielo"},
                {"source_checked.source":"scopus"}]
        venn_source["scielo_scopus"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":"lens"},
                {"source_checked.source":"scielo"},
                {"source_checked.source":{"$ne":"scopus"}}]
        venn_source["scholar_lens_scielo"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":{"$ne":"lens"}},
                {"source_checked.source":"scielo"},
                {"source_checked.source":"scopus"}]
        venn_source["scholar_scielo_scopus"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":"lens"},
                {"source_checked.source":{"$ne":"scielo"}},
                {"source_checked.source":"scopus"}]
        venn_source["scholar_lens_scopus"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":{"$ne":"scholar"}},
                {"source_checked.source":"lens"},
                {"source_checked.source":"scielo"},
                {"source_checked.source":"scopus"}]
        venn_source["lens_scielo_scopus"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":"lens"},
                {"source_checked.source":"scielo"},
                {"source_checked.source":"scopus"}]
        venn_source["scholar_lens_scielo_scopus"]=self.db['documents'].count_documents(venn_query)

        return venn_source

    def get_production(self,idx=None,max_results=100,page=1,start_year=None,end_year=None,sort=None,direction=None):
        self.db = self.dbclient["antioquia"]
        papers=[]
        initial_year=9999
        final_year=0
        total=0
        open_access={}
        
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
            result=self.db['documents'].find({"authors.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]
            if start_year and not end_year:
                cursor=self.db['documents'].find({"year_published":{"$gte":start_year},"authors.id":ObjectId(idx)})
                venn_query={"year_published":{"$gte":start_year},"authors.id":ObjectId(idx)}
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","year_published":{"$gte":start_year},"authors.id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","year_published":{"$gte":start_year},"authors.id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","year_published":{"$gte":start_year},"authors.id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","year_published":{"$gte":start_year},"authors.id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","year_published":{"$gte":start_year},"authors.id":ObjectId(idx)})}
            elif end_year and not start_year:
                cursor=self.db['documents'].find({"year_published":{"$lte":end_year},"authors.id":ObjectId(idx)})
                venn_query={"year_published":{"$lte":end_year},"authors.id":ObjectId(idx)}
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","year_published":{"$lte":end_year},"authors.id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","year_published":{"$lte":end_year},"authors.id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","year_published":{"$lte":end_year},"authors.id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","year_published":{"$lte":end_year},"authors.id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","year_published":{"$lte":end_year},"authors.id":ObjectId(idx)})}
            elif start_year and end_year:
                cursor=self.db['documents'].find({"year_published":{"$gte":start_year,"$lte":end_year},"authors.id":ObjectId(idx)})
                venn_query={"year_published":{"$gte":start_year,"$lte":end_year},"authors.id":ObjectId(idx)}
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","year_published":{"$gte":start_year,"$lte":end_year},"authors.id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","year_published":{"$gte":start_year,"$lte":end_year},"authors.id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","year_published":{"$gte":start_year,"$lte":end_year},"authors.id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","year_published":{"$gte":start_year,"$lte":end_year},"authors.id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","year_published":{"$gte":start_year,"$lte":end_year},"authors.id":ObjectId(idx)})}
            else:
                cursor=self.db['documents'].find({"authors.id":ObjectId(idx)})
                venn_query={"authors.id":ObjectId(idx)}
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","authors.id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","authors.id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","authors.id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","authors.id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","authors.id":ObjectId(idx)})}
        else:
            cursor=self.db['documents'].find()
            venn_query={}
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
                "year_published":paper["year_published"],
                "open_access_status":paper["open_access_status"]
            }

            source=self.db["sources"].find_one({"_id":paper["source"]["id"]})
            if source:
                entry["source"]={"name":source["title"],"id":str(source["_id"])}
            authors=[]
            for author in paper["authors"]:
                au_entry={}
                author_db=self.db["authors"].find_one({"_id":author["id"]})
                if author_db:
                    au_entry={"full_name":author_db["full_name"],"id":author_db["_id"]}
                affiliations=[]
                for aff in author["affiliations"]:
                    aff_entry={}
                    aff_db=self.db["institutions"].find_one({"_id":aff["id"]})
                    if aff_db:
                        aff_entry={"name":aff_db["name"],"id":aff_db["_id"]}
                    branches=[]
                    if "branches" in aff.keys():
                        for branch in aff["branches"]:
                            if "id" in branch.keys():
                                branch_db=self.db["branches"].find_one({"_id":branch["id"]})
                                if branch_db:
                                    branches.append({"name":branch_db["name"],"type":branch_db["type"],"id":branch_db["_id"]})
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
            "venn_source":self.get_venn(venn_query),
            "open_access":open_access,
            "filters":{
                "start_year":initial_year,
                "end_year":final_year
            }
        }

    @endpoint('/app/authors', methods=['GET'])
    def app_authors(self):
        """
        @api {get} /app/authors Authors
        @apiName app
        @apiGroup CoLav app
        @apiDescription Responds with information about an author

        @apiParam {String} apikey Credential for authentication
        @apiParam {String} data (info,production) Whether is the general information or the production
        @apiParam {Object} id The mongodb id of the author requested
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
            "id": "5fc66fdfb246cc0887190aa6",
            "full_name": "Diego Alejandro Restrepo Quintero",
            "affiliation": {
                "id": "60120afa4749273de6161883",
                "name": "University of Antioquia"
            },
            "country": "Colombia",
            "country_code": "CO",
            "faculty": {
                "name": "Facultad de Ciencias Exactas y Naturales",
                "type": "faculty",
                "id": "602c50d1fd74967db0663833"
            },
            "department": {
                "name": "Instituto de Física",
                "type": "department",
                "id": "602c50f9fd74967db0663859"
            },
            "group": {
                "name": "Grupo de Fenomenologia de Interacciones Fundamentales",
                "type": "group",
                "id": "602c510ffd74967db06638f9"
            },
            "external_urls": [
                {
                "source": "scopus",
                "url": "https://www.scopus.com/authid/detail.uri?authorId=7005721136"
                },
                {
                "source": "orcid",
                "url": "https://orcid.org/0000-0001-6455-5564"
                },
                {
                "source": "researcherid",
                "url": "https://publons.com/researcher/E-6977-2013"
                }
            ]
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
        elif data=="citations":
            idx = self.request.args.get('id')
            start_year=self.request.args.get('start_year')
            end_year=self.request.args.get('end_year')
            citations=self.get_citations(idx,start_year,end_year)
            if citations:
                response = self.app.response_class(
                response=self.json.dumps(citations),
                status=200,
                mimetype='application/json'
                )
            else:
                response = self.app.response_class(
                response=self.json.dumps({"status":"Request returned empty"}),
                status=204,
                mimetype='application/json'
                )
        elif data=="coauthors":
            idx = self.request.args.get('id')
            start_year=self.request.args.get('start_year')
            end_year=self.request.args.get('end_year')
            coauthors=self.get_coauthors(idx,start_year,end_year)
            if coauthors:
                response = self.app.response_class(
                response=self.json.dumps(coauthors),
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

