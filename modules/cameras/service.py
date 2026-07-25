import requests
from core.geometry import haversine_km,bearing_deg,compass
def load_nearby_cameras(cfg):
    cc=cfg.get('cameras',{}) or {}
    base=cc.get('base_url','https://511.alberta.ca/api/v2/get/cameras'); radius_km=float(cc.get('radius_km',15)); max_cameras=int(cc.get('max_cameras',4))
    e=cfg['event']; lat,lon=float(e['latitude']),float(e['longitude'])
    try:
        r=requests.get(base,params={'format':'json'},timeout=float(cc.get('timeout_seconds',20))); r.raise_for_status()
        rows=r.json()
    except Exception as ex:
        return {'status':'error','error':f'{type(ex).__name__}: {ex}'}
    cand=[]
    for c in rows:
        clat,clon=c.get('Latitude'),c.get('Longitude')
        if clat is None or clon is None:continue
        d=haversine_km(lat,lon,clat,clon)
        if d>radius_km:continue
        views=[v for v in (c.get('Views') or []) if v.get('Status')=='Enabled' and v.get('Url')]
        if not views:continue
        b=bearing_deg(lat,lon,clat,clon)
        cand.append({'name':c.get('Location') or c.get('Roadway') or f"Camera {c.get('Id')}",'roadway':c.get('Roadway'),'distance_km':round(d,2),'direction':compass(b),'image_url':views[0]['Url']})
    cand.sort(key=lambda x:x['distance_km'])
    if not cand:return {'status':'ok','count':0,'cameras':[]}
    return {'status':'ok','count':len(cand),'cameras':cand[:max_cameras]}
