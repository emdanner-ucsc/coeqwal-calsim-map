import sqlite3, json, struct, csv, math, sys
sys.setrecursionlimit(20000)
from pyproj import Transformer

MAJOR_NAMES = {
 'Sacramento River','San Joaquin River','Feather River','American River','Yuba River',
 'Trinity River','Clear Creek','Clear Creek Tunnel Outfall','Merced River','Stanislaus River',
 'Tuolumne River','Mokelumne River','Old River','Old/Middle Rivers',
 'Yolo Bypass','Sutter Bypass','Eastside Bypass',
 'California Aqueduct','Delta-Mendota Canal','Tehama Colusa Canal','Friant-kern Canal',
 'Madera Canal','Glenn Colusa Canal','Contra Costa Canal','Mokelumne Aqueduct','Putah Creek','Stony Creek','Butte Creek','Bear River'
}
PARTICLE_NAMES = {'California Aqueduct','Delta-Mendota Canal','Contra Costa Canal',
                  'Mokelumne Aqueduct','Old River','Old/Middle Rivers'}
RES_NAMES = {
 'S_SHSTA':'Shasta Lake','S_OROVL':'Lake Oroville','S_FOLSM':'Folsom Lake','S_TRNTY':'Trinity Lake',
 'S_MLRTN':'Millerton Lake','S_NMLNI':'New Melones','S_PEDRO':'Don Pedro','S_MCLRE':'Lake McClure',
 'S_WKYTN':'Whiskeytown','S_BLKBT':'Black Butte','S_ENGLB':'Englebright','S_CMPFW':'Camp Far West',
 'S_SLUIS':'San Luis Reservoir','S_KSWCK':'Keswick','S_NHGAN':'New Hogan','S_HNSLY':'Hensley Lake',
 'S_ESTMN':'Eastman Lake','S_BERRY':'Lake Berryessa','S_CLRLK':'Clear Lake','S_EPARK':'East Park',
 'S_SGRGE':'Stony Gorge','S_NBLDB':'New Bullards Bar','S_PARDE':'Pardee','S_CMCHE':'Camanche',
 'S_TULOC':'Tulloch','S_ALMNR':'Lake Almanor','S_DAVIS':'Lake Davis','S_FRMAN':'Frenchman Lake',
 'S_ANTLP':'Antelope Lake','S_LGRSV':'Los Vaqueros','S_HTCHY':'Hetch Hetchy','S_LLOYD':'Cherry Lake',
 'S_ENRNR':'Eleanor','S_BOWMN':'Bowman Lake','S_FORDY':'Fordyce','S_SPLDG':'Spaulding',
 'S_ROLLN':'Rollins','S_CBALL':'Combie','S_FRENC':'French Meadows','S_HHOLE':'Hell Hole',
 'S_LOON':'Loon Lake','S_UNVLY':'Union Valley','S_ICEH':'Ice House','S_ALOAF':'Sugar Loaf',
 'S_NTOMA':'Lake Natoma','S_JNKSN':'Jenkinson Lake','S_SLVRL':'Silver Lake','S_CAPLS':'Caples Lake',
 'S_LWBER':'Lower Bear','S_SLTSP':'Salt Springs','S_BEARD':'Beardsley','S_DONLL':'Donnells',
 'S_RLIEF':'Relief','S_PCRST':'Pinecrest','S_TURLK':'Turlock Lake','S_MDSTO':'Modesto Reservoir',
}
CANALS = {'California Aqueduct','Delta-Mendota Canal','Tehama Colusa Canal','Friant-kern Canal',
          'Madera Canal','Glenn Colusa Canal','Contra Costa Canal','Mokelumne Aqueduct','Clear Creek Tunnel Outfall'}
BYPASSES = {'Yolo Bypass','Sutter Bypass','Eastside Bypass'}
MAINSTEMS = {'Sacramento River','San Joaquin River','Feather River','American River'}

def wkb_from_gpkg(blob):
    env = {0:0,1:32,2:48,3:48,4:64}[(blob[3]>>1)&7]
    return blob[8+env:]

