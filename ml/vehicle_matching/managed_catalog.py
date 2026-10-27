"""Read the published runtime catalog without modifying frozen training bundles."""
import json
from dataclasses import fields
from urllib.request import urlopen
from urllib.error import URLError
from fastapi import HTTPException
from vehicle_matching.catalog import Vehicle

class ManagedCatalog:
    def __init__(self,url): self.url=url

    def read(self):
        try:
            with urlopen(self.url,timeout=3) as response:
                payload=json.load(response)
            if payload.get('success') is not True or not isinstance(payload.get('data'),list):
                raise ValueError('Invalid catalog envelope')
            allowed={field.name for field in fields(Vehicle)}
            vehicles=[Vehicle(**{key:value for key,value in row.items() if key in allowed}) for row in payload['data']]
            if len({v.id for v in vehicles})!=len(vehicles):raise ValueError('Duplicate catalog IDs')
            return vehicles
        except (URLError,TimeoutError,ValueError,TypeError,OSError) as error:
            # A removed vehicle must not silently return via a stale model snapshot.
            raise HTTPException(status_code=503,detail='차량 목록을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.') from error
