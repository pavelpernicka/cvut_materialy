#include "system/web_server.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "drivers/pumps.h"
#include "drivers/sensors.h"
#include "drivers/shiftreg.h"
#include "engine/queue.h"
#include "engine/renderer.h"
#include "engine/show_model.h"
#include "engine/template_fields.h"
#include "engine/water_engine.h"
#include "esp_http_server.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "system/config.h"
#include "system/diagnostics.h"
#include "system/logger.h"
#include "system/storage.h"
#include "system/websocket.h"
#include "system/wifi_manager.h"

static const char *TAG = "web_server";
static httpd_handle_t s_httpd;
static const char *GUEST_HTML =
    "<!doctype html><html><head><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>Water Curtain</title>"
    "<style>"
    "body{font-family:sans-serif;background:#eef3f6;color:#10202c;margin:0}"
    "main{max-width:42rem;margin:0 auto;padding:1.5rem}"
    "textarea,input,button,select{font:inherit}textarea{width:100%;min-height:8rem}"
    ".card{background:#fff;padding:1rem;border-radius:1rem;box-shadow:0 8px 24px rgba(0,0,0,.08);margin-bottom:1rem}"
    "button{padding:.8rem 1rem;border:0;border-radius:.7rem;background:#0d6c91;color:#fff}.toolbar{display:flex;gap:.4rem;flex-wrap:wrap}.bitmap{overflow:auto;border:1px solid #c9d6dc;border-radius:1rem;background:#f8fbfc;padding:.5rem}.bitmap canvas{display:block;touch-action:none;background:#fff;border-radius:.8rem}"
    "pre{white-space:pre-wrap;word-break:break-word}"
    "</style></head><body><main>"
    "<section class='card'><h1>Water Curtain</h1><p>Napis text do vody nebo nakresli jednoduchou bitmapu.</p><label>Typ</label><select id='kind' onchange='toggleKind()'><option value='text'>text</option><option value='bitmap'>bitmap</option></select>"
    "<div id='text_box'><textarea id='txt' maxlength='32'>AHOJ {{time}}</textarea></div>"
    "<div id='bmp_box' style='display:none'><div class='toolbar'><button onclick='bitmapClear()'>Clear</button><button onclick='bitmapInvert()'>Invert</button></div><div class='bitmap'><canvas id='guest_bitmap'></canvas></div></div><br><button onclick='sendSplash()'>SPLASH</button></section>"
    "<section class='card'><h2>Fronta</h2><div id='guest_result'></div><pre id='queue'>nacitam...</pre></section>"
    "<script>"
    "let cols=32,rows=32,data=[],down=false,paint=true;"
    "function g(id){return document.getElementById(id)}"
    "function resizeBitmap(){const c=g('guest_bitmap');const cell=12;c.width=cols*cell;c.height=rows*cell;data=new Array(cols*rows).fill(false);drawBitmap()}"
    "function idx(x,y){return y*cols+x}"
    "function drawBitmap(){const c=g('guest_bitmap');const x=c.getContext('2d');const cell=c.width/cols;x.clearRect(0,0,c.width,c.height);for(let y=0;y<rows;y++){for(let xx=0;xx<cols;xx++){x.fillStyle=data[idx(xx,y)]?'#0d6c91':'#eef4f6';x.fillRect(xx*cell,y*cell,cell-1,cell-1)}}}"
    "function bitmapClear(){data.fill(false);drawBitmap()}function bitmapInvert(){data=data.map(v=>!v);drawBitmap()}"
    "function toCell(ev){const c=g('guest_bitmap');const r=c.getBoundingClientRect();const x=Math.floor((ev.clientX-r.left)/r.width*cols);const y=Math.floor((ev.clientY-r.top)/r.height*rows);if(x<0||y<0||x>=cols||y>=rows)return null;return{x,y}}"
    "function paintCell(ev){const p=toCell(ev);if(!p)return;data[idx(p.x,p.y)]=paint;drawBitmap();ev.preventDefault()}"
    "function encodeBitmap(){let out='';for(let x=0;x<cols;x++){let mask=0n;for(let y=0;y<rows;y++){if(data[idx(x,y)]){const b=BigInt(y*2);mask|=(1n<<b);mask|=(1n<<(b+1n));}}out+=mask.toString(16).padStart(16,'0')}return out}"
    "function initBitmap(){const c=g('guest_bitmap');c.addEventListener('pointerdown',ev=>{const p=toCell(ev);if(!p)return;down=true;paint=!data[idx(p.x,p.y)];paintCell(ev)});c.addEventListener('pointermove',ev=>{if(down)paintCell(ev)});window.addEventListener('pointerup',()=>down=false);resizeBitmap()}"
    "function toggleKind(){const bmp=g('kind').value==='bitmap';g('bmp_box').style.display=bmp?'block':'none';g('text_box').style.display=bmp?'none':'block'}"
    "async function refresh(){"
    "const q=await fetch('/api/queue').then(r=>r.json());"
    "document.getElementById('queue').textContent=JSON.stringify(q,null,2);"
    "}"
    "async function sendSplash(){"
    "const payload=g('kind').value==='bitmap'?{type:'bitmap',width:cols,bitmap:encodeBitmap()}:{type:'text',text:g('txt').value};"
    "const r=await fetch('/api/splash',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});"
    "const txt=await r.text();g('guest_result').textContent=txt;refresh();}"
    "initBitmap();toggleKind();refresh();setInterval(refresh,3000);"
    "</script></main></body></html>";
