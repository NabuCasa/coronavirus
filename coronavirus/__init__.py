"""Fetch latest Corona Virus information."""
from aiohttp import ClientSession, ClientResponseError
from dataclasses import dataclass
import logging


@dataclass
class JohnsHopkinsCase:
    """Class for holding country stats."""

    URL = "https://coronacache.home-assistant.io/corona.json"
    NAME = "Johns Hopkins"

    id: str
    country: str
    confirmed: int
    deaths: int
    recovered: int
    latitude: float
    longitude: float
    updated: int

    @property
    def current(self):
        if None in (self.confirmed, self.deaths, self.recovered):
            return None
        return self.confirmed - self.deaths - self.recovered

    @staticmethod
    def from_json(item):
        attrs = item["attributes"]
        return JohnsHopkinsCase(
            id=attrs["OBJECTID"],
            country=attrs["Country_Region"],
            confirmed=attrs["Confirmed"],
            deaths=attrs["Deaths"],
            recovered=attrs["Recovered"],
            latitude=attrs["Lat"],
            longitude=attrs["Long_"],
            updated=attrs["Last_Update"],
        )


@dataclass
class WHOCase:
    """Class for holding country stats."""

    URL = "https://services.arcgis.com/5T5nSi527N4F7luB/ArcGIS/rest/services/COVID_19_Cases_by_country__pl_v2/FeatureServer/0/query?where=1%3D1&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&returnGeodetic=false&outFields=id%2Ccum_conf%2Ccum_clin%2Ccum_susp%2Ccum_death%2CDateOfReport%2CADM0_VIZ_NAME+%2CCENTER_LON%2CCENTER_LAT&returnGeometry=false&returnCentroid=false&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pjson&token="
    NAME = "World Health Organization"

    id: str
    name: str
    latitude: float
    longitude: float
    date_of_report: int
    confirmed: int
    deaths: int

    @staticmethod
    def from_json(item):
        attrs = item["attributes"]
        return WHOCase(
            id=attrs["ID"],
            name=attrs["ADM0_VIZ_NAME"],
            latitude=attrs["CENTER_LAT"],
            longitude=attrs["CENTER_LON"],
            date_of_report=attrs["DateOfReport"],
            confirmed=attrs["cum_conf"] or 0,
            deaths=attrs["cum_death"] or 0,
        )


DEFAULT_SOURCE = JohnsHopkinsCase


async def get_cases(session: ClientSession, *, source=DEFAULT_SOURCE):
    """Fetch Corona Virus cases."""
    resp = await session.get(source.URL)
    data = await resp.json(content_type=None)

    if 'error' in data:
        # API does not set correct status header so we manually check.
        raise ClientResponseError(
            resp.request_info,
            resp.history,
            status=data['error']['code'],
            message=data['error']['message'],
            headers=resp.headers
        )

    results = []

    for item in data["features"]:
        try:
            results.append(source.from_json(item))
        except KeyError:
            logging.getLogger(__name__).warning("Got wrong data: %s", item)

    return results
