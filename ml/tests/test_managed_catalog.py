import io
import json
import unittest
from unittest.mock import patch
from urllib.error import URLError
from fastapi import HTTPException
from vehicle_matching.managed_catalog import ManagedCatalog


class ManagedCatalogTests(unittest.TestCase):
    def payload(self):
        return {'id':'managed-example','brand':'Example','model':'New SUV','trim':'Base','year':'2026','price':30000000,
                'fuel':'ELECTRIC','efficiency':5.5,'source_url':'https://example.com/official','checked_on':'2026-10-26',
                'body_type':'SUV','seats':5,'length_mm':4400,'image_url':'/api/v1/vehicles/images/example.webp','memo':'internal'}
    def response(self,rows):return io.BytesIO(json.dumps({'success':True,'data':rows}).encode())
    @patch('vehicle_matching.managed_catalog.urlopen')
    def test_latest_catalog_is_read_each_request_and_empty_is_preserved(self,read):
        source=ManagedCatalog('http://localhost/catalog')
        car=self.payload();read.side_effect=[self.response([car]),self.response([{**car,'price':32000000}]),self.response([])]
        self.assertEqual(source.read()[0].price,30000000)
        self.assertEqual(source.read()[0].price,32000000)
        self.assertEqual(source.read(),[])
    @patch('vehicle_matching.managed_catalog.urlopen')
    def test_invalid_or_unavailable_catalog_never_uses_training_snapshot(self,read):
        source=ManagedCatalog('http://localhost/catalog')
        for reply in (self.response([self.payload(),self.payload()]),self.response([{**self.payload(),'price':0}]),URLError('offline')):
            read.side_effect=reply if isinstance(reply,Exception) else None
            read.return_value=reply
            with self.assertRaises(HTTPException) as caught:source.read()
            self.assertEqual(caught.exception.status_code,503)

