import requests
_geo_cache: dict[str, tuple[str,str]] = {}

def geo_ip_city(ip: str) -> tuple[str,str]:
    if not ip:
        return ("", "")
    if ip in _geo_cache:
        return _geo_cache[ip]
    try:
        r = requests.get(f"https://ipapi.co/{ip}/json/", timeout=3)
        if r.ok:
            j = r.json()
            city = j.get("city") or ""
            country = j.get("country_name") or (j.get("country") or "")
            _geo_cache[ip] = (city, country)
            return _geo_cache[ip]
    except Exception:
        pass
    return ("", "")
