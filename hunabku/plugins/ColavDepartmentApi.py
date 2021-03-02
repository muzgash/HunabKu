from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId
from pymongo import ASCENDING,DESCENDING

class ColavDepartmentApi(HunabkuPluginBase):
    def __init__(self, hunabku):
        super().__init__(hunabku)

    
    def get_production(self,idx=None,max_results=100,page=1,start_year=None,end_year=None,sort=None,direction=None):
        self.db = self.dbclient["antioquia"]
        papers=[]
        total=0
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
            elif end_year and not start_year:
                cursor=self.db['documents'].find({"year_published":{"$lte":end_year},"authors.affiliations.branches._id":ObjectId(idx)})
            elif start_year and end_year:
                cursor=self.db['documents'].find({"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches._id":ObjectId(idx)})
            else:
                cursor=self.db['documents'].find({"authors.affiliations.branches._id":ObjectId(idx)})
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
        if max_results>500:
            max_results=500

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
            entry=paper
            del(entry["abstract_idx"])
            for title in entry["titles"]:
                del(title["title_idx"])
            source=self.db["sources"].find_one({"_id":paper["source"]["_id"]})
            if source:
                del(source["title_idx"])
                del(source["publisher_idx"])
                entry["source"]=source
            authors=[]
            for author in paper["authors"]:
                au_entry=author
                if "national_id" in au_entry.keys():
                    del(au_entry["national_id"])
                author_db=self.db["authors"].find_one({"_id":author["_id"]})
                if author_db:
                    au_entry=author_db
                if "aliases" in au_entry.keys():
                    del(au_entry["aliases"])
                affiliations=[]
                for aff in author["affiliations"]:
                    aff_entry=aff
                    aff_db=self.db["institutions"].find_one({"_id":aff["_id"]})
                    if aff_db:
                        aff_entry=aff_db
                    if "name_idx" in aff_entry.keys():
                        del(aff_entry["name_idx"])
                    if "addresses" in aff_entry.keys():
                        for add in aff_entry["addresses"]:
                            if "geonames_city" in add.keys():
                                del(add["geonames_city"])
                    if "aliases" in aff_entry.keys():
                        del(aff_entry["aliases"])
                    branches=[]
                    if "branches" in aff.keys():
                        for branch in aff["branches"]:
                            branch_db=self.db["branches"].find_one({"_id":branch["_id"]})
                            if branch_db:
                                del(branch_db["aliases"])
                                del(branch_db["name_idx"])
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
        return {"data":papers,"count":len(papers),"page":page,"total_results":total}
    
    def get_info(self,idx):
        self.db = self.dbclient["antioquia"]
        department = self.db['branches'].find_one({"type":"department","_id":ObjectId(idx)})
        if department:
            entry={"id":department["_id"],
                "name":department["name"],
                "type":department["type"],
                "external_urls":department["external_urls"],
                "groups":[],
                "authors":[],
                "institution":[]
            }
            
            inst_id=""
            for rel in department["relations"]:
                if rel["type"]=="university":
                    inst_id=rel["id"]
                    break
            if inst_id:
                inst=self.db['institutions'].find_one({"_id":inst_id})
                if inst:
                    entry["institution"]=[{"name":inst["name"],"id":inst_id}]#,"logo":inst["logo"]}]

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

    @endpoint('/api/department', methods=['GET'])
    def api_department(self):
        """
        @api {get} /api/department Department
        @apiName api
        @apiGroup CoLav api
        @apiDescription Responds with information about the department

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
                    "_id": "602ef800728ecc2d8e62d704",
                    "updated": 1613690880,
                    "source_checked": [
                        {
                        "source": "lens",
                        "ts": 1613690880
                        },
                        {
                        "source": "scholar",
                        "ts": 1613690880
                        },
                        {
                        "source": "scholar",
                        "ts": 1613690880
                        },
                        {
                        "source": "scopus",
                        "ts": 1613690880
                        }
                    ],
                    "publication_type": "conference proceedings",
                    "titles": [
                        {
                        "title": "Personalized message emission in a mobile application for supporting therapeutic adherence",
                        "lang": "en"
                        }
                    ],
                    "subtitle": "",
                    "abstract": "Often chronic patients fail to follow all the recommendations in their treatments. This affects their health and increases the costs associated with their care. To help these patients to follow their therapy this paper proposes a recall and guide system implemented on a mobile device. The system emits custom messages according to the patient's inferred mental state with the intention of persuading him to adhere to his medical prescriptions. To achieve personalization, the system uses ontologies to classify the messages and to model the user. When it is necessary to issue a reminder, the selection of the message is obtained by querying the relationships between the patient's current model and the discourse ontology.",
                    "keywords": [
                        "current models",
                        "guide system",
                        "medical prescription",
                        "mental state",
                        "mobile applications",
                        "personalizations",
                        "personalized messages",
                        "system use",
                        "therapeutic adherence",
                        "health",
                        "ontology",
                        "patient treatment",
                        "mobile devices"
                    ],
                    "start_page": 15,
                    "end_page": 20,
                    "volume": "",
                    "issue": "",
                    "date_published": 1307923200,
                    "year_published": 2011,
                    "languages": [
                        "en"
                    ],
                    "bibtex": "@inproceedings{uribe2011personalized,\n  title={Personalized message emission in a mobile application for supporting therapeutic adherence},\n  author={Uribe, Jonny A and Duitama, Jhon F and G{\\'o}mez, Natalia Gaviria},\n  booktitle={2011 IEEE 13th International Conference on e-Health Networking, Applications and Services},\n  pages={15--20},\n  year={2011},\n  organization={IEEE}\n}\n",
                    "funding_organization": "",
                    "funding_details": "",
                    "is_open_access": false,
                    "open_access_status": "closed",
                    "external_ids": [
                        {
                        "source": "lens",
                        "id": "164-785-598-339-308"
                        },
                        {
                        "source": "magid",
                        "id": "2127102153"
                        },
                        {
                        "source": "doi",
                        "id": "10.1109/health.2011.6026734"
                        },
                        {
                        "source": "scopus",
                        "id": "2-s2.0-80053939280"
                        },
                        {
                        "source": "scholar",
                        "id": "7zd6q123OScJ"
                        }
                    ],
                    "urls": [
                        {
                        "source": "scopus",
                        "url": "https://www.scopus.com/inward/record.uri?eid=2-s2.0-80053939280&doi=10.1109%2fHEALTH.2011.6026734&partnerID=40&md5=a91b2ede798cc229f82ec843b786148a"
                        }
                    ],
                    "source": {
                        "_id": "602ef800728ecc2d8e62d702",
                        "source_checked": [
                        {
                            "source": "scopus",
                            "date": 1613690880
                        },
                        {
                            "source": "scholar",
                            "date": 1613690880
                        },
                        {
                            "source": "lens",
                            "date": 1613690880
                        }
                        ],
                        "updated": 1613690880,
                        "title": "2011 IEEE 13th International Conference on e-Health Networking, Applications and Services",
                        "type": "",
                        "publisher": "IEEE",
                        "institution": "",
                        "institution_id": "",
                        "country": "",
                        "submission_charges": "",
                        "submission_currency": "",
                        "apc_charges": "",
                        "apc_currency": "",
                        "serials": [
                        {
                            "type": "isbn",
                            "value": "9781612846972"
                        }
                        ],
                        "abbreviations": [
                        {
                            "type": "unknown",
                            "value": "IEEE Int. Conf. e-Health Networking, Appl. Serv., HEALTHCOM"
                        }
                        ],
                        "subjects": {}
                    },
                    "author_count": 3,
                    "authors": [
                        {
                        "_id": "602ef800728ecc2d8e62d703",
                        "national_id": "",
                        "source_checked": [
                            {
                            "source": "lens",
                            "date": 1613690880
                            },
                            {
                            "source": "scopus",
                            "date": 1613690880
                            },
                            {
                            "source": "scholar",
                            "date": 1613690880
                            }
                        ],
                        "full_name": "Jonny A. Uribe",
                        "first_names": "Jonny A.",
                        "last_names": "Uribe",
                        "initials": "JA",
                        "branches": [],
                        "keywords": [],
                        "external_ids": [
                            {
                            "source": "scholar",
                            "value": "H4vqviEAAAAJ"
                            }
                        ],
                        "corresponding": false,
                        "corresponding_address": "",
                        "corresponding_email": "",
                        "updated": 1613690880,
                        "affiliations": [
                            {
                            "_id": "60120afa4749273de6161883",
                            "name": "University of Antioquia",
                            "abbreviations": [],
                            "types": [
                                "Education"
                            ],
                            "relationships": [
                                {
                                "name": "Hôpital Saint-Vincent-de-Paul",
                                "type": "Related",
                                "external_ids": [
                                    {
                                    "source": "grid",
                                    "value": "grid.413348.9"
                                    }
                                ],
                                "id": ""
                                }
                            ],
                            "addresses": [
                                {
                                "line_1": "",
                                "line_2": "",
                                "line_3": null,
                                "lat": 6.267417,
                                "lng": -75.568389,
                                "postcode": "",
                                "primary": false,
                                "city": "Medellín",
                                "state": null,
                                "state_code": "",
                                "country": "Colombia",
                                "country_code": "CO"
                                }
                            ],
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
                            "external_ids": [
                                {
                                "source": "grid",
                                "value": "grid.412881.6"
                                },
                                {
                                "source": "isni",
                                "value": "0000 0000 8882 5269"
                                },
                                {
                                "source": "fundref",
                                "value": "501100005278"
                                },
                                {
                                "source": "orgref",
                                "value": "2696975"
                                },
                                {
                                "source": "wikidata",
                                "value": "Q1258413"
                                },
                                {
                                "source": "ror",
                                "value": "https://ror.org/03bp5hc83"
                                }
                            ],
                            "branches": []
                            }
                        ]
                        },
                        {
                        "_id": "5fccc8dbeccc163512fee533",
                        "national_id": 71598507,
                        "full_name": "John Freddy Duitama Muñoz",
                        "first_names": "John Freddy",
                        "last_names": "Duitama Muñoz",
                        "initials": "JF",
                        "affiliations": [
                            {
                            "_id": "60120afa4749273de6161883",
                            "name": "University of Antioquia",
                            "abbreviations": [],
                            "types": [
                                "Education"
                            ],
                            "relationships": [
                                {
                                "name": "Hôpital Saint-Vincent-de-Paul",
                                "type": "Related",
                                "external_ids": [
                                    {
                                    "source": "grid",
                                    "value": "grid.413348.9"
                                    }
                                ],
                                "id": ""
                                }
                            ],
                            "addresses": [
                                {
                                "line_1": "",
                                "line_2": "",
                                "line_3": null,
                                "lat": 6.267417,
                                "lng": -75.568389,
                                "postcode": "",
                                "primary": false,
                                "city": "Medellín",
                                "state": null,
                                "state_code": "",
                                "country": "Colombia",
                                "country_code": "CO"
                                }
                            ],
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
                            "external_ids": [
                                {
                                "source": "grid",
                                "value": "grid.412881.6"
                                },
                                {
                                "source": "isni",
                                "value": "0000 0000 8882 5269"
                                },
                                {
                                "source": "fundref",
                                "value": "501100005278"
                                },
                                {
                                "source": "orgref",
                                "value": "2696975"
                                },
                                {
                                "source": "wikidata",
                                "value": "Q1258413"
                                },
                                {
                                "source": "ror",
                                "value": "https://ror.org/03bp5hc83"
                                }
                            ],
                            "branches": [
                                {
                                "_id": "602c50d1fd74967db066383a",
                                "name": "Facultad de ingeniería",
                                "abbreviations": [],
                                "type": "faculty",
                                "relations": [
                                    {
                                    "name": "University of Antioquia",
                                    "collection": "institutions",
                                    "type": "university",
                                    "id": "60120afa4749273de6161883"
                                    }
                                ],
                                "addresses": [
                                    {
                                    "line_1": "",
                                    "line_2": "",
                                    "line_3": null,
                                    "lat": 6.267417,
                                    "lng": -75.568389,
                                    "postcode": "",
                                    "primary": false,
                                    "city": "Medellín",
                                    "state": null,
                                    "state_code": "",
                                    "country": "Colombia",
                                    "country_code": "CO",
                                    "email": ""
                                    }
                                ],
                                "external_urls": [
                                    {
                                    "source": "website",
                                    "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/unidades-academicas/ingenieria"
                                    }
                                ],
                                "external_ids": [],
                                "keywords": [],
                                "subjects": []
                                },
                                {
                                "_id": "602c50f9fd74967db0663889",
                                "name": "Departamento de ingeniería de sistemas",
                                "abbreviations": [],
                                "type": "department",
                                "relations": [
                                    {
                                    "name": "University of Antioquia",
                                    "collection": "institutions",
                                    "type": "university",
                                    "id": "60120afa4749273de6161883"
                                    }
                                ],
                                "addresses": [
                                    {
                                    "line_1": "",
                                    "line_2": "",
                                    "line_3": null,
                                    "lat": 6.267417,
                                    "lng": -75.568389,
                                    "postcode": "",
                                    "primary": false,
                                    "city": "Medellín",
                                    "state": null,
                                    "state_code": "",
                                    "country": "Colombia",
                                    "country_code": "CO",
                                    "email": ""
                                    }
                                ],
                                "external_urls": [],
                                "external_ids": [],
                                "keywords": [],
                                "subjects": []
                                },
                                {
                                "_id": "602c510ffd74967db06638d9",
                                "name": "Centro de investigaciones básicas y aplicadas en veterinaria- cibav",
                                "abbreviations": [],
                                "type": "group",
                                "relations": [
                                    {
                                    "name": "University of Antioquia",
                                    "collection": "institutions",
                                    "type": "university",
                                    "id": "60120afa4749273de6161883"
                                    }
                                ],
                                "addresses": [
                                    {
                                    "line_1": "",
                                    "line_2": "",
                                    "line_3": null,
                                    "lat": 6.267417,
                                    "lng": -75.568389,
                                    "postcode": "",
                                    "primary": false,
                                    "city": "Medellín",
                                    "state": null,
                                    "state_code": "",
                                    "country": "Colombia",
                                    "country_code": "CO",
                                    "email": "grupocatalizadoresyadsorbentes@udea.edu.co"
                                    }
                                ],
                                "external_urls": [
                                    {
                                    "source": "website",
                                    "url": "http://172.19.0.90:10039/wps/portal/udea/web/inicio/investigacion/grupos-investigacion/ciencias-agricolas/cibav"
                                    },
                                    {
                                    "source": "gruplac",
                                    "url": "https://scienti.colciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000015528"
                                    }
                                ],
                                "external_ids": [],
                                "keywords": [],
                                "subjects": [
                                    {
                                    "source": "area_ocde",
                                    "subjects": [
                                        "ciencias agrícolas"
                                    ]
                                    },
                                    {
                                    "source": "subarea_ocde",
                                    "subjects": [
                                        "agricultura, silvicultura y pesca"
                                    ]
                                    },
                                    {
                                    "source": "udea",
                                    "subjects": [
                                        "ciencias de la salud "
                                    ]
                                    },
                                    {
                                    "source": "gruplac",
                                    "subjects": [
                                        "anatomía veterinaria",
                                        "microbiología molecular veterinaria",
                                        "parasitología veterinaria",
                                        "farmacología y toxicología veterinaria"
                                    ]
                                    }
                                ]
                                }
                            ]
                            }
                        ],
                        "keywords": [
                            "intensive care unit",
                            "least absolute shrinkage and selection operator",
                            "prognosis prediction",
                            "sepsis",
                            "stochastic gradient boosting",
                            "moving objects",
                            "movement patterns",
                            "flocks",
                            "leadership",
                            "application software",
                            "development",
                            "model-driven software architecture",
                            "software engineering"
                        ],
                        "external_ids": [
                            {
                            "source": "scopus",
                            "value": "16635559900"
                            }
                        ],
                        "branches": [
                            {
                            "name": "Facultad de Ingeniería",
                            "type": "faculty",
                            "id": "602c50d1fd74967db066383a"
                            },
                            {
                            "name": "Departamento de Ingeniería de Sistemas",
                            "type": "department",
                            "id": "602c50f9fd74967db0663889"
                            },
                            {
                            "name": "Ingeniería y Software ",
                            "type": "group",
                            "id": "602c510ffd74967db06638d9"
                            }
                        ],
                        "updated": 1613691968
                        },
                        {
                        "_id": "5fccd24beccc163512fee53a",
                        "national_id": 42792532,
                        "full_name": "Natalia Gaviria Gomez",
                        "first_names": "Natalia",
                        "last_names": "Gaviria Gomez",
                        "initials": "N",
                        "affiliations": [
                            {
                            "_id": "60120afa4749273de6161883",
                            "name": "University of Antioquia",
                            "abbreviations": [],
                            "types": [
                                "Education"
                            ],
                            "relationships": [
                                {
                                "name": "Hôpital Saint-Vincent-de-Paul",
                                "type": "Related",
                                "external_ids": [
                                    {
                                    "source": "grid",
                                    "value": "grid.413348.9"
                                    }
                                ],
                                "id": ""
                                }
                            ],
                            "addresses": [
                                {
                                "line_1": "",
                                "line_2": "",
                                "line_3": null,
                                "lat": 6.267417,
                                "lng": -75.568389,
                                "postcode": "",
                                "primary": false,
                                "city": "Medellín",
                                "state": null,
                                "state_code": "",
                                "country": "Colombia",
                                "country_code": "CO"
                                }
                            ],
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
                            "external_ids": [
                                {
                                "source": "grid",
                                "value": "grid.412881.6"
                                },
                                {
                                "source": "isni",
                                "value": "0000 0000 8882 5269"
                                },
                                {
                                "source": "fundref",
                                "value": "501100005278"
                                },
                                {
                                "source": "orgref",
                                "value": "2696975"
                                },
                                {
                                "source": "wikidata",
                                "value": "Q1258413"
                                },
                                {
                                "source": "ror",
                                "value": "https://ror.org/03bp5hc83"
                                }
                            ],
                            "branches": [
                                {
                                "_id": "602c50d1fd74967db066383a",
                                "name": "Facultad de ingeniería",
                                "abbreviations": [],
                                "type": "faculty",
                                "relations": [
                                    {
                                    "name": "University of Antioquia",
                                    "collection": "institutions",
                                    "type": "university",
                                    "id": "60120afa4749273de6161883"
                                    }
                                ],
                                "addresses": [
                                    {
                                    "line_1": "",
                                    "line_2": "",
                                    "line_3": null,
                                    "lat": 6.267417,
                                    "lng": -75.568389,
                                    "postcode": "",
                                    "primary": false,
                                    "city": "Medellín",
                                    "state": null,
                                    "state_code": "",
                                    "country": "Colombia",
                                    "country_code": "CO",
                                    "email": ""
                                    }
                                ],
                                "external_urls": [
                                    {
                                    "source": "website",
                                    "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/unidades-academicas/ingenieria"
                                    }
                                ],
                                "external_ids": [],
                                "keywords": [],
                                "subjects": []
                                },
                                {
                                "_id": "602c50f9fd74967db066388a",
                                "name": "Departamento de ingeniería electrónica",
                                "abbreviations": [],
                                "type": "department",
                                "relations": [
                                    {
                                    "name": "University of Antioquia",
                                    "collection": "institutions",
                                    "type": "university",
                                    "id": "60120afa4749273de6161883"
                                    }
                                ],
                                "addresses": [
                                    {
                                    "line_1": "",
                                    "line_2": "",
                                    "line_3": null,
                                    "lat": 6.267417,
                                    "lng": -75.568389,
                                    "postcode": "",
                                    "primary": false,
                                    "city": "Medellín",
                                    "state": null,
                                    "state_code": "",
                                    "country": "Colombia",
                                    "country_code": "CO",
                                    "email": ""
                                    }
                                ],
                                "external_urls": [],
                                "external_ids": [],
                                "keywords": [],
                                "subjects": []
                                },
                                {
                                "_id": "602c510ffd74967db06639fe",
                                "name": "Grupo de investigación en telecomunicaciones aplicadas",
                                "abbreviations": [
                                    "GITA"
                                ],
                                "type": "group",
                                "relations": [
                                    {
                                    "name": "University of Antioquia",
                                    "collection": "institutions",
                                    "type": "university",
                                    "id": "60120afa4749273de6161883"
                                    }
                                ],
                                "addresses": [
                                    {
                                    "line_1": "",
                                    "line_2": "",
                                    "line_3": null,
                                    "lat": 6.267417,
                                    "lng": -75.568389,
                                    "postcode": "",
                                    "primary": false,
                                    "city": "Medellín",
                                    "state": null,
                                    "state_code": "",
                                    "country": "Colombia",
                                    "country_code": "CO",
                                    "email": "grupohistoriasaludpublica@udea.edu.co"
                                    }
                                ],
                                "external_urls": [
                                    {
                                    "source": "website",
                                    "url": "https://sites.google.com/site/grupotelecoudea/services"
                                    },
                                    {
                                    "source": "gruplac",
                                    "url": "https://scienti.colciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000002810"
                                    }
                                ],
                                "external_ids": [],
                                "keywords": [],
                                "subjects": [
                                    {
                                    "source": "area_ocde",
                                    "subjects": [
                                        "ingeniería y tecnología"
                                    ]
                                    },
                                    {
                                    "source": "subarea_ocde",
                                    "subjects": [
                                        "ingenierías eléctrica, electrónica e informática"
                                    ]
                                    },
                                    {
                                    "source": "udea",
                                    "subjects": [
                                        "ingeniería"
                                    ]
                                    },
                                    {
                                    "source": "gruplac",
                                    "subjects": [
                                        "comunicaciones ópticas",
                                        "contaminación e interferencia electromagnética",
                                        "diseño de antenas y dispositivos de rf",
                                        "modelamiento de sistemas de comunicaciones",
                                        "procesamiento digital de señales y análisis de patrones",
                                        "redes inalámbricas"
                                    ]
                                    }
                                ]
                                }
                            ]
                            }
                        ],
                        "keywords": [
                            "antenna arrays",
                            "antenna pattern synthesis",
                            "beamforming",
                            "linear arrays",
                            "smart antennas",
                            "performance evaluation model",
                            "throughput",
                            "single-hop wireless networks",
                            "p2p streaming",
                            "ns-3"
                        ],
                        "external_ids": [
                            {
                            "source": "scopus",
                            "value": "53163467300"
                            }
                        ],
                        "branches": [
                            {
                            "name": "Facultad de Ingeniería",
                            "type": "faculty",
                            "id": "602c50d1fd74967db066383a"
                            },
                            {
                            "name": "Departamento de Ingeniería Electrónica",
                            "type": "department",
                            "id": "602c50f9fd74967db066388a"
                            },
                            {
                            "name": "Grupo de Investigación en Telecomunicaciones Aplicadas - GITA",
                            "type": "group",
                            "id": "602c510ffd74967db06639fe"
                            }
                        ],
                        "updated": 1613690880
                        }
                    ],
                    "references_count": 18,
                    "references": [],
                    "citations_count": 8,
                    "citations_link": "/scholar?cites=2826491854088452079&as_sdt=2005&sciodt=0,5&hl=en&oe=ASCII",
                    "citations": []
                    }
                ],
                "count": 7,
                "page": 1,
                "total_results": 7
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
            papers=self.get_production(idx,max_results,page,start_year,end_year,sort,"ascending")
            if papers:
                response = self.app.response_class(
                response=self.json.dumps(papers),
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