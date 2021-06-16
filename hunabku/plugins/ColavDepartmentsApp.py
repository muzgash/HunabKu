from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId
from pymongo import ASCENDING,DESCENDING
from pickle import load
from math import log
from datetime import date

class ColavDepartmentsApp(HunabkuPluginBase):
    def __init__(self, hunabku):
        super().__init__(hunabku)

    def get_info(self,idx):
        self.db = self.dbclient["antioquia"]
        department = self.db['branches'].find_one({"type":"department","_id":ObjectId(idx)})
        if department:
            entry={"id":department["_id"],
                "name":department["name"],
                "type":department["type"],
                "abbreviations":"",
                "external_urls":department["external_urls"],
                "groups":[],
                "authors":[],
                "institution":[]
            }
            if len(department["abbreviations"])>0:
                entry["abbreviations"]=department["abbreviations"][0]
            inst_id=""
            for rel in department["relations"]:
                if rel["type"]=="university":
                    inst_id=rel["id"]
                    break
            if inst_id:
                inst=self.db['institutions'].find_one({"_id":inst_id})
                if inst:
                    entry["institution"]=[{"name":inst["name"],"id":inst_id,"logo":inst["logo_url"]}]

            for author in self.db['authors'].find({"branches.id":department["_id"]}):
                author_entry={
                    "full_name":author["full_name"],
                    "id":str(author["_id"])
                }
                entry["authors"].append(author_entry)
                for branch in author["branches"]:
                    if branch["type"]=="group" and branch["id"]:
                        branch_db=self.db["branches"].find_one({"_id":ObjectId(branch["id"])})
                        entry_group={
                            "id":branch["id"],
                            "name":branch_db["name"]
                        }
                        if not entry_group in entry["groups"]:
                            entry["groups"].append(entry_group)

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
            result=self.db['documents'].find({"authors.affiliations.branches.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.affiliations.branches.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]

            pipeline=[
                    {"$match":{"authors.affiliations.branches.id":ObjectId(idx)}}
            ]

            if start_year and not end_year:
                cites_pipeline=[
                    {"$match":{"year_published":{"$gte":start_year},"authors.affiliations.branches.id":ObjectId(idx)}}
                ]
            elif end_year and not start_year:
                cites_pipeline=[
                    {"$match":{"year_published":{"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}}
                ]
            elif start_year and end_year:
                cites_pipeline=[
                    {"$match":{"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}}
                ]
            else:
                cites_pipeline=[
                    {"$match":{"authors.affiliations.branches.id":ObjectId(idx)}}
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
                {"$match":{"authors.affiliations.branches.id":ObjectId(idx)}}
            ]
            result=self.db['documents'].find({"authors.affiliations.branches.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.affiliations.branches.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]
            if start_year and not end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year},"authors.affiliations.branches.id":ObjectId(idx)}}
                ]
            elif end_year and not start_year:
                pipeline=[
                    {"$match":{"year_published":{"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}}
                ]
            elif start_year and end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}}
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
            {"id":reg["_id"],"full_name":reg["author"]["full_name"],"count":reg["count"]} for reg in self.db["documents"].aggregate(pipeline)
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
    
    def get_invisible_colleges(self,idx=None,start_year=None,end_year=None):
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
                {"$match":{"authors.affiliations.id":ObjectId(idx)}}
            ]
            result=self.db['documents'].find({"authors.affiliations.branches.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.affiliations.branches.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]
            if start_year and not end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year},"authors.affiliations.branches.id":ObjectId(idx)}}
                ]
            elif end_year and not start_year:
                pipeline=[
                    {"$match":{"year_published":{"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}}
                ]
            elif start_year and end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}}
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

        entry=[
            {
                "words":[{"x":"colombia","value":45},
                        {"x":"patients","value":32},
                        {"x":"effect","value":30},
                        {"x":"infection","value":28},
                        {"x":"factors","value":12}],
                "total_papers":120,
                "papers_count":65,
                "cites_count":300,
                "affiliation":{"name":"Universidad de Antioquia","id":ObjectId("60120afa4749273de6161883")},
                "icid":"243ab4565bygcvh57",
                "yearly_papers":{
                    2007:34,
                    2008:2,
                    2009:44,
                    2010:23,
                    2011:12,
                    2012:41,
                    2013:75,
                    2014:15,
                    2015:24,
                    2016:1,
                    2017:31,
                    2018:9,
                    2019:11,
                    2020:28}
            },
            {
                "words":[{"x":"colombia","value":45},
                        {"x":"study","value":32},
                        {"x":"properties","value":30},
                        {"x":"characterization","value":18},
                        {"x":"activity","value":10}],
                "total_papers":160,
                "papers_count":19,
                "cites_count":56,
                "affiliation":{"name":"Universidad de Antioquia","id":ObjectId("60120afa4749273de6161883")},
                "icid":"24b54574h57",
                "yearly_papers":{
                    2007:1,
                    2008:1,
                    2009:3,
                    2010:5,
                    2011:13,
                    2012:22,
                    2013:1,
                    2014:4,
                    2015:8,
                    2016:1,
                    2017:1,
                    2018:1,
                    2019:3,
                    2020:8}
            },
            {
                "words":[{"x":"analysis","value":45},
                        {"x":"disease","value":22},
                        {"x":"treatment","value":20},
                        {"x":"model","value":12},
                        {"x":"natural","value":2}],
                "total_papers":260,
                "papers_count":12,
                "cites_count":30,
                "affiliation":{"name":"Universidad de Antioquia","id":ObjectId("60120afa4749273de6161883")},
                "icid":"2431h45675cvh57",
                "yearly_papers":{
                    2007:4,
                    2008:0,
                    2009:4,
                    2010:3,
                    2011:2,
                    2012:1,
                    2013:5,
                    2014:5,
                    2015:4,
                    2016:1,
                    2017:1,
                    2018:9,
                    2019:1,
                    2020:8}
            },
            {
                "words":[{"x":"clinical","value":45},
                        {"x":"infection","value":12},
                        {"x":"human","value":8},
                        {"x":"review","value":8},
                        {"x":"vaccine","value":5}],
                "total_papers":180,
                "papers_count":20,
                "cites_count":10,
                "affiliation":{"name":"Universidad de Antioquia","id":ObjectId("60120afa4749273de6161883")},
                "icid":"243vrrwecvh57",
                "yearly_papers":{
                    2007:4,
                    2008:2,
                    2009:4,
                    2010:3,
                    2011:1,
                    2012:1,
                    2013:7,
                    2014:5,
                    2015:2,
                    2016:1,
                    2017:1,
                    2018:9,
                    2019:11,
                    2020:2}
            },
            {
                "words":[{"x":"colombia","value":75},
                        {"x":"human","value":40},
                        {"x":"rights","value":15},
                        {"x":"property","value":8},
                        {"x":"case","value":8}],
                "total_papers":60,
                "papers_count":14,
                "cites_count":30,
                "affiliation":{"name":"Universidad de Antioquia","id":ObjectId("60120afa4749273de6161883")},
                "icid":"2431c3t56fgwec7",
                "yearly_papers":{
                    2007:3,
                    2008:2,
                    2009:4,
                    2010:2,
                    2011:1,
                    2012:4,
                    2013:7,
                    2014:1,
                    2015:2,
                    2016:1,
                    2017:3,
                    2018:9,
                    2019:1,
                    2020:2}
            },
        ]

        filters={
            "start_year":initial_year,
            "end_year":final_year
        }

        return {"data":entry,"filters":filters}
    
    def get_invisible_college_info(self,idx=None,icidx=None,start_year=None,end_year=None):
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
                {"$match":{"authors.affiliations.id":ObjectId(idx)}}
            ]
            result=self.db['documents'].find({"authors.affiliations.branches.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.affiliations.branches.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]
            if start_year and not end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year},"authors.affiliations.branches.id":ObjectId(idx)}}
                ]
            elif end_year and not start_year:
                pipeline=[
                    {"$match":{"year_published":{"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}}
                ]
            elif start_year and end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}}
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

        entry={
            "citation_network":{"nodes":load(open("./nodes.p","rb")),"edges":load(open("./edges.p","rb"))},
            "coauthors_network":{"nodes":load(open("./nodes.p","rb")),"edges":load(open("./edges.p","rb"))},
            "geo": [{"country": "Colombia","country_code": "CO","count": 815,"log_count": 6.703188113240863},
                    {"country": "Peru","country_code": "PE","count": 21,"log_count": 3.044522437723423},
                    {"country": "Cuba","country_code": "CU","count": 33,"log_count": 3.4965075614664802},
                    {"country": "Spain","country_code": "ES","count": 88,"log_count": 4.477336814478207}
                    ],
            "institution_coauthorship_count":[
                {
                    "id": "60120ad04749273de615ff3d",
                    "name": "Macquarie University",
                    "logo": "",
                    "count":2
                },
                {
                    "id": "60120ad04749273de615ff46",
                    "name": "University of Melbourne",
                    "logo": "",
                    "count":5
                },
                {
                    "id": "606a5df2aa884b9a156456a2",
                    "name": "UNAM",
                    "logo": "",
                    "count":12
                }
            ]
        }
        
        filters={}

        return {"data":entry,"filters":filters}

    def get_venn(self,venn_query):
        venn_source={
            "scholar":0,"lens":0,"wos":0,"scopus":0,
            "scholar_lens":0,"scholar_wos":0,"scholar_scopus":0,"lens_wos":0,"lens_scopus":0,"wos_scopus":0,
            "scholar_lens_wos":0,"scholar_wos_scopus":0,"scholar_lens_scopus":0,"lens_wos_scopus":0,
            "scholar_lens_wos_scopus":0
        }
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":{"$ne":"lens"}},
                {"source_checked.source":{"$ne":"wos"}},
                {"source_checked.source":{"$ne":"scopus"}}]
        venn_source["scholar"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":{"$ne":"scholar"}},
                {"source_checked.source":"lens"},
                {"source_checked.source":{"$ne":"wos"}},
                {"source_checked.source":{"$ne":"scopus"}}]
        venn_source["lens"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":{"$ne":"scholar"}},
                {"source_checked.source":{"$ne":"lens"}},
                {"source_checked.source":"wos"},
                {"source_checked.source":{"$ne":"scopus"}}]
        venn_source["wos"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":{"$ne":"scholar"}},
                {"source_checked.source":{"$ne":"lens"}},
                {"source_checked.source":{"$ne":"wos"}},
                {"source_checked.source":"scopus"}]
        venn_source["scopus"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":"lens"},
                {"source_checked.source":{"$ne":"wos"}},
                {"source_checked.source":{"$ne":"scopus"}}]
        venn_source["scholar_lens"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":{"$ne":"lens"}},
                {"source_checked.source":"wos"},
                {"source_checked.source":{"$ne":"scopus"}}]
        venn_source["scholar_wos"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":{"$ne":"lens"}},
                {"source_checked.source":{"$ne":"wos"}},
                {"source_checked.source":"scopus"}]
        venn_source["scholar_scopus"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":{"$ne":"scholar"}},
                {"source_checked.source":"lens"},
                {"source_checked.source":"wos"},
                {"source_checked.source":{"$ne":"scopus"}}]
        venn_source["lens_wos"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":{"$ne":"scholar"}},
                {"source_checked.source":"lens"},
                {"source_checked.source":{"$ne":"wos"}},
                {"source_checked.source":"scopus"}]
        venn_source["lens_scopus"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":{"$ne":"scholar"}},
                {"source_checked.source":{"$ne":"lens"}},
                {"source_checked.source":"wos"},
                {"source_checked.source":"scopus"}]
        venn_source["wos_scopus"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":"lens"},
                {"source_checked.source":"wos"},
                {"source_checked.source":{"$ne":"scopus"}}]
        venn_source["scholar_lens_wos"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":{"$ne":"lens"}},
                {"source_checked.source":"wos"},
                {"source_checked.source":"scopus"}]
        venn_source["scholar_wos_scopus"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":"lens"},
                {"source_checked.source":{"$ne":"wos"}},
                {"source_checked.source":"scopus"}]
        venn_source["scholar_lens_scopus"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":{"$ne":"scholar"}},
                {"source_checked.source":"lens"},
                {"source_checked.source":"wos"},
                {"source_checked.source":"scopus"}]
        venn_source["lens_wos_scopus"]=self.db['documents'].count_documents(venn_query)
        venn_query["$and"]=[{"source_checked.source":"scholar"},
                {"source_checked.source":"lens"},
                {"source_checked.source":"wos"},
                {"source_checked.source":"scopus"}]
        venn_source["scholar_lens_wos_scopus"]=self.db['documents'].count_documents(venn_query)

        return venn_source

    def get_production(self,idx=None,max_results=100,page=1,start_year=None,end_year=None,sort=None,direction=None):
        self.db = self.dbclient["antioquia"]
        papers=[]
        initial_year=0
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
            result=self.db['documents'].find({"authors.affiliations.branches.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.affiliations.branches.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]
            if start_year and not end_year:
                cursor=self.db['documents'].find({"year_published":{"$gte":start_year},"authors.affiliations.branches.id":ObjectId(idx)})
                venn_query={"year_published":{"$gte":start_year},"authors.affiliations.branches.id":ObjectId(idx)}
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","year_published":{"$gte":start_year},"authors.affiliations.branches.id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","year_published":{"$gte":start_year},"authors.affiliations.branches.id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","year_published":{"$gte":start_year},"authors.affiliations.branches.id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","year_published":{"$gte":start_year},"authors.affiliations.branches.id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","year_published":{"$gte":start_year},"authors.affiliations.branches.id":ObjectId(idx)})}
            elif end_year and not start_year:
                cursor=self.db['documents'].find({"year_published":{"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)})
                venn_query={"year_published":{"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","year_published":{"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","year_published":{"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","year_published":{"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","year_published":{"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","year_published":{"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)})}
            elif start_year and end_year:
                cursor=self.db['documents'].find({"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)})
                venn_query={"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)})}
            else:
                cursor=self.db['documents'].find({"authors.affiliations.branches.id":ObjectId(idx)})
                venn_query={"authors.affiliations.branches.id":ObjectId(idx)}
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","authors.affiliations.branches.id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","authors.affiliations.branches.id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","authors.affiliations.branches.id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","authors.affiliations.branches.id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","authors.affiliations.branches.id":ObjectId(idx)})}
        else:
            cursor=self.db['documents'].find()
            venn_query={}
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
            
        return {
            "data":papers,
            "open_access":open_access,
            "venn_source":self.get_venn(venn_query),
            "count":len(papers),
            "page":page,
            "total_results":total,
            "filters":{
                "start_year":initial_year,
                "end_year":final_year
                }
            }
        
    def get_csv(self,idx=None,start_year=None,end_year=None,sort=None,direction=None):
        self.db = self.dbclient["antioquia"]
        papers=[]
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
                cursor=self.db['documents'].find({"year_published":{"$gte":start_year},"authors.affiliations.branches.id":ObjectId(idx)})
            elif end_year and not start_year:
                cursor=self.db['documents'].find({"year_published":{"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)})
            elif start_year and end_year:
                cursor=self.db['documents'].find({"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)})
            else:
                cursor=self.db['documents'].find({"authors.affiliations.branches.id":ObjectId(idx)})
        else:
            cursor=self.db['documents'].find()

        if sort=="citations" and direction=="ascending":
            cursor.sort([("citations_count",ASCENDING)])
        if sort=="citations" and direction=="descending":
            cursor.sort([("citations_count",DESCENDING)])
        if sort=="year" and direction=="ascending":
            cursor.sort([("year_published",ASCENDING)])
        if sort=="year" and direction=="descending":
            cursor.sort([("year_published",DESCENDING)])

        csv_text="id\tpublication_type\ttitle\tsubtitle\tabstract\tbibtex\tstart_page\tend_page\tyear_published\tdate_published\t"
        csv_text+="funding_organization\tfunding_details\tis_open_access\topen_access_status\tdoi\tjournal_name\tpublisher\tissn\t"
        csv_text+="author_id\tauthor_name\taffiliation_id\taffiliation_name\taffiliation_country\n"

        for paper in cursor:
            csv_text+=str(paper["_id"])
            csv_text+="\t"+paper["publication_type"]
            csv_text+="\t"+paper["titles"][0]["title"].replace("\t","").replace("\n","").replace("\r","")
            csv_text+="\t"+paper["subtitle"].replace("\t","").replace("\n","").replace("\r","")
            csv_text+="\t"+paper["abstract"].replace("\t","").replace("\n","").replace("\r","")
            csv_text+="\t"+paper["bibtex"].replace("\t","").replace("\n","").replace("\r","")
            csv_text+="\t"+str(paper["start_page"])
            csv_text+="\t"+str(paper["end_page"])
            csv_text+="\t"+str(paper["year_published"])
            try:
                ts=int(paper["date_published"])
                csv_text+="\t"+date.fromtimestamp(ts).strftime("%d-%m-%Y")
            except:
                csv_text+="\t"+""
            csv_text+="\t"+paper["funding_organization"].replace("\t","").replace("\n","").replace("\r","")
            csv_text+="\t"+paper["funding_details"][0].replace("\t","").replace("\n","").replace("\r","") if isinstance(paper["funding_details"],list) else "\t"+paper["funding_details"].replace("\t","").replace("\n","").replace("\r","")
            csv_text+="\t"+str(paper["is_open_access"])
            csv_text+="\t"+paper["open_access_status"]
            doi_entry=""
            for ext in paper["external_ids"]:
                if ext["source"]=="doi":
                    doi_entry=ext["id"]
            csv_text+="\t"+str(doi_entry)

            source=self.db["sources"].find_one({"_id":paper["source"]["id"]})
            if source:
                csv_text+="\t"+source["title"].replace("\t","").replace("\n","").replace("\r","")
                csv_text+="\t"+source["publisher"]
                serial_entry=""
                for serial in source["serials"]:
                    if serial["type"]=="issn" or serial["type"]=="eissn" or serial["type"]=="pissn":
                        serial_entry=serial["value"]
                csv_text+="\t"+serial_entry

            csv_text+="\t"+str(paper["authors"][0]["id"])
            author_db=self.db["authors"].find_one({"_id":paper["authors"][0]["id"]})
            if author_db:
                csv_text+="\t"+author_db["full_name"]
            else:
                csv_text+="\t"+""
            aff_db=""
            if "affiliations" in paper["authors"][0].keys():
                if len(paper["authors"][0]["affiliations"])>0:
                    csv_text+="\t"+str(paper["authors"][0]["affiliations"][0]["id"])
                    aff_db=self.db["institutions"].find_one({"_id":paper["authors"][0]["affiliations"][0]["id"]})
            if aff_db:
                csv_text+="\t"+aff_db["name"]
                country_entry=""
                if "addresses" in aff_db.keys():
                    if len(aff_db["addresses"])>0:
                        country_entry=aff_db["addresses"][0]["country"]
                csv_text+="\t"+country_entry
            else:
                csv_text+="\t"+""
                csv_text+="\t"+""
                csv_text+="\t"+""
            csv_text+="\n"
        return csv_text

    def get_json(self,idx=None,start_year=None,end_year=None,sort=None,direction=None):
        self.db = self.dbclient["antioquia"]
        papers=[]
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
                cursor=self.db['documents'].find({"year_published":{"$gte":start_year},"authors.affiliations.branches.id":ObjectId(idx)})
            elif end_year and not start_year:
                cursor=self.db['documents'].find({"year_published":{"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)})
            elif start_year and end_year:
                cursor=self.db['documents'].find({"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)})
            else:
                cursor=self.db['documents'].find({"authors.affiliations.branches.id":ObjectId(idx)})
        else:
            cursor=self.db['documents'].find()

        if sort=="citations" and direction=="ascending":
            cursor.sort([("citations_count",ASCENDING)])
        if sort=="citations" and direction=="descending":
            cursor.sort([("citations_count",DESCENDING)])
        if sort=="year" and direction=="ascending":
            cursor.sort([("year_published",ASCENDING)])
        if sort=="year" and direction=="descending":
            cursor.sort([("year_published",DESCENDING)])

        for paper in cursor:
            entry=paper
            source=self.db["sources"].find_one({"_id":paper["source"]["id"]})
            if source:
                entry["source"]=source
            authors=[]
            for author in paper["authors"]:
                au_entry=author
                author_db=self.db["authors"].find_one({"_id":author["id"]})
                if author_db:
                    au_entry=author_db
                if "aliases" in au_entry.keys():
                    del(au_entry["aliases"])
                if "national_id" in au_entry.keys():
                    del(au_entry["national_id"])
                affiliations=[]
                for aff in author["affiliations"]:
                    aff_entry=aff
                    aff_db=self.db["institutions"].find_one({"_id":aff["id"]})
                    if aff_db:
                        aff_entry=aff_db
                    if "addresses" in aff_entry.keys():
                        for add in aff_entry["addresses"]:
                            if "geonames_city" in add.keys():
                                del(add["geonames_city"])
                    if "aliases" in aff_entry.keys():
                        del(aff_entry["aliases"])
                    branches=[]
                    if "branches" in aff.keys():
                        for branch in aff["branches"]:
                            branch_db=self.db["branches"].find_one({"_id":branch["id"]}) if "id" in branch.keys() else ""
                            if branch_db:
                                del(branch_db["aliases"])
                                if "addresses" in branch_db.keys():
                                    for add in branch_db["addresses"]:
                                        del(add["geonames_city"])
                                if "aliases" in branch_db.keys():
                                    del(branch_db["aliases"])
                                branches.append(branch_db)
                    aff_entry["branches"]=branches
                    affiliations.append(aff_entry)
                au_entry["affiliations"]=affiliations
                authors.append(au_entry)
            entry["authors"]=authors
            papers.append(entry)
        return str(papers)

    @endpoint('/app/departments', methods=['GET'])
    def app_department(self):
        """
        @api {get} /app/departments Departments
        @apiName app
        @apiGroup CoLav app
        @apiDescription Responds with information about a department

        @apiParam {String} apikey Credential for authentication
        @apiParam {String} data (info,production) Whether is the general information or the production
        @apiParam {Object} id The mongodb id of the department requested
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
                    "_id": "602ef784728ecc2d8e62d4e0",
                    "title": "A randomized clinical trial of unfractioned heparin for treatment of sepsis (the HETRASE study): design and rationale [NCT00100308]",
                    "source": {
                        "name": "Trials",
                        "_id": "600f50261fc9947fc8a8dd6c"
                    },
                    "authors": [
                        {
                        "full_name": "Fabian Alberto Jaimes Barragan",
                        "_id": "5fcec8bb3d00fffc91d2a658",
                        "affiliations": [
                            {
                            "name": "Johns Hopkins University",
                            "_id": "60120ad54749273de6160481",
                            "branches": []
                            },
                            {
                            "name": "University of Antioquia",
                            "_id": "60120afa4749273de6161883",
                            "branches": [
                                {
                                "name": "Facultad de medicina",
                                "type": "faculty",
                                "_id": "602c50d1fd74967db066383b"
                                },
                                {
                                "name": "Departamento de medicina interna",
                                "type": "department",
                                "_id": "602c50f9fd74967db0663895"
                                },
                                {
                                "name": "Grupo académico de epidemiología clínica",
                                "type": "group",
                                "_id": "602c510ffd74967db0663947"
                                }
                            ]
                            }
                        ]
                        },
                        {
                        "full_name": "Gisela De La Rosa",
                        "_id": "602ef784728ecc2d8e62d4dd",
                        "affiliations": [
                            {
                            "name": "University of Antioquia",
                            "_id": "60120afa4749273de6161883",
                            "branches": []
                            }
                        ]
                        },
                        {
                        "full_name": "Clara Maria Arango Toro",
                        "_id": "5fceb6163d00fffc91d2a641",
                        "affiliations": [
                            {
                            "name": "University of Antioquia",
                            "_id": "60120afa4749273de6161883",
                            "branches": [
                                {
                                "name": "Facultad de medicina",
                                "type": "faculty",
                                "_id": "602c50d1fd74967db066383b"
                                },
                                {
                                "name": "Departamento de medicina interna",
                                "type": "department",
                                "_id": "602c50f9fd74967db0663895"
                                },
                                {
                                "name": "Grupo endocrinología y metabolismo",
                                "type": "group",
                                "_id": "602c510ffd74967db0663a13"
                                }
                            ]
                            }
                        ]
                        },
                        {
                        "full_name": "Fernando Fortich",
                        "_id": "602ef784728ecc2d8e62d4de",
                        "affiliations": [
                            {
                            "name": "University of Antioquia",
                            "_id": "60120afa4749273de6161883",
                            "branches": []
                            }
                        ]
                        },
                        {
                        "full_name": "Carlos H. Morales",
                        "_id": "602ef784728ecc2d8e62d4df",
                        "affiliations": [
                            {
                            "name": "University of Antioquia",
                            "_id": "60120afa4749273de6161883",
                            "branches": []
                            }
                        ]
                        },
                        {
                        "full_name": "Daniel Camilo Aguirre Acevedo",
                        "_id": "5fcf8d123d00fffc91d2a6be",
                        "affiliations": [
                            {
                            "name": "University of Antioquia",
                            "_id": "60120afa4749273de6161883",
                            "branches": [
                                {
                                "name": "Facultad de medicina",
                                "type": "faculty",
                                "_id": "602c50d1fd74967db066383b"
                                },
                                {
                                "name": "Instituto de investigaciones médicas",
                                "type": "department",
                                "_id": "602c50f9fd74967db066389e"
                                },
                                {
                                "name": "Inmunodeficiencias primarias",
                                "type": "group",
                                "_id": "602c510ffd74967db0663969"
                                }
                            ]
                            }
                        ]
                        },
                        {
                        "full_name": "Pablo Javier Patiño Grajales",
                        "_id": "5fce960f3d00fffc91d2a62c",
                        "affiliations": [
                            {
                            "name": "University of Antioquia",
                            "_id": "60120afa4749273de6161883",
                            "branches": [
                                {
                                "name": "Facultad de medicina",
                                "type": "faculty",
                                "_id": "602c50d1fd74967db066383b"
                                },
                                {
                                "name": "Departamento de microbiología y parasitología",
                                "type": "department",
                                "_id": "602c50f9fd74967db0663894"
                                },
                                {
                                "name": "Inmunodeficiencias primarias",
                                "type": "group",
                                "_id": "602c510ffd74967db0663969"
                                }
                            ]
                            }
                        ]
                        }
                    ]
                    }
                ],
                "count": 44,
                "page": 1,
                "total_results": 44,
                "initial_year": 1997,
                "final_year": 2019,
                "open_access": {
                    "green": 3,
                    "gold": 16,
                    "bronze": 7,
                    "closed": 17,
                    "hybrid": 1
                },
                "venn_source": {
                    "scholar": 0,
                    "lens": 0,
                    "oadoi": 0,
                    "wos": 0,
                    "scopus": 0,
                    "lens_wos_scholar_scopus": 34,
                    "lens_scholar": 5,
                    "lens_scholar_scopus": 4,
                    "lens_wos_scholar": 1
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
        elif data=="colleges":
            idx = self.request.args.get('id')
            start_year=self.request.args.get('start_year')
            end_year=self.request.args.get('end_year')
            colleges=self.get_invisible_colleges(idx,start_year,end_year)
            if colleges:
                response = self.app.response_class(
                response=self.json.dumps(colleges),
                status=200,
                mimetype='application/json'
                )
            else:
                response = self.app.response_class(
                response=self.json.dumps({"status":"Request returned empty"}),
                status=204,
                mimetype='application/json'
                )
        elif data=="college":
            idx = self.request.args.get('id')
            icidx = self.request.args.get('icid')
            start_year=self.request.args.get('start_year')
            end_year=self.request.args.get('end_year')
            college=self.get_invisible_college_info(idx,icidx,start_year,end_year)
            if college:
                response = self.app.response_class(
                response=self.json.dumps(college),
                status=200,
                mimetype='application/json'
                )
            else:
                response = self.app.response_class(
                response=self.json.dumps({"status":"Request returned empty"}),
                status=204,
                mimetype='application/json'
                )
        elif data=="csv":
            idx = self.request.args.get('id')
            start_year=self.request.args.get('start_year')
            end_year=self.request.args.get('end_year')
            sort=self.request.args.get('sort')
            production_csv=self.get_csv(idx,start_year,end_year,sort,"descending")
            if production_csv:
                response = self.app.response_class(
                response=production_csv,
                status=200,
                mimetype='text/csv',
                headers={"Content-disposition":
                 "attachment; filename=departments.csv"}
                )
            else:
                response = self.app.response_class(
                response=self.json.dumps({"status":"Request returned empty"}),
                status=204,
                mimetype='application/json'
                )
        elif data=="json":
            idx = self.request.args.get('id')
            start_year=self.request.args.get('start_year')
            end_year=self.request.args.get('end_year')
            sort=self.request.args.get('sort')
            production_json=self.get_json(idx,start_year,end_year,sort,"descending")
            if production_json:
                response = self.app.response_class(
                response=production_json,
                status=200,
                mimetype='text/plain',
                headers={"Content-disposition":
                 "attachment; filename=departments.json"}
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

