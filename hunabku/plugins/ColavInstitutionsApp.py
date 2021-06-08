from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId
from pymongo import ASCENDING,DESCENDING
from pickle import load
from currency_converter import CurrencyConverter
from datetime import date
from math import log

class ColavInstitutionsApp(HunabkuPluginBase):
    def __init__(self, hunabku):
        super().__init__(hunabku)

    def get_info(self,idx):
        self.db = self.dbclient["antioquia"]
        institution = self.db['institutions'].find_one({"_id":ObjectId(idx)})
        if institution:
            entry={"id":institution["_id"],
                "name":institution["name"],
                "type":"institution",
                "external_urls":institution["external_urls"],
                "departments":[],
                "faculties":[],
                "area_groups":[],
                "logo":institution["logo_url"]
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
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]

            pipeline=[
                    {"$match":{"authors.affiliations.id":ObjectId(idx)}}
            ]
            if start_year and not end_year:
                cites_pipeline=[
                    {"$match":{"year_published":{"$gte":start_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            elif end_year and not start_year:
                cites_pipeline=[
                    {"$match":{"year_published":{"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            elif start_year and end_year:
                cites_pipeline=[
                    {"$match":{"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            else:
                cites_pipeline=[
                    {"$match":{"authors.affiliations.id":ObjectId(idx)}}
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
                {"$match":{"authors.affiliations.id":ObjectId(idx)}}
            ]
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]
            if start_year and not end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            elif end_year and not start_year:
                pipeline=[
                    {"$match":{"year_published":{"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            elif start_year and end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}}
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
            {"$group":{"_id":"$authors.affiliations.id","count":{"$sum":1}}},
            {"$sort":{"count":-1}},
            {"$unwind":"$_id"},
            {"$lookup":{"from":"institutions","localField":"_id","foreignField":"_id","as":"affiliation"}},
            {"$project":{"count":1,"affiliation.name":1}},
            {"$unwind":"$affiliation"}
        ])

        entry={
            "institutions":[],
            "geo":[],
            "institutions_network":{"nodes":load(open("./nodes.p","rb")),"edges":load(open("./edges.p","rb"))}
        }
 
        entry["institutions"]=[
            {"name":reg["affiliation"]["name"],"id":reg["_id"],"count":reg["count"]} for reg in self.db["documents"].aggregate(pipeline) if str(reg["_id"]) != idx
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
        for reg in self.db["documents"].aggregate(pipeline,allowDiskUse=True):
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

    def get_graduates_colleges(self,idx=None,start_year=None,end_year=None):
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
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]
            if start_year and not end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            elif end_year and not start_year:
                pipeline=[
                    {"$match":{"year_published":{"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            elif start_year and end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}}
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
                "words":[{"x":"colombia","value":45},{"x":"patients","value":32},{"x":"effect","value":30}],
                "papers_count":120,
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
                "words":[{"x":"colombia","value":45},{"x":"study","value":32},{"x":"properties","value":30}],
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
                "words":[{"x":"analysis","value":45},{"x":"disease","value":12},{"x":"treatment","value":5}],
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
                "words":[{"x":"clinical","value":45},{"x":"infection","value":12},{"x":"human","value":5}],
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
                "words":[{"x":"colombia","value":75},{"x":"human","value":40},{"x":"rights","value":5}],
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

    def get_graduates(self,idx=None,icidx=None,start_year=None,end_year=None):
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
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]
            if start_year and not end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            elif end_year and not start_year:
                pipeline=[
                    {"$match":{"year_published":{"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            elif start_year and end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}}
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
            "papers_count":1,
            "institutions_network":{"nodes":load(open("./nodes.p","rb")),"edges":load(open("./edges.p","rb"))},
            "countries_network":{"nodes":load(open("./nodes.p","rb")),"edges":load(open("./edges.p","rb"))},
            "word_cloud":[{'x': 'colombia', 'value': 64}, {'x': 'using', 'value': 52}, {'x': 'patients', 'value': 46},
            {'x': 'effect', 'value': 40}, {'x': 'study', 'value': 40}, {'x': 'analysis', 'value': 38}, {'x': 'colombian', 'value': 35},
            {'x': 'associated', 'value': 35}, {'x': 'disease', 'value': 32}, {'x': 'properties', 'value': 27}, {'x': 'colombia.', 'value': 25},
            {'x': 'clinical', 'value': 25}, {'x': 'human', 'value': 25}, {'x': 'cells', 'value': 24}, {'x': 'treatment', 'value': 23},
            {'x': 'cell', 'value': 23}, {'x': 'infection', 'value': 22}, {'x': 'characterization', 'value': 22}, {'x': 'activity', 'value': 22},
            {'x': 'review', 'value': 22}, {'x': 'pacientes', 'value': 22}, {'x': 'synthesis', 'value': 21}, {'x': 'acid', 'value': 20},
            {'x': 'virus', 'value': 20}, {'x': 'high', 'value': 20}, {'x': 'systematic', 'value': 20}, {'x': 'role', 'value': 19},
            {'x': 'model', 'value': 19}, {'x': 'tev', 'value': 19}, {'x': 'calidad', 'value': 18}, {'x': 'medellín,', 'value': 18}],
            "count_by_type":{"Académico":1,"Gubernamental":1,"Social":1,"Productivo":1},
            "geo": [{"country": "Colombia","country_code": "CO","count": 815,"log_count": 6.703188113240863},
                    {"country": "Peru","country_code": "PE","count": 21,"log_count": 3.044522437723423},
                    {"country": "Brazil","country_code": "BR","count": 33,"log_count": 3.4965075614664802}]
        }

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
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]
            if start_year and not end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            elif end_year and not start_year:
                pipeline=[
                    {"$match":{"year_published":{"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            elif start_year and end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}}
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
                "words":[{"x":"colombia","value":45},{"x":"patients","value":32},{"x":"effect","value":30}],
                "papers_count":120,
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
                "words":[{"x":"colombia","value":45},{"x":"study","value":32},{"x":"properties","value":30}],
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
                "words":[{"x":"analysis","value":45},{"x":"disease","value":12},{"x":"treatment","value":5}],
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
                "words":[{"x":"clinical","value":45},{"x":"infection","value":12},{"x":"human","value":5}],
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
                "words":[{"x":"colombia","value":75},{"x":"human","value":40},{"x":"rights","value":5}],
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
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]
            if start_year and not end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            elif end_year and not start_year:
                pipeline=[
                    {"$match":{"year_published":{"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            elif start_year and end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}}
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
            "geo":[{"country": "Colombia", "count": 5332, "country_code": "CO"}, {"country": "Switzerland", "count": 3314, "country_code": "CH"}, {"country": "Germany", "count": 3351, "country_code": "DE"}, {"country": "United Kingdom", "count": 2998, "country_code": "GB"}, {"country": "Belgium", "count": 2003, "country_code": "BE"}, {"country": "France", "count": 2695, "country_code": "FR"}, {"country": "Brazil", "count": 2579, "country_code": "BR"}, {"country": "Russia", "count": 1757, "country_code": "RU"}, {"country": "United States", "count": 19391, "country_code": "US"}, {"country": "Finland", "count": 573, "country_code": "FI"}, {"country": "Turkey", "count": 1096, "country_code": "TR"}, {"country": "India", "count": 1881, "country_code": "IN"}, {"country": "Cyprus", "count": 287, "country_code": "CY"}, {"country": "Greece", "count": 648, "country_code": "GR"}, {"country": "South Korea", "count": 1225, "country_code": "KR"}, {"country": "Italy", "count": 3375, "country_code": "IT"}, {"country": "Hungary", "count": 492, "country_code": "HU"}, {"country": "China", "count": 557, "country_code": "CN"}, {"country": "Spain", "count": 2975, "country_code": "ES"}, {"country": "Canada", "count": 893, "country_code": "CA"}, {"country": "Bulgaria", "count": 348, "country_code": "BG"}, {"country": "Croatia", "count": 183, "country_code": "HR"}, {"country": "Costa Rica", "count": 157, "country_code": "CR"}, {"country": "Serbia", "count": 147, "country_code": "RS"}, {"country": "Mexico", "count": 970, "country_code": "MX"}, {"country": "Poland", "count": 340, "country_code": "PL"}, {"country": "Chile", "count": 524, "country_code": "CL"}, {"country": "Taiwan", "count": 333, "country_code": "TW"}, {"country": "Peru", "count": 192, "country_code": "PE"}, {"country": "Netherlands", "count": 500, "country_code": "NL"}, {"country": "Lithuania", "count": 114, "country_code": "LT"}, {"country": "Czechia", "count": 114, "country_code": "CZ"}, {"country": "Pakistan", "count": 178, "country_code": "PK"}, {"country": "Thailand", "count": 121, "country_code": "TH"}, {"country": "Argentina", "count": 646, "country_code": "AR"}, {"country": "Malaysia", "count": 129, "country_code": "MY"}],
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
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]
            if start_year and not end_year:
                cursor=self.db['documents'].find({"year_published":{"$gte":start_year},"authors.affiliations.id":ObjectId(idx)})
                venn_query={"year_published":{"$gte":start_year},"authors.affiliations.id":ObjectId(idx)}
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","year_published":{"$gte":start_year},"authors.affiliations.id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","year_published":{"$gte":start_year},"authors.affiliations.id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","year_published":{"$gte":start_year},"authors.affiliations.id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","year_published":{"$gte":start_year},"authors.affiliations.id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","year_published":{"$gte":start_year},"authors.affiliations.id":ObjectId(idx)})}
            elif end_year and not start_year:
                cursor=self.db['documents'].find({"year_published":{"$lte":end_year},"authors.affiliations.id":ObjectId(idx)})
                venn_query={"year_published":{"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","year_published":{"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","year_published":{"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","year_published":{"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","year_published":{"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","year_published":{"$lte":end_year},"authors.affiliations.id":ObjectId(idx)})}
            elif start_year and end_year:
                cursor=self.db['documents'].find({"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.id":ObjectId(idx)})
                venn_query={"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.id":ObjectId(idx)})}
            else:
                cursor=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)})
                venn_query={"authors.affiliations.id":ObjectId(idx)}
                open_access={"green":self.db['documents'].count_documents({"open_access_status":"green","authors.affiliations.id":ObjectId(idx)}),
                    "gold":self.db['documents'].count_documents({"open_access_status":"gold","authors.affiliations.id":ObjectId(idx)}),
                    "bronze":self.db['documents'].count_documents({"open_access_status":"bronze","authors.affiliations.id":ObjectId(idx)}),
                    "closed":self.db['documents'].count_documents({"open_access_status":"closed","authors.affiliations.id":ObjectId(idx)}),
                    "hybrid":self.db['documents'].count_documents({"open_access_status":"hybrid","authors.affiliations.id":ObjectId(idx)})}
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
    
    def get_apc(self,idx=None,start_year=None,end_year=None):
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
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",ASCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    initial_year=result[0]["year_published"]
            result=self.db['documents'].find({"authors.affiliations.id":ObjectId(idx)},{"year_published":1}).sort([("year_published",DESCENDING)]).limit(1)
            if result:
                result=list(result)
                if len(result)>0:
                    final_year=result[0]["year_published"]

            if start_year and not end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            elif end_year and not start_year:
                pipeline=[
                    {"$match":{"year_published":{"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            elif start_year and end_year:
                pipeline=[
                    {"$match":{"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.id":ObjectId(idx)}}
                ]
            else:
                pipeline=[
                    {"$match":{"authors.affiliations.id":ObjectId(idx)}}
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
            "yearly":{},
            "faculty":{},
            "department":{},
            "group":{},
            "publisher":{},
            "openaccess":{}
        }

        pipeline.extend([
            {"$lookup":{"from":"sources","localField":"source.id","foreignField":"_id","as":"source"}},
            {"$project":{"authors":1,"source.apc_charges":1,"source.apc_currency":1,"source.publisher":1,"year_published":1,"open_access_status":1}},
            {"$match":{"source.apc_charges":{"$ne":""}}},
            {"$unwind":"$source"}
        ])

        c = CurrencyConverter()
        for reg in self.db["documents"].aggregate(pipeline):
            value=0
            if reg["source"]["apc_currency"]=="USD":
                value=reg["source"]["apc_charges"]
            else:
                try:
                    value=c.convert(reg["source"]["apc_charges"], reg["source"]["apc_currency"], 'USD')
                except Exception as e:
                    print("Could not convert currency with error: ",e)
            if reg["year_published"] in entry["yearly"].keys():
                entry["yearly"][reg["year_published"]]+=value
            else:
                entry["yearly"][reg["year_published"]]=value
            if reg["source"]["publisher"]:
                if reg["source"]["publisher"] in entry["publisher"].keys():
                    entry["publisher"][reg["source"]["publisher"]]+=value
                else:
                    entry["publisher"][reg["source"]["publisher"]]=value
            if reg["open_access_status"]:
                if reg["open_access_status"] in entry["openaccess"].keys():
                    entry["openaccess"][reg["open_access_status"]]+=value
                else:
                    entry["openaccess"][reg["open_access_status"]]=value
            found=0
            for author in reg["authors"]:
                for aff in author["affiliations"]:
                    if not "branches" in aff.keys():
                        continue
                    for branch in aff["branches"]:
                        if not "id" in branch.keys():
                            continue
                        if str(branch["type"])=="faculty":
                            if str(branch["id"]) in entry["faculty"].keys():
                                entry["faculty"][str(branch["id"])]["value"]+=value
                            else:
                                entry["faculty"][str(branch["id"])]={"name":branch["name"],"value":value}
                            found+=1
                        if branch["type"]=="department":
                            if str(branch["id"]) in entry["department"].keys():
                                entry["department"][str(branch["id"])]["value"]+=value
                            else:
                                entry["department"][str(branch["id"])]={"name":branch["name"],"value":value}
                            found+=1
                        if branch["type"]=="group":
                            if str(branch["id"]) in entry["group"].keys():
                                entry["group"][str(branch["id"])]["value"]+=value
                            else:
                                entry["group"][str(branch["id"])]={"name":branch["name"],"value":value}
                            found+=1
                if found>0:
                    break
        sorted_departments=sorted([{"id":key,"name":val["name"],"value":val["value"]} for key,val in entry["department"].items()],key=lambda x:x["value"],reverse=True)
        entry["department"]=sorted_departments
        sorted_groups=sorted([{"id":key,"name":val["name"],"value":val["value"]} for key,val in entry["group"].items()],key=lambda x:x["value"],reverse=True)
        entry["group"]=sorted_groups
        sorted_faculties=sorted([{"id":key,"name":val["name"],"value":val["value"]} for key,val in entry["faculty"].items()],key=lambda x:x["value"],reverse=True)
        entry["faculty"]=sorted_faculties
        sorted_publishers=sorted([{"name":key,"value":val} for key,val in entry["publisher"].items()],key=lambda x:x["value"],reverse=True)
        entry["publisher"]=sorted_publishers

        filters={
            "start_year":initial_year,
            "end_year":final_year
        }

        return {"data":entry,"filters":filters}

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
        @apiSuccessExample {json} Success-Response (data=citations):
            HTTP/1.1 200 OK
            {
                "data": {
                    "citations": 1815,
                    "H5": 8,
                    "yearly_citations": {
                    "2008": 10,
                    "2009": 137,
                    "2010": 240,
                    "2011": 11,
                    "2012": 46,
                    "2013": 67,
                    "2014": 88,
                    "2015": 166,
                    "2016": 66,
                    "2017": 87,
                    "2018": 35,
                    "2019": 4,
                    "2020": 4
                    },
                    "network": {}
                },
                "filters": {
                    "initial_year": 1995,
                    "final_year": 2020
                }
            }
        @apiSuccessExample {json} Success-Response (data=apc):
        HTTP/1.1 200 OK
        {
            "data": {
                "yearly": {
                "2006": 25333.215809352663,
                "2007": 31212.916051395667,
                "2008": 55634.25857670785,
                "2009": 54698.475858931975,
                "2010": 47683.47371715034,
                "2011": 84837.57770613344,
                "2012": 87631.29377989819,
                "2013": 106924.28252286707,
                "2014": 171037.16532375227,
                "2015": 159642.93025535543,
                "2016": 220892.6144583558,
                "2017": 246995.35012787356,
                "2018": 301777.0124037427,
                "2019": 346262.03413552087,
                "2020": 154102.28675748224
                },
                "faculty": {
                "602c50d1fd74967db066383b": {
                    "name": "Facultad de Medicina",
                    "value": 688505.4513403034
                },
                "602c50d1fd74967db066383a": {
                    "name": "Facultad de Ingeniería",
                    "value": 175085.68733245516
                },
                "602c50d1fd74967db0663833": {
                    "name": "Facultad de Ciencias Exactas y Naturales",
                    "value": 380902.37390428863
                },
                "602c50d1fd74967db0663831": {
                    "name": "Facultad de Ciencias Agrarias",
                    "value": 89374.5371867811
                },
                "602c50d1fd74967db0663835": {
                    "name": "Facultad de Ciencias Sociales y Humanas",
                    "value": 2237.28
                }
                },
                "department": {
                "602c50f9fd74967db0663895": {
                    "name": "Departamento de Medicina Interna",
                    "value": 69074.85558893369
                },
                "602c50f9fd74967db0663883": {
                    "name": "Departamento de Ingeniería Industrial",
                    "value": 2317.4396001110804
                },
                "602c50f9fd74967db066385a": {
                    "name": "Instituto de Biología",
                    "value": 182704.58261736613
                },
                "602c50f9fd74967db0663893": {
                    "name": "Departamento de Patología",
                    "value": 3711.3056
                },
                "602c50f9fd74967db066389c": {
                    "name": "Departamento de Medicina Física y Rehabilitación",
                    "value": 1890.3011862842297
                },
                "602c50f9fd74967db066385f": {
                    "name": "Departamento de Antropología",
                    "value": 300
                }
                },
                "group": {
                "602c510ffd74967db0663947": {
                    "name": "Grupo Académico de Epidemiología Clínica",
                    "value": 23510.433610132986
                },
                "602c510ffd74967db06638d9": {
                    "name": "Centro de Investigaciones Básicas y Aplicadas en Veterinaria",
                    "value": 12869.809579159686
                },
                "602c510ffd74967db06639d0": {
                    "name": "Grupo de Química-Física Teórica",
                    "value": 6156.785263507203
                },
                "609cbe1f2ecb2ac1eee78eb1": {
                    "name": "Grupo de Entomología Médica",
                    "value": 13696.310458738084
                },
                "602c510ffd74967db066390a": {
                    "name": "Inmunomodulación",
                    "value": 6536.5592890863645
                },
                "602c510ffd74967db0663919": {
                    "name": "Grupo de Investigación en Psicologia Cognitiva",
                    "value": 1937.2800000000002
                },
                "602c510ffd74967db06639dd": {
                    "name": "Ecología Lótica: Islas, Costas y Estuarios",
                    "value": 3586.559289086365
                },
                "602c510ffd74967db06639b1": {
                    "name": "Simulación, Diseño, Control y Optimización de Procesos",
                    "value": 1793.2796445431825
                },
                "602c510ffd74967db06639ff": {
                    "name": "Ciencia y Tecnología del Gas y Uso Racional de la Energía",
                    "value": 750
                },
                "602c510ffd74967db0663956": {
                    "name": "Grupo de Investigación en Gestión y Modelación Ambiental",
                    "value": 4445
                },
                "602c510ffd74967db0663990": {
                    "name": "Grupo Mapeo Genético",
                    "value": 376.97849989280576
                },
                "602c510ffd74967db0663a16": {
                    "name": "No lo encontre",
                    "value": 3100
                },
                "602c510ffd74967db0663970": {
                    "name": "Patología Renal y de Trasplantes",
                    "value": 2825
                },
                "602c510ffd74967db06639e9": {
                    "name": "Aerospace Science and Technology ReseArch",
                    "value": 2792.4396001110804
                },
                "602c510ffd74967db0663917": {
                    "name": "Grupo de Investigacion en Farmacologia y Toxicologia \" INFARTO\"",
                    "value": 5146.58644148918
                },
                "602c510ffd74967db06638d6": {
                    "name": "Análisis Multivariado",
                    "value": 975
                },
                "602c510ffd74967db066398b": {
                    "name": "Genética Médica",
                    "value": 2090.3011862842295
                },
                "602c510ffd74967db0663948": {
                    "name": "Grupo de Coloides",
                    "value": 1025
                },
                "602c510ffd74967db06638f3": {
                    "name": "Grupo de Biofísica",
                    "value": 3318.3070664250795
                },
                "602c510ffd74967db0663909": {
                    "name": "Diagnóstico y Control de la Contaminación",
                    "value": 3500
                },
                "602c510ffd74967db06639fd": {
                    "name": "Grupo de Investigación y Gestión sobre Patrimonio",
                    "value": 200
                }
                },
                "publisher": {
                "Hindawi Limited": 81695,
                "BMC": 352120.33776623,
                "Asociación Colombiana de Infectología": 7600,
                "MDPI AG": 336352.0133296308,
                "Public Library of Science (PLoS)": 259525,
                "Frontiers Media S.A.": 235850,
                "Nature Publishing Group": 90946.40866978905,
                "Colégio Brasileiro de Cirurgiões": 185.4154543505559,
                "The Association for Research in Vision and Ophthalmology": 31450,
                "Elsevier": 203307.67999999988,
                "Cambridge University Press": 25278.385141020815,
                "The Journal of Infection in Developing Countries": 3102.0696,
                "Arán Ediciones, S. L.": 19614.96000000001,
                "Fundação de Amparo à Pesquisa do Estado de SP": 1600,
                "BMJ Publishing Group": 48223.376978564826,
                "Wiley": 53579,
                "American Chemical Society": 1500,
                "F1000 Research Ltd": 5000,
                "Universidad de Antioquia": 98100,
                "Universidade de São Paulo": 8457.478178310004,
                "Sociedade Brasileira de Química": 4069.671679274754,
                "Pharmacotherapy Group, University of Benin, Benin City": 2000,
                "American Society for Microbiology": 14400,
                "Association of Support to Oral Health Research (APESB)": 390,
                "Instituto de Investigaciones Agropecuarias, INIA": 650,
                "Tehran University of Medical Sciences": 0,
                "Wolters Kluwer Medknow Publications": 500,
                "Oxford University Press": 21739.34566339612,
                "Fundación Revista Medicina": 0,
                "Iranian Medicinal Plants Society": 215,
                "Universidad Autónoma de Yucatán": 400,
                "Fundação Odontológica de Ribeirão Preto": 101.97849989280574,
                "Facultad de Ciencias Agrarias. Universidad Nacional de Cuyo": 300,
                "Exeley Inc.": 500
                },
                "openaccess": {
                "gold": 1723132.3620811182,
                "closed": 67762.23068810394,
                "bronze": 52978.00656463765,
                "green": 34771.15632984965,
                "hybrid": 48339.07216847288
                }
            },
            "filters": {
                "start_year": 1925,
                "end_year": 2020
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
        elif data=="apc":
            idx = self.request.args.get('id')
            start_year=self.request.args.get('start_year')
            end_year=self.request.args.get('end_year')
            apc=self.get_apc(idx,start_year,end_year)
            if apc:
                response = self.app.response_class(
                response=self.json.dumps(apc),
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
        elif data=="graduates_colleges":
            idx = self.request.args.get('id')
            start_year=self.request.args.get('start_year')
            end_year=self.request.args.get('end_year')
            graduates_colleges=self.get_graduates_colleges(idx,start_year,end_year)
            if graduates_colleges:
                response = self.app.response_class(
                response=self.json.dumps(graduates_colleges),
                status=200,
                mimetype='application/json'
                )
            else:
                response = self.app.response_class(
                response=self.json.dumps({"status":"Request returned empty"}),
                status=204,
                mimetype='application/json'
                )
        elif data=="graduates":
            idx = self.request.args.get('id')
            icidx = self.request.args.get('icid')
            start_year=self.request.args.get('start_year')
            end_year=self.request.args.get('end_year')
            graduates=self.get_graduates(idx,icidx,start_year,end_year)
            if graduates:
                response = self.app.response_class(
                response=self.json.dumps(graduates),
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

