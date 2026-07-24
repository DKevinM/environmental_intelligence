import json
from html import escape
from core.timefmt import format_long,format_short,tz_abbrev
from core.aqhi import cap as cap_aqhi
R={'LOW':'low','MODERATE':'moderate','HIGH':'high','EXTREME':'extreme','UNKNOWN':'unknown'}
def v(x,s=''):return '—' if x is None else f'{x}{s}'
MAP_JS='''(function(){
  var map=L.map('festmap',{scrollWheelZoom:false}).setView([VENUE.lat,VENUE.lon],10);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{attribution:'&copy; OpenStreetMap contributors &copy; CARTO',maxZoom:19}).addTo(map);
  function colorForPM25(x){if(x==null)return '#6c757d';if(x<12)return '#2f9e44';if(x<35.4)return '#e0a800';if(x<55.4)return '#e8590c';if(x<150.4)return '#c92a2a';if(x<250.4)return '#862e9c';return '#5c0000';}
  function colorForAQHI(x){if(x==null)return '#6c757d';if(x<=3)return '#2f9e44';if(x<=6)return '#e0a800';if(x<=10)return '#e8590c';return '#c92a2a';}
  function capAQHI(x){if(x==null)return 'n/a';var n=(typeof x==='number')?x:parseFloat(x);return (!isNaN(n)&&n>10)?'10+':x;}
  var aqhiLayer=L.geoJSON(AQHI_GRID,{style:function(f){return {fillColor:f.properties.color||'#6c757d',color:'transparent',fillOpacity:0.35};},onEachFeature:function(f,l){l.bindPopup('AQHI '+capAQHI(f.properties.value)+' &middot; confidence '+(f.properties.confidence||'unknown'));}});
  var smokeLayer=L.geoJSON(FIRESMOKE,{style:function(f){return {fillColor:colorForPM25(f.properties.pm25),color:'transparent',fillOpacity:0.35};},onEachFeature:function(f,l){var pv=f.properties.pm25;l.bindPopup('Smoke PM2.5 ~'+(pv!=null?pv.toFixed(1):'n/a')+' &micro;g/m&sup3;');}});
  var paLayer=L.layerGroup(PURPLEAIR.map(function(p){var onsite=p.distance_km<1;return L.circleMarker([p.lat,p.lon],{radius:onsite?9:6,color:'#fff',weight:onsite?2:1,fillColor:colorForPM25(p.pm25),fillOpacity:0.9}).bindPopup('<b>'+p.name+'</b><br>PM2.5: '+(p.pm25!=null?p.pm25:'n/a')+' &micro;g/m&sup3;<br>'+p.distance_km+' km from venue'+(onsite?' &middot; on-site':''));}));
  var stationLayer=L.layerGroup(STATIONS.map(function(s){return L.circleMarker([s.lat,s.lon],{radius:8,color:'#fff',weight:2,fillColor:colorForAQHI(s.aqhi),fillOpacity:0.95}).bindPopup('<b>'+s.name+'</b><br>AQHI now: '+capAQHI(s.aqhi)+'<br>+3h: '+capAQHI(s.aqhi_3h!=null?+s.aqhi_3h.toFixed(1):null)+'<br>'+s.distance_km+' km from venue');}));
  var venueMarker=L.circleMarker([VENUE.lat,VENUE.lon],{radius:10,color:'#fff',weight:3,fillColor:'#4dabf7',fillOpacity:1}).bindPopup('<b>'+VENUE.name+'</b>');
  aqhiLayer.addTo(map);smokeLayer.addTo(map);paLayer.addTo(map);stationLayer.addTo(map);venueMarker.addTo(map);
  L.control.layers(null,{'AQHI grid':aqhiLayer,'Smoke (PM2.5 model)':smokeLayer,'Community sensors':paLayer,'Official stations':stationLayer},{collapsed:false}).addTo(map);
})();'''
def build_map_section(cfg,p):
 mp=p.get('map') or {}
 firesmoke=mp.get('firesmoke') or {'type':'FeatureCollection','features':[]}
 aqhi_grid=mp.get('aqhi_grid') or {'type':'FeatureCollection','features':[]}
 purpleair=mp.get('purpleair') or []; stations=mp.get('stations') or []
 if not (firesmoke['features'] or aqhi_grid['features'] or purpleair or stations):return ''
 e=cfg['event']; venue={'name':e['name'],'lat':float(e['latitude']),'lon':float(e['longitude'])}
 data_js=(f"const FIRESMOKE={json.dumps(firesmoke)};\nconst AQHI_GRID={json.dumps(aqhi_grid)};\nconst PURPLEAIR={json.dumps(purpleair)};\nconst STATIONS={json.dumps(stations)};\nconst VENUE={json.dumps(venue)};\n")
 return f'<section class="panel"><h2>Local area map</h2><div id="festmap" style="height:480px;border-radius:12px;overflow:hidden"></div><script>{data_js}{MAP_JS}</script></section>'
