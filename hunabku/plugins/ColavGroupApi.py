from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId
from pymongo import ASCENDING,DESCENDING

class ColavGroupApi(HunabkuPluginBase):
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
        group = self.db['branches'].find_one({"type":"group","_id":ObjectId(idx)})
        if group:
            entry={"id":group["_id"],
                "name":group["name"],
                "type":group["type"],
                "external_urls":group["external_urls"],
                "departments":[],
                "groups":[],
                "authors":[],
                "institution":[]
            }
            
            inst_id=""
            for rel in group["relations"]:
                if rel["type"]=="university":
                    inst_id=rel["id"]
                    break
            if inst_id:
                inst=self.db['institutions'].find_one({"_id":inst_id})
                if inst:
                    entry["institution"]=[{"name":inst["name"],"id":inst_id}]#,"logo":inst["logo"]}]

            for author in self.db['authors'].find({"branches.id":group["_id"]}):
                author_entry={
                    "full_name":author["full_name"],
                    "id":str(author["_id"])
                }
                entry["authors"].append(author_entry)
                
            return entry
        else:
            return None

    @endpoint('/api/group', methods=['GET'])
    def api_group(self):
        """
        @api {get} /api/group Group
        @apiName api
        @apiGroup CoLav api
        @apiDescription Responds with information about the group

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
                    "updated": 1613691354,
                    "source_checked": [
                        {
                        "source": "lens",
                        "ts": 1613691354
                        },
                        {
                        "source": "wos",
                        "ts": 1613691354
                        },
                        {
                        "source": "scholar",
                        "ts": 1613691354
                        },
                        {
                        "source": "scholar",
                        "ts": 1613691354
                        },
                        {
                        "source": "scopus",
                        "ts": 1613691354
                        }
                    ],
                    "publication_type": "journal article",
                    "titles": [
                        {
                        "title": "Comments on the Riemann conjecture and index theory on Cantorian fractal space-time",
                        "lang": "en"
                        }
                    ],
                    "subtitle": "",
                    "abstract": "Abstract An heuristic proof of the Riemann conjecture is proposed. It is based on the old idea of Polya–Hilbert. A discrete/fractal derivative self-adjoint operator whose spectrum may contain the non-trivial zeroes of the zeta function is presented. To substantiate this heuristic proposal we show using generalized index-theory arguments, corresponding to the (fractal) spectral dimensions of fractal branes living in Cantorian-fractal space-time, how the required negative traces associated with those derivative operators naturally agree with the zeta function evaluated at the spectral dimensions. The ζ(0)=−1/2 plays a fundamental role. Final remarks on the recent developments in the proof of the Riemann conjecture are made.",
                    "keywords": [
                        "eigenvalues and eigenfunctions",
                        "hamiltonians",
                        "heuristic methods",
                        "mathematical models",
                        "riemann conjecture",
                        "fractals"
                    ],
                    "start_page": 1407,
                    "end_page": 1419,
                    "volume": "13",
                    "issue": "7",
                    "date_published": 1022889600,
                    "year_published": 2002,
                    "languages": [
                        "en"
                    ],
                    "bibtex": "@article{castro2002comments,\n  title={Comments on the Riemann conjecture and index theory on Cantorian fractal space-time},\n  author={Castro, Carlos and Mahecha, Jorge},\n  journal={Chaos, Solitons \\& Fractals},\n  volume={13},\n  number={7},\n  pages={1407--1419},\n  year={2002},\n  publisher={Elsevier}\n}\n",
                    "funding_organization": "Abdus Salam International Centre for Theoretical Physics, ICTP\n\nAbdus Salam International Centre for Theoretical Physics, ICTP",
                    "funding_details": [
                        "We acknowledge Jörn Steuding, Johann Wolfgang Goethe-Universität, Frankfurt, for giving us Ref. [16] . Also, very constructive comments from Matthew Watkins, School of Mathematical Sciences, University of Exeter, and Andrew Odlyzko's from ATT Labs are gratefully acknowledged. CC is indebted to E. Spallucci for his kind hospitality in Trieste were this work was completed, to A. Granik, J. Gonzalez, L. Reyes and R. Guevara for many discussions. JMG is pleased to acknowledge the support of the present work by Centro de Investigaciones en Ciencias Exactas y Naturales of the Universidad de Antioquia, CIEN, and the International Centre for Theoretical Physics, ICTP."
                    ],
                    "is_open_access": true,
                    "open_access_status": "green",
                    "external_ids": [
                        {
                        "source": "lens",
                        "id": "037-714-093-137-871"
                        },
                        {
                        "source": "doi",
                        "id": "10.1016/s0960-0779(01)00124-2"
                        },
                        {
                        "source": "magid",
                        "id": "2162579309"
                        },
                        {
                        "source": "wos",
                        "id": "000173673900004"
                        },
                        {
                        "source": "scopus",
                        "id": "2-s2.0-0036604651"
                        },
                        {
                        "source": "scholar",
                        "id": "PIHZsSMsIIEJ"
                        }
                    ],
                    "urls": [
                        {
                        "source": "scopus",
                        "url": "https://www.scopus.com/inward/record.uri?eid=2-s2.0-0036604651&doi=10.1016%2fS0960-0779%2801%2900124-2&partnerID=40&md5=f6676c8bd826e4fd140c2ad95e164234"
                        }
                    ],
                    "source": {
                        "_id": "602ef9dd728ecc2d8e62e02d",
                        "source_checked": [
                        {
                            "source": "scopus",
                            "date": 1613691354
                        },
                        {
                            "source": "wos",
                            "date": 1613691354
                        },
                        {
                            "source": "scholar",
                            "date": 1613691354
                        },
                        {
                            "source": "lens",
                            "date": 1613691354
                        }
                        ],
                        "updated": 1613691354,
                        "title": "Chaos Solitons & Fractals",
                        "type": "journal",
                        "publisher": "Elsevier Limited",
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
                            "value": "09600779"
                        },
                        {
                            "type": "coden",
                            "value": "CSFOE"
                        }
                        ],
                        "abbreviations": [
                        {
                            "type": "unknown",
                            "value": "Chaos Solitons Fractals"
                        },
                        {
                            "type": "char",
                            "value": "CHAOS SOLITON FRACT"
                        }
                        ],
                        "subjects": {}
                    },
                    "author_count": 2,
                    "authors": [
                        {
                        "_id": "602ef9dd728ecc2d8e62e02f",
                        "national_id": "",
                        "source_checked": [
                            {
                            "source": "lens",
                            "date": 1613691354
                            },
                            {
                            "source": "wos",
                            "date": 1613691354
                            },
                            {
                            "source": "scopus",
                            "date": 1613691354
                            },
                            {
                            "source": "scholar",
                            "date": 1613691354
                            }
                        ],
                        "full_name": "Carlos Castro",
                        "first_names": "Carlos",
                        "last_names": "Castro",
                        "initials": "C",
                        "branches": [],
                        "keywords": [],
                        "external_ids": [
                            {
                            "source": "scopus",
                            "value": "7202237774"
                            },
                            {
                            "source": "scholar",
                            "value": "yVQk0H4AAAAJ"
                            }
                        ],
                        "corresponding": false,
                        "corresponding_address": "",
                        "corresponding_email": "",
                        "updated": 1613691354,
                        "affiliations": [
                            {
                            "_id": "602ef9dd728ecc2d8e62e02e",
                            "name": "Center for Theoretical Studies, University of Miami",
                            "abbreviations": [],
                            "addresses": [],
                            "types": [],
                            "external_ids": [],
                            "external_urls": [],
                            "branches": []
                            }
                        ]
                        },
                        {
                        "_id": "5fc65863b246cc0887190a9f",
                        "national_id": 8298535,
                        "full_name": "Jorge Eduardo Mahecha Gomez",
                        "first_names": "Jorge Eduardo",
                        "last_names": "Mahecha Gomez",
                        "initials": "JE",
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
                                "_id": "602c50f9fd74967db0663859",
                                "name": "Instituto de física",
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
                                "name": "Grupo de física atómica y molecular",
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
                                    "state": null,
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
                            "resonant states",
                            "initial value representation",
                            "filter-diagonalization method",
                            "harmonic inversion method",
                            "classical mechanics",
                            "gauge invariance",
                            "symmetry breaking",
                            "atoms in electromagnetic traps",
                            "nonlinear dynamics and chaos",
                            "quantum chaos",
                            "bethe-salpeter equation",
                            "pseudoscalar mesons",
                            "leptonic decays",
                            "radiative decays",
                            "power counting rule"
                        ],
                        "external_ids": [
                            {
                            "source": "scopus",
                            "value": "6507002545"
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
                            "type": "group",
                            "id": "602c510ffd74967db06638fb"
                            }
                        ],
                        "updated": 1613691357
                        }
                    ],
                    "references_count": 36,
                    "references": [],
                    "citations_count": 5,
                    "citations_link": "/scholar?cites=9304485361966743868&as_sdt=2005&sciodt=0,5&hl=en&oe=ASCII",
                    "citations": []
                    }
                ],
                "count": 3,
                "page": 1,
                "total_results": 3
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