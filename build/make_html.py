import json

payload = open('build/payload.json').read()
simple = open('build/simple_payload.json').read()
scenmeta = open('build/scenario_meta.json').read()

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CalSim3 Central Valley Water Allocation</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>
  html,body{margin:0;height:100%;font-family:system-ui,-apple-system,'Segoe UI',sans-serif}
  #map{position:absolute;inset:0}
  .panel{position:absolute;z-index:1000;background:rgba(255,255,255,.94);border-radius:10px;
         box-shadow:0 2px 10px rgba(0,0,0,.25);padding:12px 16px}
  #ctrl{left:50%;transform:translateX(-50%);bottom:18px;width:min(680px,92vw)}
  #title{top:12px;left:12px;max-width:340px}
  #title h1{font-size:16px;margin:0 0 4px}
  #title p{font-size:12px;margin:0;color:#555}
  #datebox{font-size:20px;font-weight:600;min-width:150px;text-align:center}
  .row{display:flex;align-items:center;gap:10px}
  input[type=range]{flex:1}
  button{border:1px solid #bbb;background:#fff;border-radius:6px;padding:4px 10px;cursor:pointer;font-size:13px}
  button:hover{background:#eee}
  #play{width:64px;font-weight:600}
  #legend{bottom:18px;right:12px;font-size:12px;line-height:1.7}
  .sw{display:inline-block;width:22px;height:4px;border-radius:2px;vertical-align:middle;margin-right:6px}
  .dot{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:middle;margin-right:6px}
  select{font-size:13px;padding:2px}
  #strip{width:100%;height:44px;display:block;margin-top:10px;border-radius:4px;cursor:pointer}
  #stories button{font-size:12px;padding:3px 8px;border-radius:12px;border:1px solid #c9a227;background:#fdf6e3}
  #stories button:hover{background:#f5e9c8}
  #chart{top:12px;right:12px;width:min(480px,94vw);display:none}
  #chart h2{font-size:13px;margin:0 0 2px;padding-right:20px}
  #chart .sub{font-size:11px;color:#666;margin-bottom:6px}
  #chartclose{position:absolute;top:8px;right:10px;border:none;background:none;font-size:16px;color:#888;padding:0}
  #wkey div.k{display:flex;align-items:center;gap:6px;margin:1px 0}
  #wkey .bar{background:#1668a8;border-radius:2px;width:26px}
  .leaflet-tooltip{font-size:12px}
  /* ===== scenario picker ===== */
  .scenrow{margin-top:7px;font-size:12px}
  .scenrow label{font-weight:600;color:#1668a8;font-size:11px;text-transform:uppercase;letter-spacing:.04em}
  .scenrow select{width:100%;margin-top:2px;font-size:12px}
  .hydbtns{display:flex;gap:4px;margin-top:4px}
  .hydbtns button{font-size:11.5px;padding:3px 8px;border-radius:12px;flex:1;white-space:nowrap}
  .hydbtns button.on{background:#1668a8;color:#fff;border-color:#1668a8}
  .hydbtns button:disabled{opacity:.35;cursor:default}
  .scenrow .busy{font-size:11px;color:#b3541e;display:none;margin-top:3px}
  /* ===== A/B compare ===== */
  .scenhead{display:flex;justify-content:space-between;align-items:baseline}
  .cmpbtn{font-size:11px;padding:1px 8px;border-radius:10px;color:#1668a8}
  body.comparing .cmpbtn{display:none}
  .scenrowB{display:none;border-top:1px dashed #ccc;margin-top:7px;padding-top:5px}
  body.comparing .scenrowB{display:block}
  .scenrowB label{color:#e07b28!important}
  .scenrowB .hydbtns button.on{background:#e07b28;border-color:#e07b28}
  .cmpoff{font-size:11px;border:none;background:none;color:#888;padding:0 2px;cursor:pointer}
  .cmpoff:hover{color:#b2182b;background:none}
  .abpills{display:none;gap:4px;align-items:center}
  body.comparing .abpills{display:flex}
  .abpills .ablab{font-size:10.5px;color:#666;text-transform:uppercase;letter-spacing:.03em}
  .abpills button{font-size:12px;font-weight:700;padding:3px 11px;border-radius:12px}
  .abpills button[data-s="A"].on{background:#1668a8;color:#fff;border-color:#1668a8}
  .abpills button[data-s="B"].on{background:#e07b28;color:#fff;border-color:#e07b28}
  #abpills2{margin:7px 0 0}
  .cmpcap{font-size:11px;color:#555;margin:6px 0 2px}
  .cmpcap b.ca{color:#1668a8} .cmpcap b.cb{color:#e07b28}
  .sbar .trow{display:flex;align-items:center;gap:5px;margin-top:2px}
  .sbar .tl{font-size:9.5px;font-weight:700;width:9px;flex:none}
  .sbar .track.thin{height:9px;flex:1}
  .sbar .na{font-size:10px;color:#999;flex:1}
  #nosimplenote{display:none;background:#fdf6e3;border-left:3px solid #c9a227;padding:8px 10px;
                border-radius:4px;font-size:12.5px;margin:8px 0}
  body.nosimple #nosimplenote{display:block}
  body.nosimple #wytbtns,body.nosimple #syearrow,body.nosimple #sseltitle,
  body.nosimple #sbars,body.nosimple #skey,body.nosimple #skeytoggle{display:none}
  @media (max-width:700px){
    #legend{display:none}
    /* detailed mode: compact header, clear of the Big picture button */
    #title{left:8px;right:120px;top:8px;max-width:none;padding:8px 10px}
    #title h1{font-size:13.5px}
    #title p{display:none}
    #stories{flex-wrap:nowrap!important;overflow-x:auto;padding-bottom:2px}
    #stories button{white-space:nowrap}
    #simplebtn{font-size:12px;padding:5px 10px}
    .leaflet-control-zoom{display:none} /* pinch zoom on touch */
    #ctrl{width:calc(100vw - 16px);bottom:8px;padding:8px 10px}
    #ctrl .row{flex-wrap:wrap;gap:6px}
    #datebox{font-size:15px;min-width:0;margin-left:auto;text-align:right}
    #chart{top:8px;left:8px;right:8px;width:auto}
  }
  #aboutwrap{position:fixed;inset:0;z-index:2000;background:rgba(15,25,40,.45);
             display:flex;align-items:center;justify-content:center;padding:16px}
  #about{position:relative;max-width:560px;max-height:88vh;overflow-y:auto;
         font-size:13.5px;line-height:1.5;padding:18px 22px}
  #about h2{font-size:17px;margin:0 0 8px;padding-right:26px}
  #about h3{font-size:12px;margin:14px 0 6px;text-transform:uppercase;letter-spacing:.05em;color:#1668a8}
  #about p{margin:0 0 8px}
  #about .caveat{background:#fdf6e3;border-left:3px solid #c9a227;padding:8px 10px;border-radius:4px;margin:0 0 8px}
  #about .caveat p{margin:0}
  #about .krow{display:flex;align-items:center;gap:9px;margin:5px 0}
  #about .krow .sym{flex:0 0 36px;text-align:center}
  #aboutclose{position:absolute;top:8px;right:10px;border:none;background:none;font-size:18px;color:#888;padding:0}
  #aboutgo{display:block;margin:14px auto 2px;font-size:14px;font-weight:600;
           padding:7px 24px;background:#1668a8;color:#fff;border:none}
  #aboutgo:hover{background:#12578d}
  #about .credits{font-size:11.5px;color:#666;border-top:1px solid #ddd;padding-top:8px;margin-top:12px}
  #aboutbtn{font-size:11px;padding:2px 9px;border-radius:10px;float:right;margin-left:8px}
  /* ===== simple mode ===== */
  body.simple #title,body.simple #ctrl,body.simple #legend{display:none}
  body.simple #chart{display:none!important}
  body.simple .leaflet-control-zoom{display:none}
  #simplepanel{top:12px;left:12px;width:330px;max-width:92vw;display:none;
               max-height:calc(100vh - 40px);overflow-y:auto}
  body.simple #simplepanel{display:block}
  #simplepanel h1{font-size:16px;margin:0 0 3px}
  #simplepanel .sub{font-size:12px;color:#555;margin:0 0 6px}
  #sseltitle{font-size:12.5px;font-weight:600;color:#1668a8;margin:6px 0 2px}
  #wytbtns{display:flex;flex-wrap:wrap;gap:4px;margin:6px 0 4px}
  #wytbtns button{font-size:11.5px;padding:3px 8px;border-radius:12px}
  #wytbtns button.on{background:#1668a8;color:#fff;border-color:#1668a8}
  #syearrow{font-size:12px;color:#555;margin:2px 0 4px}
  .sbar{margin:7px 0 9px}
  .sbar .lbl{font-size:12px;font-weight:600;margin-bottom:2px;display:flex;justify-content:space-between}
  .sbar .lbl span:last-child{color:#666;font-weight:500}
  .sbar .track{display:flex;height:15px;border-radius:3px;overflow:hidden}
  .sbar .seg{height:100%}
  #skey{font-size:11px;color:#444;line-height:1.55;margin-top:4px}
  #skeytoggle{display:none;border:none;background:none;color:#1668a8;font-size:12px;
              font-weight:600;padding:2px 0;margin-top:4px;text-align:left;width:100%}
  #skey .dot{width:9px;height:9px}
  #detailgo{display:block;width:100%;margin-top:10px;font-size:13px;font-weight:600;
            padding:7px 0;background:#1668a8;color:#fff;border:none}
  #detailgo:hover{background:#12578d}
  #simplebtn{position:absolute;z-index:1000;top:12px;right:12px;display:none;font-weight:600}
  body.detailmode #simplebtn{display:block}
  #sarrows{position:absolute;inset:0;pointer-events:none;z-index:600}
  #sarrows polygon{pointer-events:auto}
  #sarrows text.alab{font-size:12.5px;fill:#333;font-weight:600;text-anchor:middle}
  #sarrows text.aval{font-size:11.5px;fill:#555;text-anchor:middle}
  /* simple mode on phones: bottom sheet, map on top (must come after the base
     #simplepanel/#skeytoggle rules — equal specificity, source order decides) */
  @media (max-width:700px){
    #simplepanel{top:auto;bottom:0;left:0;right:0;width:auto;max-width:none;
                 border-radius:14px 14px 0 0;max-height:52vh;padding:10px 14px}
    #skeytoggle{display:block}
    #skey{display:none}
    #skey.open{display:block}
  }
</style>
</head>
<body>
<div id="map"></div>
<div class="panel" id="title">
  <button id="aboutbtn">About</button>
  <h1>Central Valley Water Allocation &mdash; CalSim3</h1>
  <p>Monthly simulated channel flows and reservoir storage, Oct&nbsp;1921&ndash;Sep&nbsp;2021
     (COEQWAL scenario <span class="cursid">s0020</span>). Line width &prop; flow; circle size &prop; storage.</p>
  <div class="scenrow" id="scenrow1"></div>
  <div id="stories" style="margin-top:8px;display:flex;flex-wrap:wrap;gap:5px"></div>
  <div id="storyblurb" style="font-size:12px;color:#333;margin-top:6px;display:none;
       border-left:3px solid #e07b28;padding-left:8px"></div>
</div>
<div class="panel" id="ctrl">
  <div class="row">
    <button id="play">&#9654; Play</button>
    <button id="back">&#8722;1m</button>
    <button id="fwd">+1m</button>
    <button id="backy">&#8722;1y</button>
    <button id="fwdy">+1y</button>
    <div id="datebox"></div>
    <div class="abpills" id="abpills1"><span class="ablab">Map</span></div>
    <select id="speed">
      <option value="1500">Slow</option>
      <option value="800" selected>Normal</option>
      <option value="400">Fast</option>
    </select>
  </div>
  <canvas id="strip"></canvas>
  <div class="row" style="margin-top:2px">
    <input type="range" id="slider" min="0" max="1199" value="0" step="1">
  </div>
</div>
<div class="panel" id="chart">
  <button id="chartclose">&times;</button>
  <h2 id="charttitle"></h2>
  <div class="sub" id="chartsub"></div>
  <canvas id="chartmain" style="width:100%;height:170px"></canvas>
  <div class="sub" style="margin-top:6px">Average by month (Oct&ndash;Sep)</div>
  <canvas id="chartclim" style="width:100%;height:90px"></canvas>
</div>
<div class="panel" id="legend">
  <b>Legend</b><br>
  <span class="sw" style="background:#1668a8"></span>River / stream flow<br>
  <span class="sw" style="background:#e07b28"></span>Canal / aqueduct<br>
  <span class="sw" style="background:#3aa6a0"></span>Flood bypass<br>
  <span class="sw" style="background:#7fa8c9;height:2px"></span>Minor stream / canal <span style="color:#888">(zoom in)</span>
  <div id="wkey"></div>
  <span class="dot" style="background:rgba(30,90,160,.75);border:2px solid #1e5aa0"></span>Reservoir storage<br>
  <span class="dot" style="background:none;border:2px solid #1e5aa0"></span>Reservoir capacity<br>  <span style="display:inline-block;width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-bottom:11px solid #7b2d8b;vertical-align:middle;margin-right:8px"></span>Export pumping plant<br>
  <span class="dot" style="background:rgba(74,140,59,.55);border-radius:2px"></span>Farm water deliveries<br>
  <span class="dot" style="background:rgba(134,89,165,.55);border-radius:2px"></span>City water deliveries<br>
  <span class="dot" style="background:rgba(46,139,139,.55);border-radius:2px"></span>Wildlife refuge deliveries<br>
  <label style="cursor:pointer"><input type="checkbox" id="dutoggle" checked> Delivery areas <span style="color:#888">(zoom in)</span></label><br>

  <span class="sw" style="background:#fff;border:1px solid #999;height:3px"></span>Particles: normal direction<br>
  <span class="sw" style="background:#d62828;height:3px"></span>Particles: reversed flow<br>
  <label style="cursor:pointer"><input type="checkbox" id="ptoggle" checked> Flow direction particles</label><br>
  <span style="color:#666">Timeline: year type (Wet&rarr;Critical)<br>+ total reservoir storage curve</span>
</div>
<div class="panel" id="simplepanel">
  <button id="aboutbtn2" style="font-size:11px;padding:2px 9px;border-radius:10px;float:right;margin-left:8px">About</button>
  <h1>Where the water goes</h1>
  <p class="sub">Annual water balance of the Central Valley system, simulated by CalSim3
     (COEQWAL scenario <span class="cursid">s0020</span>). Arrow width &prop; water volume.</p>
  <div class="scenrow" id="scenrow2"></div>
  <div class="abpills" id="abpills2"><span class="ablab">Arrows</span></div>
  <div id="nosimplenote"><b>No annual summary for this scenario.</b> The USBR Alt3 runs
     use a different model configuration that doesn't report basin inflows, so the
     big-picture water balance can't be computed. The detailed map has everything.</div>
  <div id="wytbtns"></div>
  <div id="syearrow">or a single year:
    <select id="syear"><option value="">&mdash;</option></select></div>
  <div id="sseltitle"></div>
  <div id="sbars"></div>
  <button id="skeytoggle">Breakdown &#9662;</button>
  <div id="skey"></div>
  <button id="detailgo">Explore the detailed map &rarr;</button>
</div>
<button id="simplebtn" class="panel" style="padding:6px 14px">&larr; Big picture</button>
<div id="aboutwrap">
  <div class="panel" id="about">
    <button id="aboutclose" title="Close">&times;</button>
    <h2>A century of California water, animated</h2>
    <p>This map shows the Central Valley water system &mdash; the rivers, canals, and reservoirs
       that supply farms, cities, and wildlife refuges from Redding to Bakersfield &mdash;
       month by month across 100 years. The map opens with the big picture &mdash; where each
       year&rsquo;s water comes from and where it goes &mdash; and one click takes you into the
       detailed monthly map.</p>
    <div class="caveat"><p><b>Simulated, not observed.</b> Everything here is output from
       <b>CalSim3</b>, the planning model used by the California Department of Water Resources
       and the U.S. Bureau of Reclamation. Each COEQWAL scenario replays the weather of
       1921&ndash;2021 &mdash; or a climate-changed version of it &mdash; under a chosen set of
       infrastructure and operating rules. The map opens with the baseline (scenario s0020,
       today&rsquo;s rules); the <b>scenario picker</b> switches to alternative policies and
       climates, and <b>Compare</b> adds a second scenario &mdash; flip the map between the
       two and see both on every chart. None of it is a measurement of what actually
       happened.</p></div>
    <h3>How to read the map</h3>
    <div class="krow"><span class="sym"><span class="sw" style="background:#1668a8;height:7px;width:30px"></span></span>
      <span>Thicker lines carry more water: blue rivers, orange canals, teal flood bypasses.</span></div>
    <div class="krow"><span class="sym"><span class="dot" style="background:rgba(30,90,160,.75);border:2px solid #1e5aa0;width:9px;height:9px;margin:0 1px 0 0"></span><span class="dot" style="background:none;border:2px solid #1e5aa0;width:13px;height:13px;margin:0"></span></span>
      <span>Circles are reservoirs: the ring is total capacity, the filled center is water in storage right now.</span></div>
    <div class="krow"><span class="sym"><span class="sw" style="background:#aaa;height:3px;width:13px;margin:0 2px 0 0"></span><span class="sw" style="background:#d62828;height:3px;width:13px;margin:0"></span></span>
      <span>Moving dashes show which way water flows; <b style="color:#d62828">red</b> means the flow has reversed.</span></div>
    <div class="krow"><span class="sym"><span style="display:inline-block;width:0;height:0;border-left:7px solid transparent;border-right:7px solid transparent;border-bottom:12px solid #7b2d8b"></span></span>
      <span>Purple triangles are the two big Delta export pumping plants; they grow with pumping rate.</span></div>
    <div class="krow"><span class="sym"><span class="dot" style="background:rgba(74,140,59,.55);border-radius:2px;margin:0 1px 0 0"></span><span class="dot" style="background:rgba(134,89,165,.55);border-radius:2px;margin:0"></span></span>
      <span>Shaded areas (zoom in) are monthly water deliveries: green farms, purple cities, teal
            refuges. Dashed outlines are areas the model supplies from groundwater.</span></div>
    <div class="krow"><span class="sym"><span class="sw" style="background:linear-gradient(90deg,#2b6cb8,#c9a227,#b2182b);height:10px;width:30px"></span></span>
      <span>The bottom strip colors each year from wet (blue) to critically dry (red); the dark
            curve is total reservoir storage.</span></div>
    <h3>Explore</h3>
    <p>Press play or drag the timeline. Click any river, reservoir, or delivery area for its full
       100-year record. New here? Try the four <b>story buttons</b> in the top-left panel &mdash;
       each flies to a place and plays a moment worth watching.</p>
    <button id="aboutgo">Explore the map &rarr;</button>
    <div class="credits">Built by the <a href="https://coeqwal.berkeley.edu/" target="_blank" rel="noopener">COEQWAL
       project</a>, a University of California collaboration on equitable water allocation.
       Model: CalSim3 (DWR / USBR) &middot; Basemap &copy; OpenStreetMap contributors, tiles &copy; CARTO &middot;
       <a href="https://github.com/emdanner-ucsc/coeqwal-calsim-map" target="_blank" rel="noopener">Code &amp; data</a></div>
  </div>
</div>
<script id="data" type="application/json">__PAYLOAD__</script>
<script id="sdata" type="application/json">__SIMPLE__</script>
<script id="scenmeta" type="application/json">__SCENMETA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const MONTH_NAMES=['January','February','March','April','May','June','July','August','September','October','November','December'];
const map = L.map('map',{preferCanvas:true}).setView([38.3,-121.4],7);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
  {attribution:'&copy; OpenStreetMap &copy; CARTO', maxZoom:12}).addTo(map);
const canvas = L.canvas({padding:.3});

const COLORS={river:'#1668a8',canal:'#e07b28',bypass:'#3aa6a0'};
const QREF=D.qref;
function widthFor(q){ if(q==null||q<=0)return .6; return .8+8*Math.sqrt(Math.min(q,QREF)/QREF); }
function fmt(x){ return x==null?'n/a':x.toLocaleString(); }

const arcLayers=[];
for(const a of D.arcs){
  const latlngs=a.g.map(line=>line.map(p=>[p[1],p[0]]));
  const pl=L.polyline(latlngs,{renderer:canvas,color:COLORS[a.c],weight:1,opacity:.85});
  pl.bindTooltip('',{sticky:true});
  pl._arc=a;
  pl.on('tooltipopen',()=>{
    const q=a.q[cur];
    pl.setTooltipContent('<b>'+a.n+'</b><br>'+a.i+'<br>Flow: '+fmt(q)+' cfs'+
      (q==null?'':' ('+fmt(Math.round(cfsToTAF(q)*10)/10)+' TAF/month)')+
      '<br><span style="color:#888">Click for 100-year record</span>');
  });
  pl.on('click',()=>openChart({kind:'arc',f:a}));
  pl.addTo(map); arcLayers.push(pl);
}

// ===== minor tributaries & distribution canals (zoom-gated) =====
const MCOLORS={river:'#7fa8c9',canal:'#e5b285',bypass:'#8fc4c0'}; // muted versions of COLORS
const MINOR_MINZOOM=9;
const minorLayers=[]; let minorVisible=false;
function minorWidth(q){ if(q==null||q<=0)return .4; return .5+3.5*Math.sqrt(Math.min(q,QREF)/QREF); }
for(const a of (D.marcs||[])){
  const latlngs=a.g.map(line=>line.map(p=>[p[1],p[0]]));
  const pl=L.polyline(latlngs,{renderer:canvas,color:MCOLORS[a.c],weight:.8,opacity:.6});
  pl.bindTooltip('',{sticky:true});
  pl._arc=a;
  pl.on('tooltipopen',()=>{
    const q=a.q[cur];
    pl.setTooltipContent('<b>'+a.n+'</b><br>'+a.i+'<br>Flow: '+fmt(q)+' cfs'+
      (q==null?'':' ('+fmt(Math.round(cfsToTAF(q)*10)/10)+' TAF/month)')+
      '<br><span style="color:#888">Click for 100-year record</span>');
  });
  pl.on('click',()=>openChart({kind:'arc',f:a}));
  minorLayers.push(pl); // added to the map only at zoom >= MINOR_MINZOOM
}
function minorRestyle(i){
  for(const pl of minorLayers){
    const q=pl._arc.q[i];
    pl.setStyle({weight:minorWidth(q), opacity:(q==null||q<=0)?.25:.6});
  }
}
function minorUpdate(){
  const show=map.getZoom()>=MINOR_MINZOOM;
  if(show===minorVisible) return;
  minorVisible=show;
  for(const pl of minorLayers) show?pl.addTo(map):pl.remove();
  if(show) minorRestyle(cur);
}
map.on('zoomend',minorUpdate);

const CAPMAX=Math.max(...D.res.map(r=>r.cap));
const RMAX=24;
function radiusFor(v){ return Math.max(2, RMAX*Math.sqrt(v/CAPMAX)); }
const resLayers=[];
for(const r of D.res){
  const ring=L.circleMarker([r.ll[1],r.ll[0]],{renderer:canvas,radius:radiusFor(r.cap),
      color:'#1e5aa0',weight:1.4,fill:false,opacity:.8});
  const fillC=L.circleMarker([r.ll[1],r.ll[0]],{renderer:canvas,radius:2,stroke:false,
      fillColor:'#1e5aa0',fillOpacity:.65});
  const grp=L.featureGroup([ring,fillC]).addTo(map);
  grp.bindTooltip('',{sticky:true});
  grp.on('tooltipopen',()=>{
    const s=r.s[cur], pct=s==null?'n/a':Math.round(100*s/r.cap);
    grp.setTooltipContent('<b>'+r.n+'</b> ('+r.riv+')<br>Storage: '+fmt(s)+' of '+fmt(r.cap)+
      ' TAF max ('+pct+'%)<br><span style="color:#888">Click for 100-year record</span>');
  });
  grp.on('click',()=>openChart({kind:'res',f:r}));
  resLayers.push({r,fillC});
}

function daysInMonth(i){ const [y,m]=D.months[i].split('-').map(Number); return new Date(y,m,0).getDate(); }
function cfsToTAF(q){ return q*1.98347*daysInMonth(cur)/1000; }

// ===== click-to-chart =====
// ===== demand-unit delivery areas =====
map.createPane('dupane'); map.getPane('dupane').style.zIndex=350;
const DU_COLORS={ag:'#4a8c3b',urban:'#8659a5',refuge:'#2e8b8b'};
const DU_LABEL={ag:'Agriculture',urban:'Urban',refuge:'Wildlife refuge'};
const DEPTH_REF=0.6; // ft of applied water per month at full shade
const duLayers=[];
let duOn=true, duVisible=false;
for(const u of D.dus){
  const poly=L.polygon(u.g,{pane:'dupane',renderer:canvas,color:DU_COLORS[u.k],weight:.7,
    opacity:.5,fillColor:DU_COLORS[u.k],fillOpacity:0,interactive:true});
  poly.bindTooltip('',{sticky:true});
  poly.on('tooltipopen',()=>{
    let body;
    if(u.gw){ body='No surface-water deliveries in model<br>(supplied by groundwater)'; }
    else{
      const v=u.d[cur], ft=v*1000/u.ac;
      body='Delivery: '+v.toFixed(1)+' TAF this month ('+ft.toFixed(2)+' ft over '+fmt(u.ac)+' acres)'+
           '<br><span style="color:#888">Click for 100-year record</span>';
    }
    poly.setTooltipContent('<b>'+DU_LABEL[u.k]+' service area '+u.i+'</b><br>'+body);
  });
  if(!u.gw) poly.on('click',()=>openChart({kind:'du',f:u}));
  duLayers.push({u,poly}); // added to the map by duUpdate when visible
}
function duUpdate(){
  const want = duOn && map.getZoom()>=8;
  if(want!==duVisible){
    // add/remove rather than style to transparent: hidden polygons must not
    // capture hover/clicks meant for the thin minor arcs beneath them
    for(const o of duLayers) want?o.poly.addTo(map):o.poly.remove();
    duVisible=want;
  }
  if(!duVisible) return;
  for(const o of duLayers){
    if(o.u.gw){ o.poly.setStyle({fillOpacity:.04,opacity:.35,dashArray:'3,4'}); continue; }
    const ft=o.u.d[cur]*1000/o.u.ac;
    o.poly.setStyle({fillOpacity:Math.min(.62,.62*ft/DEPTH_REF),opacity:.5,dashArray:null});
  }
}
map.on('zoomend',duUpdate);

// ===== export pumping plants =====
const PQMAX = Math.max(...D.pumps.flatMap(p=>p.q.filter(v=>v!=null)));
function pumpIcon(q){
  const s = q==null||q<=0 ? 7 : 8 + 20*Math.sqrt(q/PQMAX);
  return L.divIcon({className:'', iconSize:[2*s,2*s], iconAnchor:[s,s*1.2],
    html:'<div style="width:0;height:0;border-left:'+s+'px solid transparent;'+
         'border-right:'+s+'px solid transparent;border-bottom:'+(s*1.7)+'px solid #7b2d8b;'+
         'opacity:.88"></div>'});
}
const pumpMarkers=[];
for(const p of D.pumps){
  const mk=L.marker([p.ll[1],p.ll[0]],{icon:pumpIcon(p.q[0]),zIndexOffset:800});
  mk.bindTooltip('',{sticky:true});
  mk.on('tooltipopen',()=>{
    const q=p.q[cur];
    mk.setTooltipContent('<b>'+p.n+'</b><br>'+p.sub+'<br>Exporting: '+fmt(q)+' cfs'+
      (q==null?'':' ('+fmt(Math.round(cfsToTAF(q)*10)/10)+' TAF/month)')+
      '<br><span style="color:#888">Click for 100-year record</span>');
  });
  mk.on('click',()=>openChart({kind:'pump',f:p}));
  mk.addTo(map); pumpMarkers.push({p,mk});
}

let chartFeat=null;
const chartEl=document.getElementById('chart');
function openChart(cf){ chartFeat=cf; chartEl.style.display='block'; drawChart(); }
document.getElementById('chartclose').onclick=()=>{ chartFeat=null; chartEl.style.display='none'; };
function setupCanvas(cv){
  const dpr=window.devicePixelRatio||1, w=cv.clientWidth, h=cv.clientHeight;
  cv.width=w*dpr; cv.height=h*dpr;
  const c=cv.getContext('2d'); c.setTransform(dpr,0,0,dpr,0,0);
  return [c,w,h];
}
function niceMax(v){ const p=Math.pow(10,Math.floor(Math.log10(v||1))); return Math.ceil(v/p)*p; }
// look up a feature's series in a cached scenario (compare mode reads BOTH
// sides from scenCache rather than the live, swapped-in-place feature object)
function seriesOf(sid, kind, f){
  const sc=scenCache[sid]; if(!sc) return null;
  const m = kind==='res'?sc.res : kind==='du'?sc.dus : kind==='pump'?sc.pumps : sc.arcs;
  return m[f.i]||null;
}
function drawChart(){
  if(!chartFeat) return;
  const isRes = chartFeat.kind==='res', isDU = chartFeat.kind==='du', f=chartFeat.f;
  const unit = isRes ? 'TAF' : isDU ? 'TAF/mo' : 'cfs';
  // A always solid blue, B always dashed orange, regardless of which the map shows
  const vals  = sidB ? (seriesOf(sidA,chartFeat.kind,f)||[]) : (isDU ? f.d : (isRes ? f.s : f.q));
  const valsB = sidB ? (seriesOf(sidB,chartFeat.kind,f)||[]) : null;
  document.getElementById('charttitle').textContent = isDU
    ? DU_LABEL[f.k]+' service area '+f.i+' — deliveries'
    : f.n + (isRes ? ' — storage' : chartFeat.kind==='pump' ? ' — Delta exports' : ' — flow');
  const v=vals[cur];
  document.getElementById('chartsub').innerHTML = sidB
    ? f.i+' &middot; '+D.months[cur]+': <b style="color:#1668a8">A '+fmt(v)+'</b> / '+
      '<b style="color:#e07b28">B '+fmt(valsB[cur])+'</b> '+unit+
      ' <span style="color:#999">(A '+sidA+' &middot; B '+sidB+')</span>'
    : f.i+' &middot; '+D.months[cur]+': <b>'+fmt(v)+' '+unit+'</b>'+
      (isRes||isDU||v==null?'':' ('+fmt(Math.round(cfsToTAF(v)*10)/10)+' TAF/mo)');
  // --- main: full record
  const [c,w,h]=setupCanvas(document.getElementById('chartmain'));
  const finite=vals.filter(x=>x!=null).concat(valsB?valsB.filter(x=>x!=null):[]);
  if(!finite.length){ c.clearRect(0,0,w,h); return; }
  const vmax=niceMax(Math.max(...finite));
  const vmin=Math.min(0,...finite);
  const yof=v=> h-14-(h-22)*((v-vmin)/(vmax-vmin||1));
  c.clearRect(0,0,w,h);
  // wyt background bands (subtle; the displayed scenario's year types)
  for(let k=0;k<D.wyt.length;k++){
    c.fillStyle=WYT_COLORS[D.wyt[k]-1]; c.globalAlpha=.13;
    c.fillRect(k/D.wyt.length*w,0,w/D.wyt.length+1,h-14);
  }
  c.globalAlpha=1;
  // zero line if negative values
  if(vmin<0){ c.strokeStyle='#999'; c.lineWidth=1; c.setLineDash([3,3]);
    c.beginPath(); c.moveTo(0,yof(0)); c.lineTo(w,yof(0)); c.stroke(); c.setLineDash([]); }
  const line=(vv,color,dash)=>{
    c.strokeStyle=color; c.lineWidth=1; c.setLineDash(dash||[]);
    c.beginPath(); let pen=false;
    for(let i=0;i<vv.length;i++){ if(vv[i]==null){ pen=false; continue; }
      const x=(i+.5)/vv.length*w; pen?c.lineTo(x,yof(vv[i])):c.moveTo(x,yof(vv[i])); pen=true; }
    c.stroke(); c.setLineDash([]);
  };
  line(vals, isRes?'#1e5aa0':'#1668a8');
  if(valsB) line(valsB, '#e07b28', [4,3]);
  // capacity line for reservoirs
  if(isRes){ c.strokeStyle='#b2182b'; c.setLineDash([4,3]);
    c.beginPath(); c.moveTo(0,yof(f.cap)); c.lineTo(w,yof(f.cap)); c.stroke(); c.setLineDash([]); }
  // decade ticks
  c.fillStyle='#666'; c.font='10px system-ui'; c.textAlign='center';
  for(let y=1930;y<=2020;y+=10){ const x=((y-1921.75)*12)/1200*w; c.fillText(String(y),x,h-3); }
  c.textAlign='left'; c.fillText(fmt(vmax)+' '+unit,3,10);
  if(vmin<0) c.fillText(fmt(Math.round(vmin)),3,yof(vmin)-2);
  // current-month marker
  c.strokeStyle='#111'; c.lineWidth=1.5;
  const mx=(cur+.5)/1200*w;
  c.beginPath(); c.moveTo(mx,0); c.lineTo(mx,h-14); c.stroke();
  // --- climatology: mean by calendar month (Oct-Sep)
  const [c2,w2,h2]=setupCanvas(document.getElementById('chartclim'));
  const climOf=vv=>{
    const sums=Array(12).fill(0), cnts=Array(12).fill(0);
    for(let i=0;i<vv.length;i++){ if(vv[i]!=null){ sums[i%12]+=vv[i]; cnts[i%12]++; } }
    return sums.map((s,k)=>cnts[k]?s/cnts[k]:null);
  };
  const means=climOf(vals), meansB=valsB?climOf(valsB):null;
  const mfin=means.filter(x=>x!=null).concat(meansB?meansB.filter(x=>x!=null):[]);
  const mmax=niceMax(Math.max(...mfin,0)), mmin=Math.min(0,...mfin);
  c2.clearRect(0,0,w2,h2);
  const LBL=['O','N','D','J','F','M','A','M','J','J','A','S'];
  const y2=v=> h2-13-(h2-20)*((v-mmin)/(mmax-mmin||1));
  for(let k=0;k<12;k++){
    const x=k/12*w2+3, bw=w2/12-6;
    c2.fillStyle = k===cur%12 ? '#e07b28' : '#9ec5e0';
    const y0=y2(Math.max(0,mmin)), y1=y2(means[k]==null?0:means[k]);
    c2.fillRect(x, Math.min(y0,y1), bw, Math.abs(y0-y1)||1);
    c2.fillStyle='#666'; c2.font='10px system-ui'; c2.textAlign='center';
    c2.fillText(LBL[k], x+bw/2, h2-2);
  }
  if(meansB){  // B climatology as a dashed step-line over A's bars
    c2.strokeStyle='#c05f10'; c2.lineWidth=1.6; c2.setLineDash([4,3]);
    c2.beginPath(); let pen=false;
    for(let k=0;k<12;k++){ if(meansB[k]==null){ pen=false; continue; }
      const x=k/12*w2+3+(w2/12-6)/2, y=y2(meansB[k]);
      pen?c2.lineTo(x,y):c2.moveTo(x,y); pen=true; }
    c2.stroke(); c2.setLineDash([]);
  }
  c2.textAlign='left'; c2.fillStyle='#666'; c2.fillText(fmt(Math.round(mmax))+' '+unit,3,10);
}

// ===== legend flow-width key =====
(function(){
  const box=document.getElementById('wkey');
  for(const q of [1000,10000,50000]){
    const d=document.createElement('div'); d.className='k';
    d.innerHTML='<div class="bar" style="height:'+widthFor(q).toFixed(1)+'px"></div>'+fmt(q)+' cfs';
    box.appendChild(d);
  }
})();

const WYT_NAMES=['Wet','Above Normal','Below Normal','Dry','Critical'];
const WYT_COLORS=['#2b6cb8','#74add1','#c9a227','#e2703a','#b2182b'];
// ===== A/B comparison state (scenario section wires the UI) =====
// sidA/sidB are fixed sides; `shown` is which one the map currently displays.
// Color language everywhere: A = solid blue #1668a8, B = dashed orange #e07b28.
let sidA='s0020', sidB=null, shown='A';
// total storage across mapped reservoirs, per month (recomputed per scenario;
// TSMAX has a frozen floor at the base scenario's max so curves stay comparable)
let TSTOR=[], TSTORB=null, TSMAX=1, TSMAX_BASE=null;
function recomputeStorage(){
  // solid curve: A's storage when comparing, else the displayed scenario's
  // (identical unless shown==='B'); dashed curve: B's.
  TSTORB=null;
  if(sidB && scenCache[sidA] && scenCache[sidB]){
    const of=sid=>{ const R=scenCache[sid].res;
      return D.months.map((_,i)=>{ let s=0; for(const r of D.res){ const v=(R[r.i]||[])[i]; if(v!=null) s+=v; } return s; }); };
    TSTOR=of(sidA); TSTORB=of(sidB);
  }else{
    TSTOR = D.months.map((_,i)=>{ let s=0; for(const r of D.res){ const v=r.s[i]; if(v!=null) s+=v; } return s; });
  }
  const m = Math.max(...TSTOR, ...(TSTORB||[0]));
  if(TSMAX_BASE==null) TSMAX_BASE=m;
  TSMAX = Math.max(m, TSMAX_BASE);
}
recomputeStorage();
const strip = document.getElementById('strip');
let stripBase=null;
function buildStrip(){
  const dpr = window.devicePixelRatio||1;
  const w = strip.clientWidth, h = strip.clientHeight;
  if(!w){ stripBase=null; return; }  // #ctrl hidden (simple mode); rebuilt on mode switch
  strip.width=w*dpr; strip.height=h*dpr;
  stripBase = document.createElement('canvas');
  stripBase.width=w*dpr; stripBase.height=h*dpr;
  const c = stripBase.getContext('2d'); c.scale(dpr,dpr);
  const nwy = D.wyt.length;
  for(let k=0;k<nwy;k++){
    c.fillStyle = WYT_COLORS[D.wyt[k]-1];
    c.globalAlpha = .55;
    c.fillRect(k/nwy*w, 0, w/nwy+1, h);
  }
  c.globalAlpha = 1;
  // total storage curve (A / displayed scenario)
  c.strokeStyle='rgba(15,25,60,.85)'; c.lineWidth=1.4;
  c.beginPath();
  for(let i=0;i<TSTOR.length;i++){
    const x=(i+.5)/TSTOR.length*w, y=h-3-(h-8)*(TSTOR[i]/TSMAX);
    i?c.lineTo(x,y):c.moveTo(x,y);
  }
  c.stroke();
  // scenario B's storage curve, dashed orange (year-type bands stay the
  // displayed scenario's — across hydrologies the classifications differ)
  if(TSTORB){
    c.strokeStyle='rgba(224,123,40,.95)'; c.lineWidth=1.4; c.setLineDash([5,4]);
    c.beginPath();
    for(let i=0;i<TSTORB.length;i++){
      const x=(i+.5)/TSTORB.length*w, y=h-3-(h-8)*(TSTORB[i]/TSMAX);
      i?c.lineTo(x,y):c.moveTo(x,y);
    }
    c.stroke(); c.setLineDash([]);
  }
  strip.title = sidB
    ? 'Storage curves: solid = A ('+sidA+'), dashed = B ('+sidB+'). Year-type bands: '+
      (shown==='B'?sidB:sidA)+' only.'
    : 'Year type (Wet→Critical) + total reservoir storage';
}
function updateStrip(i){
  if(!stripBase) return;
  const ctx = strip.getContext('2d');
  ctx.clearRect(0,0,strip.width,strip.height);
  ctx.drawImage(stripBase,0,0);
  const dpr = window.devicePixelRatio||1;
  const x = ((i+.5)/1200)*strip.clientWidth*dpr;
  ctx.fillStyle='#111';
  ctx.fillRect(x-1*dpr,0,2*dpr,strip.height);
}
function stripScrub(e){
  const rect = strip.getBoundingClientRect();
  const f = Math.max(0,Math.min(.9999,(e.clientX-rect.left)/rect.width));
  setPlaying(false); render(Math.floor(f*1200));
}
strip.addEventListener('pointerdown', e=>{ strip.setPointerCapture(e.pointerId); stripScrub(e);
  strip.onpointermove=stripScrub; });
strip.addEventListener('pointerup', ()=>{ strip.onpointermove=null; });
window.addEventListener('resize', ()=>{ buildStrip(); updateStrip(cur); });

let cur=0, playing=false, timer=null, simpleOn=false;
const slider=document.getElementById('slider'), datebox=document.getElementById('datebox');

function render(i){
  cur=i;
  const [y,m]=D.months[i].split('-');
  const wy=Math.floor(i/12);
  datebox.innerHTML=MONTH_NAMES[+m-1]+' '+y+
    '<div style="font-size:11px;font-weight:500;color:'+WYT_COLORS[D.wyt[wy]-1]+'">'+WYT_NAMES[D.wyt[wy]-1]+' year</div>';
  for(const o of pumpMarkers) o.mk.setIcon(pumpIcon(o.p.q[i]));
  duUpdate();
  updateStrip(i);
  if(chartFeat) drawChart();
  slider.value=i;
  for(const pl of arcLayers){
    const q=pl._arc.q[i];
    pl.setStyle({weight:widthFor(q), opacity:(q==null||q<=0)?.35:.85});
  }
  if(minorVisible) minorRestyle(i);
  for(const o of resLayers){
    const s=o.r.s[i];
    o.fillC.setRadius(s==null?0:radiusFor(s));
  }
}
function step(n){
  render(((cur+n)%1200+1200)%1200);
  if(storyEnd!==null && cur>=storyEnd){ setPlaying(false); storyEnd=null; }
}
function setPlaying(p){
  playing=p;
  document.getElementById('play').innerHTML=p?'&#10074;&#10074; Pause':'&#9654; Play';
  clearInterval(timer);
  if(p) timer=setInterval(()=>step(1), +document.getElementById('speed').value);
}
document.getElementById('play').onclick=()=>setPlaying(!playing);
document.getElementById('back').onclick=()=>step(-1);
document.getElementById('fwd').onclick=()=>step(1);
document.getElementById('backy').onclick=()=>step(-12);
document.getElementById('fwdy').onclick=()=>step(12);
document.getElementById('speed').onchange=()=>{ if(playing) setPlaying(true); };
slider.oninput=e=>{ setPlaying(false); render(+e.target.value); };
// ===== guided stories =====
// month index: (Y-1921)*12 + (M-10)
const STORIES=[
 {label:'1976\u201377 Drought', view:[[38.3,-121.4],7], start:648, end:677,
  blurb:'The two driest back-to-back years on record to that point. Watch reservoir circles shrink to dots and rivers thin to threads \u2014 by late 1977 total storage hits its lowest level of the century.'},
 {label:'1997 New Year\u2019s Flood', view:[[39.1,-121.8],8], start:901, end:908,
  blurb:'A warm atmospheric river melts deep snowpack. Watch the Feather and Sacramento swell in January, and the Yolo and Sutter Bypasses \u2014 normally dry \u2014 open up to carry the flood past the cities.'},
 {label:'The Delta Reversed', view:[[37.93,-121.45],10], start:956, end:971,
  blurb:'Red particles flow backwards. The SWP and CVP export pumps near Tracy pull Old and Middle Rivers \u2014 and at times the lower San Joaquin itself \u2014 upstream toward the intakes, then south down the aqueducts.'},
 {label:'Drought to Deluge 2012\u201317', view:[[38.3,-121.4],7], start:1080, end:1151,
  blurb:'Five dry years drain the system \u2014 then the wettest winter on record refills it in months. The whiplash California\u2019s water system is built to absorb, compressed into one animation.'}
];
let storyEnd=null;
const blurbEl=document.getElementById('storyblurb');
function runStory(s){
  setPlaying(false); storyEnd=null;
  blurbEl.style.display='block'; blurbEl.textContent=s.blurb;
  render(s.start);
  map.flyTo(s.view[0], s.view[1], {duration:1.4});
  map.once('moveend', ()=>{ storyEnd=s.end; setPlaying(true); });
}
(function(){
  const box=document.getElementById('stories');
  for(const s of STORIES){
    const b=document.createElement('button'); b.textContent=s.label;
    b.onclick=()=>runStory(s); box.appendChild(b);
  }
})();

// ===== about panel =====
const aboutwrap=document.getElementById('aboutwrap');
function aboutShow(){ aboutwrap.style.display='flex'; }
function aboutHide(){ aboutwrap.style.display='none'; }
document.getElementById('aboutbtn').onclick=aboutShow;
document.getElementById('aboutclose').onclick=aboutHide;
document.getElementById('aboutgo').onclick=aboutHide;
aboutwrap.addEventListener('click',e=>{ if(e.target===aboutwrap) aboutHide(); });
document.addEventListener('keydown',e=>{ if(e.key==='Escape') aboutHide(); });

buildStrip();
render(0);

// ===== Particle flow layer (Delta channels + aqueducts) =====
const P_ARCS = D.arcs.filter(a=>a.p);
const QP = (()=>{ const v=[]; for(const a of P_ARCS) for(const q of a.q) if(q!=null) v.push(Math.abs(q));
                  v.sort((x,y)=>x-y); return v[Math.floor(v.length*.98)]||1; })();
const pcv = document.createElement('canvas');
pcv.style.cssText='position:absolute;inset:0;pointer-events:none;z-index:500';
map.getContainer().appendChild(pcv);
const pctx = pcv.getContext('2d');
let projArcs=[], particles=[], panim=null, particlesOn=true, moving=false;

function reproject(){
  const sz = map.getSize();
  pcv.width=sz.x; pcv.height=sz.y;
  projArcs=[]; particles=[];
  const b = map.getBounds().pad(0.15);
  for(const a of P_ARCS){
    for(const line of a.g){
      // cheap bbox reject
      let inview=false;
      for(const pt of line){ if(b.contains([pt[1],pt[0]])){ inview=true; break; } }
      if(!inview) continue;
      const pts = line.map(pt=>map.latLngToContainerPoint([pt[1],pt[0]]));
      const cum=[0];
      for(let i=1;i<pts.length;i++)
        cum.push(cum[i-1]+Math.hypot(pts[i].x-pts[i-1].x, pts[i].y-pts[i-1].y));
      const L = cum[pts.length-1];
      if(L<8) continue;
      const tier = a.p===2 ? 2 : 1;
      const pa = {arc:a, pts, cum, L, tier};
      projArcs.push(pa);
    }
  }
  // generate particles: tier 1 (canals/Delta) first, then tier 2 (mainstem rivers), capped
  const CAP = 2500;
  projArcs.sort((x,y)=>x.tier-y.tier);
  for(const pa of projArcs){
    if(particles.length >= CAP) break;
    const spacing = pa.tier===1 ? 26 : 48;
    const n = Math.max(1, Math.min(40, Math.round(pa.L/spacing)));
    for(let k=0;k<n && particles.length<CAP;k++)
      particles.push({pa, t: Math.random()*pa.L, px:null, py:null});
  }
}
function posAt(pa, t){
  const {pts,cum} = pa;
  let lo=0, hi=cum.length-1;
  while(lo<hi-1){ const mid=(lo+hi)>>1; if(cum[mid]<=t) lo=mid; else hi=mid; }
  const seg = cum[hi]-cum[lo] || 1;
  const f = (t-cum[lo])/seg;
  return [pts[lo].x+f*(pts[hi].x-pts[lo].x), pts[lo].y+f*(pts[hi].y-pts[lo].y)];
}
function ptick(){
  panim = requestAnimationFrame(ptick);
  if(moving || !particlesOn || simpleOn) return;
  // fade previous frame -> trails
  pctx.globalCompositeOperation='destination-out';
  pctx.fillStyle='rgba(0,0,0,0.14)';
  pctx.fillRect(0,0,pcv.width,pcv.height);
  pctx.globalCompositeOperation='source-over';
  pctx.lineCap='round';
  for(const p of particles){
    const q = p.pa.arc.q[cur];
    if(q==null || Math.abs(q)<25){ p.px=null; continue; }
    const dir = q>=0?1:-1;
    const sp = 0.15 + 1.0*Math.sqrt(Math.min(Math.abs(q),QP)/QP);
    p.t += sp*dir;
    if(p.t>p.pa.L){ p.t-=p.pa.L; p.px=null; }
    if(p.t<0){ p.t+=p.pa.L; p.px=null; }
    const [x,y] = posAt(p.pa, p.t);
    if(p.px!=null){
      if(p.pa.tier===1){
        pctx.strokeStyle = dir<0 ? 'rgba(214,40,40,0.95)' : 'rgba(255,255,255,0.95)';
        pctx.lineWidth = 2.2;
      }else{
        pctx.strokeStyle = dir<0 ? 'rgba(214,40,40,0.75)' : 'rgba(255,255,255,0.5)';
        pctx.lineWidth = 1.6;
      }
      pctx.beginPath(); pctx.moveTo(p.px,p.py); pctx.lineTo(x,y); pctx.stroke();
    }
    p.px=x; p.py=y;
  }
}
function pclear(){ pctx.clearRect(0,0,pcv.width,pcv.height); }
map.on('movestart zoomstart', ()=>{ moving=true; pclear(); });
map.on('moveend zoomend viewreset resize', ()=>{ reproject(); moving=false; });
document.getElementById('ptoggle').onchange = e=>{ particlesOn=e.target.checked; pclear(); };
document.getElementById('dutoggle').onchange = e=>{ duOn=e.target.checked; duUpdate(); };
reproject();
ptick();

// ===== simple mode (big-picture view) =====
const SD0 = JSON.parse(document.getElementById('sdata').textContent);
let SD = SD0;   // swapped per scenario; null when the scenario lacks simple-mode data
const S_BOUNDS = [[34.2,-124.2],[41.3,-117.8]];  // arrow composition extent, ~detailed-view domain
// arrow centerlines: cubic bezier control points (lon,lat) — hand-authored
const S_ARROWS = {
  sac:    {pts:[[-122.25,40.45],[-122.05,39.6],[-121.75,39.05],[-121.8,38.4]],
           color:'#4a90c4', lt:.45, dl:[-58,0], name:'Sacramento'},
  east:   {pts:[[-120.65,38.7],[-121.0,38.5],[-121.25,38.4],[-121.55,38.25]],
           color:'#4a90c4', lt:.1, dl:[34,-12], name:'Eastside'},
  sj:     {pts:[[-119.8,36.9],[-120.5,37.05],[-121.05,37.35],[-121.55,37.9]],
           color:'#4a90c4', lt:.02, dl:[48,10], name:'San Joaquin'},
  outflow:{pts:[[-122.05,38.05],[-122.3,38.02],[-122.55,37.88],[-123.1,37.5]],
           color:'#2b6ca3', lt:.95, dl:[-14,34], name:'Delta outflow'},
  swp:    {pts:[[-121.68,37.68],[-121.0,36.5],[-119.95,35.55],[-118.95,34.85]],
           color:'#d97e2a', lt:.72, dl:[42,4], name:'SWP exports'},
  cvp:    {pts:[[-121.55,37.6],[-121.35,37.2],[-121.1,36.95],[-120.7,36.7]],
           color:'#a85d1c', lt:1, dl:[-26,30], name:'CVP exports'}
};
let ssel = {t:'all'};
const sAllCache = {};   // per-sid long-term means (payloads are immutable)
function sdataOf(sid){  // current selection applied to a given scenario's simple payload
  const sp = scenCache[sid] && scenCache[sid].simple;
  if(!sp) return null;
  if(ssel.t==='wyt') return sp.composites[ssel.v]||null;
  if(ssel.t==='year') return sp.years.find(y=>y.wy===ssel.v)||null;
  if(!sAllCache[sid]){
    const o = {name:'All years', n:sp.years.length};
    for(const g of ['arrows','sources','uses','outflow']){
      o[g]={};
      for(const k in sp.years[0][g])
        o[g][k]=sp.years.reduce((s,y)=>s+y[g][k],0)/sp.years.length;
    }
    sAllCache[sid]=o;
  }
  return sAllCache[sid];
}
function sdata(){ return sdataOf(curSid); }
const sarrsvg = document.createElementNS('http://www.w3.org/2000/svg','svg');
sarrsvg.id='sarrows'; sarrsvg.style.display='none';
map.getContainer().appendChild(sarrsvg);

function sbez(p,t){ const u=1-t;
  return [0,1].map(i=>u*u*u*p[0][i]+3*u*u*t*p[1][i]+3*u*t*t*p[2][i]+t*t*t*p[3][i]); }
function sArrowPoly(ctrl,w,sc){
  const n=48, pts=[]; for(let i=0;i<=n;i++) pts.push(sbez(ctrl,i/n));
  const headLen=Math.min(Math.max(w*1.15,10*sc),24*sc);
  let acc=0, cut=n;
  for(let i=n;i>0;i--){ acc+=Math.hypot(pts[i-1][0]-pts[i][0],pts[i-1][1]-pts[i][1]);
    if(acc>=headLen){ cut=i-1; break; } }
  const body=pts.slice(0,cut+1), tip=pts[n];
  const nrm=(i,arr)=>{ const a=arr[Math.max(i-1,0)], b=arr[Math.min(i+1,arr.length-1)];
    const dx=b[0]-a[0], dy=b[1]-a[1], L=Math.hypot(dx,dy)||1; return [-dy/L,dx/L]; };
  const left=[],right=[];
  for(let i=0;i<body.length;i++){ const [nx,ny]=nrm(i,body), p=body[i];
    left.push([p[0]+nx*w/2,p[1]+ny*w/2]); right.push([p[0]-nx*w/2,p[1]-ny*w/2]); }
  const [nx,ny]=nrm(body.length-1,body), hb=body[body.length-1];
  const hw=Math.min(w*.95,14*sc);
  const poly=left.concat([[hb[0]+nx*(w/2+hw),hb[1]+ny*(w/2+hw)],tip,
    [hb[0]-nx*(w/2+hw),hb[1]-ny*(w/2+hw)]],right.reverse());
  return poly.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ');
}
function drawArrows(){
  if(!simpleOn) return;
  const d=sdata(); if(!d){ sarrsvg.innerHTML=''; return; }
  const sz=map.getSize();
  sarrsvg.setAttribute('width',sz.x); sarrsvg.setAttribute('height',sz.y);
  const pA=map.latLngToContainerPoint([38,-121]), pB=map.latLngToContainerPoint([39,-121]);
  const sc=(pA.y-pB.y)/55;           // scale relative to the mockup's 55 px/deg
  const k=1.5*sc;                    // px of arrow width per maf
  let out='';
  for(const key in S_ARROWS){
    const a=S_ARROWS[key], maf=d.arrows[key]/1000;
    const w=Math.max(maf*k,2);
    const ctrl=a.pts.map(pt=>{ const c=map.latLngToContainerPoint([pt[1],pt[0]]); return [c.x,c.y]; });
    out+='<polygon points="'+sArrowPoly(ctrl,w,sc)+'" fill="'+a.color+'" fill-opacity=".82">'+
         '<title>'+a.name+': '+maf.toFixed(1)+' maf</title></polygon>';
    const lp=sbez(ctrl,a.lt), lx=lp[0]+a.dl[0]*sc, ly=lp[1]+a.dl[1]*sc;
    out+='<text class="alab" x="'+lx.toFixed(0)+'" y="'+ly.toFixed(0)+'">'+a.name+'</text>'+
         '<text class="aval" x="'+lx.toFixed(0)+'" y="'+(ly+13).toFixed(0)+'">'+maf.toFixed(1)+' maf</text>';
  }
  sarrsvg.innerHTML=out;
}
const S_SEGC = {rsac:'#4a90c4', rsj:'#74add1', stor:'#1e5aa0', ag:'#4a8c3b',
  urban:'#8659a5', refuge:'#2e8b8b', losses:'#a5a5a5', other:'#7f98ad',
  req:'#3aa6a0', unc:'#9ec5e0'};
function segsFor(d){  // [group name, [label, value, color][]] triples for one scenario
  const S=d.sources,U=d.uses,O=d.outflow, rel=S.storage_release;
  const src=[['Sacramento basin runoff',S.runoff_sac,S_SEGC.rsac],
             ['San Joaquin basin runoff',S.runoff_sj,S_SEGC.rsj]];
  if(rel>0) src.push(['Released from reservoirs',rel,S_SEGC.stor]);
  if(S.other>50) src.push(['Other inflows (net)',S.other,S_SEGC.other]);
  const use=[['Farms (incl. Delta)',U.ag+U.in_delta,S_SEGC.ag],
             ['Cities',U.urban,S_SEGC.urban],
             ['Wildlife refuges',U.refuge,S_SEGC.refuge],
             ['Losses & other',U.losses,S_SEGC.losses]];
  if(rel<0) use.push(['Stored in reservoirs',-rel,S_SEGC.stor]);
  const ofl=[['Required (environment)',O.required,S_SEGC.req],
             ['Uncaptured (wet-year surplus)',O.uncaptured,S_SEGC.unc]];
  return [['Water sources',src],['Water uses',use],['Delta outflow',ofl]];
}
function trackHtml(segs,bmax,cls){
  let t='<div class="track'+(cls||'')+'">';
  for(const [lab,v,col] of segs){
    if(v<=0) continue;
    t+='<div class="seg" style="width:'+(v/bmax*100).toFixed(2)+'%;background:'+col+
       '" title="'+lab+': '+(v/1000).toFixed(1)+' maf"></div>';
  }
  return t+'</div>';
}
function drawBars(){
  const m=v=>(v/1000).toFixed(1);
  const titleOf=d=>
    ssel.t==='year' ? 'Water year '+d.wy+' — '+WYT_NAMES[d.wyt-1]
                    : (ssel.t==='wyt' ? 'Average '+d.name+' year'+(sidB?'':' ('+d.n+' of '+SD.years.length+')')
                                      : 'Average of all '+(sidB?'':d.n+' ')+'years');
  if(!sidB){                       // ===== single scenario (unchanged behavior)
    const d=sdata(); if(!d) return;
    document.getElementById('sseltitle').textContent = titleOf(d);
    const bars=segsFor(d);
    const bmax=Math.max(...bars.map(b=>b[1].reduce((s,x)=>s+x[1],0)));
    let html='', key='';
    for(const [name,segs] of bars){
      const tot=segs.reduce((s,x)=>s+x[1],0);
      html+='<div class="sbar"><div class="lbl"><span>'+name+'</span><span>'+m(tot)+' maf</span></div>'+
            trackHtml(segs,bmax);
      for(const [lab,v,col] of segs) if(v>0)
        key+='<span class="dot" style="background:'+col+'"></span>'+lab+' ('+m(v)+')<br>';
      html+='</div>';
    }
    document.getElementById('sbars').innerHTML=html;
    document.getElementById('skey').innerHTML=key;
    return;
  }
  // ===== comparing: one thin track per scenario in each group =====
  const dA=sdataOf(sidA), dB=sdataOf(sidB);
  const d0=dA||dB; if(!d0) return;   // shown side lacking simple data is handled by nosimple
  document.getElementById('sseltitle').textContent = titleOf(d0);
  const cap='<div class="cmpcap"><b class="ca">A '+sidA+'</b> vs <b class="cb">B '+sidB+'</b>'+
            (dA&&dB?'':' — '+(dA?sidB:sidA)+' has no annual summary for this selection')+'</div>';
  const barsA=dA?segsFor(dA):null, barsB=dB?segsFor(dB):null;
  const bmax=Math.max(...[barsA,barsB].filter(Boolean).flatMap(bs=>bs.map(b=>b[1].reduce((s,x)=>s+x[1],0))));
  let html=cap, key='';
  for(let g=0;g<3;g++){
    const name=(barsA||barsB)[g][0];
    const totA=barsA?barsA[g][1].reduce((s,x)=>s+x[1],0):null;
    const totB=barsB?barsB[g][1].reduce((s,x)=>s+x[1],0):null;
    html+='<div class="sbar"><div class="lbl"><span>'+name+'</span><span>'+
          '<b style="color:#1668a8">'+(totA==null?'–':m(totA))+'</b> / '+
          '<b style="color:#e07b28">'+(totB==null?'–':m(totB))+'</b> maf</span></div>';
    html+='<div class="trow"><span class="tl" style="color:#1668a8">A</span>'+
          (barsA?trackHtml(barsA[g][1],bmax,' thin'):'<span class="na">no data</span>')+'</div>';
    html+='<div class="trow"><span class="tl" style="color:#e07b28">B</span>'+
          (barsB?trackHtml(barsB[g][1],bmax,' thin'):'<span class="na">no data</span>')+'</div>';
    html+='</div>';
    // key: union of segment labels, A / B values side by side
    const labs=[], seen={};
    for(const bs of [barsA,barsB]) if(bs)
      for(const [lab,v,col] of bs[g][1]) if(v>0 && !seen[lab]){ seen[lab]=col; labs.push(lab); }
    for(const lab of labs){
      const vA=barsA&&(barsA[g][1].find(x=>x[0]===lab)||[])[1];
      const vB=barsB&&(barsB[g][1].find(x=>x[0]===lab)||[])[1];
      key+='<span class="dot" style="background:'+seen[lab]+'"></span>'+lab+
           ' ('+(vA>0?m(vA):'–')+' / '+(vB>0?m(vB):'–')+')<br>';
    }
  }
  document.getElementById('sbars').innerHTML=html;
  document.getElementById('skey').innerHTML=key;
}
function sRefresh(){ drawArrows(); drawBars(); }
function sFit(){  // frame CA in the space right of the panel (or below it on phones)
  const pnl=document.getElementById('simplepanel');
  const narrow=window.innerWidth<700;
  const padTL=narrow?[10,10]:[pnl.offsetWidth+28,10];
  const padBR=narrow?[10,pnl.offsetHeight+14]:[10,10]; // sheet sits at the bottom on phones
  map.fitBounds(S_BOUNDS,{animate:false,paddingTopLeft:padTL,paddingBottomRight:padBR});
}
function setMode(simple){
  simpleOn=simple;
  document.body.classList.toggle('simple',simple);
  document.body.classList.toggle('detailmode',!simple);
  for(const p of ['overlayPane','markerPane','shadowPane','tooltipPane','dupane']){
    const el=map.getPane(p); if(el) el.style.display=simple?'none':'';
  }
  pcv.style.display=simple?'none':'';
  sarrsvg.style.display=simple?'':'none';
  const ia=[map.dragging,map.scrollWheelZoom,map.doubleClickZoom,map.touchZoom,map.boxZoom,map.keyboard];
  if(simple){
    setPlaying(false); chartFeat=null; chartEl.style.display='none';
    for(const h of ia) h.disable();
    sFit();
    sRefresh();
  }else{
    for(const h of ia) h.enable();
    map.setView([38.3,-121.4],7,{animate:false});
    pclear();
    buildStrip(); updateStrip(cur);  // strip has zero size while hidden in simple mode
  }
  updateHash();  // hoisted from the scenario section; no-op until hashReady
}
let buildYearSel=null, updateWytUI=null, resetWytSel=null;
(function(){
  const bb=document.getElementById('wytbtns'), sel=document.getElementById('syear');
  const mk=(label,fn)=>{ const b=document.createElement('button'); b.textContent=label;
    b.onclick=()=>{ fn(); sel.value=''; upd(b); }; bb.appendChild(b); return b; };
  function upd(active){ for(const b of bb.children) b.classList.toggle('on',b===active); }
  const ball=mk('All years',()=>{ ssel={t:'all'}; sRefresh(); });
  for(let t=1;t<=5;t++){
    const b=mk(WYT_NAMES[t-1],()=>{ ssel={t:'wyt',v:String(t)}; sRefresh(); });
    b.dataset.t=String(t);
  }
  ball.classList.add('on');
  buildYearSel=function(){
    sel.innerHTML='<option value="">&mdash;</option>';
    if(!SD) return;
    for(const y of SD.years){
      const o=document.createElement('option'); o.value=y.wy;
      o.textContent=y.wy+' ('+WYT_NAMES[y.wyt-1]+')'; sel.appendChild(o);
    }
  };
  buildYearSel();
  updateWytUI=function(){  // a scenario's hydrology may have no years of some type
    for(const b of bb.children)
      if(b.dataset.t) b.disabled = !(SD && SD.composites[b.dataset.t]);
  };
  updateWytUI();
  resetWytSel=function(){ ssel={t:'all'}; sel.value=''; upd(ball); };
  sel.onchange=()=>{ if(sel.value==='') return;
    ssel={t:'year',v:+sel.value}; upd(null); sRefresh(); };
})();
document.getElementById('skeytoggle').onclick=function(){
  const open=document.getElementById('skey').classList.toggle('open');
  this.innerHTML='Breakdown '+(open?'&#9652;':'&#9662;');
  sFit();
};
document.getElementById('detailgo').onclick=()=>setMode(false);
document.getElementById('simplebtn').onclick=()=>setMode(true);
document.getElementById('aboutbtn2').onclick=aboutShow;
map.on('resize', ()=>{ if(simpleOn){ sFit(); sRefresh(); } });

// ===== scenario switching =====
// Feature geometry is fixed; a scenario swap only replaces the time series
// (arcs q, res s, pumps q, dus d, wyt, simple-mode payload) and re-renders.
// qref / capacity rings / particle speed scale stay frozen from the base
// scenario so widths and circle sizes are visually comparable across scenarios.
const SCEN = JSON.parse(document.getElementById('scenmeta').textContent);
const SCEN_DIR = 'scenarios/';
const HYD_SHORT = {hist:'Historical', cc50:'Moderate CC', cc95:'Severe CC'};
let curSid = 's0020', fetching = false;
const scenCache = { s0020: (()=>{   // snapshot of the embedded default
  const o={sid:'s0020',wyt:D.wyt,arcs:{},res:{},pumps:{},dus:{},simple:SD0};
  for(const a of D.arcs) o.arcs[a.i]=a.q;
  for(const a of (D.marcs||[])) o.arcs[a.i]=a.q;
  for(const r of D.res) o.res[r.i]=r.s;
  for(const p of D.pumps) o.pumps[p.i]=p.q;
  for(const u of D.dus) if(u.d) o.dus[u.i]=u.d;
  return o;
})() };
const runOf={}, themeOf={};
for(const t of SCEN.themes) for(const h in t.runs){
  runOf[t.w+'|'+h]=t.runs[h]; themeOf[t.runs[h]]=[t.w,h];
}
const NULLQ = D.months.map(()=>null), ZEROD = D.months.map(()=>0);

function applyScenario(data){
  for(const a of D.arcs) a.q = data.arcs[a.i]||NULLQ;
  for(const a of (D.marcs||[])) a.q = data.arcs[a.i]||NULLQ;
  for(const r of D.res) r.s = data.res[r.i]||NULLQ;
  for(const p of D.pumps) p.q = data.pumps[p.i]||NULLQ;
  for(const u of D.dus) if(u.d) u.d = data.dus[u.i]||ZEROD;
  D.wyt = data.wyt;
  SD = data.simple;
  document.body.classList.toggle('nosimple', !SD);
  buildYearSel(); updateWytUI();
  if(ssel.t!=='all' && (!SD || (ssel.t==='wyt' && !SD.composites[ssel.v]) ||
     (ssel.t==='year' && !SD.years.find(y=>y.wy===ssel.v)))) resetWytSel();
  recomputeStorage(); buildStrip();
  for(const el of document.querySelectorAll('.cursid')) el.textContent=data.sid;
  render(cur);
  if(simpleOn) sRefresh();
}

const pickers=[];
async function fetchScenario(sid){   // resolve a sid to cached data (shared busy UI)
  if(scenCache[sid]) return scenCache[sid];
  fetching=true;
  for(const p of pickers){ p.busy.style.display='block'; p.sel.disabled=true; }
  try{
    const rsp=await fetch(SCEN_DIR+sid+'.json');
    if(!rsp.ok) throw new Error('HTTP '+rsp.status);
    scenCache[sid]=await rsp.json();
    const keep=new Set(['s0020',sid,sidA,sidB]);   // never evict a side in use
    const extra=Object.keys(scenCache).filter(k=>!keep.has(k));
    while(extra.length>4) delete scenCache[extra.shift()];  // cap memory
    for(const p of pickers){ p.busy.style.display='none'; p.sel.disabled=false; }
    return scenCache[sid];
  }catch(e){
    for(const p of pickers){
      p.sel.disabled=false;
      p.busy.textContent = location.protocol==='file:'
        ? 'Other scenarios need the map served from its folder (with scenarios/) over http — or use the web version.'
        : 'Could not load scenario data — check your connection.';
      p.busy.style.display='block';
    }
    setTimeout(()=>{ for(const p of pickers){ p.busy.style.display='none';
      p.busy.textContent='Loading scenario…'; } }, 6000);
    throw e;
  }finally{ fetching=false; }
}
function refreshCompareViews(){   // everything that overlays B without flipping the map
  recomputeStorage(); buildStrip(); updateStrip(cur);
  if(chartFeat) drawChart();
  if(simpleOn) sRefresh();
}
function showSide(side){          // flip the whole map to one side (both are cached)
  shown = sidB ? side : 'A';
  curSid = shown==='B' ? sidB : sidA;
  applyScenario(scenCache[curSid]);
  syncPickers(); syncPills(); updateHash();
}
async function selectScenario(sid, side){
  side = side||'A';
  if(!sid || sid===(side==='B'?sidB:sidA) || fetching) return;
  try{ await fetchScenario(sid); }catch(e){ syncPickers(); return; }
  if(side==='B') sidB=sid; else sidA=sid;
  showSide(side);                 // touching a side's picker shows that side
}
function defaultB(){              // same theme, other hydrology (Eric, July 2026)
  const [w,h]=themeOf[sidA];
  const pref = h==='hist' ? ['cc50','cc95'] : ['hist', h==='cc50'?'cc95':'cc50'];
  for(const k of pref){ const s=runOf[w+'|'+k]; if(s) return s; }
  if(sidA!=='s0020') return 's0020';        // single-hydrology theme: vs baseline
  return runOf['2.1|hist'];                 // baseline itself: vs first policy theme
}
async function setCompare(sid){
  if(fetching || !sid || sid===sidA) return;
  try{ await fetchScenario(sid); }catch(e){ return; }
  sidB=sid;
  document.body.classList.add('comparing');
  refreshCompareViews(); syncPickers(); syncPills(); updateHash();
}
function clearCompare(){
  if(!sidB) return;
  const wasB = shown==='B';
  sidB=null; shown='A';
  document.body.classList.remove('comparing');
  if(wasB) showSide('A'); else{ refreshCompareViews(); updateHash(); }
  syncPickers(); syncPills();
}
// --- A/B pill groups (control bar + simple panel)
const pillGroups=[];
function buildPills(container){
  for(const s of ['A','B']){
    const b=document.createElement('button'); b.dataset.s=s; b.textContent=s;
    b.onclick=()=>{ if(sidB && shown!==s) showSide(s); };
    container.appendChild(b);
  }
  pillGroups.push(container);
}
function syncPills(){
  for(const g of pillGroups) for(const b of g.querySelectorAll('button')){
    b.classList.toggle('on', b.dataset.s===shown);
    b.title='Show scenario '+b.dataset.s+' ('+(b.dataset.s==='A'?sidA:(sidB||'–'))+') on the map';
  }
}
function buildPicker(container, side){
  const head=document.createElement('div'); head.className='scenhead';
  const lab=document.createElement('label');
  lab.textContent = side==='B' ? 'Scenario B' : 'Scenario';
  head.appendChild(lab);
  if(side==='A'){
    const cb=document.createElement('button'); cb.className='cmpbtn';
    cb.textContent='+ Compare'; cb.title='Add a second scenario to compare against';
    cb.onclick=()=>setCompare(defaultB());
    head.appendChild(cb);
  }else{
    const xb=document.createElement('button'); xb.className='cmpoff';
    xb.innerHTML='&times; stop comparing'; xb.onclick=clearCompare;
    head.appendChild(xb);
  }
  const sel=document.createElement('select');
  sel.title = side==='B' ? 'Scenario to compare against' : 'Choose a management scenario';
  for(const f in SCEN.families){
    const g=document.createElement('optgroup'); g.label=SCEN.families[f];
    let any=false;
    for(const t of SCEN.themes) if(t.f===f){
      const o=document.createElement('option'); o.value=t.w; o.textContent=t.label;
      g.appendChild(o); any=true;
    }
    if(any) sel.appendChild(g);
  }
  const hb=document.createElement('div'); hb.className='hydbtns';
  for(const h in SCEN.hyd){
    const b=document.createElement('button'); b.dataset.h=h;
    b.textContent=HYD_SHORT[h]||h; b.title=SCEN.hyd[h]+' hydrology';
    b.onclick=()=>{ if(b.disabled) return;
      selectScenario(runOf[sel.value+'|'+h], side); };
    hb.appendChild(b);
  }
  sel.onchange=()=>{
    const curHyd=themeOf[side==='B'?(sidB||sidA):sidA][1];
    const h = runOf[sel.value+'|'+curHyd] ? curHyd
            : Object.keys(SCEN.hyd).find(k=>runOf[sel.value+'|'+k]);
    selectScenario(runOf[sel.value+'|'+h], side);
  };
  const busy=document.createElement('div'); busy.className='busy';
  busy.textContent='Loading scenario…';
  container.append(head, sel, hb, busy);
  pickers.push({sel, hb, busy, side});
}
function syncPickers(){
  for(const p of pickers){
    const sid = p.side==='B' ? sidB : sidA;
    if(!sid) continue;                      // hidden B picker while not comparing
    const [w,h]=themeOf[sid];
    p.sel.value=w;
    for(const b of p.hb.children){
      b.classList.toggle('on', b.dataset.h===h);
      b.disabled = !runOf[w+'|'+b.dataset.h];
    }
  }
}
for(const id of ['scenrow1','scenrow2']){
  const row=document.getElementById(id);
  buildPicker(row,'A');
  const bwrap=document.createElement('div'); bwrap.className='scenrowB';
  buildPicker(bwrap,'B');
  row.appendChild(bwrap);
}
buildPills(document.getElementById('abpills1'));
buildPills(document.getElementById('abpills2'));
syncPickers(); syncPills();

// ===== URL hash: mode + scenario A/B, so links reproduce a comparison =====
// #detail            → detailed mode (backward compatible)
// #a=s0030&b=s0020   → comparison; v=b means the map is showing side B
let hashReady=false;
function updateHash(){
  if(!hashReady) return;
  const parts=[];
  if(!simpleOn) parts.push('detail');
  if(sidA!=='s0020') parts.push('a='+sidA);
  if(sidB){ parts.push('b='+sidB); if(shown==='B') parts.push('v=b'); }
  history.replaceState(null,'', parts.length ? '#'+parts.join('&')
                                             : location.pathname+location.search);
}
(function(){
  const P={}; let det=false;
  for(const t of location.hash.replace(/^#/,'').split('&')){
    if(t==='detail'){ det=true; continue; }
    const i=t.indexOf('='); if(i>0) P[t.slice(0,i)]=t.slice(i+1);
  }
  setMode(!det);   // setMode(simple)
  (async()=>{
    try{
      if(P.a && themeOf[P.a] && P.a!==sidA){
        await fetchScenario(P.a);
        sidA=P.a; showSide('A');
      }
      if(P.b && themeOf[P.b] && P.b!==sidA){
        await setCompare(P.b);
        if(P.v==='b' && sidB) showSide('B');
      }
    }catch(e){ /* fetch-failure message already shown by fetchScenario */ }
    hashReady=true; updateHash();
  })();
})();
</script>
</body>
</html>"""

html = (html.replace('__PAYLOAD__', payload).replace('__SIMPLE__', simple)
            .replace('__SCENMETA__', scenmeta))
open('CalSim3_water_map.html','w').write(html)
import os
print('HTML MB:', os.path.getsize('CalSim3_water_map.html')/1e6)