def read_wkb(wkb):
    def parse(buf, pos):
        fmt = '<' if buf[pos]==1 else '>'
        typ = struct.unpack_from(fmt+'I', buf, pos+1)[0] % 1000
        pos += 5
        if typ==1:
            x,y = struct.unpack_from(fmt+'2d', buf, pos); return ('Point',[x,y]), pos+16
        if typ==2:
            n = struct.unpack_from(fmt+'I', buf, pos)[0]; pos+=4
            pts = struct.unpack_from(fmt+f'{2*n}d', buf, pos); pos+=16*n
            return ('LineString',[[pts[i],pts[i+1]] for i in range(0,2*n,2)]), pos
        if typ==5:
            n = struct.unpack_from(fmt+'I', buf, pos)[0]; pos+=4
            lines=[]
            for _ in range(n):
                (t,c), pos = parse(buf,pos); lines.append(c)
            return ('MultiLineString',lines), pos
        raise ValueError(typ)
    return parse(wkb,0)[0]

def rdp(pts, eps):
    if len(pts)<3: return pts
    def pld(p,a,b):
        if a==b: return math.dist(p,a)
        t=max(0,min(1,((p[0]-a[0])*(b[0]-a[0])+(p[1]-a[1])*(b[1]-a[1]))/((b[0]-a[0])**2+(b[1]-a[1])**2)))
        return math.dist(p,(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
    dmax,idx=0,0
    for i in range(1,len(pts)-1):
        d=pld(pts[i],pts[0],pts[-1])
        if d>dmax: dmax,idx=d,i
    if dmax>eps:
        return rdp(pts[:idx+1],eps)[:-1]+rdp(pts[idx:],eps)
    return [pts[0],pts[-1]]

# --- CSV header: case-insensitive variable map
with open('s0020_coeqwal_calsim_output.csv') as f:
    r = csv.reader(f); next(r); b = next(r)
up = {}
for i,v in enumerate(b):
    if v.upper() not in up: up[v.upper()] = (v,i)

con = sqlite3.connect('20221103v2_cs3_cvhydroregion.gpkg')
cur = con.cursor()
tr = Transformer.from_crs(3310,4326,always_xy=True)

arcs=[]
for name, arc_id, typ, geom in cur.execute('SELECT NAME, Arc_ID, Type, geom FROM CalSim3_Arcs_prj3310 WHERE Arc_ID IS NOT NULL'):
    if name in MAJOR_NAMES and typ=='CH' and arc_id.upper() in up:
        t, coords = read_wkb(wkb_from_gpkg(geom))
        lines = coords if t=='MultiLineString' else [coords]
        out=[]
        for ln in lines:
            s = rdp(ln,50)
            xs,ys = zip(*s)
            lon,lat = tr.transform(xs,ys)
            out.append([[round(lo,5),round(la,5)] for lo,la in zip(lon,lat)])
        cat = 'canal' if name in CANALS else ('bypass' if name in BYPASSES else 'river')
        a = {'i':arc_id,'n':name,'c':cat,'g':out,'col':up[arc_id.upper()][1]}
        if name in PARTICLE_NAMES: a['p']=1
        elif name in MAINSTEMS: a['p']=2
        arcs.append(a)

res=[]
for cid, rname, geom in cur.execute('SELECT CalSim_ID, Riv_Name, geom FROM CS3_SelectedReservoirNodes_prj3310'):
    var = ('S_'+str(cid)).upper()
    if var in up:
        t, xy = read_wkb(wkb_from_gpkg(geom))
        lon,lat = tr.transform(xy[0],xy[1])
        res.append({'i':up[var][0],'n':RES_NAMES.get('S_'+str(cid), str(cid)),'riv':rname,
                    'll':[round(lon,5),round(lat,5)],'col':up[var][1]})
print('arcs:', len(arcs), '(particles:', sum(1 for a in arcs if a.get('p')), ') res:', len(res))

# --- time series
PUMPS = [
 {'var':'D_OMR027_CAA000','head_arc':'C_CAA000','n':'Banks Pumping Plant','sub':'State Water Project'},
 {'var':'D_OMR028_DMC000','head_arc':'C_DMC003','n':'Jones Pumping Plant','sub':'Central Valley Project'},
]
wytcol = up['WYT_SAC_'][1]
for p in PUMPS: p['col'] = up[p['var'].upper()][1]
cols = {a['col'] for a in arcs} | {r['col'] for r in res} | {wytcol} | {p['col'] for p in PUMPS}
series = {c:[] for c in cols}
months=[]
with open('s0020_coeqwal_calsim_output.csv') as f:
    r = csv.reader(f)
    for _ in range(7): next(r)
    for row in r:
        months.append(row[0][:7])
        for c in cols:
            v=row[c]
            series[c].append(round(float(v),1) if v else None)

for a in arcs:
    a['q']=[None if v is None else round(v) for v in series[a['col']]]; del a['col']
for rv in res:
    s=series[rv['col']]; del rv['col']
    rv['cap']=round(max(v for v in s if v is not None),1)
    rv['s']=s

allq = sorted(v for a in arcs for v in a['q'] if v is not None and v>0)
qref = allq[int(len(allq)*0.98)]
wyt = [int(series[wytcol][wy*12+11]) for wy in range(len(months)//12)]
arcmap = {a['i']: a for a in arcs}
pumps = []
for p in PUMPS:
    head = arcmap[p['head_arc']]['g'][0][0]   # first vertex of canal head arc
    q = [None if v is None else round(v) for v in series[p['col']]]
    pumps.append({'i':p['var'],'n':p['n'],'sub':p['sub'],'ll':head,'q':q})
    print(p['n'], 'at', head, 'max export', max(v for v in q if v is not None), 'cfs')
# ===== demand units =====
import shapefile as shp
import re as _re
sf = shp.Reader('Shapefiles/DemandUnits.shp')
fields = [f[0] for f in sf.fields[1:]]
dupat = _re.compile(r'^D_.+?_(\d{2}[NS]?_[A-Z]{2}\d*)$')
# map DU -> delivery column indices (DIVERSION type only)
with open('s0020_coeqwal_calsim_output.csv') as f:
    rr = csv.reader(f); next(rr); bb = next(rr); cc = next(rr)
from collections import defaultdict
du_colidx = defaultdict(list)
for i,(nm,tp) in enumerate(zip(bb,cc)):
    if tp=='DIVERSION':
        m = dupat.match(nm)
        if m: du_colidx[m.group(1)].append(i)
# monthly TAF per column set (cfs -> TAF using days in month)
def dim(mi):
    y,mo = months[mi].split('-'); y,mo=int(y),int(mo)
    import calendar; return calendar.monthrange(y,mo)[1]
DAYS=[dim(i) for i in range(len(months))]
# read delivery columns in one pass
needed = sorted({i for v in du_colidx.values() for i in v})
dseries = {i:[] for i in needed}
with open('s0020_coeqwal_calsim_output.csv') as f:
    rr = csv.reader(f)
    for _ in range(7): next(rr)
    for mi,row in enumerate(rr):
        for i in needed:
            v=row[i]
            dseries[i].append(float(v) if v else 0.0)

def ring_area(pts):
    s=0
    for i in range(len(pts)-1):
        s+=pts[i][0]*pts[i+1][1]-pts[i+1][0]*pts[i][1]
    return s/2

KIND={'A':'ag','U':'urban','R':'refuge'}
dus=[]
for srec in sf.iterShapeRecords():
    du = srec.record[1]
    if not du: continue
    suffix = du.split('_')[1]
    kind = KIND.get(suffix[1],'ag')
    acres = srec.record[3]/4046.856
    pts = srec.shape.points; parts=list(srec.shape.parts)+[len(pts)]
    polys=[]  # list of [exterior, hole, hole...]
    for pi in range(len(parts)-1):
        ring = [list(p) for p in pts[parts[pi]:parts[pi+1]]]
        if len(ring)<4: continue
        a = ring_area(ring)
        simp = rdp(ring, 75)
        if len(simp)<4: continue
        xs,ys = zip(*simp)
        lon,lat = tr.transform(xs,ys)
        ll = [[round(la,5),round(lo,5)] for lo,la in zip(lon,lat)]
        if a < 0:   # shapefile exterior = clockwise = negative signed area
            polys.append([ll])
        elif polys and abs(a) > 2e5:
            polys[-1].append(ll)
    if not polys: continue
    cols = du_colidx.get(du,[])
    d = [round(sum(dseries[i][mi] for i in cols)*1.98347*DAYS[mi]/1000,2) for mi in range(len(months))] if cols else None
    e = {'i':du,'k':kind,'ac':round(acres),'g':polys}
    if d: e['d']=d
    else: e['gw']=1
    dus.append(e)
print('DU polygons:', len(dus), '| with deliveries:', sum(1 for d in dus if 'd' in d),
      '| gw-only:', sum(1 for d in dus if d.get('gw')))
peak = max((max(d['d']) for d in dus if 'd' in d))
print('peak monthly delivery (TAF):', peak)

json.dump({'months':months,'arcs':arcs,'res':res,'qref':qref,'wyt':wyt,'pumps':pumps,'dus':dus},
          open('build/payload.json','w'), separators=(',',':'))
import os; print('payload MB:', os.path.getsize('build/payload.json')/1e6)
