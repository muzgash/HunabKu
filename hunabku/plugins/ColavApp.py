from hunabku.HunabkuBase import HunabkuPluginBase, endpoint
from bson import ObjectId
import pprint

class ColavApp(HunabkuPluginBase):
    def __init__(self, hunabku):
        super().__init__(hunabku)
        self.pretty_json=pprint.pformat('{"authors": [], "external_urls": [{"source": "website", "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/unidades-academicas/ciencias-exactas-naturales"}], "type": "faculty", "groups": [], "institution": [], "id": "602599029e9b96dff8bf00ab", "departments": [{"name": "Decanatura facultad de ciencias exactas y naturales", "id": "602599059e9b96dff8bf00d5"}, {"name": "Instituto de matem\u00e1ticas", "id": "602599059e9b96dff8bf00d0"}, {"name": "Instituto de f\u00edsica", "id": "602599059e9b96dff8bf00d1"}, {"name": "Instituto de biolog\u00eda", "id": "602599059e9b96dff8bf00d2"}, {"name": "Instituto de qu\u00edmica", "id": "602599059e9b96dff8bf00d3"}, {"name": "Centro de investigaciones de ciencias exactas y naturales", "id": "602599059e9b96dff8bf00d4"}], "name": "Facultad de ciencias exactas y naturales"}')

    @endpoint('/api/faculty', methods=['GET'])
    def api_faculty(self):
        """
        @api {get} /api/faculty Requests faculty general information or the list of papers
        @apiName api
        @apiGroup CoLav api
        @apiDescription Responds with information about the faculty

        @apiParam {String} data Wether is the general information or the list of papers
        @apiParam {Object} id the id of the faculty requested in mongodb
        @apiParam {String} apikey  Credential for authentication

        @apiError (Error 401) msg  The HTTP 401 Unauthorized invalid authentication apikey for the target resource.
        @apiError (Error 204) msg  The HTTP 204 No Content.
        @apiError (Error 401) msg  The HTTP 200 OK.

        @apiSuccessExample {json} Success-Response (info=data):
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
        @apiSuccessExample {json} Success-Response (info=list):
            HTTP/1.1 200 OK
            [
                {
                    "abbreviations": [
                    "FCEN"
                    ],
                    "external_urls": [
                    {
                        "source": "website",
                        "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/unidades-academicas/ciencias-exactas-naturales"
                    }
                    ],
                    "name": "Facultad de ciencias exactas y naturales",
                    "id": "602599029e9b96dff8bf00ab"
                },
                {
                    "abbreviations": [],
                    "external_urls": [
                    {
                        "source": "website",
                        "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/institucional/unidades-academicas/facultades/ciencias-farmaceuticas-alimentarias"
                    }
                    ],
                    "name": "Facultad de ciencias farmacéuticas y alimentarias",
                    "id": "602599029e9b96dff8bf00ac"
                }
            ]
        @apiSuccessExample {json} Success-Response (info=paper):
        [
            {
                "_id": "602ef788728ecc2d8e62d4f1",
                "updated": 1613690757,
                "source_checked": [
                {
                    "source": "lens",
                    "ts": 1613690757
                },
                {
                    "source": "wos",
                    "ts": 1613690757
                },
                {
                    "source": "scholar",
                    "ts": 1613690757
                },
                {
                    "source": "scholar",
                    "ts": 1613690757
                },
                {
                    "source": "scopus",
                    "ts": 1613690757
                }
                ],
                "publication_type": "journal article",
                "titles": [
                {
                    "title": "Product and quotient of correlated beta variables",
                    "lang": "en",
                    "title_idx": "product and quotient of correlated beta variables"
                }
                ],
                "subtitle": "",
                "abstract": "Abstract Let U , V , W be independent random variables having a standard gamma distribution with respective shape parameters a , b , c , and define X = U / ( U + W ) , Y = V / ( V + W ) . Clearly, X and Y are correlated each having a beta distribution, X ∼ B ( a , c ) and Y ∼ B ( b , c ) . In this article we derive probability density functions of X Y , X / Y and X / ( X + Y ) .",
                "abstract_idx": "abstract let u , v , w be independent random variables having a standard gamma distribution with respective shape parameters a , b , c , and define x = u / ( u + w ) , y = v / ( v + w ) . clearly, x and y are correlated each having a beta distribution, x ∼ b ( a , c ) and y ∼ b ( b , c ) . in this article we derive probability density functions of x y , x / y and x / ( x + y ) .",
                "keywords": [
                "cluster analysis",
                "probability distributions",
                "random variables",
                "yttrium alloys",
                "beta distribution",
                "bivariate distribution",
                "gauss hypergeometric function",
                "product",
                "quotient",
                "probability density function"
                ],
                "start_page": 105,
                "end_page": 109,
                "volume": "22",
                "issue": "1",
                "date_published": "",
                "year_published": 2009,
                "languages": [
                "en"
                ],
                "bibtex": "@article{nagar2009product,\n  title={Product and quotient of correlated beta variables},\n  author={Nagar, Daya K and Orozco-Casta{\\~n}eda, Johanna Marcela and Gupta, Arjun K},\n  journal={Applied Mathematics Letters},\n  volume={22},\n  number={1},\n  pages={105--109},\n  year={2009},\n  publisher={Elsevier}\n}\n",
                "funding_organization": "Universidad de Antioquia, UdeA",
                "funding_details": [
                "The research work of DKN and JMO-C was supported by the Comité para el Desarrollo de la Investigación, Universidad de Antioquia research grant no. IN550CE."
                ],
                "is_open_access": false,
                "open_access_status": "closed",
                "external_ids": [
                {
                    "source": "lens",
                    "id": "017-994-271-766-456"
                },
                {
                    "source": "doi",
                    "id": "10.1016/j.aml.2008.02.014"
                },
                {
                    "source": "magid",
                    "id": "2097225090"
                },
                {
                    "source": "wos",
                    "id": "000262240800021"
                },
                {
                    "source": "scopus",
                    "id": "2-s2.0-55849151367"
                },
                {
                    "source": "scholar",
                    "id": "_fj95eM0K1IJ"
                }
                ],
                "urls": [
                {
                    "source": "scopus",
                    "url": "https://www.scopus.com/inward/record.uri?eid=2-s2.0-55849151367&doi=10.1016%2fj.aml.2008.02.014&partnerID=40&md5=c9769e0da8fdc04b8259694901b4caaa"
                }
                ],
                "source": {
                "_id": "602ef788728ecc2d8e62d4ef",
                "source_checked": [
                    {
                    "source": "scopus",
                    "date": 1613690757
                    },
                    {
                    "source": "wos",
                    "date": 1613690757
                    },
                    {
                    "source": "scholar",
                    "date": 1613690757
                    },
                    {
                    "source": "lens",
                    "date": 1613690757
                    }
                ],
                "updated": 1613690757,
                "title": "Applied Mathematics Letters",
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
                    "value": "08939659"
                    },
                    {
                    "type": "coden",
                    "value": "AMLEE"
                    }
                ],
                "abbreviations": [
                    {
                    "type": "unknown",
                    "value": "Appl Math Lett"
                    },
                    {
                    "type": "char",
                    "value": "APPL MATH LETT"
                    },
                    {
                    "type": "iso",
                    "value": "Appl. Math. Lett."
                    }
                ],
                "subjects": {},
                "title_idx": "applied mathematics letters",
                "publisher_idx": "elsevier limited"
                },
                "author_count": 3,
                "authors": [
                {
                    "_id": "5fc5b0a5b246cc0887190a69",
                    "national_id": 279739,
                    "full_name": "Daya Krishna Nagar",
                    "first_names": "Daya  Krishna",
                    "last_names": "Nagar",
                    "initials": "DK",
                    "aliases": [
                    "daya k. nagar",
                    "nagar d.k.",
                    "arjun k. gupta",
                    "arjun k gupta",
                    "daya k nagar",
                    "ak gupta"
                    ],
                    "affiliations": [
                    {
                        "_id": "60120afa4749273de6161883",
                        "branches": [
                        {
                            "_id": "602c50d1fd74967db0663833",
                            "name": "Facultad de ciencias exactas y naturales",
                            "name_idx": "facultad de ciencias exactas y naturales",
                            "aliases": [],
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
                                },
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
                            "_id": "602c50f9fd74967db0663858",
                            "name": "Instituto de matemáticas",
                            "name_idx": "instituto de matematicas",
                            "aliases": [],
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
                                },
                                "email": ""
                            }
                            ],
                            "external_urls": [],
                            "external_ids": [],
                            "keywords": [],
                            "subjects": []
                        },
                        {
                            "_id": "602c510ffd74967db06638d6",
                            "name": "Análisis multivariado",
                            "name_idx": "analisis multivariado",
                            "aliases": [],
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
                                },
                                "email": ""
                            }
                            ],
                            "external_urls": [
                            {
                                "source": "website",
                                "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/investigacion/grupos-investigacion/ciencias-naturales-exactas/analisis-multivariado"
                            },
                            {
                                "source": "gruplac",
                                "url": "https://scienti.colciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000001670"
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
                                "matemática"
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
                                "análisis multivariado",
                                "computación",
                                "funciones especiales",
                                "pruebas de hipótesis y estimación",
                                "teoría de las distribuciones"
                                ]
                            }
                            ]
                        }
                        ]
                    }
                    ],
                    "keywords": [
                    "beta distribution",
                    "bivariate distribution",
                    "extended beta function",
                    "extended confluent hypergeometric function",
                    "gauss hypergeometric function",
                    "product",
                    "quotient",
                    "confluent hypergeometric function",
                    "extended gamma function",
                    "gamma function",
                    "macdonald distribution",
                    "moment generating function"
                    ],
                    "external_ids": [
                    {
                        "source": "scopus",
                        "value": "6701857476"
                    }
                    ],
                    "branches": [
                    {
                        "name": "Facultad de Ciencias Exactas y Naturales",
                        "type": "faculty",
                        "id": "602c50d1fd74967db0663833"
                    },
                    {
                        "name": "Instituto de matemáticas",
                        "type": "department",
                        "id": "602c50f9fd74967db0663858"
                    },
                    {
                        "name": "Análisis Multivariado",
                        "type": "group",
                        "id": "602c510ffd74967db06638d6"
                    }
                    ],
                    "updated": 1613690947
                },
                {
                    "_id": "5fc5bebab246cc0887190a70",
                    "national_id": 43463670,
                    "full_name": "Johanna Marcela Orozco Castañeda",
                    "first_names": "Johanna Marcela",
                    "last_names": "Orozco Castañeda",
                    "initials": "JM",
                    "aliases": [
                    "johanna marcela orozco-castañeda",
                    "orozco-castañeda j.m.",
                    "johanna marcela orozco-castaneda",
                    "orozco castañeda, j.m.,"
                    ],
                    "affiliations": [
                    {
                        "_id": "60120afa4749273de6161883",
                        "branches": [
                        {
                            "_id": "602c50d1fd74967db0663833",
                            "name": "Facultad de ciencias exactas y naturales",
                            "name_idx": "facultad de ciencias exactas y naturales",
                            "aliases": [],
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
                                },
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
                            "_id": "602c50f9fd74967db0663858",
                            "name": "Instituto de matemáticas",
                            "name_idx": "instituto de matematicas",
                            "aliases": [],
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
                                },
                                "email": ""
                            }
                            ],
                            "external_urls": [],
                            "external_ids": [],
                            "keywords": [],
                            "subjects": []
                        }
                        ]
                    }
                    ],
                    "keywords": [
                    "appell's second hypergeometric function",
                    "beta distribution",
                    "confluent hypergeometric function",
                    "gauss hypergeometric function",
                    "gamma distribution",
                    "transformation",
                    "bivariate distribution",
                    "dirichlet distribution",
                    "hypergeometric function",
                    "moments",
                    "product",
                    "positively quadrant dependent",
                    "quotient"
                    ],
                    "external_ids": [
                    {
                        "source": "scopus",
                        "value": "24179436300"
                    }
                    ],
                    "branches": [
                    {
                        "name": "Facultad de Ciencias Exactas y Naturales",
                        "type": "faculty",
                        "id": "602c50d1fd74967db0663833"
                    },
                    {
                        "name": "Instituto de matemáticas",
                        "type": "department",
                        "id": "602c50f9fd74967db0663858"
                    },
                    {
                        "name": "Sin Grupo Asociado",
                        "type": "group",
                        "id": ""
                    }
                    ],
                    "updated": 1613690757
                },
                {
                    "_id": "5fc5b0a5b246cc0887190a69",
                    "national_id": 279739,
                    "full_name": "Daya Krishna Nagar",
                    "first_names": "Daya  Krishna",
                    "last_names": "Nagar",
                    "initials": "DK",
                    "aliases": [
                    "daya k. nagar",
                    "nagar d.k.",
                    "arjun k. gupta",
                    "arjun k gupta",
                    "daya k nagar",
                    "ak gupta"
                    ],
                    "affiliations": [
                    {
                        "_id": "60120add4749273de616099f",
                        "branches": []
                    },
                    {
                        "_id": "602ef788728ecc2d8e62d4f0",
                        "branches": []
                    }
                    ],
                    "keywords": [
                    "beta distribution",
                    "bivariate distribution",
                    "extended beta function",
                    "extended confluent hypergeometric function",
                    "gauss hypergeometric function",
                    "product",
                    "quotient"
                    ],
                    "external_ids": [
                    {
                        "source": "scopus",
                        "value": "6701857476"
                    }
                    ],
                    "branches": [
                    {
                        "name": "Facultad de Ciencias Exactas y Naturales",
                        "type": "faculty",
                        "id": "602c50d1fd74967db0663833"
                    },
                    {
                        "name": "Instituto de matemáticas",
                        "type": "department",
                        "id": "602c50f9fd74967db0663858"
                    },
                    {
                        "name": "Análisis Multivariado",
                        "type": "group",
                        "id": "602c510ffd74967db06638d6"
                    }
                    ],
                    "updated": 1613690947
                }
                ],
                "references_count": 11,
                "references": [],
                "citations_count": 17,
                "citations_link": "/scholar?cites=5920884288529496317&as_sdt=2005&sciodt=0,5&hl=en&oe=ASCII",
                "citations": []
            }
            ]
        """
        data = self.request.args.get('data')
        if not self.valid_apikey():
            return self.apikey_error()
        if data=="list":
            self.db = self.dbclient["antioquia"]
            if "id" in self.request.args:
                iid = self.request.args.get('id')
                db_response=self.db['branches'].find({"type":"faculty","relations.id":ObjectId(iid)})
            else:
                db_response=self.db['branches'].find({"type":"faculty"})
            if db_response:
                faculty_list=[]
                for fac in db_response:
                    entry={
                        "name":fac["name"],
                        "id":str(fac["_id"]),
                        "abbreviations":fac["abbreviations"],
                        "external_urls":fac["external_urls"]
                    }
                    faculty_list.append(entry)
                print(faculty_list)
                response = self.app.response_class(
                response=self.json.dumps(faculty_list),
                status=200,
                mimetype='application/json'
                )
            else:
                response = self.app.response_class(
                response=self.json.dumps({}),
                status=204,
                mimetype='application/json'
                )
        elif data=="info":
            idx = self.request.args.get('id')
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
                        entry["institution"]=[{"name":inst["name"],"id":inst_id}]#,"logo":inst["logo"]}]

                for dep in self.db['branches'].find({"type":"department","relations.id":faculty["_id"]}):
                    dep_entry={
                        "name":dep["name"],
                        "id":str(dep["_id"])
                    }
                    entry["departments"].append(dep_entry)
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
                
                response = self.app.response_class(
                response=self.json.dumps(entry),
                status=200,
                mimetype='application/json'
                )
            else:
                response = self.app.response_class(
                response=self.json.dumps({"status":"Request returned empty"}),
                status=204,
                mimetype='application/json'
            )
        elif data=="papers":
            idx = self.request.args.get('id')
            self.db = self.dbclient["antioquia"]
            papers=[]
            for paper in self.db['documents'].find({"authors.affiliations.branches._id":ObjectId(idx)}):
                entry=paper
                source=self.db["sources"].find_one({"_id":paper["source"]["_id"]})
                if source:
                    entry["source"]=source
                authors=[]
                for author in paper["authors"]:
                    au_entry=author
                    author_db=self.db["authors"].find_one({"_id":author["_id"]})
                    if author_db:
                        au_entry=author_db
                    affiliations=[]
                    for aff in author["affiliations"]:
                        aff_entry=aff
                        aff_db=self.db["institutions"].find_one({"_id":aff["_id"]})
                        branches=[]
                        if "branches" in aff.keys():
                            for branch in aff["branches"]:
                                branch_db=self.db["branches"].find_one({"_id":branch["_id"]})
                                if branch_db:
                                    branches.append(branch_db)
                        aff_entry["branches"]=branches
                        affiliations.append(aff_entry)
                    au_entry["affiliations"]=affiliations
                    authors.append(au_entry)
                entry["authors"]=authors
                papers.append(entry)
            if papers:
                response = self.app.response_class(
                response=self.json.dumps(papers),
                status=200,
                mimetype='application/json'
                )
            #else:
            #    response = self.app.response_class(
            #    response=self.json.dumps({"status":"Request returned empty"}),
            #    status=204,
            #    mimetype='application/json
            #    )
        else:
            response = self.app.response_class(
                response=self.json.dumps({}),
                status=400,
                mimetype='application/json'
            )
        
        return response

    @endpoint('/app/faculty', methods=['GET'])
    def app_faculty(self):
        """
        @api {get} /app/faculty Requests faculty general information or the list of papers
        @apiName app
        @apiGroup CoLav app
        @apiDescription Responds with information about the faculty

        @apiParam {String} data Wether is the general information or the list of papers
        @apiParam {Object} id the id of the faculty requested in mongodb
        @apiParam {String} apikey  Credential for authentication

        @apiError (Error 401) msg  The HTTP 401 Unauthorized invalid authentication apikey for the target resource.
        @apiError (Error 204) msg  The HTTP 204 No Content.
        @apiError (Error 401) msg  The HTTP 200 OK.

        @apiSuccessExample {json} Success-Response (info=data):
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
        @apiSuccessExample {json} Success-Response (info=list):
            HTTP/1.1 200 OK
            [
                {
                    "abbreviations": [
                    "FCEN"
                    ],
                    "external_urls": [
                    {
                        "source": "website",
                        "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/unidades-academicas/ciencias-exactas-naturales"
                    }
                    ],
                    "name": "Facultad de ciencias exactas y naturales",
                    "id": "602599029e9b96dff8bf00ab"
                },
                {
                    "abbreviations": [],
                    "external_urls": [
                    {
                        "source": "website",
                        "url": "http://www.udea.edu.co/wps/portal/udea/web/inicio/institucional/unidades-academicas/facultades/ciencias-farmaceuticas-alimentarias"
                    }
                    ],
                    "name": "Facultad de ciencias farmacéuticas y alimentarias",
                    "id": "602599029e9b96dff8bf00ac"
                }
            ]
        """
        data = self.request.args.get('data')
        if not self.valid_apikey():
            return self.apikey_error()
        if data=="list":
            self.db = self.dbclient["antioquia"]
            if "id" in self.request.args:
                iid = self.request.args.get('id')
                db_response=self.db['branches'].find({"type":"faculty","relations.id":ObjectId(iid)})
            else:
                db_response=self.db['branches'].find({"type":"faculty"})
            if db_response:
                faculty_list=[]
                for fac in db_response:
                    entry={
                        "name":fac["name"],
                        "id":str(fac["_id"]),
                        "abbreviations":fac["abbreviations"],
                        "external_urls":fac["external_urls"]
                    }
                    faculty_list.append(entry)
                print(faculty_list)
                response = self.app.response_class(
                response=self.json.dumps(faculty_list),
                status=200,
                mimetype='application/json'
                )
            else:
                response = self.app.response_class(
                response=self.json.dumps({}),
                status=204,
                mimetype='application/json'
                )
        elif data=="info":
            idx = self.request.args.get('id')
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
                        entry["institution"]=[{"name":inst["name"],"id":inst_id}]#,"logo":inst["logo"]}]

                for dep in self.db['branches'].find({"type":"department","relations.id":faculty["_id"]}):
                    dep_entry={
                        "name":dep["name"],
                        "id":str(dep["_id"])
                    }
                    entry["departments"].append(dep_entry)
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
                
                response = self.app.response_class(
                response=self.json.dumps(entry),
                status=200,
                mimetype='application/json'
                )
            else:
                response = self.app.response_class(
                response=self.json.dumps({"status":"Request returned empty"}),
                status=204,
                mimetype='application/json'
            )
        #elif data=="papers":
        #    idx = self.request.args.get('id')
        #    self.db = self.dbclient["antioquia"]
        #    papers=[]

        else:
            response = self.app.response_class(
                response=self.json.dumps({}),
                status=400,
                mimetype='application/json'
            )
        
        return response