static const char *ADMIN_HTML =
    "<!doctype html><html><head><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1,maximum-scale=1'>"
    "<title>Water Curtain Admin</title>"
    "<style>"
    ":root{--bg:#edf3f4;--card:#ffffff;--ink:#102028;--muted:#58727d;--line:#c9d6dc;--accent:#0d6c91;--accent2:#d95f02;--on:#0f8b4c}"
    "*{box-sizing:border-box}body{margin:0;font-family:system-ui,sans-serif;background:linear-gradient(180deg,#edf3f4,#dfe9ec);color:var(--ink)}"
    "main{max-width:76rem;margin:0 auto;padding:1rem 1rem 3rem}"
    "h1{margin:.2rem 0 1rem;font-size:1.8rem}h2{margin:.1rem 0 .8rem;font-size:1.1rem}h3{margin:.8rem 0 .4rem;font-size:1rem}"
    ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(20rem,1fr));gap:1rem}.wide{grid-column:1/-1}"
    ".card{background:rgba(255,255,255,.96);padding:1rem;border-radius:1.15rem;box-shadow:0 12px 28px rgba(0,0,0,.08)}"
    "button,input,textarea,select{font:inherit}button{border:0;border-radius:1rem;background:var(--accent);color:#fff;padding:.9rem 1rem;margin:.2rem;min-height:2.9rem}"
    "button.alt{background:#5d7480}button.warn{background:var(--accent2)}button.good{background:var(--on)}"
    "input,textarea,select{width:100%;padding:.8rem .9rem;border:1px solid var(--line);border-radius:.9rem;background:#fff}"
    "label{display:block;font-size:.9rem;color:var(--muted);margin:.55rem 0 .22rem}"
    "textarea{min-height:6rem}pre{white-space:pre-wrap;word-break:break-word;background:#f5f8f9;padding:.8rem;border-radius:.9rem;border:1px solid var(--line)}"
    ".pill{display:inline-block;padding:.32rem .6rem;border-radius:999px;background:#eef6fa;color:#0b5977;margin:.15rem .2rem .15rem 0}"
    ".toolbar{display:flex;flex-wrap:wrap;gap:.35rem}.mini-grid{display:grid;grid-template-columns:1fr 1fr;gap:.75rem}.row{display:flex;gap:.6rem;flex-wrap:wrap;align-items:center}.muted{color:var(--muted);font-size:.92rem}"
    ".list{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:.8rem}.list button{background:#eff4f6;color:var(--ink);border:1px solid var(--line)}.list button.active{background:var(--accent);color:#fff}"
    ".stack{display:grid;gap:.45rem}.list-row{display:flex;gap:.35rem;align-items:center;flex-wrap:wrap}.list-row button{margin:0}.small{min-height:2.2rem;padding:.55rem .8rem;border-radius:.75rem}"
    ".playlist-editor{display:grid;gap:.45rem}.playlist-item{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:.45rem;align-items:center;padding:.55rem .65rem;background:#f5f8f9;border:1px solid var(--line);border-radius:.9rem}.playlist-item strong{display:block}.playlist-item .muted{font-size:.85rem}"
    ".bitmap-wrap{overflow:auto;border:1px solid var(--line);border-radius:1rem;background:#f8fbfc;padding:.5rem}.bitmap-wrap canvas{display:block;touch-action:none;background:#fff;border-radius:.8rem}"
    "@media (max-width:700px){main{padding:.8rem}.mini-grid{grid-template-columns:1fr}button{flex:1 1 auto}}"
    "</style></head><body><main><h1>Water Curtain Admin</h1><div class='grid'>"
    "<section class='card'><h2>Status</h2><div id='status_summary' class='muted'>nacitam...</div><pre id='status'>nacitam...</pre></section>"
    "<section class='card'><h2>Diagnostics</h2><div id='diag_summary' class='muted'>nacitam...</div><pre id='diagnostics'>nacitam...</pre></section>"
    "<section class='card'><h2>Ventily a Engine</h2><div class='toolbar'>"
    "<button onclick=\"post('/api/engine/start')\">Start show</button>"
    "<button onclick=\"post('/api/engine/pause')\">Pause</button>"
    "<button onclick=\"post('/api/engine/resume')\">Resume</button>"
    "<button onclick=\"post('/api/engine/stop')\">Stop</button>"
    "<button onclick=\"post('/api/valves/all_off')\">All off</button>"
    "<button onclick=\"post('/api/valves/clear_live')\">Clear live</button>"
    "<button onclick=\"post('/api/valves/all_on_pulse')\">All on pulse</button>"
    "<button onclick=\"post('/api/valves/chase')\">Chase</button></div>"
    "<div class='row'><input id='valve' type='number' min='0' max='63' value='0'><button onclick='singleValve()'>Single valve</button></div></section>"
    "<section class='card'><h2>Cerpadla</h2><div class='toolbar'>"
    "<button onclick=\"pumpAuto(1)\">Pump1 AUTO</button><button onclick=\"pump(1,true)\">Pump1 ON</button><button onclick=\"pump(1,false)\">Pump1 OFF</button>"
    "<button onclick=\"pumpAuto(2)\">Pump2 AUTO</button><button onclick=\"pump(2,true)\">Pump2 ON</button><button onclick=\"pump(2,false)\">Pump2 OFF</button>"
    "<button class='warn' onclick=\"post('/api/pumps/drain')\">Vypustit</button></div><div id='pump_summary' class='muted'></div><pre id='pumps'>nacitam...</pre></section>"
    "<section class='card'><h2>Sensors</h2><div id='water_summary' class='muted' style='margin-bottom:.7rem'></div><canvas id='currents' width='420' height='160' style='width:100%;border:1px solid var(--line);border-radius:.8rem;background:#fff'></canvas><pre id='sensors'>nacitam...</pre></section>"
    "<section class='card'><h2>Fronta</h2><div class='toolbar'><button onclick=\"post('/api/queue/clear')\">Clear queue</button></div><div id='queue_controls' class='stack muted'>nacitam...</div><pre id='queue'>nacitam...</pre></section>"
    "<section class='card wide'><h2>Pump Settings</h2><div class='mini-grid'><div><h3>Pump1</h3><label>Mode</label><select id='pump1_mode'><option value='off'>off</option><option value='two_level_sensors'>two_level_sensors</option><option value='high_level_only'>high_level_only</option><option value='timed_after_drain'>timed_after_drain</option><option value='pwm_interval'>pwm_interval</option></select><label>Max current A</label><input id='pump1_max_current_a' type='number' step='0.01'><label>Min current when on A</label><input id='pump1_min_current_a' type='number' step='0.01'><label>Fill timeout s</label><input id='pump1_fill_timeout_s2' type='number' min='0'><label>Interval period ms</label><input id='pump1_interval_period_ms' type='number' min='0'><label>Duty percent</label><input id='pump1_duty_percent' type='number' min='0' max='100'><label>Only after water used</label><select id='pump1_only_after_water_used'><option value='true'>true</option><option value='false'>false</option></select><div class='toolbar'><button class='good' onclick='savePumpConfig(1)'>Save pump1</button></div></div>"
    "<div><h3>Pump2</h3><label>Mode</label><select id='pump2_mode'><option value='off'>off</option><option value='two_level_sensors'>two_level_sensors</option><option value='high_level_only'>high_level_only</option><option value='timed_after_drain'>timed_after_drain</option><option value='pwm_interval'>pwm_interval</option></select><label>Max current A</label><input id='pump2_max_current_a' type='number' step='0.01'><label>Min current when on A</label><input id='pump2_min_current_a' type='number' step='0.01'><label>Fill timeout s</label><input id='pump2_fill_timeout_s2' type='number' min='0'><label>Interval period ms</label><input id='pump2_interval_period_ms' type='number' min='0'><label>Duty percent</label><input id='pump2_duty_percent' type='number' min='0' max='100'><label>Only after water used</label><select id='pump2_only_after_water_used'><option value='true'>true</option><option value='false'>false</option></select><div class='toolbar'><button class='good' onclick='savePumpConfig(2)'>Save pump2</button></div></div></div><pre id='pump_config_status'>nacitam...</pre></section>"
    "<section class='card wide'><h2>Screens</h2><div id='screen_list' class='list'></div>"
    "<div class='toolbar'><button onclick='newScreen(0)'>New text</button><button onclick='newScreen(1)'>New bitmap</button><button onclick='newScreen(2)'>New sensor</button><button onclick='newScreen(3)'>New clock</button><button onclick='newScreen(4)'>New test</button></div>"
    "<div id='screen_quick_actions' class='muted'>Klik na screen ho nacte do editoru. Tlacitko +Playlist ho prida do aktualniho playlistu.</div><div class='mini-grid'>"
    "<div><label>Screen id</label><input id='screen_id'><label>Name</label><input id='screen_name'><label>Type</label><select id='screen_type' onchange='screenTypeChanged()'><option value='0'>text</option><option value='1'>bitmap</option><option value='2'>sensor</option><option value='3'>clock</option><option value='4'>test</option></select><label>Duration ms na sloupec</label><input id='screen_duration_ms' type='number' min='1' value='35'><label>Hold ms na konci</label><input id='screen_hold_ms' type='number' min='0' value='0'><label>Repeat count</label><input id='screen_repeat_count' type='number' min='1' value='1'><label>Gap columns</label><input id='screen_gap_columns' type='number' min='0' value='6'><label>Layout</label><select id='screen_layout'><option value='0'>scroll</option><option value='1'>center</option><option value='2'>static</option></select><label>Enabled</label><select id='screen_enabled'><option value='true'>true</option><option value='false'>false</option></select><label>Rich text</label><select id='screen_rich_text'><option value='false'>false</option><option value='true'>true</option></select><label>Text / rich text / template</label><textarea id='screen_text' placeholder='AHOJ {{time}}'></textarea><div id='screen_hint' class='muted'>Rich text tagy: [speed=24], [gap=6], [pause=400], [reset]. Dlouhy text pouzij s layout=scroll.</div><div class='toolbar'><button class='good' onclick='saveScreen()'>Save screen</button><button onclick='previewScreen()'>Preview</button><button onclick='testScreen()'>Test screen</button><button class='warn' onclick='deleteScreen()'>Delete screen</button></div></div>"
    "<div><div id='bitmap_tools'><label>Bitmap columns</label><select id='bitmap_cols' onchange='bitmapColsChanged()'><option value='16'>16</option><option value='24'>24</option><option value='32' selected>32</option><option value='48'>48</option><option value='64'>64</option></select><div class='toolbar'><button onclick='bitmapClear()'>Clear</button><button onclick='bitmapInvert()'>Invert</button><button onclick='bitmapFill()'>Fill</button></div><div class='muted'>Touch mode: 32 radku pro kresleni prstem, firmware je pri ulozeni rozsiri na 64 ventilu.</div><div class='bitmap-wrap'><canvas id='bitmap_canvas'></canvas></div></div><h3>Nahled</h3><div class='bitmap-wrap'><canvas id='preview_canvas' width='576' height='140'></canvas></div><div id='preview_meta' class='muted'>Bez nahledu</div></div>"
    "</div></section>"
    "<section class='card wide'><h2>Playlists</h2><div id='playlist_list' class='list'></div><div class='mini-grid'><div><label>Playlist id</label><input id='playlist_id'><label>Name</label><input id='playlist_name'><label>Loop</label><select id='playlist_loop'><option value='true'>true</option><option value='false'>false</option></select><label>Default idle playlist</label><select id='playlist_default_idle'><option value='false'>false</option><option value='true'>true</option></select><label>Items</label><div id='playlist_editor' class='playlist-editor'></div><div class='toolbar'><button class='small' onclick='playlistAddCurrentScreen()'>Add current screen</button><button class='small alt' onclick='playlistSyncFromText()'>Import raw text</button><button class='small alt' onclick='playlistClear()'>Clear items</button></div><textarea id='playlist_items' placeholder='screen-clock|1|true&#10;screen-temp|2|true'></textarea><div class='muted'>Vizualni editor drzi poradi a repeat. Textarea zustava pro hromadne vlozeni nebo rychlou upravu.</div><div class='toolbar'><button class='good' onclick='savePlaylist()'>Save playlist</button><button onclick='startPlaylist()'>Start playlist</button><button class='warn' onclick='deletePlaylist()'>Delete playlist</button></div></div><div><h3>Dostupne screens</h3><div id='playlist_hint'></div><pre id='playlists'>nacitam...</pre></div></div></section>"
    "<section class='card wide'><h2>Config</h2><div class='mini-grid'><div>"
    "<label>Device name</label><input id='cfg_device_name'>"
    "<label>Wi-Fi mode</label><select id='cfg_wifi_mode'><option value='ap'>ap</option><option value='client'>client</option><option value='ap_client'>ap_client</option></select>"
    "<label>AP SSID</label><input id='cfg_ap_ssid'>"
    "<label>AP password</label><input id='cfg_ap_password'>"
    "<label>Client SSID</label><input id='cfg_client_ssid'>"
    "<label>Client password</label><input id='cfg_client_password'>"
    "</div><div>"
    "<label>Column period ms</label><input id='cfg_column_period_ms' type='number' min='1'>"
    "<label>Max queue</label><input id='cfg_max_queue' type='number' min='1' max='255'>"
    "<label>Max text length</label><input id='cfg_max_text_length' type='number' min='1' max='255'>"
    "<label>Level low invert</label><select id='cfg_level_low_invert'><option value='false'>false</option><option value='true'>true</option></select>"
    "<label>Level high invert</label><select id='cfg_level_high_invert'><option value='false'>false</option><option value='true'>true</option></select>"
    "<label>Level debounce ms</label><input id='cfg_level_debounce_ms' type='number' min='0'>"
    "<label>Pump1 fill timeout s</label><input id='cfg_pump1_fill_timeout_s' type='number' min='0'>"
    "<label>ADC current scale</label><input id='cfg_current_adc_scale' type='number' step='0.0001'>"
    "<label>ADC current offset</label><input id='cfg_current_adc_offset' type='number' step='0.0001'>"
    "</div></div><div class='toolbar'><button class='good' onclick='saveConfig()'>Apply config</button><button onclick=\"post('/api/config/save')\">Save to flash</button><button onclick='exportConfig()'>Export bundle</button><button onclick='importConfig()'>Import bundle</button><button class='warn' onclick='resetConfig()'>Factory reset</button></div><textarea id='config_bundle' placeholder='Sem vloz export bundle pro import'></textarea><pre id='config_status'>nacitam...</pre></section>"
    "<section class='card'><h2>Logs</h2><div class='toolbar'><button onclick='loadLogs()'>Refresh logs</button><button class='warn' onclick=\"post('/api/logs/clear')\">Clear logs</button></div><pre id='logs'>nacitam...</pre></section>"
    "<section class='card'><h2>System</h2><div class='toolbar'><button class='warn' onclick='if(confirm(\"Reboot?\"))post(\"/api/system/reboot\")'>Reboot</button><button class='warn' onclick='if(confirm(\"Factory reset?\"))post(\"/api/system/factory_reset\")'>Factory reset</button><button onclick='wifiReconnect()'>Wi-Fi reconnect</button></div><pre id='wifi'>nacitam...</pre></section>"
    "</div><script>"
    "let currentConfig=null;let screensCache=[];let playlistsCache=[];let playlistDraftItems=[];let bitmapCols=32;const bitmapRows=32;let bitmapData=[];let bitmapPointerDown=false;let bitmapPaintValue=true;let ws=null;"
    "async function post(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):''});const t=await r.text();refresh();return {ok:r.ok,text:t,status:r.status};}"
    "function el(id){return document.getElementById(id)}"
    "function setValue(id,value){el(id).value=(value===undefined||value===null)?'':value}"
    "function singleValve(){post('/api/valves/single',{valve:Number(el('valve').value||0)})}"
    "function pump(id,on){post(`/api/pumps/${id}/manual`,{on})}"
    "function pumpAuto(id){post(`/api/pumps/${id}/auto`,{enabled:true})}"
    "function typeName(v){if(v===0)return 'text'; if(v===1)return 'bitmap'; if(v===2)return 'sensor'; if(v===3)return 'clock'; if(v===4)return 'test'; return 'unknown'}"
    "function waterStateLabel(v){if(v===1)return 'LOW'; if(v===2)return 'FILLING'; if(v===3)return 'HIGH'; if(v===4)return 'ERROR'; return 'UNKNOWN'}"
    "function drawCurrents(s){const c=el('currents');const x=c.getContext('2d');x.clearRect(0,0,c.width,c.height);x.strokeStyle='#d8e2e8';x.strokeRect(0,0,c.width,c.height);const colors=['#0d6c91','#d95f02'];for(let k=0;k<2;k++){const arr=s.pump_current_history_a[k]||[];x.beginPath();x.strokeStyle=colors[k];for(let i=0;i<arr.length;i++){const px=(i/(Math.max(arr.length-1,1)))*(c.width-10)+5;const py=c.height-5-Math.min(arr[i]||0,5)/5*(c.height-10);if(i===0)x.moveTo(px,py);else x.lineTo(px,py)}x.stroke()}}"
    "function renderWaterSummary(s){el('water_summary').textContent=`Water state: ${waterStateLabel(s.water_state)} | low=${s.level_low} | high=${s.level_high} | AHT20=${s.aht20_present} | RTC=${s.rtc_present}`}"
    "function renderPumpSummary(p){const p1=p.pump1; const p2=p.pump2; el('pump_summary').textContent=`Pump1: ${p1.on?'ON':'OFF'} ${p1.auto_enabled?'AUTO':''} ${p1.manual_override?'MANUAL':''} ${p1.timed_out?'TIMEOUT':''} | Pump2: ${p2.on?'ON':'OFF'} ${p2.auto_enabled?'AUTO':''} ${p2.manual_override?'MANUAL':''} ${p2.timed_out?'TIMEOUT':''}`}"
    "function coreLabel(v){return v===255?'any':String(v)}"
    "function renderDiagnosticsSummary(d){el('diag_summary').textContent=`uptime ${Math.round((d.uptime_ms||0)/1000)} s | free heap ${(d.free_heap_bytes||0)} B | min ${(d.min_free_heap_bytes||0)} B | largest ${(d.largest_free_block_bytes||0)} B | sensor core ${coreLabel((d.task_core||[])[0]??255)} | engine core ${coreLabel((d.task_core||[])[3]??255)}`}"
    "function fillPumpConfigUi(cfg){['1','2'].forEach(n=>{const p=cfg.pumps[`pump${n}`];if(!p)return;setValue(`pump${n}_mode`,p.mode);setValue(`pump${n}_max_current_a`,p.max_current_a);setValue(`pump${n}_min_current_a`,p.min_current_when_on_a);setValue(`pump${n}_fill_timeout_s2`,p.fill_timeout_s);setValue(`pump${n}_interval_period_ms`,p.interval_period_ms);setValue(`pump${n}_duty_percent`,p.duty_percent);setValue(`pump${n}_only_after_water_used`,String(!!p.only_after_water_used))})}"
    "function fillConfig(cfg){currentConfig=cfg;setValue('cfg_device_name',cfg.device_name);setValue('cfg_wifi_mode',cfg.wifi.mode);setValue('cfg_ap_ssid',cfg.wifi.ap_ssid);setValue('cfg_ap_password',cfg.wifi.ap_password);setValue('cfg_client_ssid',cfg.wifi.client_ssid);setValue('cfg_client_password',cfg.wifi.client_password);setValue('cfg_column_period_ms',cfg.engine.column_period_ms);setValue('cfg_max_queue',cfg.exhibition.max_queue);setValue('cfg_max_text_length',cfg.exhibition.max_text_length);setValue('cfg_level_low_invert',String(cfg.sensors.level_low_invert));setValue('cfg_level_high_invert',String(cfg.sensors.level_high_invert));setValue('cfg_level_debounce_ms',cfg.sensors.level_debounce_ms);setValue('cfg_pump1_fill_timeout_s',cfg.sensors.pump1_fill_timeout_s);setValue('cfg_current_adc_scale',cfg.sensors.current_adc_scale);setValue('cfg_current_adc_offset',cfg.sensors.current_adc_offset);fillPumpConfigUi(cfg);el('config_status').textContent=JSON.stringify(cfg,null,2);el('pump_config_status').textContent=JSON.stringify(cfg.pumps,null,2)}"
    "async function loadConfig(){const cfg=await fetch('/api/config').then(r=>r.json());fillConfig(cfg)}"
    "async function saveConfig(){if(!currentConfig){return}const cfg=JSON.parse(JSON.stringify(currentConfig));cfg.device_name=el('cfg_device_name').value;cfg.wifi.mode=el('cfg_wifi_mode').value;cfg.wifi.ap_ssid=el('cfg_ap_ssid').value;cfg.wifi.ap_password=el('cfg_ap_password').value;cfg.wifi.client_ssid=el('cfg_client_ssid').value;cfg.wifi.client_password=el('cfg_client_password').value;cfg.engine.column_period_ms=Number(el('cfg_column_period_ms').value||35);cfg.engine.default_frame_duration_ms=cfg.engine.column_period_ms;cfg.exhibition.max_queue=Number(el('cfg_max_queue').value||50);cfg.exhibition.max_text_length=Number(el('cfg_max_text_length').value||32);cfg.sensors.level_low_invert=el('cfg_level_low_invert').value==='true';cfg.sensors.level_high_invert=el('cfg_level_high_invert').value==='true';cfg.sensors.level_debounce_ms=Number(el('cfg_level_debounce_ms').value||100);cfg.sensors.pump1_fill_timeout_s=Number(el('cfg_pump1_fill_timeout_s').value||60);cfg.sensors.current_adc_scale=Number(el('cfg_current_adc_scale').value||1);cfg.sensors.current_adc_offset=Number(el('cfg_current_adc_offset').value||0);const res=await post('/api/config',cfg);el('config_status').textContent=res.text;await loadConfig()}"
    "async function exportConfig(){const data=await fetch('/api/config/export').then(r=>r.json());el('config_bundle').value=JSON.stringify(data,null,2);el('config_status').textContent='bundle exported'}"
    "async function importConfig(){let payload={};try{payload=JSON.parse(el('config_bundle').value)}catch(e){el('config_status').textContent='invalid import json';return}const res=await post('/api/config/import',payload);el('config_status').textContent=res.text;await loadConfig();await loadScreens();await loadPlaylists();await refresh()}"
    "async function savePumpConfig(id){const payload={mode:el(`pump${id}_mode`).value,max_current_a:Number(el(`pump${id}_max_current_a`).value||5),min_current_when_on_a:Number(el(`pump${id}_min_current_a`).value||0.1),fill_timeout_s:Number(el(`pump${id}_fill_timeout_s2`).value||60),interval_period_ms:Number(el(`pump${id}_interval_period_ms`).value||10000),duty_percent:Number(el(`pump${id}_duty_percent`).value||40),only_after_water_used:el(`pump${id}_only_after_water_used`).value==='true',enabled:true};const res=await post(`/api/pumps/${id}/config`,payload);el('pump_config_status').textContent=res.text;await loadConfig();await refresh()}"
    "async function loadLogs(){const logs=await fetch('/api/logs').then(r=>r.json());el('logs').textContent=JSON.stringify(logs,null,2)}"
    "async function wifiReconnect(){await post('/api/wifi/reconnect')}"
    "async function loadWifi(){const wifi=await fetch('/api/wifi').then(r=>r.json());el('wifi').textContent=JSON.stringify(wifi,null,2)}"
    "function renderQueueControls(q){const box=el('queue_controls');const items=q.items||[];if(!items.length){box.textContent='fronta prazdna';return;}box.innerHTML='';items.forEach((item,idx)=>{const row=document.createElement('div');row.className='list-row';const text=document.createElement('span');text.textContent=`${idx+1}. ${item.id} (${item.author||'-'})`;const up=document.createElement('button');up.className='small';up.textContent='↑';up.onclick=()=>post('/api/queue/move',{id:item.id,direction:-1});const dn=document.createElement('button');dn.className='small';dn.textContent='↓';dn.onclick=()=>post('/api/queue/move',{id:item.id,direction:1});const del=document.createElement('button');del.className='small warn';del.textContent='X';del.onclick=()=>post('/api/queue/delete',{id:item.id});row.appendChild(text);row.appendChild(up);row.appendChild(dn);row.appendChild(del);box.appendChild(row)})}"
    "async function resetConfig(){await post('/api/config/reset');await loadConfig()}"
    "function bitmapResize(cols){bitmapCols=cols;el('bitmap_cols').value=String(cols);bitmapData=new Array(bitmapCols*bitmapRows).fill(false);const c=el('bitmap_canvas');const cell=18;c.width=bitmapCols*cell;c.height=bitmapRows*cell;drawBitmap()}"
    "function bitmapColsChanged(){bitmapResize(Number(el('bitmap_cols').value||32))}"
    "function bitmapIndex(x,y){return y*bitmapCols+x}"
    "function bitmapClear(){bitmapData.fill(false);drawBitmap()}"
    "function bitmapFill(){bitmapData.fill(true);drawBitmap()}"
    "function bitmapInvert(){bitmapData=bitmapData.map(v=>!v);drawBitmap()}"
    "function drawBitmap(){const c=el('bitmap_canvas');const g=c.getContext('2d');const cell=c.width/bitmapCols;g.clearRect(0,0,c.width,c.height);g.fillStyle='#fff';g.fillRect(0,0,c.width,c.height);for(let y=0;y<bitmapRows;y++){for(let x=0;x<bitmapCols;x++){g.fillStyle=bitmapData[bitmapIndex(x,y)]?'#0d6c91':'#eef4f6';g.fillRect(x*cell,y*cell,cell-1,cell-1)}}}"
    "function bitmapEventToCell(ev){const c=el('bitmap_canvas');const r=c.getBoundingClientRect();const x=Math.floor((ev.clientX-r.left)/r.width*bitmapCols);const y=Math.floor((ev.clientY-r.top)/r.height*bitmapRows);if(x<0||y<0||x>=bitmapCols||y>=bitmapRows)return null;return {x,y}}"
    "function bitmapPaint(ev){const p=bitmapEventToCell(ev);if(!p)return;bitmapData[bitmapIndex(p.x,p.y)]=bitmapPaintValue;drawBitmap();ev.preventDefault()}"
    "function initBitmapCanvas(){const c=el('bitmap_canvas');c.addEventListener('pointerdown',ev=>{const p=bitmapEventToCell(ev);if(!p)return;bitmapPointerDown=true;bitmapPaintValue=!bitmapData[bitmapIndex(p.x,p.y)];bitmapPaint(ev)});c.addEventListener('pointermove',ev=>{if(bitmapPointerDown)bitmapPaint(ev)});window.addEventListener('pointerup',()=>{bitmapPointerDown=false});bitmapResize(32)}"
    "function encodeBitmap(){let out='';for(let x=0;x<bitmapCols;x++){let mask=0n;for(let y=0;y<bitmapRows;y++){if(bitmapData[bitmapIndex(x,y)]){const b=BigInt(y*2);mask|=(1n<<b);mask|=(1n<<(b+1n));}}out+=mask.toString(16).padStart(16,'0')}return out}"
    "function decodeBitmap(frameCount,hex){const cols=Math.max(16,Math.min(Number(frameCount||32),64));bitmapResize(cols);if(!hex){drawBitmap();return}for(let x=0;x<bitmapCols;x++){const chunk=hex.slice(x*16,x*16+16);let mask=0n;try{mask=chunk?BigInt('0x'+chunk):0n}catch(e){mask=0n}for(let y=0;y<bitmapRows;y++){const b=BigInt(y*2);const on=((mask>>b)&1n)===1n||((mask>>(b+1n))&1n)===1n;bitmapData[bitmapIndex(x,y)]=on}}drawBitmap()}"
    "function screenTypeChanged(){const type=Number(el('screen_type').value||0);const showBitmap=type===1;el('bitmap_tools').style.display=showBitmap?'block':'none';el('screen_text').placeholder=type===3?'CAS {{time}}':(type===2?'T {{temp}} [gap=4] H {{humidity}}':'AHOJ {{time}}')}"
    "function readScreenForm(){const type=Number(el('screen_type').value||0);return{id:el('screen_id').value.trim(),name:el('screen_name').value.trim(),type,duration_ms:Number(el('screen_duration_ms').value||35),hold_ms:Number(el('screen_hold_ms').value||0),enabled:el('screen_enabled').value==='true',rich_text:el('screen_rich_text').value==='true',repeat_count:Number(el('screen_repeat_count').value||1),gap_columns:Number(el('screen_gap_columns').value||6),layout:Number(el('screen_layout').value||0),text:el('screen_text').value,bitmap_frames:type===1?bitmapCols:0,bitmap:type===1?encodeBitmap():''}}"
    "function fillScreenForm(screen){setValue('screen_id',screen.id);setValue('screen_name',screen.name);setValue('screen_type',screen.type);setValue('screen_duration_ms',screen.duration_ms||35);setValue('screen_hold_ms',screen.hold_ms||0);setValue('screen_repeat_count',screen.repeat_count||1);setValue('screen_gap_columns',screen.gap_columns||6);setValue('screen_layout',screen.layout||0);setValue('screen_enabled',String(screen.enabled));setValue('screen_rich_text',String(!!screen.rich_text));setValue('screen_text',screen.text||'');screenTypeChanged();if(screen.type===1){decodeBitmap(screen.bitmap_frames||32,screen.bitmap||'')}else{bitmapResize(Number(el('bitmap_cols').value||32))}}"
    "function newScreen(type){const id='screen-'+Date.now();fillScreenForm({id,name:'',type,duration_ms:35,enabled:true,text:'',bitmap_frames:32,bitmap:''})}"
    "function renderScreenList(){const box=el('screen_list');box.innerHTML='';screensCache.forEach((screen,idx)=>{const row=document.createElement('div');row.className='list-row';const pick=document.createElement('button');pick.textContent=`${screen.name||screen.id} [${typeName(screen.type)}]`;pick.className=`small ${el('screen_id').value===screen.id?'active':''}`;pick.onclick=()=>fillScreenForm(screen);const add=document.createElement('button');add.textContent='+ Playlist';add.className='small alt';add.onclick=()=>addScreenToPlaylist(screen.id);row.appendChild(pick);row.appendChild(add);box.appendChild(row);if(idx===0 && !el('screen_id').value){fillScreenForm(screen)}});el('playlist_hint').innerHTML=screensCache.map(s=>`<span class=\"pill\">${s.id}</span>`).join('')}"
    "async function loadScreens(){const res=await fetch('/api/screens').then(r=>r.json());screensCache=res.screens||[];renderScreenList()}"
    "function drawPreviewFrames(frames){const c=el('preview_canvas');const g=c.getContext('2d');const cols=Math.max(frames.length,1);const w=Math.max(4,Math.floor(c.width/cols));g.clearRect(0,0,c.width,c.height);g.fillStyle='#fff';g.fillRect(0,0,c.width,c.height);for(let i=0;i<frames.length;i++){let mask=0n;try{mask=BigInt('0x'+frames[i].mask)}catch(e){mask=0n}for(let y=0;y<64;y++){const on=((mask>>BigInt(y))&1n)===1n;g.fillStyle=on?'#0d6c91':'#eef4f6';g.fillRect(i*w,c.height-((y+1)*2),Math.max(1,w-1),2)}}}"
    "async function previewScreen(){const payload=readScreenForm();const res=await post('/api/screens/preview',payload);if(!res.ok){el('preview_meta').textContent=res.text;return}let data={};try{data=JSON.parse(res.text)}catch(e){el('preview_meta').textContent='Preview parse failed';return}drawPreviewFrames(data.frames||[]);el('preview_meta').textContent=`Frames: ${data.frame_count||0}`}"
    "async function saveScreen(){const payload=readScreenForm();const res=await post('/api/screens',payload);if(!res.ok){alert(res.text)}await loadScreens();await refresh();await previewScreen()}"
    "async function testScreen(){const id=el('screen_id').value.trim();if(!id)return;await post('/api/screens/test',{id})}"
    "async function deleteScreen(){const id=el('screen_id').value.trim();if(!id)return;if(!confirm(`Delete screen ${id}?`))return;const res=await post('/api/screens/delete',{id});if(!res.ok){alert(res.text)}setValue('screen_id','');await loadScreens()}"
    "function playlistLinesToItems(txt){return txt.split(/\\n+/).map(v=>v.trim()).filter(Boolean).map(line=>{const parts=line.split('|').map(v=>v.trim());return {screen_id:parts[0]||'',repeat_count:Math.max(1,Number(parts[1]||1)),enabled:(parts[2]||'true')!=='false'}}).filter(v=>v.screen_id)}"
    "function syncPlaylistTextarea(){el('playlist_items').value=playlistDraftItems.map(item=>`${item.screen_id}|${item.repeat_count||1}|${item.enabled!==false}`).join('\\n')}"
    "function renderPlaylistEditor(){const box=el('playlist_editor');box.innerHTML='';if(!playlistDraftItems.length){box.innerHTML=\"<div class='muted'>Playlist je prazdny. Pridej screen z horniho seznamu nebo pouzij Add current screen.</div>\";syncPlaylistTextarea();return;}playlistDraftItems.forEach((item,idx)=>{const row=document.createElement('div');row.className='playlist-item';const info=document.createElement('div');info.innerHTML=`<strong>${item.screen_id}</strong><div class='muted'>repeat ${item.repeat_count||1} | ${item.enabled!==false?'enabled':'disabled'}</div>`;const tools=document.createElement('div');tools.className='toolbar';[['↑',()=>playlistMove(idx,-1)],['↓',()=>playlistMove(idx,1)],['-R',()=>playlistRepeat(idx,-1)],['+R',()=>playlistRepeat(idx,1)],[item.enabled!==false?'Disable':'Enable',()=>playlistToggle(idx)],['X',()=>playlistRemove(idx)]].forEach(([label,fn])=>{const b=document.createElement('button');b.className='small';b.textContent=label;b.onclick=fn;tools.appendChild(b)});row.appendChild(info);row.appendChild(tools);box.appendChild(row)});syncPlaylistTextarea()}"
    "function fillPlaylistForm(p){setValue('playlist_id',p.id);setValue('playlist_name',p.name);setValue('playlist_loop',String(p.loop));setValue('playlist_default_idle',String(!!p.is_default_idle));playlistDraftItems=(p.items||[]).map(item=>({screen_id:item.screen_id,repeat_count:item.repeat_count||1,enabled:item.enabled!==false}));renderPlaylistEditor()}"
    "function playlistSyncFromText(){playlistDraftItems=playlistLinesToItems(el('playlist_items').value);renderPlaylistEditor()}"
    "function playlistClear(){playlistDraftItems=[];renderPlaylistEditor()}"
    "function playlistMove(idx,delta){const next=idx+delta;if(next<0||next>=playlistDraftItems.length)return;const tmp=playlistDraftItems[idx];playlistDraftItems[idx]=playlistDraftItems[next];playlistDraftItems[next]=tmp;renderPlaylistEditor()}"
    "function playlistRepeat(idx,delta){playlistDraftItems[idx].repeat_count=Math.max(1,Number(playlistDraftItems[idx].repeat_count||1)+delta);renderPlaylistEditor()}"
    "function playlistToggle(idx){playlistDraftItems[idx].enabled=!(playlistDraftItems[idx].enabled!==false);renderPlaylistEditor()}"
    "function playlistRemove(idx){playlistDraftItems.splice(idx,1);renderPlaylistEditor()}"
    "function addScreenToPlaylist(screenId){if(!screenId)return;playlistDraftItems.push({screen_id:screenId,repeat_count:1,enabled:true});renderPlaylistEditor()}"
    "function playlistAddCurrentScreen(){addScreenToPlaylist(el('screen_id').value.trim())}"
    "function renderPlaylistList(){const box=el('playlist_list');box.innerHTML='';playlistsCache.forEach((p,idx)=>{const b=document.createElement('button');b.textContent=`${p.name||p.id} (${(p.items||[]).length})`;b.className=el('playlist_id').value===p.id?'active':'';b.onclick=()=>fillPlaylistForm(p);box.appendChild(b);if(idx===0 && !el('playlist_id').value){fillPlaylistForm(p)}});el('playlists').textContent=JSON.stringify(playlistsCache,null,2)}"
    "async function loadPlaylists(){const res=await fetch('/api/playlists').then(r=>r.json());playlistsCache=res.playlists||[];renderPlaylistList()}"
    "async function savePlaylist(){const payload={id:el('playlist_id').value.trim(),name:el('playlist_name').value.trim(),loop:el('playlist_loop').value==='true',is_default_idle:el('playlist_default_idle').value==='true',items:playlistDraftItems};const res=await post('/api/playlists',payload);if(!res.ok){alert(res.text)}await loadPlaylists()}"
    "async function startPlaylist(){const id=el('playlist_id').value.trim();if(!id)return;await post('/api/playlists/start',{id})}"
    "async function deletePlaylist(){const id=el('playlist_id').value.trim();if(!id)return;if(!confirm(`Delete playlist ${id}?`))return;const res=await post('/api/playlists/delete',{id});if(!res.ok){alert(res.text)}setValue('playlist_id','');await loadPlaylists()}"
    "async function refresh(){const status=await fetch('/api/status').then(r=>r.json());const sensors=await fetch('/api/sensors').then(r=>r.json());const pumps=await fetch('/api/pumps').then(r=>r.json());const queue=await fetch('/api/queue').then(r=>r.json());const diagnostics=await fetch('/api/diagnostics').then(r=>r.json());el('status_summary').textContent=`IP ${status.ip} | mode ${status.mode} | engine ${status.engine_state} | queue ${status.queue_len} | playlist ${status.playlist_id||'-'} | screen ${status.screen_id||'-'}`;el('status').textContent=JSON.stringify(status,null,2);el('sensors').textContent=JSON.stringify(sensors,null,2);el('queue').textContent=JSON.stringify(queue,null,2);el('pumps').textContent=JSON.stringify(pumps,null,2);el('diagnostics').textContent=JSON.stringify(diagnostics,null,2);drawCurrents(sensors);renderWaterSummary(sensors);renderPumpSummary(pumps);renderDiagnosticsSummary(diagnostics);renderQueueControls(queue);await loadWifi()}"
    "function applyWsSnapshot(msg){if(!msg||msg.type!=='snapshot')return;el('status_summary').textContent=`IP ${msg.status.ip} | mode ${msg.status.mode} | engine ${msg.status.engine_state} | queue ${msg.status.queue_len} | playlist ${msg.engine?.playlist_id||'-'} | screen ${msg.engine?.screen_id||'-'}`;el('status').textContent=JSON.stringify({...msg.status,engine:msg.engine},null,2);el('sensors').textContent=JSON.stringify(msg.sensors,null,2);el('pumps').textContent=JSON.stringify(msg.pumps,null,2);if(msg.diagnostics){el('diagnostics').textContent=JSON.stringify(msg.diagnostics,null,2);renderDiagnosticsSummary(msg.diagnostics)}drawCurrents(msg.sensors);renderWaterSummary(msg.sensors);renderPumpSummary(msg.pumps)}"
    "function connectWs(){try{ws=new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/ws');ws.onmessage=ev=>{try{applyWsSnapshot(JSON.parse(ev.data))}catch(e){}};ws.onclose=()=>setTimeout(connectWs,1500)}catch(e){setTimeout(connectWs,1500)}}"
    "async function boot(){initBitmapCanvas();connectWs();el('playlist_items').addEventListener('change',playlistSyncFromText);await loadConfig();await loadScreens();await loadPlaylists();await refresh();await loadLogs();await previewScreen();setInterval(refresh,4000);setInterval(loadLogs,7000)}"
    "boot();"
    "</script></main></body></html>";

