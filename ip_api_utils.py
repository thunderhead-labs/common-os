import requests

API_KEY = "YOUR API KEY"


def get_location_data(url: str):
    req = requests.get(
        f"http://pro.ip-api.com/json/{url}?key={API_KEY}&"
        f"fields=status,message,continent,country,countryCode,region,"
        f"regionName,city,zip,lat,lon,timezone,isp,org,as,query"
    )
    if req.status_code == 200:
        if req.json()["status"] == "fail":
            return "fail", req.content
        else:
            resp = req.json()
            ip, continent, country, region, city, lat, lon, isp, org, as_ = (
                resp["query"],
                resp["continent"],
                resp["country"],
                resp["regionName"],
                resp["city"],
                resp["lat"],
                resp["lon"],
                resp["isp"],
                resp["org"],
                resp["as"],
            )
            if isp.lower() == "cloudflare":
                continent = isp.lower()
            return ip, continent, country, region, city, lat, lon, isp, org, as_
    else:
        return "fail", f"{req.status_code}-{req.content}"