def build_html(cfg,p):
 w=p['weather'];c=w['current'];aq=p['air_quality']['current'];fx=p['air_quality']['forecast'];a=p['assessment'];n=p['narrative']
 tz=cfg['project'].get('timezone','America/Edmonton'); tzab=tz_abbrev(tz)
 cards=''.join(f"<article class='hazard {R.get(x['risk'],'unknown')}'><small>{k.replace('_',' ').title()}</small><b>{x['risk']}</b><span>{v(cap_aqhi(x.get('indicator')) if k=='air_quality' else x.get('indicator'))} {x.get('unit','')}</span></article>" for k,x in a['hazards'].items())
 rows=''.join(f"<tr><td>{v(format_short(r.get('time'),tz))}</td><td>{v(r.get('temperature_c'),'°C')}</td><td>{v(r.get('precipitation_probability_pct'),'%')}</td><td>{v(r.get('precipitation_mm'),' mm')}</td><td>{v(r.get('wind_gust_kmh'),' km/h')}</td><td>{v(r.get('weather_code'))}</td></tr>" for r in w.get('hourly',[])[:12])
 rec=''.join(f'<li>{escape(x)}</li>' for x in n['recommendations'])
 blend=aq.get('blend') or {}; pollutant=aq.get('pollutant') or {}; pa=aq.get('purpleair') or {}
 extra=''
 if blend.get('status')=='ok':extra+=f"<div>Blend estimate<b>{v(cap_aqhi(blend.get('value')))}</b><small>confidence {escape(str(blend.get('confidence','—')))}</small></div>"
 if pollutant.get('status')=='ok':extra+=f"<div>PM2.5 (station)<b>{v(pollutant.get('value'),' µg/m³')}</b><small>{escape(str(pollutant.get('station_name','')))} · {v(pollutant.get('distance_km'),' km')}</small></div>"
 if pa.get('status')=='ok':extra+=f"<div>PM2.5 (community)<b>{v(pa.get('pm25'),' µg/m³')}</b><small>{escape(str(pa.get('name','')))} · {v(pa.get('distance_km'),' km')}</small></div>"
 extra_section=f'<section class="panel"><h2>Local air quality readings</h2><div class="aq">{extra}</div></section>' if extra else ''
 valid_label=format_short(fx.get('valid_at'),tz) or '+3h'
 map_section=build_map_section(cfg,p)
 return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{escape(cfg['project']['name'])}</title><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><style>body{{margin:0;background:#0f1720;color:#f4f7fa;font-family:Arial}}header,main,footer{{max-width:1300px;margin:auto;padding:20px}}.panel,.metric,.hazard{{background:#172330;border:1px solid #304152;border-radius:12px;padding:16px}}.grid{{display:grid;gap:12px}}.metrics{{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}}.hazards{{grid-template-columns:repeat(auto-fit,minmax(180px,1fr))}}.hazard b,.metric b{{display:block;font-size:25px;margin:8px 0}}.low{{border-color:#2f9e44}}.moderate{{border-color:#e0a800}}.high{{border-color:#e8590c}}.extreme{{border-color:#c92a2a}}.unknown{{border-color:#6c757d}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #304152;text-align:left}}section{{margin-bottom:15px}}.aq{{display:flex;gap:10px}}.aq div{{flex:1;text-align:center;background:#111c26;padding:14px;border-radius:8px}}.aq b{{display:block;font-size:26px}}.leaflet-container{{background:#111c26}}</style></head><body><header><h1>{escape(cfg['project']['name'])}</h1><p>{escape(cfg['event']['venue'])} · Generated {escape(format_long(p['generated_at'],tz))}</p></header><main><section class="panel"><h2>Overall risk: {a['overall_risk']}</h2></section><section class="grid metrics"><div class="metric">Temperature<b>{v(c.get('temperature_c'),'°C')}</b></div><div class="metric">Feels like<b>{v(c.get('apparent_temperature_c'),'°C')}</b></div><div class="metric">Wind<b>{v(c.get('wind_speed_kmh'),' km/h')}</b></div><div class="metric">Gust<b>{v(c.get('wind_gust_kmh'),' km/h')}</b></div><div class="metric">Current AQHI<b>{v(cap_aqhi(aq.get('aqhi')))}</b><small>{escape(str(aq.get('station_name','Unavailable')))}</small></div></section><section class="panel"><h2>Hazard assessment</h2><div class="grid hazards">{cards}</div></section><section class="panel"><h2>Environmental intelligence summary</h2><p>{escape(n['summary'])}</p><h3>Recommendations</h3><ul>{rec}</ul></section><section class="panel"><h2>AQHI outlook</h2><div class="aq"><div>Now<b>{v(cap_aqhi(aq.get('aqhi')))}</b></div><div>{escape(valid_label)}<b>{v(cap_aqhi(fx.get('plus_3h')))}</b></div></div></section>{extra_section}{map_section}<section class="panel"><h2>Hourly weather outlook <small style="font-weight:normal">(times in {escape(tzab)})</small></h2><div style="overflow:auto"><table><tr><th>Time</th><th>Temp</th><th>Precip chance</th><th>Precip</th><th>Gust</th><th>Code</th></tr>{rows}</table></div></section></main><footer>Demo decision-support product. Confirm official warnings and procedures before operational use.</footer></body></html>'''