static esp_err_t respond_json(httpd_req_t *req, const char *json)
{
    httpd_resp_set_type(req, "application/json");
    return httpd_resp_sendstr(req, json);
}

static esp_err_t respond_html(httpd_req_t *req, const char *html)
{
    httpd_resp_set_type(req, "text/html; charset=utf-8");
    return httpd_resp_sendstr(req, html);
}

static esp_err_t respond_ok(httpd_req_t *req)
{
    return respond_json(req, "{\"ok\":true}");
}

static esp_err_t request_read_body(httpd_req_t *req, char *buf, size_t buf_size)
{
    if (buf == NULL || buf_size == 0) {
        return ESP_ERR_INVALID_ARG;
    }
    if (req->content_len <= 0) {
        buf[0] = '\0';
        return ESP_OK;
    }
    if ((size_t) req->content_len >= buf_size) {
        return ESP_ERR_INVALID_SIZE;
    }

    int ret = httpd_req_recv(req, buf, req->content_len);
    if (ret <= 0) {
        return ESP_FAIL;
    }
    buf[ret] = '\0';
    return ESP_OK;
}

static bool request_body_bool(const char *body, const char *key, bool default_value)
{
    char needle[32];
    snprintf(needle, sizeof(needle), "\"%s\":", key);
    const char *p = strstr(body, needle);
    if (p == NULL) {
        return default_value;
    }
    p += strlen(needle);
    while (*p == ' ' || *p == '\t') {
        ++p;
    }
    if (strncmp(p, "true", 4) == 0) {
        return true;
    }
    if (strncmp(p, "false", 5) == 0) {
        return false;
    }
    return default_value;
}

