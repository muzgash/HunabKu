from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId
from pymongo import ASCENDING,DESCENDING

class ColavFacultiesApi(HunabkuPluginBase):
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
        faculty = self.colav_db['branches'].find_one({"type":"faculty","_id":ObjectId(idx)})
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
                inst=self.colav_db['institutions'].find_one({"_id":inst_id})
                if inst:
                    entry["institution"]=[{"name":inst["name"],"id":inst_id,"logo":inst["logo_url"]}]

            for author in self.colav_db['authors'].find({"branches.id":faculty["_id"]}):
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
                    if branch["type"]=="department":
                        branch_db=self.colav_db["branches"].find_one({"_id":ObjectId(branch["id"])})
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
            "id": "602c50d1fd74967db0663835",
            "name": "Facultad de Ciencias Sociales y Humanas",
            "type": "faculty",
            "external_urls": [
                {
                "source": "website",
                "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/institucional/unidades-academicas/facultades/ciencias-sociales-humanas"
                }
            ],
            "departments": [
                {
                "id": "602c50f9fd74967db066385e",
                "name": "Departamento de Historia"
                },
                {
                "id": "602c50f9fd74967db066385f",
                "name": "Departamento de Antropología"
                },
                {
                "id": "602c50f9fd74967db0663860",
                "name": "Departamento de Sicología"
                },
                {
                "id": "602c50f9fd74967db0663861",
                "name": "Departamento de Sociología"
                },
                {
                "id": "602c50f9fd74967db0663862",
                "name": "Departamento de Trabajo Social"
                },
                {
                "id": "602c50f9fd74967db0663863",
                "name": "Departamento de Psicoanálisis"
                }
            ],
            "groups": [
                {
                "id": "602c510ffd74967db06639c7",
                "name": "Grupo de Investigación en Historia Social"
                },
                {
                "id": "602c510ffd74967db06638d5",
                "name": "Analisis de Residuos"
                },
                {
                "id": "602c510ffd74967db06639e3",
                "name": "Psicoanálisis, Sujeto y Sociedad"
                }
            ],
            "authors": [
                {
                "full_name": "Cesar Augusto Lenis Ballesteros",
                "id": "5fc7a46b9a7d07412f6cd3a0"
                },
                {
                "full_name": "Alberto Leon Gutierrez Tamayo",
                "id": "5fc81ecf9a7d07412f6cd3c1"
                },
                {
                "full_name": "Guillermo Antonio Correa Montoya",
                "id": "5fc820459a7d07412f6cd3c2"
                },
                {
                "full_name": "Jesus Gallo",
                "id": "5fc822199a7d07412f6cd3c3"
                },
                {
                "full_name": "Gabriel Jaime Velez Cuartas",
                "id": "5fc823a79a7d07412f6cd3c4"
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
                "_id": "606a4c6aaa884b9a1562e46a",
                "updated": 1617579113,
                "source_checked": [
                    {
                    "source": "lens",
                    "ts": 1617579113
                    },
                    {
                    "source": "oadoi",
                    "ts": 1617579113
                    },
                    {
                    "source": "scholar",
                    "ts": 1617579113
                    }
                ],
                "publication_type": "journal article",
                "titles": [
                    {
                    "title": "Representaciones sobre lo indígena y su vínculo con tendencias culturales globalizadas",
                    "lang": "es"
                    }
                ],
                "subtitle": "",
                "abstract": "This article describes a set of representations about native cultures manifested in a sector of the non-indigenous population of Colombia, where shamanism is increasingly mentioned, and where natives are imagined as having a spiritual and alternative wisdom beneficial to western societies. The analysis of these and other ideas reveals similarities with the narratives used to represent other indigenous or ethnic cultures in different latitudes. Those similarities, it is argued, do not come from objective cultural resemblances between ethnic groups; they come from common sociocultural characteristics of the people who construct those representations of the ethnic. These findings support the conclusion that this kind of indigenism is the local manifestation of a globalized ideology centered on the ideals and needs of the modern self.",
                "keywords": [],
                "start_page": 163,
                "end_page": 184,
                "volume": "14",
                "issue": "27",
                "date_published": 1435708800,
                "year_published": 2015,
                "languages": [],
                "bibtex": "@article{sarrazin2015representaciones,\n  title={Representaciones sobre lo ind{\\'\\i}gena y su v{\\'\\i}nculo con tendencias culturales globalizadas},\n  author={Sarrazin, Jean Paul},\n  journal={Anagramas Rumbos y Sentidos de la Comunicaci{\\'o}n},\n  volume={14},\n  number={27},\n  pages={163--184},\n  year={2015}\n}\n",
                "funding_organization": "",
                "funding_details": "",
                "is_open_access": true,
                "open_access_status": "gold",
                "external_ids": [
                    {
                    "source": "lens",
                    "id": "174-213-784-605-277"
                    },
                    {
                    "source": "magid",
                    "id": "2206271623"
                    },
                    {
                    "source": "doi",
                    "id": "10.22395/angr.v14n27a9"
                    },
                    {
                    "source": "scholar",
                    "id": "5OZ9yk1GuksJ"
                    }
                ],
                "urls": [],
                "source": {
                    "_id": "600f50271fc9947fc8a8de90",
                    "updated": 1617579114,
                    "source_checked": [
                    {
                        "source": "doaj",
                        "ts": 1611616295
                    },
                    {
                        "source": "scholar",
                        "date": 1617579113
                    },
                    {
                        "source": "lens",
                        "date": 1617579113
                    }
                    ],
                    "title": "Anagramas Rumbos y Sentidos de la Comunicación",
                    "type": "",
                    "publisher": "Universidad de Medellín, Sello Editorial",
                    "publisher_idx": "universidad de medellín, sello editorial",
                    "institution": "Universidad de Medellín",
                    "institution_id": "60120d554749273de6167ede",
                    "external_urls": [
                    {
                        "source": "site",
                        "url": "http://revistas.udem.edu.co/index.php/anagramas"
                    }
                    ],
                    "country": "CO",
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
                        "value": "16922522"
                    },
                    {
                        "type": "eissn",
                        "value": "22484086"
                    }
                    ],
                    "abbreviations": [],
                    "aliases": [],
                    "subjects": [
                    {
                        "code": "P87-96",
                        "scheme": "LCC",
                        "term": "Communication. Mass media"
                    }
                    ],
                    "keywords": [
                    "literature",
                    "education",
                    "culture",
                    "comunication",
                    "social movements",
                    "movies"
                    ],
                    "author_copyright": "False",
                    "license": [
                    {
                        "embedded_example_url": "http://revistas.udem.edu.co/index.php/anagramas/article/view/1180",
                        "NC": true,
                        "ND": false,
                        "BY": true,
                        "open_access": true,
                        "title": "CC BY-NC",
                        "type": "CC BY-NC",
                        "embedded": true,
                        "url": "http://revistas.udem.edu.co/index.php/anagramas/about/editorialPolicies#openAccessPolicy",
                        "SA": false
                    }
                    ],
                    "languages": [
                    "EN",
                    "PT",
                    "ES"
                    ],
                    "plagiarism_detection": false,
                    "active": true,
                    "publication_time": 6,
                    "deposit_policies": ""
                },
                "author_count": 1,
                "authors": [
                    {
                    "_id": "5fc817dd9a7d07412f6cd3bc",
                    "full_name": "Jean Paul Sarrazin Martinez",
                    "first_names": "Jean Paul",
                    "last_names": "Sarrazin Martinez",
                    "initials": "JP",
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
                            "_id": "602c50d1fd74967db0663835",
                            "name": "Facultad de Ciencias Sociales y Humanas",
                            "abbreviations": [
                                "FCSH"
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
                                "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/institucional/unidades-academicas/facultades/ciencias-sociales-humanas"
                                }
                            ],
                            "external_ids": [],
                            "keywords": [],
                            "subjects": []
                            },
                            {
                            "_id": "602c50f9fd74967db0663861",
                            "name": "Departamento de Sociología",
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
                            "_id": "602c510ffd74967db0663936",
                            "name": "Religión, Cultura y Sociedad",
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
                                "email": "gruporeligionculturaysociedad@udea.edu.co"
                                }
                            ],
                            "external_urls": [
                                {
                                "source": "gruplac",
                                "url": "https://scienti.colciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000001604"
                                }
                            ],
                            "external_ids": [
                                {
                                "source": "colciencias",
                                "id": "COL0015669"
                                }
                            ],
                            "keywords": [],
                            "subjects": [
                                {
                                "source": "area_ocde",
                                "subjects": [
                                    "humanidades"
                                ]
                                },
                                {
                                "source": "subarea_ocde",
                                "subjects": [
                                    "historia y arqueología"
                                ]
                                },
                                {
                                "source": "udea",
                                "subjects": [
                                    "ciencias sociales"
                                ]
                                },
                                {
                                "source": "gruplac",
                                "subjects": [
                                    "conflictos, religiones y religiosidades",
                                    "esoterismos y espiritualidades mágicas",
                                    "globalización, secularización y revitalización de las religiones",
                                    "iconografía de lo sagrado",
                                    "instituciones y sociabilidades religiosas"
                                ]
                                }
                            ]
                            }
                        ]
                        }
                    ],
                    "keywords": [
                        "elites",
                        "cultural hegemony",
                        "indigenism",
                        "identity"
                    ],
                    "external_ids": [
                        {
                        "source": "orcid",
                        "value": "0000-0002-8022-4674"
                        },
                        {
                        "source": "researchid",
                        "value": "B-2896-2017"
                        },
                        {
                        "source": "scopus",
                        "value": "56457940700"
                        }
                    ],
                    "branches": [
                        {
                        "name": "Facultad de Ciencias Sociales y Humanas",
                        "type": "faculty",
                        "id": "602c50d1fd74967db0663835"
                        },
                        {
                        "name": "Departamento de Sociología",
                        "type": "department",
                        "id": "602c50f9fd74967db0663861"
                        },
                        {
                        "name": "Religión, Cultura y Sociedad",
                        "id": "602c510ffd74967db0663936",
                        "type": "group"
                        }
                    ],
                    "updated": 1619412232
                    }
                ],
                "references_count": 33,
                "references": [],
                "citations_count": 24,
                "citations_link": "/scholar?cites=5456751198436452068&as_sdt=2005&sciodt=0,5&hl=en&oe=ASCII",
                "citations": [],
                "topics": [
                    {
                    "source": "lens",
                    "topics": [
                        "Ethnic group",
                        "Sociology",
                        "Ideology",
                        "Sociocultural evolution",
                        "Globalization",
                        "Modernity",
                        "Population",
                        "Social science",
                        "Shamanism",
                        "Indigenous"
                    ]
                    }
                ]
                },
                {
                "_id": "606a4c92aa884b9a1562e896",
                "updated": 1617579154,
                "source_checked": [
                    {
                    "source": "lens",
                    "ts": 1617579154
                    },
                    {
                    "source": "oadoi",
                    "ts": 1617579154
                    },
                    {
                    "source": "scholar",
                    "ts": 1617579154
                    }
                ],
                "publication_type": "journal article",
                "titles": [
                    {
                    "title": "Lucha por el reconocimiento en los modelos de medición: el caso de la Universidad de Antioquia",
                    "lang": "es"
                    }
                ],
                "subtitle": "",
                "abstract": "Este articulo aporta a la fundamentacion de una sociologia del conocimiento la recuperacion del concepto de lucha intersubjetiva por el reconocimiento. De forma paralela, expone algunos hallazgos de la fase empirico-cualitativa de la investigacion: Linea base para la construccion de indicadores de comunicacion del conocimiento en el area de ciencias sociales, humanidades y artes . En cuanto a la categoria teorica, los investigadores del area de Ciencias Sociales, Humanidades y Artes de la Universidad de Antioquia reclaman que sus disciplinas sean vistas como una forma particular de conocer . Adicionalmente, consideran que, tal como se encuentran configurados, el Sistema Nacional de Ciencia, Tecnologia e Innovacion (sncti) y el Sistema Universitario de Investigacion (sui) tienen una vision unidimensional del conocimiento.",
                "keywords": [],
                "start_page": 259,
                "end_page": 281,
                "volume": "14",
                "issue": "34",
                "date_published": 1512086400,
                "year_published": 2017,
                "languages": [],
                "bibtex": "@article{pineres2017lucha,\n  title={Lucha por el reconocimiento en los modelos de medici{\\'o}n: el caso de la Universidad de Antioquia},\n  author={Pi{\\~n}eres Sus, Juan David and V{\\'e}lez Cuartas, Gabriel and Montes Sep{\\'u}lveda, Carolina},\n  journal={Andamios},\n  volume={14},\n  number={34},\n  pages={259--281},\n  year={2017},\n  publisher={Colegio de Humanidades y Ciencias Sociales, Universidad Aut{\\'o}noma de la~�}\n}\n",
                "funding_organization": "",
                "funding_details": "",
                "is_open_access": true,
                "open_access_status": "bronze",
                "external_ids": [
                    {
                    "source": "lens",
                    "id": "094-568-608-170-967"
                    },
                    {
                    "source": "doi",
                    "id": "10.29092/uacm.v14i34.589"
                    },
                    {
                    "source": "magid",
                    "id": "2780077950"
                    },
                    {
                    "source": "scholar",
                    "id": "692pv4hGPxwJ"
                    }
                ],
                "urls": [],
                "source": {
                    "_id": "606a4c92aa884b9a1562e894",
                    "source_checked": [
                    {
                        "source": "scholar",
                        "date": 1619423437
                    },
                    {
                        "source": "lens",
                        "date": 1617579154
                    },
                    {
                        "source": "scopus",
                        "date": 1619423437
                    },
                    {
                        "source": "wos",
                        "date": 1619423437
                    }
                    ],
                    "updated": 1619423437,
                    "title": "Andamios",
                    "type": "journal",
                    "publisher": "Universidad Nacional Autonoma de Mexico",
                    "institution": "",
                    "institution_id": "",
                    "country": "MX",
                    "submission_charges": "",
                    "submission_currency": "",
                    "apc_charges": "",
                    "apc_currency": "",
                    "serials": [
                    {
                        "type": "pissn",
                        "value": "18700063"
                    }
                    ],
                    "abbreviations": [
                    {
                        "type": "unknown",
                        "value": "Andamios"
                    },
                    {
                        "type": "char",
                        "value": "ANDAMIOS"
                    }
                    ],
                    "subjects": {}
                },
                "author_count": 3,
                "authors": [
                    {
                    "_id": "5fc7dd169a7d07412f6cd3b3",
                    "full_name": "Juan David Piñeres Sus",
                    "first_names": "Juan David",
                    "last_names": "Piñeres Sus",
                    "initials": "JD",
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
                            "_id": "602c50d1fd74967db0663835",
                            "name": "Facultad de Ciencias Sociales y Humanas",
                            "abbreviations": [
                                "FCSH"
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
                                "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/institucional/unidades-academicas/facultades/ciencias-sociales-humanas"
                                }
                            ],
                            "external_ids": [],
                            "keywords": [],
                            "subjects": []
                            },
                            {
                            "_id": "602c50f9fd74967db0663860",
                            "name": "Departamento de Sicología",
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
                            "_id": "602c510ffd74967db0663919",
                            "name": "Grupo de Investigación en Psicologia Cognitiva",
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
                                "email": "grupopsicologiacognitiva@udea.edu.co"
                                }
                            ],
                            "external_urls": [
                                {
                                "source": "website",
                                "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/investigacion/grupos-investigacion/ciencias-sociales/psicologia-cognitiva"
                                },
                                {
                                "source": "gruplac",
                                "url": "https://scienti.colciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000001824"
                                }
                            ],
                            "external_ids": [
                                {
                                "source": "colciencias",
                                "id": "COL0011447"
                                }
                            ],
                            "keywords": [],
                            "subjects": [
                                {
                                "source": "area_ocde",
                                "subjects": [
                                    "ciencias sociales"
                                ]
                                },
                                {
                                "source": "subarea_ocde",
                                "subjects": [
                                    "psicología"
                                ]
                                },
                                {
                                "source": "udea",
                                "subjects": [
                                    "ciencias sociales"
                                ]
                                },
                                {
                                "source": "gruplac",
                                "subjects": [
                                    "evolución y cognición",
                                    "neuropsicologia y educación",
                                    "perfiles cognitivos y psicometría",
                                    "psicología cliníca y de la salud",
                                    "cultura y cognición"
                                ]
                                }
                            ]
                            }
                        ]
                        }
                    ],
                    "keywords": [
                        "historical-pedagogical anthropology",
                        "bentham debate",
                        "flood",
                        "risk perception"
                    ],
                    "external_ids": [
                        {
                        "source": "orcid",
                        "value": "0000-0003-1870-4113"
                        },
                        {
                        "source": "scopus",
                        "value": "57193865053"
                        },
                        {
                        "source": "scholar",
                        "value": "UepzjHwAAAAJ"
                        },
                        {
                        "source": "scopus",
                        "value": "57215416522"
                        }
                    ],
                    "branches": [
                        {
                        "name": "Facultad de Ciencias Sociales y Humanas",
                        "type": "faculty",
                        "id": "602c50d1fd74967db0663835"
                        },
                        {
                        "name": "Departamento de Sicología",
                        "type": "department",
                        "id": "602c50f9fd74967db0663860"
                        },
                        {
                        "name": "Grupo de Investigación en Psicologia Cognitiva",
                        "id": "602c510ffd74967db0663919",
                        "type": "group"
                        }
                    ],
                    "updated": 1619423437
                    },
                    {
                    "_id": "5fc823a79a7d07412f6cd3c4",
                    "full_name": "Gabriel Jaime Velez Cuartas",
                    "first_names": "Gabriel Jaime",
                    "last_names": "Velez Cuartas",
                    "initials": "GJ",
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
                            "_id": "602c50d1fd74967db0663835",
                            "name": "Facultad de Ciencias Sociales y Humanas",
                            "abbreviations": [
                                "FCSH"
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
                                "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/institucional/unidades-academicas/facultades/ciencias-sociales-humanas"
                                }
                            ],
                            "external_ids": [],
                            "keywords": [],
                            "subjects": []
                            },
                            {
                            "_id": "602c50f9fd74967db0663861",
                            "name": "Departamento de Sociología",
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
                            "_id": "602c510ffd74967db0663988",
                            "name": "Redes y Actores Sociales",
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
                                "email": "grupoaliado@udea.edu.co"
                                }
                            ],
                            "external_urls": [
                                {
                                "source": "gruplac",
                                "url": "https://scienti.colciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000011521"
                                },
                                {
                                "source": "scholar",
                                "url": "https://scholar.google.com/citations?user=Zy-vPf0AAAAJ"
                                }
                            ],
                            "external_ids": [
                                {
                                "source": "colciencias",
                                "id": "COL0114177"
                                },
                                {
                                "source": "bupp",
                                "id": "ES84190016"
                                }
                            ],
                            "keywords": [],
                            "subjects": [
                                {
                                "source": "area_ocde",
                                "subjects": [
                                    "ciencias sociales"
                                ]
                                },
                                {
                                "source": "subarea_ocde",
                                "subjects": [
                                    "sociología"
                                ]
                                },
                                {
                                "source": "udea",
                                "subjects": [
                                    "ciencias sociales"
                                ]
                                },
                                {
                                "source": "gruplac",
                                "subjects": [
                                    "análisis de redes y capital social",
                                    "estudios sociales de la ciencia y sociedad del conocimiento",
                                    "precariedad, subjetividad y género",
                                    "problemas rurales y ruralidades",
                                    "redes de políticas públicas y acción colectiva",
                                    "teoría sociológica relacional"
                                ]
                                }
                            ]
                            }
                        ]
                        }
                    ],
                    "keywords": [
                        "invisible colleges",
                        "intellectual property",
                        "caribbean",
                        "arts",
                        "fight for acknowledgement",
                        "humanities",
                        "knowledge sociology",
                        "science",
                        "social sciences"
                    ],
                    "external_ids": [
                        {
                        "source": "orcid",
                        "value": "0000-0003-2350-4650"
                        },
                        {
                        "source": "scopus",
                        "value": "56348967600"
                        },
                        {
                        "source": "scholar",
                        "value": "HcAnZ0MAAAAJ"
                        },
                        {
                        "source": "scopus",
                        "value": "57194502920"
                        }
                    ],
                    "branches": [
                        {
                        "name": "Facultad de Ciencias Sociales y Humanas",
                        "type": "faculty",
                        "id": "602c50d1fd74967db0663835"
                        },
                        {
                        "name": "Departamento de Sociología",
                        "type": "department",
                        "id": "602c50f9fd74967db0663861"
                        },
                        {
                        "name": "Redes y Actores Sociales",
                        "id": "602c510ffd74967db0663988",
                        "type": "group"
                        }
                    ],
                    "updated": 1619654364
                    },
                    {
                    "_id": "606a4c92aa884b9a1562e895",
                    "source_checked": [
                        {
                        "source": "lens",
                        "date": 1617579154
                        },
                        {
                        "source": "scholar",
                        "date": 1617579154
                        }
                    ],
                    "full_name": "Carolina Sepúlveda",
                    "first_names": "Carolina",
                    "last_names": "Sepúlveda",
                    "initials": "C",
                    "branches": [],
                    "keywords": [],
                    "external_ids": [],
                    "corresponding": false,
                    "corresponding_address": "",
                    "corresponding_email": "",
                    "updated": 1619614750,
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
                    }
                ],
                "references_count": "",
                "references": [],
                "citations_count": 4,
                "citations_link": "/scholar?cites=2035423109739830763&as_sdt=2005&sciodt=0,5&hl=en&oe=ASCII",
                "citations": [],
                "topics": [
                    {
                    "source": "lens",
                    "topics": [
                        "Sociology",
                        "Humanities",
                        "Linea",
                        "Social science"
                    ]
                    }
                ]
                }
            ],
            "count": 100,
            "page": 1,
            "total_results": 389
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