from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId
from pymongo import ASCENDING,DESCENDING

class ColavFacultiesApi(HunabkuPluginBase):
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
            cursor.sort([("citations_count",ASCENDING)])
        if sort=="citations" and direction=="descending":
            cursor.sort([("citations_count",DESCENDING)])
        if sort=="year" and direction=="ascending":
            cursor.sort([("year_published",ASCENDING)])
        if sort=="year" and direction=="descending":
            cursor.sort([("year_published",DESCENDING)])

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
                author_db=self.db["authors"].find_one({"_id":author["_id"]})
                if author_db:
                    au_entry=author_db
                if "aliases" in au_entry.keys():
                    del(au_entry["aliases"])
                if "national_id" in au_entry.keys():
                    del(au_entry["national_id"])
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
        faculty = self.db['branches'].find_one({"type":"faculty","_id":ObjectId(idx)})
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
            for rel in faculty["relations"]:
                if rel["type"]=="university":
                    inst_id=rel["id"]
                    break
            if inst_id:
                inst=self.db['institutions'].find_one({"_id":inst_id})
                if inst:
                    entry["institution"]=[{"name":inst["name"],"id":inst_id,"logo":""}]

            for author in self.db['authors'].find({"branches.id":faculty["_id"]}):
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
                    if branch["type"]=="department":
                        branch_db=self.db["branches"].find_one({"_id":ObjectId(branch["id"])})
                        entry_department={
                            "id":branch["id"],
                            "name":branch_db["name"]
                        }
                        if not entry_department in entry["departments"]:
                            entry["departments"].append(entry_department)
            return entry
        else:
            return None

    @endpoint('/api/faculties', methods=['GET'])
    def api_faculty(self):
        """
        @api {get} /api/faculties Faculties
        @apiName api
        @apiGroup CoLav api
        @apiDescription Responds with information about a faculty

        @apiParam {String} apikey Credential for authentication
        @apiParam {String} data (info,production) Whether is the general information or the production
        @apiParam {Object} id The mongodb id of the faculty requested
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
                    "_id": "602ef7c2728ecc2d8e62d5d9",
                    "updated": 1613690817,
                    "source_checked": [
                        {
                        "source": "lens",
                        "ts": 1613690817
                        },
                        {
                        "source": "scholar",
                        "ts": 1613690817
                        },
                        {
                        "source": "scholar",
                        "ts": 1613690817
                        }
                    ],
                    "publication_type": "journal article",
                    "titles": [
                        {
                        "title": "Avaliação do co-digestão anaeróbia de lodo de esgotos locais com resíduos dos alimentos",
                        "lang": "pt"
                        }
                    ],
                    "subtitle": "",
                    "abstract": "Resumo A digestao anaerobia e um processo muito utilizado para o tratamento dos lodos produzidos em estacoes de tratamento de esgoto, devido as suas vantagens tecnicas e economicas. Este artigo apresenta um estudo em que o co-digestao de lodo de esgotos com residuos de alimentos (RA) foi avaliado como uma estrategia para otimizar a digestao dos lodos. Foram realizados mono-digestao e co-digestao dos substratos em condicoes mesoflicas (35°C) utilizando reactores descontinuos. Os lodos utilizado foram: lodo primaria (LP), lodos secundario espessadas (LSE) e uma mistura de LP com LSE em 60:40 a base de solidos totais (LP:LSE). As co-digestoes foram realizadas utilizando diferentes proporcoes de misturas de substratos a base de solidos totais volateis: LP:RA=30:70, LP:RA=50:50, LP:RA=70:30 (LP+LSE):RA=70:30. A maxima producao de metano, 0,25LCH4/gSVadicionado, foi obtido por mistura de LP:RA=30:70, apresentando uma producao 32% maior que a obtida no mono-digestao de lodo primario. Palabras-chave: co-digestao, producao de metano, lodo primaria, lodos secundario espessadas, residuos de alimentos.",
                    "keywords": [],
                    "start_page": 63,
                    "end_page": 70,
                    "volume": "29",
                    "issue": "1",
                    "date_published": 1464739200,
                    "year_published": 2016,
                    "languages": [],
                    "bibtex": "@article{julio2016evaluacion,\n  title={Evaluaci{\\'o}n de la co-digesti{\\'o}n anaerobia de lodos de aguas residuales municipales con residuos de alimentos},\n  author={Julio Guerrero, Ileana Consuelo and Pel{\\'a}ez Jaramillo, Carlos Alberto and Molina Perez, Francisco Jos{\\'e}},\n  journal={Revista ion},\n  volume={29},\n  number={1},\n  pages={63--70},\n  year={2016}\n}\n",
                    "funding_organization": "",
                    "funding_details": "",
                    "is_open_access": true,
                    "open_access_status": "gold",
                    "external_ids": [
                        {
                        "source": "lens",
                        "id": "006-555-275-310-954"
                        },
                        {
                        "source": "magid",
                        "id": "2586352813"
                        },
                        {
                        "source": "doi",
                        "id": "10.18273/revion.v29n1-2016005"
                        },
                        {
                        "source": "scholar",
                        "id": "98gk4Pc-DLYJ"
                        }
                    ],
                    "urls": [],
                    "source": {
                        "_id": "600f50281fc9947fc8a8e80b",
                        "updated": 1611616296,
                        "source_checked": [
                        {
                            "source": "doaj",
                            "ts": 1611616296
                        }
                        ],
                        "title": "Revista Ion",
                        "type": "",
                        "publisher": "Universidad Industrial de Santander",
                        "institution": "",
                        "institution_id": "",
                        "external_urls": [
                        {
                            "source": "site",
                            "url": "http://revistas.uis.edu.co/index.php/revistaion/index"
                        }
                        ],
                        "country": "CO",
                        "editorial_review": "Blind peer review",
                        "submission_charges": "",
                        "submission_charges_url": "",
                        "submmission_currency": "",
                        "apc_charges": "",
                        "apc_currency": "",
                        "apc_url": "",
                        "serials": [
                        {
                            "type": "pissn",
                            "value": "0120100X"
                        },
                        {
                            "type": "eissn",
                            "value": "21458480"
                        }
                        ],
                        "abbreviations": [],
                        "aliases": [],
                        "subjects": [
                        {
                            "code": "Q",
                            "scheme": "LCC",
                            "term": "Science"
                        },
                        {
                            "code": "QD1-999",
                            "scheme": "LCC",
                            "term": "Chemistry"
                        }
                        ],
                        "keywords": [
                        "fuels and biofuels",
                        "engineering",
                        "materials science",
                        "chemical and physics science",
                        "bioprocess and green technologies"
                        ],
                        "author_copyright": "False",
                        "license": [
                        {
                            "embedded_example_url": "",
                            "NC": false,
                            "ND": false,
                            "BY": true,
                            "open_access": true,
                            "title": "CC BY",
                            "type": "CC BY",
                            "embedded": false,
                            "url": "http://revistas.uis.edu.co/index.php/revistaion/about/editorialPolicies#openAccessPolicy",
                            "SA": false
                        }
                        ],
                        "languages": [
                        "EN",
                        "PT",
                        "ES"
                        ],
                        "plagiarism_detection": true,
                        "active": "",
                        "publication_time": 24,
                        "deposit_policies": ""
                    },
                    "author_count": 3,
                    "authors": [
                        {
                        "_id": "602ef7c2728ecc2d8e62d5d8",
                        "national_id": "",
                        "source_checked": [
                            {
                            "source": "lens",
                            "date": 1613690817
                            },
                            {
                            "source": "scholar",
                            "date": 1613690817
                            }
                        ],
                        "full_name": "Ileana Consuelo Julio Guerrero",
                        "first_names": "Ileana Consuelo Julio",
                        "last_names": "Guerrero",
                        "initials": "ICJ",
                        "branches": [],
                        "keywords": [],
                        "external_ids": [
                            {
                            "source": "scholar",
                            "value": "2BFy8QIAAAAJ"
                            }
                        ],
                        "corresponding": false,
                        "corresponding_address": "",
                        "corresponding_email": "",
                        "updated": 1613690817,
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
                        "_id": "5fc75a099a7d07412f6cd38a",
                        "national_id": 70561251,
                        "full_name": "Carlos Alberto Pelaez Jaramillo",
                        "first_names": "Carlos Alberto",
                        "last_names": "Pelaez Jaramillo",
                        "initials": "CA",
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
                                "_id": "602c50d1fd74967db0663833",
                                "name": "Facultad de ciencias exactas y naturales",
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
                                "_id": "602c50f9fd74967db066385b",
                                "name": "Instituto de química",
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
                                "_id": "602c510ffd74967db066390f",
                                "name": "Grupo interdisciplinario de estudios moleculares",
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
                                    "email": "laboratoriogiemudea@gmail.com"
                                    }
                                ],
                                "external_urls": [
                                    {
                                    "source": "website",
                                    "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/investigacion/grupos-investigacion/ciencias-naturales-exactas/giem"
                                    },
                                    {
                                    "source": "gruplac",
                                    "url": "https://scienti.colciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000001876"
                                    }
                                ],
                                "external_ids": [],
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
                                        "ciencias químicas"
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
                                        "aprovechamiento energético y material de biomasa residual",
                                        "bioensayos ",
                                        "electroquímica",
                                        "estudios agroecosistémicos",
                                        "microbiología",
                                        "productos naturales y formulación",
                                        "servicios a la comunidad"
                                    ]
                                    }
                                ]
                                }
                            ]
                            }
                        ],
                        "keywords": [
                            "agriculture",
                            "caffeine oleate",
                            "insecticide",
                            "o/w emulsion",
                            "drosophila melanogaster",
                            "hypothenemus hampei",
                            "shell microstructure",
                            "chitin",
                            "chemical hydrolysis",
                            "papain"
                        ],
                        "external_ids": [
                            {
                            "source": "scopus",
                            "value": "55496048500"
                            }
                        ],
                        "branches": [
                            {
                            "name": "Facultad de Ciencias Exactas y Naturales",
                            "type": "faculty",
                            "id": "602c50d1fd74967db0663833"
                            },
                            {
                            "name": "Instituto de Química",
                            "type": "department",
                            "id": "602c50f9fd74967db066385b"
                            },
                            {
                            "name": "Grupo Interdisciplinario de Estudios Moleculares",
                            "type": "group",
                            "id": "602c510ffd74967db066390f"
                            }
                        ],
                        "updated": 1613691619
                        },
                        {
                        "_id": "5fcbea95eccc163512fee506",
                        "national_id": 3352862,
                        "full_name": "Francisco Jose Molina Perez",
                        "first_names": "Francisco Jose",
                        "last_names": "Molina Perez",
                        "initials": "FJ",
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
                                "_id": "602c50f9fd74967db0663886",
                                "name": "Departamento de ingeniería sanitaria  y ambiental",
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
                                "_id": "602c510ffd74967db0663956",
                                "name": "Grupo de investigación en gestión y modelación ambiental",
                                "abbreviations": [
                                    "GAIA"
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
                                    "email": "grupogaia@udea.edu.co"
                                    }
                                ],
                                "external_urls": [
                                    {
                                    "source": "website",
                                    "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/investigacion/grupos-investigacion/ciencias-naturales-exactas/gaia"
                                    },
                                    {
                                    "source": "gruplac",
                                    "url": "https://scienti.colciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000008106"
                                    }
                                ],
                                "external_ids": [],
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
                                        "ciencias de la tierra y medioambientales"
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
                                        "ecología de ecosistemas acuáticos costeros",
                                        "ecotoxicología acuática",
                                        "geología, geomorfología, hidrología, suelos y paleoecologia",
                                        "limnología básica y aplicada",
                                        "microbiología ambiental y aplicada",
                                        "modelación de sistemas ambientales",
                                        "tratamiento biológico de residuos y aguas residuales"
                                    ]
                                    }
                                ]
                                }
                            ]
                            }
                        ],
                        "keywords": [
                            "landfill leachate",
                            "fenton oxidation",
                            "phylogeny"
                        ],
                        "external_ids": [
                            {
                            "source": "orcid",
                            "value": "0000-0002-3491-4586"
                            },
                            {
                            "source": "scopus",
                            "value": "8437667900"
                            }
                        ],
                        "branches": [
                            {
                            "name": "Facultad de Ingeniería",
                            "type": "faculty",
                            "id": "602c50d1fd74967db066383a"
                            },
                            {
                            "name": "Departamento de Ingeniería Sanitaria  y Ambiental",
                            "type": "department",
                            "id": "602c50f9fd74967db0663886"
                            },
                            {
                            "name": "Grupo de Investigación en Gestión y Modelación Ambiental (GAIA)",
                            "type": "group",
                            "id": "602c510ffd74967db0663956"
                            }
                        ],
                        "updated": 1613690818
                        }
                    ],
                    "references_count": "",
                    "references": [],
                    "citations_count": 5,
                    "citations_link": "/scholar?cites=13117929048961763575&as_sdt=2005&sciodt=0,5&hl=en&oe=ASCII",
                    "citations": []
                    }
                ],
                "count": 82,
                "page": 1,
                "total_results": 82
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