static int request_body_int(const char *body, const char *key, int default_value)
{
    char needle[32];
    snprintf(needle, sizeof(needle), "\"%s\":", key);
    const char *p = strstr(body, needle);
    if (p == NULL) {
        return default_value;
    }
    p += strlen(needle);
    return atoi(p);
}

static float request_body_float(const char *body, const char *key, float default_value)
{
    char needle[32];
    snprintf(needle, sizeof(needle), "\"%s\":", key);
    const char *p = strstr(body, needle);
    if (p == NULL) {
        return default_value;
    }
    p += strlen(needle);
    return strtof(p, NULL);
}

static void request_body_string(const char *body, const char *key, char *out, size_t out_size)
{
    char needle[32];
    snprintf(needle, sizeof(needle), "\"%s\":\"", key);
    const char *p = strstr(body, needle);
    if (p == NULL || out == NULL || out_size == 0) {
        if (out != NULL && out_size > 0) {
            out[0] = '\0';
        }
        return;
    }
    p += strlen(needle);
    size_t i = 0;
    while (p[i] != '\0' && p[i] != '"' && i + 1 < out_size) {
        out[i] = p[i];
        ++i;
    }
    out[i] = '\0';
}

static void response_send_screen_list(char *body, size_t body_size)
{
    int cursor = snprintf(body, body_size, "{\"ok\":true,\"screens\":[");
    for (size_t i = 0; i < show_model_get_screen_count(); ++i) {
        const screen_model_t *screen = show_model_get_screen_by_index(i);
        if (screen == NULL) continue;
        cursor += snprintf(body + cursor,
            body_size - (size_t) cursor,
            "%s{\"id\":\"%s\",\"name\":\"%s\",\"type\":%u,\"duration_ms\":%u,\"hold_ms\":%u,\"enabled\":%s,\"rich_text\":%s,"
            "\"repeat_count\":%u,\"gap_columns\":%u,\"layout\":%u,\"text\":\"%s\",\"bitmap_frames\":%u,\"bitmap\":\"%s\"}",
            i == 0 ? "" : ",",
            screen->id,
            screen->name,
            (unsigned) screen->type,
            (unsigned) screen->duration_ms,
            (unsigned) screen->hold_ms,
            screen->enabled ? "true" : "false",
            screen->rich_text ? "true" : "false",
            (unsigned) screen->repeat_count,
            (unsigned) screen->gap_columns,
            (unsigned) screen->layout,
            screen->text,
            (unsigned) screen->bitmap_frames,
            screen->bitmap);
    }
    snprintf(body + cursor, body_size - (size_t) cursor, "]}");
}

static void response_send_playlist_list(char *body, size_t body_size)
{
    int cursor = snprintf(body, body_size, "{\"ok\":true,\"playlists\":[");
    for (size_t i = 0; i < show_model_get_playlist_count(); ++i) {
        const playlist_model_t *playlist = show_model_get_playlist_by_index(i);
        if (playlist == NULL) continue;
        cursor += snprintf(body + cursor,
            body_size - (size_t) cursor,
            "%s{\"id\":\"%s\",\"name\":\"%s\",\"loop\":%s,\"is_default_idle\":%s,\"items\":[",
            i == 0 ? "" : ",",
            playlist->id,
            playlist->name,
            playlist->loop ? "true" : "false",
            playlist->is_default_idle ? "true" : "false");
        for (size_t j = 0; j < playlist->item_count; ++j) {
            cursor += snprintf(body + cursor,
                body_size - (size_t) cursor,
                "%s{\"screen_id\":\"%s\",\"enabled\":%s,\"repeat_count\":%u}",
                j == 0 ? "" : ",",
                playlist->items[j].screen_id,
                playlist->items[j].enabled ? "true" : "false",
                (unsigned) playlist->items[j].repeat_count);
        }
        cursor += snprintf(body + cursor, body_size - (size_t) cursor, "]}");
    }
    snprintf(body + cursor, body_size - (size_t) cursor, "]}");
}

static void parse_screen_from_body(const char *body, screen_model_t *screen)
{
    memset(screen, 0, sizeof(*screen));
    request_body_string(body, "id", screen->id, sizeof(screen->id));
    request_body_string(body, "name", screen->name, sizeof(screen->name));
    request_body_string(body, "text", screen->text, sizeof(screen->text));
    request_body_string(body, "bitmap", screen->bitmap, sizeof(screen->bitmap));
    screen->type = (screen_type_t) request_body_int(body, "type", SCREEN_TEXT);
    screen->duration_ms = (uint32_t) request_body_int(body, "duration_ms", 35);
    screen->hold_ms = (uint32_t) request_body_int(body, "hold_ms", 0);
    screen->enabled = request_body_bool(body, "enabled", true);
    screen->rich_text = request_body_bool(body, "rich_text", false);
    screen->repeat_count = (uint8_t) request_body_int(body, "repeat_count", 1);
    screen->gap_columns = (uint8_t) request_body_int(body, "gap_columns", 6);
    screen->layout = (screen_layout_t) request_body_int(body, "layout", SCREEN_LAYOUT_SCROLL);
    screen->bitmap_frames = (uint8_t) request_body_int(body, "bitmap_frames", 0);
}

static void parse_playlist_from_body(const char *body, playlist_model_t *playlist)
{
    memset(playlist, 0, sizeof(*playlist));
    request_body_string(body, "id", playlist->id, sizeof(playlist->id));
    request_body_string(body, "name", playlist->name, sizeof(playlist->name));
    playlist->loop = request_body_bool(body, "loop", true);
    playlist->is_default_idle = request_body_bool(body, "is_default_idle", false);
    const char *items = strstr(body, "\"items\":[");
    if (items != NULL) {
        items += strlen("\"items\":[");
        while ((items = strchr(items, '{')) != NULL && playlist->item_count < PLAYLIST_MAX_ITEMS) {
            playlist_item_t *item = &playlist->items[playlist->item_count];
            memset(item, 0, sizeof(*item));
            char screen_id[32];
            request_body_string(items, "screen_id", screen_id, sizeof(screen_id));
            snprintf(item->screen_id, sizeof(item->screen_id), "%s", screen_id);
            item->enabled = request_body_bool(items, "enabled", true);
            item->repeat_count = (uint8_t) request_body_int(items, "repeat_count", 1);
            ++playlist->item_count;
            ++items;
            if (strchr(items, ']') != NULL && strchr(items, '{') > strchr(items, ']')) {
                break;
            }
        }
    }
}

