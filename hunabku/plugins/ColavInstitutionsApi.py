from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId
from pymongo import ASCENDING,DESCENDING

class ColavInstitutionsApi(HunabkuPluginBase):
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
                cursor=self.colav_db['documents'].find({"year_published":{"$gte":start_year},"authors.affiliations.id":ObjectId(idx)})
            elif end_year and not start_year:
                cursor=self.colav_db['documents'].find({"year_published":{"$lte":end_year},"authors.affiliations.id":ObjectId(idx)})
            elif start_year and end_year:
                cursor=self.colav_db['documents'].find({"year_published":{"$gte":start_year,"$lte":end_year},"authors.affiliations.id":ObjectId(idx)})
            else:
                cursor=self.colav_db['documents'].find({"authors.affiliations.id":ObjectId(idx)})
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
            source=self.colav_db["sources"].find_one({"_id":paper["source"]["id"]})
            if source:
                entry["source"]=source
            authors=[]
            for author in paper["authors"]:
                au_entry=author
                author_db=self.colav_db["authors"].find_one({"_id":author["id"]})
                if author_db:
                    au_entry=author_db
                affiliations=[]
                for aff in author["affiliations"]:
                    aff_entry=aff
                    aff_db=self.colav_db["institutions"].find_one({"_id":aff["id"]})
                    if aff_db:
                        aff_entry=aff_db
                    branches=[]
                    if "branches" in aff.keys():
                        for branch in aff["branches"]:
                            branch_db=self.colav_db["branches"].find_one({"_id":branch["id"]}) if "id" in branch.keys() else ""
                            if branch_db:
                                branches.append(branch_db)
                    aff_entry["branches"]=branches
                    affiliations.append(aff_entry)
                au_entry["affiliations"]=affiliations
                authors.append(au_entry)
            entry["authors"]=authors
            papers.append(entry)
        return {"data":papers,"count":len(papers),"page":page,"total_results":total}
    
    def get_info(self,idx):
        institution = self.colav_db['institutions'].find_one({"_id":ObjectId(idx)})
        if institution:
            entry={"id":institution["_id"],
                "name":institution["name"],
                "external_urls":institution["external_urls"],
                "departments":[],
                "faculties":[],
                "groups":[],
                "area_groups":[],
                "logo":institution["logo_url"]
            }

            for dep in self.colav_db['branches'].find({"type":"department","relations.id":ObjectId(idx)}):
                dep_entry={
                    "name":dep["name"],
                    "id":str(dep["_id"])
                }
                entry["departments"].append(dep_entry)
            
            for fac in self.colav_db['branches'].find({"type":"faculty","relations.id":ObjectId(idx)}):
                fac_entry={
                    "name":fac["name"],
                    "id":str(fac["_id"])
                }
                entry["faculties"].append(fac_entry)
            
            for grp in self.colav_db['branches'].find({"type":"group","relations.id":ObjectId(idx)}):
                grp_entry={
                    "name":grp["name"],
                    "id":str(grp["_id"])
                }
                entry["groups"].append(grp_entry)
            
            return entry
        else:
            return None

    @endpoint('/api/institutions', methods=['GET'])
    def api_institutions(self):
        """
        @api {get} /api/institutions Institution
        @apiName api
        @apiGroup CoLav api
        @apiDescription Responds with information about the institution

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
        HTTP/1.1 200 OK
        {
            "id": "60120afa4749273de6161883",
            "name": "Universidad de Antioquia",
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
                "name": "Departamento de Artes Visuales",
                "id": "602c50f9fd74967db0663854"
                },
                {
                "name": "Departamento de Formación Académica",
                "id": "602c50f9fd74967db0663873"
                },
                {
                "name": "Departamento de Formación Académica",
                "id": "602c50f9fd74967db06638a6"
                },
                {
                "name": "Escuela de Medicina Veterinaria",
                "id": "602c50f9fd74967db06638a9"
                },
                {
                "name": "Departamento de Producción Agropecuaria",
                "id": "602c50f9fd74967db06638aa"
                },
                {
                "name": "Centro de Investigaciones Agrarias, Ciagra",
                "id": "602c50f9fd74967db06638ab"
                },
                {
                "name": "Departamento de Formación Básica Profesional",
                "id": "602c50f9fd74967db06638ae"
                },
                {
                "name": "Departamento de Formación Profesional",
                "id": "602c50f9fd74967db06638af"
                },
                {
                "name": "Departamento de Extensión y Posgrados",
                "id": "602c50f9fd74967db06638b0"
                },
                {
                "name": "Departamento de Ciencias Básicas",
                "id": "602c50f9fd74967db06638b3"
                },
                {
                "name": "Departamento de Ciencias Específicas",
                "id": "602c50f9fd74967db06638b4"
                },
                {
                "name": "Programa Gestión Tecnológica",
                "id": "602c50f9fd74967db06638d1"
                }
            ],
            "faculties": [
                {
                "name": "Facultad de Artes",
                "id": "602c50d1fd74967db0663830"
                },
                {
                "name": "Facultad de Ciencias Agrarias",
                "id": "602c50d1fd74967db0663831"
                },
                {
                "name": "Facultad de Ciencias Económicas",
                "id": "602c50d1fd74967db0663832"
                },
                {
                "name": "Instituto de Estudios Regionales",
                "id": "602c50d1fd74967db0663845"
                },
                {
                "name": "Corporación Académica Ambiental",
                "id": "602c50d1fd74967db0663846"
                },
                {
                "name": "Corporación Académica Ciencias Básicas Biomédicas",
                "id": "602c50d1fd74967db0663847"
                },
                {
                "name": "Corporación Académica Para el Estudio de Patologías Tropicales",
                "id": "602c50d1fd74967db0663848"
                }
            ],
            "area_groups": [],
            "logo": "https://upload.wikimedia.org/wikipedia/commons/f/fb/Escudo-UdeA.svg"
        }
        @apiSuccessExample {json} Success-Response (data=production):
        HTTP/1.1 200 OK
        {
            "data": [
                {
                "_id": "606a4c52aa884b9a1562e190",
                "updated": 1617579088,
                "source_checked": [
                    {
                    "source": "lens",
                    "ts": 1617579080
                    },
                    {
                    "source": "oadoi",
                    "ts": 1617579088
                    },
                    {
                    "source": "scholar",
                    "ts": 1617579088
                    }
                ],
                "publication_type": "book chapter",
                "titles": [
                    {
                    "title": "Programming Optimization of Roasted Coffee Production in a Coffee Roasting Company",
                    "lang": "en"
                    }
                ],
                "subtitle": "",
                "abstract": "This work focuses on the development of a methodology to support the planning of aggregated production within a roasted coffee industrializing company. The methodology involves optimization techniques and computational tools for the assigning of lots to roasting lines while minimizing total costs and fulfilling the specifications of the process.",
                "keywords": [],
                "start_page": 471,
                "end_page": 480,
                "volume": "",
                "issue": "",
                "date_published": 1571097600,
                "year_published": 2019,
                "languages": [],
                "bibtex": "@inproceedings{giraldo2020programming,\n  title={Programming Optimization of Roasted Coffee Production in a Coffee Roasting Company},\n  author={Giraldo H, Joaqu{\\'\\i}n H},\n  booktitle={Operations Management for Social Good: 2018 POMS International Conference in Rio},\n  pages={471--480},\n  year={2020},\n  organization={Springer}\n}\n",
                "funding_organization": "",
                "funding_details": "",
                "is_open_access": false,
                "open_access_status": "closed",
                "external_ids": [
                    {
                    "source": "lens",
                    "id": "002-020-650-202-669"
                    },
                    {
                    "source": "magid",
                    "id": "2980909116"
                    },
                    {
                    "source": "doi",
                    "id": "10.1007/978-3-030-23816-2_46"
                    },
                    {
                    "source": "scholar",
                    "id": "lL73wzUJm4EJ"
                    }
                ],
                "urls": [],
                "source": {
                    "_id": "606a4c52aa884b9a1562e18e",
                    "source_checked": [
                    {
                        "source": "scholar",
                        "date": 1617579088
                    },
                    {
                        "source": "lens",
                        "date": 1617579088
                    }
                    ],
                    "updated": 1617579088,
                    "title": "Operations Management for Social Good",
                    "type": "",
                    "publisher": "Springer International Publishing",
                    "institution": "",
                    "institution_id": "",
                    "country": "",
                    "submission_charges": "",
                    "submission_currency": "",
                    "apc_charges": "",
                    "apc_currency": "",
                    "serials": [
                    {
                        "type": "pissn",
                        "value": "21987246"
                    },
                    {
                        "type": "eissn",
                        "value": "21987254"
                    }
                    ],
                    "abbreviations": [],
                    "subjects": {}
                },
                "author_count": 1,
                "authors": [
                    {
                    "_id": "606a4c52aa884b9a1562e18f",
                    "national_id": "",
                    "source_checked": [
                        {
                        "source": "lens",
                        "date": 1617579088
                        },
                        {
                        "source": "scholar",
                        "date": 1617579088
                        }
                    ],
                    "full_name": "H H Joaquín Giraldo",
                    "first_names": "H H Joaquín",
                    "last_names": "Giraldo",
                    "initials": "HHJ",
                    "aliases": [
                        "h h joaquín giraldo",
                        "joaquı́n h giraldo h"
                    ],
                    "branches": [],
                    "keywords": [],
                    "external_ids": [],
                    "corresponding": true,
                    "corresponding_address": "",
                    "corresponding_email": "",
                    "updated": 1617579088,
                    "affiliations": [
                        {
                        "_id": "60120afa4749273de6161883",
                        "name": "Universidad de Antioquia",
                        "aliases": [],
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
                            "country_code": "CO",
                            "geonames_city": {
                                "id": 3674962,
                                "city": "Medellín",
                                "nuts_level1": null,
                                "nuts_level2": null,
                                "nuts_level3": null,
                                "geonames_admin1": {
                                "name": "Antioquia",
                                "ascii_name": "Antioquia",
                                "code": "CO.02"
                                },
                                "geonames_admin2": {
                                "name": "Medellín",
                                "ascii_name": "Medellin",
                                "code": "CO.02.05001"
                                },
                                "license": {
                                "attribution": "Data from geonames.org under a CC-BY 3.0 license",
                                "license": "http://creativecommons.org/licenses/by/3.0/"
                                }
                            }
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
                    }
                ],
                "references_count": 6,
                "references": [],
                "citations_count": 0,
                "citations_link": "",
                "citations": [],
                "topics": [
                    {
                    "source": "lens",
                    "topics": [
                        "Roasting",
                        "Business",
                        "Total cost",
                        "Process engineering",
                        "Coffee roasting"
                    ]
                    }
                ]
                },
                {
                "_id": "606a4c52aa884b9a1562e192",
                "updated": 1617579085,
                "source_checked": [
                    {
                    "source": "lens",
                    "ts": 1617579080
                    },
                    {
                    "source": "oadoi",
                    "ts": 1617579085
                    },
                    {
                    "source": "scholar",
                    "ts": 1617579085
                    }
                ],
                "publication_type": "journal article",
                "titles": [
                    {
                    "title": "Evaluación económica del stent medicado vs. convencional para pacientes con infarto agudo de miocardio con elevación del ST en Colombia",
                    "lang": "es"
                    }
                ],
                "subtitle": "",
                "abstract": "Resumen Objetivo Analizar la costo-efectividad y el valor esperado de la informacion perfecta del stent medicado con sirolimus comparado con el convencional para pacientes con infarto agudo de miocardio con elevacion del ST en Colombia. Metodos Se construyo un modelo de Markov bajo la perspectiva del pagador y un horizonte temporal de diez anos. Las probabilidades de transicion se extrajeron de estudios clinicos identificados a partir de revisiones de la literatura. Los costos se estimaron mediante el uso de consenso de expertos y manuales tarifarios colombianos. Se realizo un analisis de sensibilidad deterministico alrededor del horizonte temporal, precio del stent medicado y tasa de descuento. Se construyo un analisis de sensibilidad probabilistico (10.000 simulaciones de Monte Carlo) y el valor esperado de la informacion perfecta para la decision global y grupos de parametros. Resultados En el caso base, el costo por ano de vida ajustado por calidad se ubico en 53.749.654 $. Los resultados no son sensibles al horizonte temporal ni a la tasa de descuento, pero si al precio del stent medicado. El valor esperado de la informacion perfecta fue significativamente mayor para la probabilidad de muerte y de sufrir una trombosis muy tardia del stent . Conclusiones El stent medicado con sirolimus no es costo-efectivo para pacientes con infarto agudo de miocardio con elevacion del ST en Colombia. Se recomienda mayor investigacion futura sobre la probabilidad de muerte y trombosis muy tardia del stent , asi como en subgrupos especificos de pacientes y stents medicados de segunda generacion.",
                "keywords": [],
                "start_page": 364,
                "end_page": 371,
                "volume": "21",
                "issue": "6",
                "date_published": 1414800000,
                "year_published": 2014,
                "languages": [],
                "bibtex": "@article{ceballos2014economic,\n  title={Economic evaluation of medicated stent vs. standard stent for patients with acute myocardial infarction with ST elevation in Colombia},\n  author={Ceballos, Mateo},\n  journal={Revista Colombiana de Cardiolog{\\'\\i}a},\n  volume={21},\n  number={6},\n  pages={364--371},\n  year={2014},\n  publisher={Sociedad Colombiana de Cardiologia}\n}\n",
                "funding_organization": "",
                "funding_details": "",
                "is_open_access": true,
                "open_access_status": "gold",
                "external_ids": [
                    {
                    "source": "lens",
                    "id": "101-092-542-835-129"
                    },
                    {
                    "source": "magid",
                    "id": "1967859901"
                    },
                    {
                    "source": "coreid",
                    "id": "82782675"
                    },
                    {
                    "source": "doi",
                    "id": "10.1016/j.rccar.2014.06.005"
                    },
                    {
                    "source": "scholar",
                    "id": "JdWY8CFxctwJ"
                    }
                ],
                "urls": [],
                "source": {
                    "_id": "600f50261fc9947fc8a8d2e8",
                    "updated": 1617579141,
                    "source_checked": [
                    {
                        "source": "doaj",
                        "ts": 1611616294
                    },
                    {
                        "source": "scopus",
                        "date": 1617579130
                    },
                    {
                        "source": "scholar",
                        "date": 1617579130
                    },
                    {
                        "source": "lens",
                        "date": 1617579130
                    }
                    ],
                    "title": "Revista Colombiana de Cardiología",
                    "title_idx": "revista colombiana de cardiología",
                    "type": "",
                    "publisher": "Elsevier",
                    "publisher_idx": "elsevier",
                    "institution": "Sociedad Colombiana de Cardiología y Cirugía Cardiovascular",
                    "institution_id": "",
                    "external_urls": [
                    {
                        "source": "site",
                        "url": "https://www.journals.elsevier.com/revista-colombiana-de-cardiologia/"
                    }
                    ],
                    "country": "ES",
                    "editorial_review": "Double blind peer review",
                    "submission_charges": "",
                    "submission_charges_url": "",
                    "submmission_currency": "",
                    "apc_charges": "",
                    "apc_currency": "",
                    "apc_url": "",
                    "serials": [
                    {
                        "type": "pissn",
                        "value": "01205633"
                    }
                    ],
                    "abbreviations": [
                    {
                        "type": "unknown",
                        "value": "Rev. Colomb. Cardiol."
                    }
                    ],
                    "aliases": [],
                    "subjects": [
                    {
                        "code": "RC666-701",
                        "scheme": "LCC",
                        "term": "Diseases of the circulatory (Cardiovascular) system"
                    }
                    ],
                    "keywords": [
                    "cardiovascular diseases",
                    "medical and surgery therapy",
                    "pediatric cardiology"
                    ],
                    "author_copyright": "False",
                    "license": [
                    {
                        "embedded_example_url": "http://www.sciencedirect.com/science/article/pii/S0120563316301887",
                        "NC": true,
                        "ND": true,
                        "BY": true,
                        "open_access": true,
                        "title": "CC BY-NC-ND",
                        "type": "CC BY-NC-ND",
                        "embedded": true,
                        "url": "https://www.elsevier.com/journals/revista-colombiana-de-cardiologia/0120-5633/open-access-journal",
                        "SA": false
                    }
                    ],
                    "languages": [
                    "EN",
                    "ES"
                    ],
                    "plagiarism_detection": true,
                    "active": true,
                    "publication_time": 17,
                    "deposit_policies": ""
                },
                "author_count": 1,
                "authors": [
                    {
                    "_id": "606a4c52aa884b9a1562e191",
                    "national_id": "",
                    "source_checked": [
                        {
                        "source": "lens",
                        "date": 1617579085
                        },
                        {
                        "source": "scholar",
                        "date": 1617579085
                        }
                    ],
                    "full_name": "Mateo Ceballos",
                    "first_names": "Mateo",
                    "last_names": "Ceballos",
                    "initials": "M",
                    "aliases": [
                        "mateo ceballos",
                        "ceballos, m.,",
                        "m. ceballos",
                        "m ceballos",
                        "P. Castro",
                        "p castro",
                        "Mateo Ceballos"
                    ],
                    "branches": [],
                    "keywords": [],
                    "external_ids": [
                        {
                        "source": "scholar",
                        "value": "IR4SXtgAAAAJ"
                        },
                        {
                        "source": "scopus",
                        "value": "56100586000"
                        },
                        {
                        "source": "scholar",
                        "value": "nhel9lYAAAAJ"
                        }
                    ],
                    "corresponding": true,
                    "corresponding_address": "",
                    "corresponding_email": "",
                    "updated": 1619612326,
                    "affiliations": [
                        {
                        "_id": "60120afa4749273de6161883",
                        "name": "Universidad de Antioquia",
                        "aliases": [],
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
                            "country_code": "CO",
                            "geonames_city": {
                                "id": 3674962,
                                "city": "Medellín",
                                "nuts_level1": null,
                                "nuts_level2": null,
                                "nuts_level3": null,
                                "geonames_admin1": {
                                "name": "Antioquia",
                                "ascii_name": "Antioquia",
                                "code": "CO.02"
                                },
                                "geonames_admin2": {
                                "name": "Medellín",
                                "ascii_name": "Medellin",
                                "code": "CO.02.05001"
                                },
                                "license": {
                                "attribution": "Data from geonames.org under a CC-BY 3.0 license",
                                "license": "http://creativecommons.org/licenses/by/3.0/"
                                }
                            }
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
                    }
                ],
                "references_count": 23,
                "references": [],
                "citations_count": 0,
                "citations_link": "",
                "citations": [],
                "topics": [
                    {
                    "source": "lens",
                    "topics": [
                        "Humanities",
                        "Stent",
                        "St elevation myocardial infarction",
                        "Medicine"
                    ]
                    }
                ]
                }
            ],
            "count": 2,
            "page": 1,
            "total_results": 25961
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
            production=self.get_production(idx,max_results,page,start_year,end_year,sort,"ascending")
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