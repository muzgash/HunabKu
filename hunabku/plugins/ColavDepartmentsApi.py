from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId
from pymongo import ASCENDING,DESCENDING

class ColavDepartmentsApi(HunabkuPluginBase):
    def __init__(self, hunabku):
        super().__init__(hunabku)

    
    def get_production(self,idx=None,max_results=100,page=1,start_year=None,end_year=None,sort=None,direction=None):
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
                cursor=self.colav_db['documents'].find({"year_published":{"$gte":start_year},"authors.affiliations.branches.id":ObjectId(idx)})
            elif end_year and not start_year:
                cursor=self.colav_db['documents'].find({"year_published":{"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)})
            elif start_year and end_year:
                cursor=self.colav_db['documents'].find({"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.branches.id":ObjectId(idx)})
            else:
                cursor=self.colav_db['documents'].find({"authors.affiliations.branches.id":ObjectId(idx)})
        else:
            cursor=self.colav_db['documents'].find()

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
            cursor.sort([("citations_count",ASCENDING)])
        if sort=="citations" and direction=="descending":
            cursor.sort([("citations_count",DESCENDING)])
        if sort=="year" and direction=="ascending":
            cursor.sort([("year_published",ASCENDING)])
        if sort=="year" and direction=="descending":
            cursor.sort([("year_published",DESCENDING)])

        for paper in cursor:
            entry=paper
            source=self.colav_db["sources"].find_one({"_id":paper["source"]["id"]})
            if source:
                entry["source"]=source
            authors=[]
            for author in paper["authors"]:
                au_entry=author
                author_db=self.colav_db["authors"].find_one({"_id":author["id"]})
                if author_db:
                    au_entry=author_db
                if "aliases" in au_entry.keys():
                    del(au_entry["aliases"])
                if "national_id" in au_entry.keys():
                    del(au_entry["national_id"])
                affiliations=[]
                for aff in author["affiliations"]:
                    aff_entry=aff
                    aff_db=self.colav_db["institutions"].find_one({"_id":aff["id"]})
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
                            branch_db=self.colav_db["branches"].find_one({"_id":branch["id"]}) if "id" in branch.keys() else ""
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
        return {"data":papers,"count":len(papers),"page":page,"total_results":total}
    
    def get_info(self,idx):
        department = self.colav_db['branches'].find_one({"type":"department","_id":ObjectId(idx)})
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
                inst=self.colav_db['institutions'].find_one({"_id":inst_id})
                if inst:
                    entry["institution"]=[{"name":inst["name"],"id":inst_id,"logo":inst["logo_url"]}]

            for author in self.colav_db['authors'].find({"branches.id":department["_id"]}):
                author_entry={
                    "full_name":author["full_name"],
                    "id":str(author["_id"])
                }
                entry["authors"].append(author_entry)
                for branch in author["branches"]:
                    if branch["type"]=="group" and branch["id"]:
                        branch_db=self.colav_db["branches"].find_one({"_id":ObjectId(branch["id"])})
                        entry_group={
                            "id":branch["id"],
                            "name":branch_db["name"]
                        }
                        if not entry_group in entry["groups"]:
                            entry["groups"].append(entry_group)
            return entry
        else:
            return None

    @endpoint('/api/departments', methods=['GET'])
    def api_departments(self):
        """
        @api {get} /api/departments Departments
        @apiName api
        @apiGroup CoLav api
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
            "id": "602c50f9fd74967db0663859",
            "name": "Instituto de Física",
            "type": "department",
            "external_urls": [],
            "groups": [
                {
                "id": "602c510ffd74967db06638f9",
                "name": "Grupo de Fenomenologia de Interacciones Fundamentales"
                },
                {
                "id": "602c510ffd74967db06639e1",
                "name": "Grupo de Fisica y Astrofisica Computacional"
                },
                {
                "id": "602c510ffd74967db06638f3",
                "name": "Grupo de Biofísica"
                },
                {
                "id": "602c510ffd74967db06638fb",
                "name": "Grupo de Fisica Atomica y Molecular"
                },
                {
                "id": "602c510ffd74967db06638e9",
                "name": "Fisica Industrial y de la Radiación"
                },
                {
                "id": "602c510ffd74967db0663912",
                "name": "Grupo de Fisica Nuclear"
                },
                {
                "id": "602c510ffd74967db0663a15",
                "name": "Grupo Teórico de Ciencias de los Materiales"
                }
            ],
            "authors": [
                {
                "full_name": "Oscar Alberto Zapata Noreña",
                "id": "5fc5ccb8b246cc0887190a81"
                },
                {
                "full_name": "Nelson Vanegas Arbelaez",
                "id": "5fc6287fb246cc0887190a94"
                },
                {
                "full_name": "John Jairo Zuluaga Quintero",
                "id": "5fc62920b246cc0887190a95"
                },
                {
                "full_name": "Jorge Ivan Zuluaga Callejas",
                "id": "5fc62b22b246cc0887190a96"
                },
                {
                "full_name": "Johann Mazo Zuluaga",
                "id": "5fc630ecb246cc0887190a97"
                },
                {
                "full_name": "Oscar Antonio Restrepo Gutierrez",
                "id": "5fc63219b246cc0887190a98"
                },
                {
                "full_name": "Juan Jose Quiros Arroyave",
                "id": "5fc63262b246cc0887190a99"
                },
                {
                "full_name": "John Fredy Barrera Ramirez",
                "id": "5fc639fcb246cc0887190a9a"
                },
                {
                "full_name": "Marco Antonio Giraldo Cadavid",
                "id": "5fc63b37b246cc0887190a9b"
                },
                {
                "full_name": "Oscar Luis Arnache Olmos",
                "id": "5fc6433fb246cc0887190a9c"
                },
                {
                "full_name": "Boris Anghelo Rodriguez Rey",
                "id": "5fc6487fb246cc0887190a9d"
                },
                {
                "full_name": "Alvaro Luis Morales Aramburo",
                "id": "5fc65665b246cc0887190a9e"
                },
                {
                "full_name": "Jorge Eduardo Mahecha Gomez",
                "id": "5fc65863b246cc0887190a9f"
                },
                {
                "full_name": "Leonardo Augusto Pachon Contreras",
                "id": "5fc65b6fb246cc0887190aa1"
                },
                {
                "full_name": "Cesar Augusto Barrero Meneses",
                "id": "5fc662f1b246cc0887190aa2"
                },
                {
                "full_name": "Jose Patricio Valencia Valencia",
                "id": "5fc6632db246cc0887190aa3"
                },
                {
                "full_name": "Jaime Alberto Osorio Velez",
                "id": "5fc668b8b246cc0887190aa4"
                },
                {
                "full_name": "Jorge Mario Osorio Guillen",
                "id": "5fc66debb246cc0887190aa5"
                },
                {
                "full_name": "Diego Alejandro Restrepo Quintero",
                "id": "5fc66fdfb246cc0887190aa6"
                },
                {
                "full_name": "Edgar Alberto Rueda Munoz",
                "id": "5fc671d0b246cc0887190aa7"
                },
                {
                "full_name": "Esteban Silva Villa",
                "id": "5fc673a6b246cc0887190aa8"
                }
            ],
            "institution": [
                {
                "name": "Universidad de Antioquia",
                "id": "60120afa4749273de6161883",
                "logo": "https://upload.wikimedia.org/wikipedia/commons/f/fb/Escudo-UdeA.svg"
                }
            ]
        }
        @apiSuccessExample {json} Success-Response (data=production):
        HTTP/1.1 200 OK
        {
            "data": [
                {
                "_id": "606a4c54aa884b9a1562e1b7",
                "updated": 1617579091,
                "source_checked": [
                    {
                    "source": "lens",
                    "ts": 1617579080
                    },
                    {
                    "source": "wos",
                    "ts": 1617579085
                    },
                    {
                    "source": "oadoi",
                    "ts": 1617579091
                    },
                    {
                    "source": "scholar",
                    "ts": 1617579091
                    },
                    {
                    "source": "scopus",
                    "ts": 1617579091
                    }
                ],
                "publication_type": "journal article",
                "titles": [
                    {
                    "title": "Density operator of a system pumped with polaritons: a Jaynes-Cummings-like approach.",
                    "lang": "en"
                    }
                ],
                "subtitle": "",
                "abstract": "We investigate the effects of considering two different incoherent excitation mechanisms on microcavity quantum dot systems modeled using the Jaynes-Cummings Hamiltonian. When the system is incoherently pumped with polaritons it is able to sustain a large number of photons inside the cavity with Poisson-like statistics in the stationary limit, and it also leads to a separable exciton-photon state. We also investigate the effects of both types of pumpings (excitonic and polaritonic) in the emission spectrum of the cavity. We show that the polaritonic pumping considered here is unable to modify the dynamical regimes of the system at variance with the excitonic pumping. Finally, we obtain a closed form expression for the negativity of the density matrices that the quantum master equation considered here generates.",
                "keywords": [
                    "closed-form expression",
                    "density matrix",
                    "density operators",
                    "dynamical regime",
                    "emission spectrums",
                    "excitation mechanisms",
                    "jaynes-cummings",
                    "jaynes-cummings hamiltonian",
                    "photon state",
                    "polaritons",
                    "quantum dot",
                    "photons",
                    "quantum dots"
                ],
                "start_page": 25301,
                "end_page": "",
                "volume": "23",
                "issue": "2",
                "date_published": 1291852800,
                "year_published": 2010,
                "languages": [
                    "en"
                ],
                "bibtex": "@article{quesada2010density,\n  title={Density operator of a system pumped with polaritons: a Jaynes--Cummings-like approach},\n  author={Quesada, Nicol{\\'a}s and Vinck-Posada, Herbert and Rodr{\\'\\i}guez, Boris A},\n  journal={Journal of Physics: Condensed Matter},\n  volume={23},\n  number={2},\n  pages={025301},\n  year={2010},\n  publisher={IOP Publishing}\n}\n",
                "funding_organization": "",
                "funding_details": "",
                "is_open_access": true,
                "open_access_status": "green",
                "external_ids": [
                    {
                    "source": "lens",
                    "id": "117-523-410-768-967"
                    },
                    {
                    "source": "magid",
                    "id": "2032078246"
                    },
                    {
                    "source": "doi",
                    "id": "10.1088/0953-8984/23/2/025301"
                    },
                    {
                    "source": "pmid",
                    "id": "21406838"
                    },
                    {
                    "source": "wos",
                    "id": "000285190900005"
                    },
                    {
                    "source": "scopus",
                    "id": "2-s2.0-78651479995"
                    },
                    {
                    "source": "scholar",
                    "id": "u9ICMr0fD2gJ"
                    }
                ],
                "urls": [
                    {
                    "source": "scopus",
                    "url": "https://www.scopus.com/inward/record.uri?eid=2-s2.0-78651479995&doi=10.1088%2f0953-8984%2f23%2f2%2f025301&partnerID=40&md5=1977625c6ebc93ed23e526ee5690405d"
                    }
                ],
                "source": {
                    "_id": "606a4c54aa884b9a1562e1b4",
                    "source_checked": [
                    {
                        "source": "scopus",
                        "date": 1617579091
                    },
                    {
                        "source": "wos",
                        "date": 1617579091
                    },
                    {
                        "source": "scholar",
                        "date": 1617579091
                    },
                    {
                        "source": "lens",
                        "date": 1617579091
                    }
                    ],
                    "updated": 1617579091,
                    "title": "Journal of Physics: Condensed Matter",
                    "type": "journal",
                    "publisher": "IOP Publishing Ltd.",
                    "institution": "",
                    "institution_id": "",
                    "country": "GB",
                    "submission_charges": "",
                    "submission_currency": "",
                    "apc_charges": "",
                    "apc_currency": "",
                    "serials": [
                    {
                        "type": "unknown",
                        "value": "09538984"
                    },
                    {
                        "type": "coden",
                        "value": "JCOME"
                    },
                    {
                        "type": "eissn",
                        "value": "1361648X"
                    }
                    ],
                    "abbreviations": [
                    {
                        "type": "unknown",
                        "value": "J Phys Condens Matter"
                    },
                    {
                        "type": "char",
                        "value": "J PHYS-CONDENS MAT"
                    },
                    {
                        "type": "iso",
                        "value": "J. Phys.-Condes. Matter"
                    }
                    ],
                    "subjects": {}
                },
                "author_count": 3,
                "authors": [
                    {
                    "_id": "606a4c54aa884b9a1562e1b5",
                    "source_checked": [
                        {
                        "source": "lens",
                        "date": 1617579091
                        },
                        {
                        "source": "wos",
                        "date": 1617579091
                        },
                        {
                        "source": "scopus",
                        "date": 1617579091
                        },
                        {
                        "source": "scholar",
                        "date": 1617579091
                        }
                    ],
                    "full_name": "Nicolás Quesada",
                    "first_names": "Nicolás",
                    "last_names": "Quesada",
                    "initials": "N",
                    "branches": [],
                    "keywords": [],
                    "external_ids": [
                        {
                        "source": "scopus",
                        "value": "36521642400"
                        },
                        {
                        "source": "scholar",
                        "value": "dZNVjOEAAAAJ"
                        },
                        {
                        "source": "scopus",
                        "value": "35071924300"
                        }
                    ],
                    "corresponding": true,
                    "corresponding_address": "Instituto de Física, Universidad de Antioquia, Medellín, A A 1226 Medellín, Colombia",
                    "corresponding_email": "nquesada@pegasus.udea.edu.co",
                    "updated": 1619654988,
                    "affiliations": [
                        {
                        "_id": "60120afa4749273de6161883",
                        "name": "Universidad de Antioquia",
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
                        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/f/fb/Escudo-UdeA.svg",
                        "branches": []
                        }
                    ]
                    },
                    {
                    "_id": "606a4c54aa884b9a1562e1b6",
                    "source_checked": [
                        {
                        "source": "lens",
                        "date": 1617579091
                        },
                        {
                        "source": "wos",
                        "date": 1617579091
                        },
                        {
                        "source": "scopus",
                        "date": 1617579091
                        },
                        {
                        "source": "scholar",
                        "date": 1617579091
                        }
                    ],
                    "full_name": "Herbert Vinck-Posada",
                    "first_names": "Herbert",
                    "last_names": "Vinck-Posada",
                    "initials": "H",
                    "branches": [],
                    "keywords": [],
                    "external_ids": [
                        {
                        "source": "scopus",
                        "value": "8357224800"
                        },
                        {
                        "source": "scholar",
                        "value": "PrGy6_IAAAAJ"
                        },
                        {
                        "source": "researchid",
                        "value": "P-7202-2016"
                        },
                        {
                        "source": "orcid",
                        "value": "0000-0002-5727-8025"
                        },
                        {
                        "source": "scopus",
                        "value": "36888027400"
                        },
                        {
                        "source": "scholar",
                        "value": "dZNVjOEAAAAJ"
                        },
                        {
                        "source": "scholar",
                        "value": "DYfFSwsAAAAJ"
                        }
                    ],
                    "corresponding": false,
                    "corresponding_address": "",
                    "corresponding_email": "",
                    "updated": 1619654988,
                    "affiliations": [
                        {
                        "_id": "60120ad44749273de6160274",
                        "name": "National University of Colombia",
                        "abbreviations": [
                            "UNAL"
                        ],
                        "types": [
                            "Education"
                        ],
                        "relationships": [],
                        "addresses": [
                            {
                            "line_1": "",
                            "line_2": "",
                            "line_3": null,
                            "lat": 4.635556,
                            "lng": -74.082778,
                            "postcode": "",
                            "primary": false,
                            "city": "Bogotá",
                            "state": null,
                            "state_code": "",
                            "country": "Colombia",
                            "country_code": "CO"
                            }
                        ],
                        "external_urls": [
                            {
                            "source": "wikipedia",
                            "url": "http://en.wikipedia.org/wiki/National_University_of_Colombia"
                            },
                            {
                            "source": "site",
                            "url": "http://unal.edu.co/"
                            }
                        ],
                        "external_ids": [
                            {
                            "source": "grid",
                            "value": "grid.10689.36"
                            },
                            {
                            "source": "isni",
                            "value": "0000 0001 0286 3748"
                            },
                            {
                            "source": "fundref",
                            "value": "501100002753"
                            },
                            {
                            "source": "orgref",
                            "value": "1215553"
                            },
                            {
                            "source": "wikidata",
                            "value": "Q1150419"
                            },
                            {
                            "source": "ror",
                            "value": "https://ror.org/059yx9a68"
                            }
                        ],
                        "logo_url": "",
                        "branches": []
                        }
                    ]
                    },
                    {
                    "_id": "5fc6487fb246cc0887190a9d",
                    "full_name": "Boris Anghelo Rodriguez Rey",
                    "first_names": "Boris Anghelo",
                    "last_names": "Rodriguez Rey",
                    "initials": "BA",
                    "affiliations": [
                        {
                        "_id": "60120afa4749273de6161883",
                        "name": "Universidad de Antioquia",
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
                        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/f/fb/Escudo-UdeA.svg",
                        "branches": [
                            {
                            "_id": "602c50d1fd74967db0663833",
                            "name": "Facultad de Ciencias Exactas y Naturales",
                            "abbreviations": [
                                "FCEN"
                            ],
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
                                "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/unidades-academicas/ciencias-exactas-naturales"
                                }
                            ],
                            "external_ids": [],
                            "keywords": [],
                            "subjects": []
                            },
                            {
                            "_id": "602c50f9fd74967db0663859",
                            "name": "Instituto de Física",
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
                            "_id": "602c510ffd74967db06638fb",
                            "name": "Grupo de Fisica Atomica y Molecular",
                            "abbreviations": [
                                "GFAM"
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
                                "state": "",
                                "state_code": "",
                                "country": "Colombia",
                                "country_code": "CO",
                                "email": "grupogenmol@udea.edu.co"
                                }
                            ],
                            "external_urls": [
                                {
                                "source": "website",
                                "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/investigacion/grupos-investigacion/ciencias-naturales-exactas/gfam"
                                },
                                {
                                "source": "gruplac",
                                "url": "https://scienti.colciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000001682"
                                }
                            ],
                            "external_ids": [
                                {
                                "source": "colciencias",
                                "id": "COL0008441"
                                }
                            ],
                            "keywords": [],
                            "subjects": [
                                {
                                "source": "area_ocde",
                                "subjects": [
                                    "ciencias naturales"
                                ]
                                },
                                {
                                "source": "subarea_ocde",
                                "subjects": [
                                    "ciencias físicas"
                                ]
                                },
                                {
                                "source": "udea",
                                "subjects": [
                                    "ciencias exactas y naturales"
                                ]
                                },
                                {
                                "source": "gruplac",
                                "subjects": [
                                    "dinámica de sistemas no lineales",
                                    "fundamentos de la mécanica cuántica",
                                    "ionización de átomos y moléculas",
                                    "propiedades y procesos de dímeros alcalinos",
                                    "sistemas cuánticos abiertos",
                                    "sistemas finitos"
                                ]
                                }
                            ]
                            }
                        ]
                        }
                    ],
                    "keywords": [
                        "teleconnections",
                        "information transference",
                        "regional enso influence",
                        "seasonal state index",
                        "luminescence",
                        "microcavities",
                        "optical properties",
                        "polaritons",
                        "bec",
                        "optical encryption",
                        "chaotic phase generation",
                        "synchronization system"
                    ],
                    "external_ids": [
                        {
                        "source": "scopus",
                        "value": "7102299387"
                        },
                        {
                        "source": "orcid",
                        "value": "0000-0001-5298-218X"
                        },
                        {
                        "source": "scopus",
                        "value": "57208737126"
                        },
                        {
                        "source": "scholar",
                        "value": "swUKsPkAAAAJ"
                        }
                    ],
                    "branches": [
                        {
                        "name": "Facultad de Ciencias Exactas y Naturales",
                        "type": "faculty",
                        "id": "602c50d1fd74967db0663833"
                        },
                        {
                        "name": "Instituto de Física",
                        "type": "department",
                        "id": "602c50f9fd74967db0663859"
                        },
                        {
                        "name": "Grupo de Fisica Atomica y Molecular",
                        "id": "602c510ffd74967db06638fb",
                        "type": "group"
                        }
                    ],
                    "updated": 1619612575
                    }
                ],
                "references_count": 28,
                "references": [],
                "citations_count": 13,
                "citations_link": "/scholar?cites=7498246802043491003&as_sdt=2005&sciodt=0,5&hl=en&oe=ASCII",
                "citations": [],
                "topics": [
                    {
                    "source": "lens",
                    "topics": [
                        "Physics",
                        "Quantum dot",
                        "Master equation",
                        "Polariton",
                        "Photon",
                        "Hamiltonian (quantum mechanics)",
                        "Condensed matter physics",
                        "Quantum master equation",
                        "Quantum system",
                        "Quantum electrodynamics",
                        "Quantum mechanics",
                        "Jaynes–Cummings model"
                    ]
                    }
                ]
                }
            ],
            "count": 100,
            "page": 1,
            "total_results": 930
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
            papers=self.get_production(idx,max_results,page,start_year,end_year,sort,"descending")
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