static esp_err_t guest_ui_get(httpd_req_t *req)
{
    return respond_html(req, GUEST_HTML);
}

static esp_err_t admin_ui_get(httpd_req_t *req)
{
    return respond_html(req, ADMIN_HTML);
}

static bool uri_extract_id(const char *uri, const char *prefix, const char *suffix, char *out, size_t out_size)
{
    if (uri == NULL || prefix == NULL || out == NULL || out_size == 0) {
        return false;
    }
    size_t prefix_len = strlen(prefix);
    if (strncmp(uri, prefix, prefix_len) != 0) {
        return false;
    }
    const char *start = uri + prefix_len;
    const char *end = suffix == NULL ? uri + strlen(uri) : strstr(start, suffix);
    if (end == NULL || end <= start) {
        return false;
    }
    size_t len = (size_t) (end - start);
    if (len >= out_size) {
        len = out_size - 1;
    }
    memcpy(out, start, len);
    out[len] = '\0';
    return true;
}

static esp_err_t api_status_get(httpd_req_t *req)
{
    char body[640];
    water_engine_status_t engine = water_engine_get_status();
    const sensor_snapshot_t *s = sensors_get_cached();
    snprintf(body,
        sizeof(body),
        "{\"ok\":true,\"ip\":\"%s\",\"mode\":\"%s\",\"queue_len\":%u,"
        "\"engine_state\":%u,\"frame_period_ms\":%u,\"level_low\":%s,"
        "\"level_high\":%s,\"water_state\":%u,\"temp\":%.1f,\"humidity\":%.1f,"
        "\"engine_core\":%u,\"playlist_id\":\"%s\",\"screen_id\":\"%s\"}",
        wifi_manager_get_ip(),
        wifi_manager_get_mode(),
        (unsigned) queue_len(),
        (unsigned) engine.state,
        (unsigned) engine.frame_period_ms,
        s->level_low ? "true" : "false",
        s->level_high ? "true" : "false",
        (unsigned) s->water_state,
        (double) s->temperature_c,
        (double) s->humidity_pct,
        (unsigned) engine.core_id,
        engine.playlist_id,
        engine.screen_id);
    return respond_json(req, body);
}

static esp_err_t api_diagnostics_get(httpd_req_t *req)
{
    char body[768];
    diagnostics_snapshot_t snapshot;
    if (diagnostics_get_snapshot(&snapshot) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"diag_snapshot_failed\"}");
    }
    snprintf(body,
        sizeof(body),
        "{\"ok\":true,\"uptime_ms\":%" PRIu64 ",\"reset_reason\":%u,"
        "\"free_heap_bytes\":%u,\"min_free_heap_bytes\":%u,\"largest_free_block_bytes\":%u,"
        "\"task_core\":[%u,%u,%u,%u],\"task_stack_hwm_words\":[%u,%u,%u,%u]}",
        snapshot.uptime_ms,
        (unsigned) snapshot.reset_reason,
        (unsigned) snapshot.free_heap_bytes,
        (unsigned) snapshot.min_free_heap_bytes,
        (unsigned) snapshot.largest_free_block_bytes,
        (unsigned) snapshot.task_core[DIAG_TASK_SENSOR],
        (unsigned) snapshot.task_core[DIAG_TASK_LED],
        (unsigned) snapshot.task_core[DIAG_TASK_WEBSOCKET],
        (unsigned) snapshot.task_core[DIAG_TASK_ENGINE],
        (unsigned) snapshot.task_stack_hwm_words[DIAG_TASK_SENSOR],
        (unsigned) snapshot.task_stack_hwm_words[DIAG_TASK_LED],
        (unsigned) snapshot.task_stack_hwm_words[DIAG_TASK_WEBSOCKET],
        (unsigned) snapshot.task_stack_hwm_words[DIAG_TASK_ENGINE]);
    return respond_json(req, body);
}

static esp_err_t api_sensors_get(httpd_req_t *req)
{
    char body[1400];
    const sensor_snapshot_t *s = sensors_get_cached();
    int cursor = snprintf(body,
        sizeof(body),
        "{\"ok\":true,\"level_low\":%s,\"level_high\":%s,\"water_state\":%u,"
        "\"aht20_present\":%s,\"rtc_present\":%s,"
        "\"adc_valid\":[%s,%s,%s],\"adc_raw\":[%d,%d,%d],"
        "\"pump1_current\":%.3f,\"pump2_current\":%.3f,\"temp\":%.1f,"
        "\"humidity\":%.1f,\"unix_time\":%" PRIu64 ","
        "\"pump_current_history_a\":[[",
        s->level_low ? "true" : "false",
        s->level_high ? "true" : "false",
        (unsigned) s->water_state,
        s->aht20_present ? "true" : "false",
        s->rtc_present ? "true" : "false",
        s->adc_valid[0] ? "true" : "false",
        s->adc_valid[1] ? "true" : "false",
        s->adc_valid[2] ? "true" : "false",
        s->adc_raw[0],
        s->adc_raw[1],
        s->adc_raw[2],
        (double) s->pump_currents_a[0],
        (double) s->pump_currents_a[1],
        (double) s->temperature_c,
        (double) s->humidity_pct,
        s->unix_time);
    for (size_t i = 0; i < SENSOR_HISTORY_LEN; ++i) {
        size_t idx = (s->history_head + 1U + i) % SENSOR_HISTORY_LEN;
        cursor += snprintf(body + cursor, sizeof(body) - (size_t) cursor, "%s%.3f", i == 0 ? "" : ",", (double) s->pump_current_history_a[0][idx]);
    }
    cursor += snprintf(body + cursor, sizeof(body) - (size_t) cursor, "],[");
    for (size_t i = 0; i < SENSOR_HISTORY_LEN; ++i) {
        size_t idx = (s->history_head + 1U + i) % SENSOR_HISTORY_LEN;
        cursor += snprintf(body + cursor, sizeof(body) - (size_t) cursor, "%s%.3f", i == 0 ? "" : ",", (double) s->pump_current_history_a[1][idx]);
    }
    snprintf(body + cursor, sizeof(body) - (size_t) cursor, "]]}");
    return respond_json(req, body);
}

static esp_err_t api_pumps_get(httpd_req_t *req)
{
    char body[1024];
    pump_state_t p1;
    pump_state_t p2;
    pumps_get_state(0, &p1);
    pumps_get_state(1, &p2);
    snprintf(body,
        sizeof(body),
        "{\"ok\":true,\"pump1\":{\"on\":%s,\"mode\":%u,\"manual_override\":%s,\"auto_enabled\":%s,\"timed_out\":%s,\"current\":%.3f,\"max_current\":%.3f,"
        "\"min_current\":%.3f,\"interval_period_ms\":%u,\"duty_percent\":%u,\"only_after_water_used\":%s,\"fault_overcurrent\":%s,\"fault_undercurrent\":%s,"
        "\"last_switch_ms\":%" PRIu64 ",\"last_runtime_ms\":%u,\"last_reason\":\"%s\"},"
        "\"pump2\":{\"on\":%s,\"mode\":%u,\"manual_override\":%s,\"auto_enabled\":%s,\"timed_out\":%s,\"current\":%.3f,\"max_current\":%.3f,"
        "\"min_current\":%.3f,\"interval_period_ms\":%u,\"duty_percent\":%u,\"only_after_water_used\":%s,\"fault_overcurrent\":%s,\"fault_undercurrent\":%s,"
        "\"last_switch_ms\":%" PRIu64 ",\"last_runtime_ms\":%u,\"last_reason\":\"%s\"}}",
        p1.output_on ? "true" : "false",
        (unsigned) p1.mode,
        p1.manual_override ? "true" : "false",
        p1.auto_enabled ? "true" : "false",
        p1.timed_out ? "true" : "false",
        (double) p1.current_a,
        (double) p1.max_current_a,
        (double) p1.min_current_when_on_a,
        (unsigned) p1.interval_period_ms,
        (unsigned) p1.duty_percent,
        p1.only_after_water_used ? "true" : "false",
        p1.fault_overcurrent ? "true" : "false",
        p1.fault_undercurrent ? "true" : "false",
        p1.last_switch_ms,
        (unsigned) p1.last_runtime_ms,
        p1.last_reason,
        p2.output_on ? "true" : "false",
        (unsigned) p2.mode,
        p2.manual_override ? "true" : "false",
        p2.auto_enabled ? "true" : "false",
        p2.timed_out ? "true" : "false",
        (double) p2.current_a,
        (double) p2.max_current_a,
        (double) p2.min_current_when_on_a,
        (unsigned) p2.interval_period_ms,
        (unsigned) p2.duty_percent,
        p2.only_after_water_used ? "true" : "false",
        p2.fault_overcurrent ? "true" : "false",
        p2.fault_undercurrent ? "true" : "false",
        p2.last_switch_ms,
        (unsigned) p2.last_runtime_ms,
        p2.last_reason);
    return respond_json(req, body);
}

static esp_err_t api_pump_config_post(httpd_req_t *req, uint8_t index)
{
    char body[768];
    pump_config_model_t cfg = *(index == 0 ? &config_get()->pumps.pump1 : &config_get()->pumps.pump2);
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    cfg.enabled = request_body_bool(body, "enabled", cfg.enabled);
    request_body_string(body, "mode", cfg.mode, sizeof(cfg.mode));
    cfg.invert_output = request_body_bool(body, "invert_output", cfg.invert_output);
    cfg.max_current_a = request_body_float(body, "max_current_a", cfg.max_current_a);
    cfg.min_current_when_on_a = request_body_float(body, "min_current_when_on_a", cfg.min_current_when_on_a);
    cfg.fill_timeout_s = (uint32_t) request_body_int(body, "fill_timeout_s", (int) cfg.fill_timeout_s);
    cfg.interval_period_ms = (uint32_t) request_body_int(body, "interval_period_ms", (int) cfg.interval_period_ms);
    cfg.duty_percent = (uint8_t) request_body_int(body, "duty_percent", cfg.duty_percent);
    cfg.only_after_water_used = request_body_bool(body, "only_after_water_used", cfg.only_after_water_used);
    if (pumps_set_config(index, &cfg) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"pump_config_failed\"}");
    }
    logger_event(LOG_CAT_SYSTEM, "pump%u config updated", (unsigned) index + 1);
    return respond_ok(req);
}

static esp_err_t api_pump1_config_post(httpd_req_t *req) { return api_pump_config_post(req, 0); }
static esp_err_t api_pump2_config_post(httpd_req_t *req) { return api_pump_config_post(req, 1); }

static esp_err_t api_wifi_get(httpd_req_t *req)
{
    char body[384];
    wifi_status_t wifi = wifi_manager_get_status();
    snprintf(body,
        sizeof(body),
        "{\"ok\":true,\"mode\":\"%s\",\"ip\":\"%s\",\"ssid\":\"%s\",\"rssi\":%d,"
        "\"sta_has_ip\":%s,\"ap_active\":%s,\"fallback_ap\":%s}",
        wifi.mode,
        wifi.ip,
        wifi.ssid,
        (int) wifi.rssi,
        wifi.sta_has_ip ? "true" : "false",
        wifi.ap_active ? "true" : "false",
        wifi.fallback_ap ? "true" : "false");
    return respond_json(req, body);
}

