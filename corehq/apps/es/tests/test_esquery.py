from unittest import TestCase
from mock import patch

from corehq.apps.es import filters
from corehq.apps.es import forms, users
from corehq.apps.es.es_query import HQESQuery
from corehq.apps.es.tests.utils import ElasticTestMixin
from corehq.elastic import SIZE_LIMIT


class TestESQuery(ElasticTestMixin, TestCase):
    maxDiff = 1000

    def test_basic_query(self):
        json_output = {
            "query": {
                "filtered": {
                    "filter": {
                        "and": [
                            {"match_all": {}}
                        ]
                    },
                    "query": {"match_all": {}}
                }
            },
            "size": SIZE_LIMIT
        }
        self.checkQuery(HQESQuery('forms'), json_output)

    def test_query_size(self):
        json_output = {
            "query": {
                "filtered": {
                    "filter": {
                        "and": [
                            {"match_all": {}}
                        ]
                    },
                    "query": {"match_all": {}}
                }
            },
            "size": 0
        }
        # use `is not None`; 0 or 1000000 == 1000000
        self.checkQuery(HQESQuery('forms').size(0), json_output)
        json_output['size'] = 123
        self.checkQuery(HQESQuery('forms').size(123), json_output)

    def test_form_query(self):
        json_output = {
            "query": {
                "filtered": {
                    "filter": {
                        "and": [
                            {"not": {"missing": {
                                "field": "domain"}}},
                            {"term": {"doc_type": "xforminstance"}},
                            {"not": {"missing":
                                {"field": "xmlns"}}},
                            {"not": {"missing":
                                {"field": "form.meta.userID"}}},
                        ]
                    },
                    "query": {"match_all": {}}
                }
            },
            "size": SIZE_LIMIT
        }
        query = forms.FormES()
        self.checkQuery(query, json_output)

    def test_user_query(self):
        json_output = {
            "query": {
                "filtered": {
                    "filter": {
                        "and": [
                            {"term": {"is_active": True}},
                            {"term": {"base_doc": "couchuser"}},
                        ]
                    },
                    "query": {"match_all": {}}
                }
            },
            "size": SIZE_LIMIT
        }
        query = users.UserES()
        self.checkQuery(query, json_output)

    def test_filtered_forms(self):
        json_output = {
            "query": {
                "filtered": {
                    "filter": {
                        "and": [
                            {"term": {"domain.exact": "zombocom"}},
                            {"term": {"xmlns.exact": "banana"}},
                            {"not": {"missing": {
                                "field": "domain"}}},
                            {"term": {"doc_type": "xforminstance"}},
                            {"not": {"missing":
                                {"field": "xmlns"}}},
                            {"not": {"missing":
                                {"field": "form.meta.userID"}}},
                        ]
                    },
                    "query": {"match_all": {}}
                }
            },
            "size": SIZE_LIMIT
        }
        query = forms.FormES()\
                .filter(filters.domain("zombocom"))\
                .xmlns('banana')
        self.checkQuery(query, json_output)

    @patch('corehq.apps.locations.models.SQLLocation.objects.get_locations_and_children_ids')
    def test_users_at_locations_and_descendants_query(self, locations_patch):
        location_ids = ['09d1a58cb849e53bb3a456a5957d998a', '09d1a58cb849e53bb3a456a5957d99ba']
        children_ids = ['19d1a58cb849e53bb3a456a5957d998a', '19d1a58cb849e53bb3a456a5957d99ba']
        all_ids = location_ids + children_ids
        locations_patch.return_value = location_ids + children_ids
        json_output = {
            'query': {
                'filtered': {
                    'filter': {
                        'and': [
                            {'or': (
                                {'and': (
                                    {'term': {'doc_type': 'CommCareUser'}},
                                    {'terms': {'assigned_location_ids': all_ids}}
                                )
                                },
                                {'and': (
                                    {'term': {'doc_type': 'WebUser'}},
                                    {'terms': {'domain_memberships.assigned_location_ids': all_ids}}
                                )
                                }
                            )}, {'term':{'is_active': True}},
                            {'term': {'base_doc': 'couchuser'}}
                        ]
                    },
                    'query': {'match_all': {}}}},
            'size': 1000000
        }

        query = (users.UserES()
                 .users_at_locations_and_descendants_query(location_ids))
        self.checkQuery(query, json_output)

    def test_remove_all_defaults(self):
        # Elasticsearch fails if you pass it an empty list of filters
        query = (users.UserES()
                 .remove_default_filter('not_deleted')
                 .remove_default_filter('active'))
        filters = query.raw_query['query']['filtered']['filter']['and']
        self.assertTrue(len(filters) > 0)

    def test_values_list(self):
        example_response = {
            u'_shards': {u'failed': 0, u'successful': 5, u'total': 5},
            u'hits': {u'hits': [{
                u'_id': u'8063dff5-460b-46f2-b4d0-5871abfd97d4',
                u'_index': u'xforms_1cce1f049a1b4d864c9c25dc42648a45',
                u'_score': 1.0,
                u'_type': u'xform',
                u'_source': {
                    u'app_id': u'fe8481a39c3738749e6a4766fca99efd',
                    u'doc_type': u'xforminstance',
                    u'domain': u'mikesproject',
                    u'xmlns': u'http://openrosa.org/formdesigner/3a7cc07c-551c-4651-ab1a-d60be3017485'
                    }
                },
                {
                    u'_id': u'dc1376cd-0869-4c13-a267-365dfc2fa754',
                    u'_index': u'xforms_1cce1f049a1b4d864c9c25dc42648a45',
                    u'_score': 1.0,
                    u'_type': u'xform',
                    u'_source': {
                        u'app_id': u'3d622620ca00d7709625220751a7b1f9',
                        u'doc_type': u'xforminstance',
                        u'domain': u'jacksproject',
                        u'xmlns': u'http://openrosa.org/formdesigner/54db1962-b938-4e2b-b00e-08414163ead4'
                        }
                    }
                ],
                u'max_score': 1.0,
                u'total': 5247
                },
            u'timed_out': False,
            u'took': 4
        }
        fields = [u'app_id', u'doc_type', u'domain']
        query = forms.FormES()
        with patch('corehq.apps.es.es_query.run_query', return_value=example_response):
            response = query.values_list(*fields)
            self.assertEqual(
                [
                    (u'fe8481a39c3738749e6a4766fca99efd', u'xforminstance', u'mikesproject'),
                    (u'3d622620ca00d7709625220751a7b1f9', u'xforminstance', u'jacksproject')
                ],
                response
            )

            response = query.values_list('domain', flat=True)
            self.assertEqual([u'mikesproject', u'jacksproject'], response)