static esp_err_t api_wifi_post(httpd_req_t *req)
{
    char body[1024];
    app_config_t cfg = *config_get();
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    request_body_string(body, "mode", cfg.wifi.mode, sizeof(cfg.wifi.mode));
    request_body_string(body, "ap_ssid", cfg.wifi.ap_ssid, sizeof(cfg.wifi.ap_ssid));
    request_body_string(body, "ap_password", cfg.wifi.ap_password, sizeof(cfg.wifi.ap_password));
    request_body_string(body, "client_ssid", cfg.wifi.client_ssid, sizeof(cfg.wifi.client_ssid));
    request_body_string(body, "client_password", cfg.wifi.client_password, sizeof(cfg.wifi.client_password));
    cfg.wifi.fallback_ap = request_body_bool(body, "fallback_ap", cfg.wifi.fallback_ap);
    config_set(&cfg);
    if (wifi_manager_apply_config(&cfg.wifi) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"wifi_apply_failed\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_wifi_reconnect_post(httpd_req_t *req)
{
    if (wifi_manager_reconnect() != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"wifi_reconnect_failed\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_sensors_raw_get(httpd_req_t *req)
{
    char body[512];
    const sensor_snapshot_t *s = sensors_get_cached();
    snprintf(body,
        sizeof(body),
        "{\"ok\":true,\"level_raw\":{\"low\":%s,\"high\":%s},\"adc_raw\":[%d,%d,%d],"
        "\"adc_valid\":[%s,%s,%s],\"current_scale\":%.5f,\"current_offset\":%.5f}",
        s->level_low ? "true" : "false",
        s->level_high ? "true" : "false",
        s->adc_raw[0],
        s->adc_raw[1],
        s->adc_raw[2],
        s->adc_valid[0] ? "true" : "false",
        s->adc_valid[1] ? "true" : "false",
        s->adc_valid[2] ? "true" : "false",
        (double) config_get()->sensors.current_adc_scale,
        (double) config_get()->sensors.current_adc_offset);
    return respond_json(req, body);
}

static esp_err_t api_sensors_calibrate_post(httpd_req_t *req)
{
    char body[512];
    app_config_t cfg = *config_get();
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    const char *scale = strstr(body, "\"current_adc_scale\":");
    const char *offset = strstr(body, "\"current_adc_offset\":");
    if (scale != NULL) {
        cfg.sensors.current_adc_scale = strtof(scale + strlen("\"current_adc_scale\":"), NULL);
    }
    if (offset != NULL) {
        cfg.sensors.current_adc_offset = strtof(offset + strlen("\"current_adc_offset\":"), NULL);
    }
    cfg.sensors.level_low_invert = request_body_bool(body, "level_low_invert", cfg.sensors.level_low_invert);
    cfg.sensors.level_high_invert = request_body_bool(body, "level_high_invert", cfg.sensors.level_high_invert);
    cfg.sensors.level_debounce_ms = (uint32_t) request_body_int(body, "level_debounce_ms", (int) cfg.sensors.level_debounce_ms);
    config_set(&cfg);
    return respond_ok(req);
}

static esp_err_t api_pump_auto(httpd_req_t *req, uint8_t index)
{
    char body[128];
    bool enabled = true;
    if (request_read_body(req, body, sizeof(body)) == ESP_OK && body[0] != '\0') {
        enabled = request_body_bool(body, "enabled", true);
    }
    if (pumps_set_auto(index, enabled) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"pump_auto_failed\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_pump1_auto_post(httpd_req_t *req) { return api_pump_auto(req, 0); }
static esp_err_t api_pump2_auto_post(httpd_req_t *req) { return api_pump_auto(req, 1); }

static esp_err_t api_pumps_drain_post(httpd_req_t *req)
{
    water_engine_status_t status = water_engine_get_status();
    if (status.state == WATER_ENGINE_PLAYING_SHOW || status.state == WATER_ENGINE_PLAYING_GUEST_ITEM) {
        httpd_resp_set_status(req, "409 Conflict");
        return respond_json(req, "{\"ok\":false,\"error\":\"engine_busy\"}");
    }
    pumps_all_off();
    ESP_ERROR_CHECK(water_engine_drain_pulse(1500));
    pumps_start_drain_cooldown(3000);
    return respond_ok(req);
}

static esp_err_t api_queue_delete_post(httpd_req_t *req)
{
    char body[128];
    char id[32];
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    request_body_string(body, "id", id, sizeof(id));
    if (queue_remove_by_id(id) != ESP_OK) {
        httpd_resp_set_status(req, "404 Not Found");
        return respond_json(req, "{\"ok\":false,\"error\":\"queue_item_not_found\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_queue_move_post(httpd_req_t *req)
{
    char body[128];
    char id[32];
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    request_body_string(body, "id", id, sizeof(id));
    int direction = request_body_int(body, "direction", -1);
    if (queue_move_by_id(id, direction) != ESP_OK) {
        httpd_resp_set_status(req, "404 Not Found");
        return respond_json(req, "{\"ok\":false,\"error\":\"queue_move_failed\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_queue_item_delete(httpd_req_t *req)
{
    char id[32];
    if (!uri_extract_id(req->uri, "/api/queue/", NULL, id, sizeof(id))) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_queue_uri\"}");
    }
    if (queue_remove_by_id(id) != ESP_OK) {
        httpd_resp_set_status(req, "404 Not Found");
        return respond_json(req, "{\"ok\":false,\"error\":\"queue_item_not_found\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_queue_item_move_post(httpd_req_t *req)
{
    char id[32];
    if (!uri_extract_id(req->uri, "/api/queue/", "/move", id, sizeof(id))) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_queue_uri\"}");
    }
    char body[64];
    int direction = -1;
    if (request_read_body(req, body, sizeof(body)) == ESP_OK && body[0] != '\0') {
        direction = request_body_int(body, "direction", -1);
    }
    if (queue_move_by_id(id, direction) != ESP_OK) {
        httpd_resp_set_status(req, "404 Not Found");
        return respond_json(req, "{\"ok\":false,\"error\":\"queue_move_failed\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_screens_get(httpd_req_t *req)
{
    char body[8192];
    response_send_screen_list(body, sizeof(body));
    return respond_json(req, body);
}

static esp_err_t api_screens_post(httpd_req_t *req)
{
    char body[2048];
    screen_model_t screen = {0};
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    parse_screen_from_body(body, &screen);
    if (show_model_upsert_screen(&screen) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"screen_save_failed\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_screen_preview_post(httpd_req_t *req)
{
    char body[2048];
    screen_model_t screen = {0};
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    parse_screen_from_body(body, &screen);
    rendered_sequence_t sequence = {0};
    if (renderer_render_screen(&screen, &sequence) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"preview_failed\"}");
    }
    char response[4096];
    int cursor = snprintf(response, sizeof(response), "{\"ok\":true,\"frame_count\":%u,\"frames\":[", (unsigned) sequence.frame_count);
    size_t limit = sequence.frame_count > 96 ? 96 : sequence.frame_count;
    for (size_t i = 0; i < limit; ++i) {
        cursor += snprintf(response + cursor, sizeof(response) - (size_t) cursor, "%s{\"mask\":\"%016" PRIx64 "\",\"duration_ms\":%u}",
            i == 0 ? "" : ",",
            sequence.frames[i].valves,
            (unsigned) sequence.frames[i].duration_ms);
    }
    snprintf(response + cursor, sizeof(response) - (size_t) cursor, "]}");
    renderer_free_sequence(&sequence);
    return respond_json(req, response);
}

static esp_err_t api_screen_test_post(httpd_req_t *req)
{
    char body[128];
    char id[32];
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    request_body_string(body, "id", id, sizeof(id));
    if (water_engine_play_screen_now(id) != ESP_OK) {
        httpd_resp_set_status(req, "404 Not Found");
        return respond_json(req, "{\"ok\":false,\"error\":\"screen_not_found\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_screen_delete_post(httpd_req_t *req)
{
    char body[128];
    char id[32];
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    request_body_string(body, "id", id, sizeof(id));
    if (show_model_delete_screen(id) != ESP_OK) {
        httpd_resp_set_status(req, "404 Not Found");
        return respond_json(req, "{\"ok\":false,\"error\":\"screen_not_found\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_screens_item_get(httpd_req_t *req)
{
    char id[32];
    if (!uri_extract_id(req->uri, "/api/screens/", NULL, id, sizeof(id))) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_screen_uri\"}");
    }
    const screen_model_t *screen = show_model_get_screen_by_id(id);
    if (screen == NULL) {
        httpd_resp_set_status(req, "404 Not Found");
        return respond_json(req, "{\"ok\":false,\"error\":\"screen_not_found\"}");
    }
    char body[2048];
    snprintf(body,
        sizeof(body),
        "{\"ok\":true,\"id\":\"%s\",\"name\":\"%s\",\"type\":%u,\"duration_ms\":%u,\"hold_ms\":%u,\"enabled\":%s,\"rich_text\":%s,"
        "\"repeat_count\":%u,\"gap_columns\":%u,\"layout\":%u,\"text\":\"%s\",\"bitmap_frames\":%u,\"bitmap\":\"%s\"}",
        screen->id,
        screen->name,
        (unsigned) screen->type,
        (unsigned) screen->duration_ms,
        (unsigned) screen->hold_ms,
        screen->enabled ? "true" : "false",
        screen->rich_text ? "true" : "false",
        (unsigned) screen->repeat_count,
        (unsigned) screen->gap_columns,
        (unsigned) screen->layout,
        screen->text,
        (unsigned) screen->bitmap_frames,
        screen->bitmap);
    return respond_json(req, body);
}

static esp_err_t api_screens_item_put(httpd_req_t *req)
{
    char body[2048];
    screen_model_t screen = {0};
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    parse_screen_from_body(body, &screen);
    if (screen.id[0] == '\0') {
        uri_extract_id(req->uri, "/api/screens/", NULL, screen.id, sizeof(screen.id));
    }
    if (show_model_upsert_screen(&screen) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"screen_save_failed\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_screens_item_delete(httpd_req_t *req)
{
    char id[32];
    if (!uri_extract_id(req->uri, "/api/screens/", NULL, id, sizeof(id))) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_screen_uri\"}");
    }
    if (show_model_delete_screen(id) != ESP_OK) {
        httpd_resp_set_status(req, "404 Not Found");
        return respond_json(req, "{\"ok\":false,\"error\":\"screen_not_found\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_screens_item_test_post(httpd_req_t *req)
{
    char id[32];
    if (!uri_extract_id(req->uri, "/api/screens/", "/test", id, sizeof(id))) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_screen_uri\"}");
    }
    if (water_engine_play_screen_now(id) != ESP_OK) {
        httpd_resp_set_status(req, "404 Not Found");
        return respond_json(req, "{\"ok\":false,\"error\":\"screen_not_found\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_playlists_get(httpd_req_t *req)
{
    char body[4096];
    response_send_playlist_list(body, sizeof(body));
    return respond_json(req, body);
}

static esp_err_t api_playlists_post(httpd_req_t *req)
{
    char body[2048];
    playlist_model_t playlist = {0};
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    parse_playlist_from_body(body, &playlist);
    if (show_model_upsert_playlist(&playlist) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"playlist_save_failed\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_playlist_start_post(httpd_req_t *req)
{
    char body[128];
    char id[32];
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    request_body_string(body, "id", id, sizeof(id));
    if (water_engine_start_playlist(id) != ESP_OK) {
        httpd_resp_set_status(req, "404 Not Found");
        return respond_json(req, "{\"ok\":false,\"error\":\"playlist_not_found\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_playlist_delete_post(httpd_req_t *req)
{
    char body[128];
    char id[32];
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    request_body_string(body, "id", id, sizeof(id));
    if (show_model_delete_playlist(id) != ESP_OK) {
        httpd_resp_set_status(req, "404 Not Found");
        return respond_json(req, "{\"ok\":false,\"error\":\"playlist_not_found\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_playlists_item_get(httpd_req_t *req)
{
    char id[32];
    if (!uri_extract_id(req->uri, "/api/playlists/", NULL, id, sizeof(id))) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_playlist_uri\"}");
    }
    const playlist_model_t *playlist = show_model_get_playlist_by_id(id);
    if (playlist == NULL) {
        httpd_resp_set_status(req, "404 Not Found");
        return respond_json(req, "{\"ok\":false,\"error\":\"playlist_not_found\"}");
    }
    char body[1024];
    int cursor = snprintf(body, sizeof(body), "{\"ok\":true,\"id\":\"%s\",\"name\":\"%s\",\"loop\":%s,\"is_default_idle\":%s,\"items\":[",
        playlist->id, playlist->name, playlist->loop ? "true" : "false", playlist->is_default_idle ? "true" : "false");
    for (size_t i = 0; i < playlist->item_count; ++i) {
        cursor += snprintf(body + cursor, sizeof(body) - (size_t) cursor, "%s{\"screen_id\":\"%s\",\"enabled\":%s,\"repeat_count\":%u}",
            i == 0 ? "" : ",", playlist->items[i].screen_id, playlist->items[i].enabled ? "true" : "false", (unsigned) playlist->items[i].repeat_count);
    }
    snprintf(body + cursor, sizeof(body) - (size_t) cursor, "]}");
    return respond_json(req, body);
}

static esp_err_t api_playlists_item_put(httpd_req_t *req)
{
    char body[2048];
    playlist_model_t playlist = {0};
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    parse_playlist_from_body(body, &playlist);
    if (playlist.id[0] == '\0') {
        uri_extract_id(req->uri, "/api/playlists/", NULL, playlist.id, sizeof(playlist.id));
    }
    if (show_model_upsert_playlist(&playlist) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"playlist_save_failed\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_playlists_item_delete(httpd_req_t *req)
{
    char id[32];
    if (!uri_extract_id(req->uri, "/api/playlists/", NULL, id, sizeof(id))) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_playlist_uri\"}");
    }
    if (show_model_delete_playlist(id) != ESP_OK) {
        httpd_resp_set_status(req, "404 Not Found");
        return respond_json(req, "{\"ok\":false,\"error\":\"playlist_not_found\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_playlists_item_start_post(httpd_req_t *req)
{
    char id[32];
    if (!uri_extract_id(req->uri, "/api/playlists/", "/start", id, sizeof(id))) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_playlist_uri\"}");
    }
    if (water_engine_start_playlist(id) != ESP_OK) {
        httpd_resp_set_status(req, "404 Not Found");
        return respond_json(req, "{\"ok\":false,\"error\":\"playlist_not_found\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_config_get(httpd_req_t *req)
{
    char *json = NULL;
    if (config_to_json(config_get(), &json) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"config_serialize_failed\"}");
    }
    esp_err_t err = respond_json(req, json);
    free(json);
    return err;
}

static esp_err_t api_config_post(httpd_req_t *req)
{
    char body[2048];
    app_config_t new_config;
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    if (config_from_json(body, &new_config) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_json\"}");
    }
    config_set(&new_config);
    return respond_ok(req);
}

static esp_err_t api_config_save_post(httpd_req_t *req)
{
    if (storage_save_config(config_get()) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"save_failed\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_config_export_get(httpd_req_t *req)
{
    char *config_json = NULL;
    char screens_json[12288];
    char playlists_json[8192];
    char body[24576];
    if (config_to_json(config_get(), &config_json) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"config_export_failed\"}");
    }
    if (show_model_export_json(screens_json, sizeof(screens_json), playlists_json, sizeof(playlists_json)) != ESP_OK) {
        free(config_json);
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"show_export_failed\"}");
    }
    snprintf(body, sizeof(body), "{\"ok\":true,\"config\":%s,\"screens\":%s,\"playlists\":%s}", config_json, screens_json, playlists_json);
    free(config_json);
    return respond_json(req, body);
}

static esp_err_t api_config_import_post(httpd_req_t *req)
{
    char body[24576];
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    const char *cfg_ptr = strstr(body, "\"config\":");
    const char *screens_ptr = strstr(body, "\"screens\":");
    const char *playlists_ptr = strstr(body, "\"playlists\":");
    if (cfg_ptr == NULL || screens_ptr == NULL || playlists_ptr == NULL) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"missing_bundle_parts\"}");
    }

    app_config_t imported;
    if (config_from_json(cfg_ptr + strlen("\"config\":"), &imported) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_config_bundle\"}");
    }

    const char *screens_start = strchr(screens_ptr, '[');
    const char *playlists_start = strchr(playlists_ptr, '[');
    const char *screens_end = playlists_start == NULL ? NULL : playlists_start - 1;
    if (screens_start == NULL || playlists_start == NULL || screens_end == NULL) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_show_bundle\"}");
    }
    size_t screens_len = (size_t) (screens_end - screens_start);
    size_t playlists_len = strlen(playlists_start);
    char *screens_json = calloc(screens_len + 2U, 1U);
    char *playlists_json = calloc(playlists_len + 1U, 1U);
    if (screens_json == NULL || playlists_json == NULL) {
        free(screens_json);
        free(playlists_json);
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"no_mem\"}");
    }
    memcpy(screens_json, screens_start, screens_len);
    screens_json[screens_len] = '\0';
    memcpy(playlists_json, playlists_start, playlists_len);
    playlists_json[playlists_len] = '\0';

    config_set(&imported);
    if (storage_save_config(&imported) != ESP_OK || show_model_import_json(screens_json, playlists_json) != ESP_OK) {
        free(screens_json);
        free(playlists_json);
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"import_failed\"}");
    }
    free(screens_json);
    free(playlists_json);
    logger_event(LOG_CAT_SYSTEM, "config bundle imported");
    return respond_ok(req);
}

static esp_err_t api_config_reset_post(httpd_req_t *req)
{
    app_config_t defaults;
    config_load_defaults(&defaults);
    config_set(&defaults);
    if (storage_save_config(&defaults) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"reset_save_failed\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_pump_manual(httpd_req_t *req, uint8_t index)
{
    char body[128];
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    bool on = request_body_bool(body, "on", false);
    if (pumps_set_manual(index, on) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"pump_manual_failed\"}");
    }
    return respond_ok(req);
}

static esp_err_t api_pump1_manual_post(httpd_req_t *req)
{
    return api_pump_manual(req, 0);
}

static esp_err_t api_pump2_manual_post(httpd_req_t *req)
{
    return api_pump_manual(req, 1);
}

static esp_err_t api_engine_start_post(httpd_req_t *req)
{
    ESP_ERROR_CHECK(water_engine_start());
    return respond_ok(req);
}

static esp_err_t api_engine_stop_post(httpd_req_t *req)
{
    ESP_ERROR_CHECK(water_engine_stop());
    return respond_ok(req);
}

static esp_err_t api_engine_pause_post(httpd_req_t *req)
{
    ESP_ERROR_CHECK(water_engine_pause());
    return respond_ok(req);
}

static esp_err_t api_engine_resume_post(httpd_req_t *req)
{
    ESP_ERROR_CHECK(water_engine_resume());
    return respond_ok(req);
}

static esp_err_t api_engine_next_post(httpd_req_t *req)
{
    ESP_ERROR_CHECK(water_engine_next());
    return respond_ok(req);
}

static esp_err_t api_engine_all_off_post(httpd_req_t *req)
{
    ESP_ERROR_CHECK(water_engine_all_off());
    return respond_ok(req);
}

static esp_err_t api_valves_all_off_post(httpd_req_t *req)
{
    ESP_ERROR_CHECK(water_engine_all_off());
    return respond_ok(req);
}

static esp_err_t api_valves_clear_live_post(httpd_req_t *req)
{
    ESP_ERROR_CHECK(water_engine_stop());
    return respond_ok(req);
}

static esp_err_t api_valves_all_on_pulse_post(httpd_req_t *req)
{
    shiftreg_self_test_all_on(400);
    return respond_ok(req);
}

static esp_err_t api_valves_chase_post(httpd_req_t *req)
{
    shiftreg_self_test_chase(40);
    return respond_ok(req);
}

static esp_err_t api_valves_single_post(httpd_req_t *req)
{
    char body[128];
    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }
    int valve = request_body_int(body, "valve", 0);
    if (valve < 0 || valve > 63) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_valve\"}");
    }
    ESP_ERROR_CHECK(water_engine_set_live_mask(1ULL << valve));
    return respond_ok(req);
}

static esp_err_t api_queue_get(httpd_req_t *req)
{
    char body[1024];
    size_t len = queue_len();
    int cursor = snprintf(body, sizeof(body), "{\"ok\":true,\"len\":%u,\"items\":[", (unsigned) len);
    for (size_t i = 0; i < len && cursor > 0 && (size_t) cursor < sizeof(body); ++i) {
        queue_item_t item;
        if (queue_peek(&item, i) != ESP_OK) {
            continue;
        }
        cursor += snprintf(body + cursor,
            sizeof(body) - (size_t) cursor,
            "%s{\"id\":\"%s\",\"author\":\"%s\",\"priority\":%u,\"duration_ms\":%u}",
            i == 0 ? "" : ",",
            item.id,
            item.author,
            (unsigned) item.priority,
            (unsigned) item.estimated_duration_ms);
    }
    snprintf(body + cursor, sizeof(body) - (size_t) cursor, "]}");
    return respond_json(req, body);
}

static esp_err_t api_queue_clear_post(httpd_req_t *req)
{
    queue_clear();
    return respond_ok(req);
}

static esp_err_t api_logs_get(httpd_req_t *req)
{
    char body[12288];
    logger_snapshot_json(body, sizeof(body));
    return respond_json(req, body);
}

static esp_err_t api_logs_clear_post(httpd_req_t *req)
{
    logger_clear();
    return respond_ok(req);
}

static esp_err_t api_system_reboot_post(httpd_req_t *req)
{
    respond_ok(req);
    logger_event(LOG_CAT_SYSTEM, "system reboot requested");
    esp_restart();
    return ESP_OK;
}

static esp_err_t api_system_factory_reset_post(httpd_req_t *req)
{
    app_config_t defaults;
    config_load_defaults(&defaults);
    config_set(&defaults);
    if (storage_save_config(&defaults) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"factory_reset_failed\"}");
    }
    logger_clear();
    logger_event(LOG_CAT_SYSTEM, "factory reset applied");
    return respond_ok(req);
}

static esp_err_t api_splash_post(httpd_req_t *req)
{
    char body[2048];
    char text[96];
    char rendered[128];
    queue_item_t item = {0};
    static uint64_t s_last_guest_request_ms;

    if (request_read_body(req, body, sizeof(body)) != ESP_OK) {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"invalid_body\"}");
    }

    const app_config_t *cfg = config_get();
    uint64_t now_ms = (uint64_t) (esp_timer_get_time() / 1000ULL);
    if (cfg->exhibition.cooldown_s > 0 && now_ms < s_last_guest_request_ms + (uint64_t) cfg->exhibition.cooldown_s * 1000ULL) {
        httpd_resp_set_status(req, "429 Too Many Requests");
        return respond_json(req, "{\"ok\":false,\"error\":\"cooldown\"}");
    }

    bool bitmap_mode = strstr(body, "\"type\":\"bitmap\"") != NULL;
    request_body_string(body, "text", text, sizeof(text));
    if (!bitmap_mode && text[0] == '\0') {
        httpd_resp_set_status(req, "400 Bad Request");
        return respond_json(req, "{\"ok\":false,\"error\":\"missing_text\"}");
    }

    snprintf(item.id, sizeof(item.id), "guest-%" PRIu64, (uint64_t) esp_timer_get_time());
    snprintf(item.author, sizeof(item.author), "guest");
    snprintf(item.source_ip, sizeof(item.source_ip), "web");
    item.priority = 3;
    item.created_ms = (uint64_t) esp_timer_get_time() / 1000ULL;
    item.estimated_duration_ms = 3000;
    screen_model_t splash_screen = { .duration_ms = 35, .enabled = true };
    snprintf(splash_screen.id, sizeof(splash_screen.id), "%s", item.id);
    snprintf(splash_screen.name, sizeof(splash_screen.name), "Guest splash");
    if (bitmap_mode) {
        if (!cfg->exhibition.allow_bitmap) {
            httpd_resp_set_status(req, "403 Forbidden");
            return respond_json(req, "{\"ok\":false,\"error\":\"bitmap_disabled\"}");
        }
        splash_screen.type = SCREEN_BITMAP;
        splash_screen.bitmap_frames = (uint8_t) request_body_int(body, "width", 32);
        request_body_string(body, "bitmap", splash_screen.bitmap, sizeof(splash_screen.bitmap));
        snprintf(rendered, sizeof(rendered), "bitmap");
    } else {
        if (template_fields_render(text, rendered, sizeof(rendered)) != ESP_OK) {
            httpd_resp_set_status(req, "500 Internal Server Error");
            return respond_json(req, "{\"ok\":false,\"error\":\"render_failed\"}");
        }
        splash_screen.type = SCREEN_TEXT;
        snprintf(splash_screen.text, sizeof(splash_screen.text), "%s", rendered);
    }
    if (renderer_render_screen(&splash_screen, &item.sequence) != ESP_OK) {
        httpd_resp_set_status(req, "500 Internal Server Error");
        return respond_json(req, "{\"ok\":false,\"error\":\"sequence_render_failed\"}");
    }
    if (item.sequence.frame_count > 0) {
        item.estimated_duration_ms = (uint32_t) item.sequence.frame_count * 35U;
    }

    if (queue_push(&item) != ESP_OK) {
        renderer_free_sequence(&item.sequence);
        httpd_resp_set_status(req, "429 Too Many Requests");
        return respond_json(req, "{\"ok\":false,\"error\":\"queue_full\"}");
    }
    s_last_guest_request_ms = now_ms;
    logger_event(LOG_CAT_GUEST, "guest splash queued id=%s type=%s pos=%u", item.id, bitmap_mode ? "bitmap" : "text", (unsigned) queue_len());

    char response[256];
    snprintf(response,
        sizeof(response),
        "{\"ok\":true,\"id\":\"%s\",\"position\":%u,\"estimated_wait_ms\":%u,\"preview\":\"%s\"}",
        item.id,
        (unsigned) queue_len(),
        (unsigned) (queue_len() * item.estimated_duration_ms),
        rendered);
    return respond_json(req, response);
}

esp_err_t web_server_start(void)
{
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 80;
    config.stack_size = 12288;
    config.uri_match_fn = httpd_uri_match_wildcard;

    if (httpd_start(&s_httpd, &config) != ESP_OK) {
        return ESP_FAIL;
    }

    httpd_uri_t root = {
        .uri = "/",
        .method = HTTP_GET,
        .handler = guest_ui_get,
    };
    httpd_uri_t admin = {
        .uri = "/admin",
        .method = HTTP_GET,
        .handler = admin_ui_get,
    };
    httpd_uri_t status = {
        .uri = "/api/status",
        .method = HTTP_GET,
        .handler = api_status_get,
    };
    httpd_uri_t diagnostics = {
        .uri = "/api/diagnostics",
        .method = HTTP_GET,
        .handler = api_diagnostics_get,
    };
    httpd_uri_t sensors = {
        .uri = "/api/sensors",
        .method = HTTP_GET,
        .handler = api_sensors_get,
    };
    httpd_uri_t sensors_raw = {
        .uri = "/api/sensors/raw",
        .method = HTTP_GET,
        .handler = api_sensors_raw_get,
    };
    httpd_uri_t sensors_calibrate = {
        .uri = "/api/sensors/calibrate",
        .method = HTTP_POST,
        .handler = api_sensors_calibrate_post,
    };
    httpd_uri_t pumps = {
        .uri = "/api/pumps",
        .method = HTTP_GET,
        .handler = api_pumps_get,
    };
    httpd_uri_t wifi_get_uri = {
        .uri = "/api/wifi",
        .method = HTTP_GET,
        .handler = api_wifi_get,
    };
    httpd_uri_t wifi_post_uri = {
        .uri = "/api/wifi",
        .method = HTTP_POST,
        .handler = api_wifi_post,
    };
    httpd_uri_t wifi_reconnect_uri = {
        .uri = "/api/wifi/reconnect",
        .method = HTTP_POST,
        .handler = api_wifi_reconnect_post,
    };
    httpd_uri_t config_get_uri = {
        .uri = "/api/config",
        .method = HTTP_GET,
        .handler = api_config_get,
    };
    httpd_uri_t config_post_uri = {
        .uri = "/api/config",
        .method = HTTP_POST,
        .handler = api_config_post,
    };
    httpd_uri_t config_save_uri = {
        .uri = "/api/config/save",
        .method = HTTP_POST,
        .handler = api_config_save_post,
    };
    httpd_uri_t config_export_uri = {
        .uri = "/api/config/export",
        .method = HTTP_GET,
        .handler = api_config_export_get,
    };
    httpd_uri_t config_import_uri = {
        .uri = "/api/config/import",
        .method = HTTP_POST,
        .handler = api_config_import_post,
    };
    httpd_uri_t config_reset_uri = {
        .uri = "/api/config/reset",
        .method = HTTP_POST,
        .handler = api_config_reset_post,
    };
    httpd_uri_t pump1_manual = {
        .uri = "/api/pumps/1/manual",
        .method = HTTP_POST,
        .handler = api_pump1_manual_post,
    };
    httpd_uri_t pump1_auto = {
        .uri = "/api/pumps/1/auto",
        .method = HTTP_POST,
        .handler = api_pump1_auto_post,
    };
    httpd_uri_t pump1_config = {
        .uri = "/api/pumps/1/config",
        .method = HTTP_POST,
        .handler = api_pump1_config_post,
    };
    httpd_uri_t pump2_manual = {
        .uri = "/api/pumps/2/manual",
        .method = HTTP_POST,
        .handler = api_pump2_manual_post,
    };
    httpd_uri_t pump2_auto = {
        .uri = "/api/pumps/2/auto",
        .method = HTTP_POST,
        .handler = api_pump2_auto_post,
    };
    httpd_uri_t pump2_config = {
        .uri = "/api/pumps/2/config",
        .method = HTTP_POST,
        .handler = api_pump2_config_post,
    };
    httpd_uri_t pumps_drain = {
        .uri = "/api/pumps/drain",
        .method = HTTP_POST,
        .handler = api_pumps_drain_post,
    };
    httpd_uri_t queue_get = {
        .uri = "/api/queue",
        .method = HTTP_GET,
        .handler = api_queue_get,
    };
    httpd_uri_t queue_clear = {
        .uri = "/api/queue/clear",
        .method = HTTP_POST,
        .handler = api_queue_clear_post,
    };
    httpd_uri_t queue_delete = {
        .uri = "/api/queue/delete",
        .method = HTTP_POST,
        .handler = api_queue_delete_post,
    };
    httpd_uri_t queue_move = {
        .uri = "/api/queue/move",
        .method = HTTP_POST,
        .handler = api_queue_move_post,
    };
    httpd_uri_t queue_item_delete = {
        .uri = "/api/queue/*",
        .method = HTTP_DELETE,
        .handler = api_queue_item_delete,
    };
    httpd_uri_t queue_item_move = {
        .uri = "/api/queue/*/move",
        .method = HTTP_POST,
        .handler = api_queue_item_move_post,
    };
    httpd_uri_t splash = {
        .uri = "/api/splash",
        .method = HTTP_POST,
        .handler = api_splash_post,
    };
    httpd_uri_t logs_get = {
        .uri = "/api/logs",
        .method = HTTP_GET,
        .handler = api_logs_get,
    };
    httpd_uri_t logs_clear = {
        .uri = "/api/logs/clear",
        .method = HTTP_POST,
        .handler = api_logs_clear_post,
    };
    httpd_uri_t screens = {
        .uri = "/api/screens",
        .method = HTTP_GET,
        .handler = api_screens_get,
    };
    httpd_uri_t screens_post = {
        .uri = "/api/screens",
        .method = HTTP_POST,
        .handler = api_screens_post,
    };
    httpd_uri_t screens_test = {
        .uri = "/api/screens/test",
        .method = HTTP_POST,
        .handler = api_screen_test_post,
    };
    httpd_uri_t screens_preview = {
        .uri = "/api/screens/preview",
        .method = HTTP_POST,
        .handler = api_screen_preview_post,
    };
    httpd_uri_t screens_delete = {
        .uri = "/api/screens/delete",
        .method = HTTP_POST,
        .handler = api_screen_delete_post,
    };
    httpd_uri_t screens_item_get = {
        .uri = "/api/screens/*",
        .method = HTTP_GET,
        .handler = api_screens_item_get,
    };
    httpd_uri_t screens_item_put = {
        .uri = "/api/screens/*",
        .method = HTTP_PUT,
        .handler = api_screens_item_put,
    };
    httpd_uri_t screens_item_delete = {
        .uri = "/api/screens/*",
        .method = HTTP_DELETE,
        .handler = api_screens_item_delete,
    };
    httpd_uri_t screens_item_test = {
        .uri = "/api/screens/*/test",
        .method = HTTP_POST,
        .handler = api_screens_item_test_post,
    };
    httpd_uri_t playlists = {
        .uri = "/api/playlists",
        .method = HTTP_GET,
        .handler = api_playlists_get,
    };
    httpd_uri_t playlists_post = {
        .uri = "/api/playlists",
        .method = HTTP_POST,
        .handler = api_playlists_post,
    };
    httpd_uri_t playlists_start = {
        .uri = "/api/playlists/start",
        .method = HTTP_POST,
        .handler = api_playlist_start_post,
    };
    httpd_uri_t playlists_delete = {
        .uri = "/api/playlists/delete",
        .method = HTTP_POST,
        .handler = api_playlist_delete_post,
    };
    httpd_uri_t playlists_item_get = {
        .uri = "/api/playlists/*",
        .method = HTTP_GET,
        .handler = api_playlists_item_get,
    };
    httpd_uri_t playlists_item_put = {
        .uri = "/api/playlists/*",
        .method = HTTP_PUT,
        .handler = api_playlists_item_put,
    };
    httpd_uri_t playlists_item_delete = {
        .uri = "/api/playlists/*",
        .method = HTTP_DELETE,
        .handler = api_playlists_item_delete,
    };
    httpd_uri_t playlists_item_start = {
        .uri = "/api/playlists/*/start",
        .method = HTTP_POST,
        .handler = api_playlists_item_start_post,
    };
    httpd_uri_t engine_start = {
        .uri = "/api/engine/start",
        .method = HTTP_POST,
        .handler = api_engine_start_post,
    };
    httpd_uri_t engine_stop = {
        .uri = "/api/engine/stop",
        .method = HTTP_POST,
        .handler = api_engine_stop_post,
    };
    httpd_uri_t engine_pause = {
        .uri = "/api/engine/pause",
        .method = HTTP_POST,
        .handler = api_engine_pause_post,
    };
    httpd_uri_t engine_resume = {
        .uri = "/api/engine/resume",
        .method = HTTP_POST,
        .handler = api_engine_resume_post,
    };
    httpd_uri_t engine_next = {
        .uri = "/api/engine/next",
        .method = HTTP_POST,
        .handler = api_engine_next_post,
    };
    httpd_uri_t engine_all_off = {
        .uri = "/api/engine/all_off",
        .method = HTTP_POST,
        .handler = api_engine_all_off_post,
    };
    httpd_uri_t valves_all_off = {
        .uri = "/api/valves/all_off",
        .method = HTTP_POST,
        .handler = api_valves_all_off_post,
    };
    httpd_uri_t valves_clear_live = {
        .uri = "/api/valves/clear_live",
        .method = HTTP_POST,
        .handler = api_valves_clear_live_post,
    };
    httpd_uri_t valves_all_on_pulse = {
        .uri = "/api/valves/all_on_pulse",
        .method = HTTP_POST,
        .handler = api_valves_all_on_pulse_post,
    };
    httpd_uri_t valves_chase = {
        .uri = "/api/valves/chase",
        .method = HTTP_POST,
        .handler = api_valves_chase_post,
    };
    httpd_uri_t valves_single = {
        .uri = "/api/valves/single",
        .method = HTTP_POST,
        .handler = api_valves_single_post,
    };
    httpd_uri_t system_reboot = {
        .uri = "/api/system/reboot",
        .method = HTTP_POST,
        .handler = api_system_reboot_post,
    };
    httpd_uri_t system_factory_reset = {
        .uri = "/api/system/factory_reset",
        .method = HTTP_POST,
        .handler = api_system_factory_reset_post,
    };

    httpd_register_uri_handler(s_httpd, &root);
    httpd_register_uri_handler(s_httpd, &admin);
    httpd_register_uri_handler(s_httpd, &status);
    httpd_register_uri_handler(s_httpd, &diagnostics);
    httpd_register_uri_handler(s_httpd, &sensors);
    httpd_register_uri_handler(s_httpd, &sensors_raw);
    httpd_register_uri_handler(s_httpd, &sensors_calibrate);
    httpd_register_uri_handler(s_httpd, &pumps);
    httpd_register_uri_handler(s_httpd, &wifi_get_uri);
    httpd_register_uri_handler(s_httpd, &wifi_post_uri);
    httpd_register_uri_handler(s_httpd, &wifi_reconnect_uri);
    httpd_register_uri_handler(s_httpd, &config_get_uri);
    httpd_register_uri_handler(s_httpd, &config_post_uri);
    httpd_register_uri_handler(s_httpd, &config_save_uri);
    httpd_register_uri_handler(s_httpd, &config_export_uri);
    httpd_register_uri_handler(s_httpd, &config_import_uri);
    httpd_register_uri_handler(s_httpd, &config_reset_uri);
    httpd_register_uri_handler(s_httpd, &pump1_manual);
    httpd_register_uri_handler(s_httpd, &pump1_auto);
    httpd_register_uri_handler(s_httpd, &pump1_config);
    httpd_register_uri_handler(s_httpd, &pump2_manual);
    httpd_register_uri_handler(s_httpd, &pump2_auto);
    httpd_register_uri_handler(s_httpd, &pump2_config);
    httpd_register_uri_handler(s_httpd, &pumps_drain);
    httpd_register_uri_handler(s_httpd, &queue_get);
    httpd_register_uri_handler(s_httpd, &queue_clear);
    httpd_register_uri_handler(s_httpd, &queue_delete);
    httpd_register_uri_handler(s_httpd, &queue_move);
    httpd_register_uri_handler(s_httpd, &queue_item_delete);
    httpd_register_uri_handler(s_httpd, &queue_item_move);
    httpd_register_uri_handler(s_httpd, &splash);
    httpd_register_uri_handler(s_httpd, &logs_get);
    httpd_register_uri_handler(s_httpd, &logs_clear);
    httpd_register_uri_handler(s_httpd, &screens);
    httpd_register_uri_handler(s_httpd, &screens_post);
    httpd_register_uri_handler(s_httpd, &screens_test);
    httpd_register_uri_handler(s_httpd, &screens_preview);
    httpd_register_uri_handler(s_httpd, &screens_delete);
    httpd_register_uri_handler(s_httpd, &screens_item_get);
    httpd_register_uri_handler(s_httpd, &screens_item_put);
    httpd_register_uri_handler(s_httpd, &screens_item_delete);
    httpd_register_uri_handler(s_httpd, &screens_item_test);
    httpd_register_uri_handler(s_httpd, &playlists);
    httpd_register_uri_handler(s_httpd, &playlists_post);
    httpd_register_uri_handler(s_httpd, &playlists_start);
    httpd_register_uri_handler(s_httpd, &playlists_delete);
    httpd_register_uri_handler(s_httpd, &playlists_item_get);
    httpd_register_uri_handler(s_httpd, &playlists_item_put);
    httpd_register_uri_handler(s_httpd, &playlists_item_delete);
    httpd_register_uri_handler(s_httpd, &playlists_item_start);
    httpd_register_uri_handler(s_httpd, &engine_start);
    httpd_register_uri_handler(s_httpd, &engine_stop);
    httpd_register_uri_handler(s_httpd, &engine_pause);
    httpd_register_uri_handler(s_httpd, &engine_resume);
    httpd_register_uri_handler(s_httpd, &engine_next);
    httpd_register_uri_handler(s_httpd, &engine_all_off);
    httpd_register_uri_handler(s_httpd, &valves_all_off);
    httpd_register_uri_handler(s_httpd, &valves_clear_live);
    httpd_register_uri_handler(s_httpd, &valves_all_on_pulse);
    httpd_register_uri_handler(s_httpd, &valves_chase);
    httpd_register_uri_handler(s_httpd, &valves_single);
    httpd_register_uri_handler(s_httpd, &system_reboot);
    httpd_register_uri_handler(s_httpd, &system_factory_reset);
    ESP_ERROR_CHECK(websocket_register_httpd(s_httpd));
    ESP_LOGI(TAG, "HTTP server started on port 80");
    return ESP_OK;
}

httpd_handle_t web_server_get_handle(void)
{
    return s_httpd;
}
