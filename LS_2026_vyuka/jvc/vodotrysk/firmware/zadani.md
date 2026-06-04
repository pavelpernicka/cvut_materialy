Projekt: ESP32-S3 Water Curtain Controller

Cíl:
Vytvořit kompletní firmware pro řídicí desku vodní clony / vodotrysku se 64 elektromagnetickými ventily, 2 čerpadly, hladinovými senzory, měřením proudu, RTC, AHT20, WS2812B a webovým UI běžícím přímo z ESP32-S3.

MCU:
- ESP32-S3-WROOM-1-N16R8
- 16 MB flash
- 8 MB PSRAM
- native USB pro programování a debug
- firmware v ESP-IDF
- build/flash přes Makefile nad idf.py
Hlavní vlastnosti:
- řízení 64 solenoidů přes 8× 74HC595 / shift registry
- řízení 2 čerpadel přes MOSFETy
- měření proudu čerpadel přes INA180A2
- měření hladiny vody přes 1 nebo 2 hladinové senzory
- AHT20 teplota/vlhkost přes I2C
- DS3231 RTC přes I2C
- WS2812B stavová LED
- webové UI na portu 80
- režim AP i Wi-Fi client
- fallback AP při chybě připojení
- guest / exhibition režim
- admin dashboard
- živé ladění ventilů, čerpadel, senzorů a parametrů
- ukládání konfigurace
- queue systém pro požadavky návštěvníků
- dynamické textové proměnné typu {{time}}, {{temp}}, {{month}}, {{pump1_current}}
Pinmapa podle aktuálního schématu:

USB:
GPIO19 = USB_D-
GPIO20 = USB_D+

Shift registry:
GPIO10 = SERIAL_DATA
GPIO11 = SERIAL_SHIFT_CLK
GPIO12 = SERIAL_LATCH_CLK
GPIO13 = SERIAL_CLEAR
GPIO14 = SERIAL_ENABLE

I2C:
GPIO38 = I2C_SDA
GPIO39 = I2C_SCL

LED:
GPIO18 = WS2812B
GPIO41 = LED_INT

Hladina:
GPIO6 = WATER_LEVEL_1
GPIO7 = WATER_LEVEL_2

ADC proudy:
GPIO1 = CURR_ADC1
GPIO2 = CURR_ADC2
GPIO4 = CURR_ADC3

Čerpadla:
GPIO45 = SW_PUMP1  POZOR: strapping pin, doporučeno přesunout
GPIO47 = SW_PUMP2

UART header:
TXD0/RXD0 vyvedeno, ale primárně se má používat native USB CDC/JTAG.

Doporučená změna:

SW_PUMP1 nepoužívat na GPIO45.
GPIO45 je strapping pin ESP32-S3 a může dělat problémy při bootu.

Doporučení:
SW_PUMP1 -> GPIO15
SW_PUMP2 -> GPIO47 ponechat.
Adresářová struktura projektu:

water-curtain-fw/
  Makefile
  CMakeLists.txt
  sdkconfig.defaults
  partitions.csv
  README.md

  main/
    app_main.c

    board/
      pinmap.h
      board_config.h

    drivers/
      shiftreg.c
      shiftreg.h
      pumps.c
      pumps.h
      sensors.c
      sensors.h
      ws2812.c
      ws2812.h
      rtc_ds3231.c
      rtc_ds3231.h
      aht20.c
      aht20.h

    engine/
      water_engine.c
      water_engine.h
      renderer.c
      renderer.h
      font5x7.c
      font5x7.h
      queue.c
      queue.h
      show_model.c
      show_model.h
      template_fields.c
      template_fields.h

    system/
      config.c
      config.h
      storage.c
      storage.h
      wifi_manager.c
      wifi_manager.h
      web_server.c
      web_server.h
      websocket.c
      websocket.h
      logger.c
      logger.h
      safety.c
      safety.h
      diagnostics.c
      diagnostics.h

  web/
    index.html
    admin.html
    app.js
    admin.js
    style.css
    assets/

  tools/
    pack_web.py
Základní firmware architektura:

Core 0:
- Wi-Fi
- HTTP server
- WebSocket
- REST API
- storage/config
- guest/admin UI

Core 1:
- realtime water engine
- shift register SPI output
- čerpadla
- bezpečnostní logika

FreeRTOS tasky:

1) water_engine_task
- pinned to core 1
- vysoká priorita
- přehrává předrenderované framy
- ovládá 64 ventilů přes shift registry
- nikdy nesmí čekat na web/API/storage

2) renderer_task
- převádí texty, bitmapy, čas a senzory na frame sekvence
- může běžet s nižší prioritou
- výsledek dává do queue

3) pump_control_task
- řídí čerpadla podle zvoleného režimu
- sleduje hladinové senzory
- měří proud
- hlídá chyby

4) sensor_task
- periodicky čte:
  - WATER_LEVEL_1
  - WATER_LEVEL_2
  - ADC proudů
  - AHT20
  - DS3231
  - napájecí stav, pokud bude dostupný

5) web_server_task
- REST API
- statické soubory
- guest/admin UI

6) websocket_task
- push live stavu do UI

7) config_task
- ukládá konfiguraci s debounce
- nikdy nezapisuje flash při každém pohybu slideru

8) diagnostics_task
- USB log
- reset reason
- stav tasků
- watchdog info
Princip řízení vodní clony:

Vodní clona je 64px vysoký vertikální displej.
Každý časový krok je jeden sloupec obrazu.

Jeden frame:
- 64bit maska ventilů
- každý bit odpovídá jednomu solenoidu

Příklad:
bit 0  = ventil 0
bit 1  = ventil 1
...
bit 63 = ventil 63

Frame struktura:

typedef struct {
    uint64_t valves;
    uint16_t duration_ms;
} water_frame_t;

Sekvence:

typedef struct {
    water_frame_t *frames;
    size_t frame_count;
    bool owns_memory;
} rendered_sequence_t;
Shift register driver:

Použít SPI peripheral, ne bitbang.

GPIO:
MOSI  = SERIAL_DATA
SCLK  = SERIAL_SHIFT_CLK
LATCH = SERIAL_LATCH_CLK
CLEAR = SERIAL_CLEAR
OE    = SERIAL_ENABLE

Funkce:

void shiftreg_init(void);
void shiftreg_write_u64(uint64_t mask);
void shiftreg_all_off(void);
void shiftreg_enable(bool enable);
void shiftreg_clear(void);
void shiftreg_self_test_chase(uint32_t delay_ms);
void shiftreg_self_test_all_on(uint32_t ms);

Požadavky:
- při bootu všechny ventily vypnuté
- SERIAL_ENABLE držet v disabled stavu, dokud není firmware připraven
- při panic/error okamžitě all_off
- možnost invertovat bit order
- možnost invertovat logiku výstupů
- možnost nastavit mapování ventilů, protože fyzické pořadí nemusí sedět s logickým pořadím
Water engine:

Funkce:
- přehrávání show
- přehrávání guest splash požadavků
- fronta požadavků
- loop playlist
- pause/resume/stop
- emergency stop
- live preview do admin UI

Stavy:
- IDLE
- PLAYING_SHOW
- PLAYING_GUEST_ITEM
- PAUSED
- ERROR
- EMERGENCY_STOP

API funkce:

water_engine_start();
water_engine_stop();
water_engine_pause();
water_engine_resume();
water_engine_next();
water_engine_enqueue(sequence, source, priority);
water_engine_clear_queue();
water_engine_get_status();
Queue systém:

Typy položek:
- ADMIN_NOW
- ADMIN_QUEUE
- SCHEDULED_SHOW
- GUEST_SPLASH
- TEST_PATTERN

Priority:
0 = emergency/test
1 = admin immediate
2 = scheduled playlist
3 = guest splash

Queue item:

typedef struct {
    char id[32];
    char source_ip[48];
    char author[32];
    uint8_t priority;
    uint64_t created_ms;
    uint32_t estimated_duration_ms;
    rendered_sequence_t sequence;
} queue_item_t;

Vlastnosti:
- thread-safe
- max délka fronty nastavitelná
- guest požadavky rate-limitované
- při plné frontě HTTP 429
- admin může mazat položky
- admin může položku posunout nahoru/dolů
- admin může frontu vyčistit
Show model:

Show se nesmí hardcodovat v C kódu.
Vše se ukládá jako JSON konfigurace.

Screen:

{
  "id": "screen-uuid",
  "name": "Clock screen",
  "type": "text|bitmap|sensor|clock|test",
  "duration_ms": 3000,
  "enabled": true,
  "content": {
    "text": "Čas: {{time}}",
    "bitmap": [],
    "font": "5x7",
    "align": "center",
    "scroll": true,
    "speed": 80,
    "invert": false
  }
}

Playlist:

{
  "id": "playlist-main",
  "name": "Main loop",
  "loop": true,
  "screens": [
    "screen-1",
    "screen-2",
    "screen-3"
  ]
}
Dynamická pole / template systém:

Text v editoru může obsahovat proměnné:

Čas:
{{time}}          např. 18:42
{{time_sec}}      např. 18:42:15
{{hour}}
{{minute}}
{{second}}
{{date}}          např. 2026-06-01
{{day}}
{{month}}
{{year}}
{{weekday}}

AHT20:
{{temp}}          teplota
{{humidity}}      vlhkost

Pumpa:
{{pump1_state}}
{{pump2_state}}
{{pump1_current}}
{{pump2_current}}
{{pump1_current_max}}
{{pump2_current_max}}

Hladina:
{{level_low}}
{{level_high}}
{{water_state}}

Systém:
{{queue_len}}
{{ip}}
{{ssid}}
{{uptime}}
{{mode}}
{{free_heap}}
{{fps}}

Příklad textu:
"Ahoj! Je {{time}}, teplota {{temp}} C"

Template engine:
- před renderem nahradí proměnné aktuálními hodnotami
- pokud hodnota není dostupná, použije "--"
- musí podporovat formátování:
  {{temp:1}} = jedno desetinné místo
  {{pump1_current:2}} = dvě desetinná místa
Pump control:

Čerpadla:
- PUMP1
- PUMP2

Každé čerpadlo má:
- GPIO výstup
- ADC proud
- režim řízení
- ochrany
- ruční override
- PWM/duty-cycle režim
- log spínání

Pump mode enum:

PUMP_MODE_OFF
PUMP_MODE_MANUAL_ON
PUMP_MODE_TWO_LEVEL_SENSORS
PUMP_MODE_HIGH_LEVEL_ONLY
PUMP_MODE_TIMED_AFTER_DRAIN
PUMP_MODE_PWM_INTERVAL

1) Režim se dvěma senzory:
- WATER_LEVEL_LOW
- WATER_LEVEL_HIGH

Logika:
- pokud hladina klesne na LOW → zapnout čerpadlo
- čerpat dokud není HIGH
- po dosažení HIGH vypnout
- hysterese vzniká fyzicky mezi senzory
- timeout ochrana: pokud se HIGH nedosáhne za max_fill_time_s, vypnout a chyba

2) Režim s jedním senzorem:
- používá se jen HIGH senzor
- čerpadlo může běžet, dokud HIGH není aktivní
- když HIGH aktivní → vypnout
- vhodné jako ochrana proti přetečení
- zapnutí podle požadavku systému nebo podle timed režimu

3) Režim bez senzorů:
- čerpadlo řízené časově
- čerpá jen tehdy, když se nedávno odpouštělo / běžel vodní efekt
- nastavitelné:
  - after_drain_delay_ms
  - pump_on_ms
  - pump_off_ms
  - duty_cycle_percent
  - max_run_time_s
  - cooldown_s

4) PWM / interval režim:
- není nutně rychlé PWM pro motor, spíš pomalé dávkování
- perioda např. 10 s
- duty např. 40 %
- tedy 4 s ON, 6 s OFF
- používat pro doplňování vody, ne pro vysokofrekvenční PWM

5) Manual/debug:
- admin může čerpadlo zapnout/vypnout ručně
- musí být timeout, aby nezůstalo zapnuté omylem
Pump safety:

Ochrany:
- overcurrent
- undercurrent
- dry run podezření
- timeout plnění
- high level reached
- sensor error
- ADC error
- MOSFET stuck-on podezření
- brownout reset history

Proudové limity:
pump_current_warn_a
pump_current_max_a
pump_current_min_when_on_a

Detekce:
- pokud pumpa ON a proud je moc nízký → čerpadlo odpojeno / neběží
- pokud pumpa OFF a proud není nulový → MOSFET stuck / chyba měření
- pokud proud moc vysoký → vypnout

Log událostí:
- pump on
- pump off
- reason
- current at switch
- max current during run
- runtime
Admin dashboard:

Musí ukazovat živě:

Stav systému:
- uptime
- IP adresa
- Wi-Fi mode AP/client
- RSSI
- free heap
- PSRAM free
- teplota/vlhkost
- RTC čas
- queue length
- active screen
- active mode
- water engine state

Ventily:
- aktuální 64bit frame
- grafický preview 64 ventilů
- počet aktivních ventilů
- frame period
- FPS / column rate
- tlačítka:
  - all off
  - all on krátce
  - chase test
  - single valve test
  - pattern test

Čerpadla:
- PUMP1 stav
- PUMP2 stav
- proud PUMP1
- proud PUMP2
- max proud
- poslední sepnutí
- důvod sepnutí
- mód řízení
- ruční override
- emergency off

Hladina:
- WATER_LEVEL_1
- WATER_LEVEL_2
- interpretovaný stav:
  - LOW
  - FILLING
  - HIGH
  - ERROR
  - UNKNOWN

Napájení:
- pokud dostupné, zobrazit +12 V / +5 V / +3.3 V
- jinak alespoň odhad/stav podle ADC proudů a reset reason

Log:
- posledních třeba 200 událostí
- filtrovat podle:
  - system
  - pump
  - water engine
  - guest
  - sensor
  - error
Admin UI funkce:

/admin

Sekce:
1) Dashboard
2) Screens editor
3) Playlist editor
4) Guest/exhibition nastavení
5) Pump settings
6) Sensor calibration
7) Valve test
8) Wi-Fi settings
9) System/debug
10) Import/export config

Screens editor:
- vytvořit screen
- typ: text / bitmap / clock / sensor / test
- textové pole s podporou {{variables}}
- náhled výsledku
- bitmap editor
- nastavení scroll/center/invert/speed/repeat
- duration
- uložit
- test now
- add to queue

Bitmap editor:
- canvas 64×N
- kreslení myší/prstem
- guma
- invert
- clear
- shift left/right/up/down
- import/export JSON
- možnost vložit text do bitmapy

Playlist editor:
- drag & drop pořadí
- enable/disable položky
- loop on/off
- repeat count
- test playlist

Pump settings:
- pro každé čerpadlo:
  - mode
  - GPIO read-only podle board configu
  - current calibration
  - max current
  - min current
  - fill timeout
  - interval period
  - duty
  - only after water used
  - manual test

Sensor calibration:
- invert hladinových vstupů
- debounce
- raw stav
- interpretovaný stav
- ADC zero offset
- current scale
Guest / exhibition mode:

Když je exhibition mode zapnutý:
- GET / zobrazí guest UI
- /admin zůstává admin UI
- guest nemá přístup k systémovým nastavením

Guest UI:
- velké pole “Napiš text do vody”
- tlačítko SPLASH
- jednoduchý bitmap editor
- ukázka náhledu
- stav fronty
- zpráva “Jsi 5. v pořadí”
- limit délky textu
- cooldown mezi požadavky
- zákaz nebezpečných znaků není nutný, ale escapovat HTML
- možnost adminem vypnout bitmapy

Guest API:
POST /api/splash

Body:
{
  "type": "text",
  "text": "AHOJ",
  "client_id": "random"
}

nebo:

{
  "type": "bitmap",
  "bitmap": {
    "width": 64,
    "height": 64,
    "data": [...]
  }
}

Server:
- validuje velikost
- nahradí forbidden hodnoty
- přerenderuje
- vloží do fronty
- vrátí queue position

Response:
{
  "ok": true,
  "id": "...",
  "position": 7,
  "estimated_wait_ms": 42000
}
REST API:

Status:
GET /api/status

Config:
GET /api/config
POST /api/config
POST /api/config/save
POST /api/config/reset

Screens:
GET /api/screens
POST /api/screens
GET /api/screens/:id
PUT /api/screens/:id
DELETE /api/screens/:id
POST /api/screens/:id/test

Playlist:
GET /api/playlists
POST /api/playlists
PUT /api/playlists/:id
DELETE /api/playlists/:id
POST /api/playlists/:id/start

Queue:
GET /api/queue
POST /api/queue/clear
DELETE /api/queue/:id
POST /api/queue/:id/move

Splash:
POST /api/splash

Water engine:
POST /api/engine/start
POST /api/engine/stop
POST /api/engine/pause
POST /api/engine/resume
POST /api/engine/next
POST /api/engine/all_off

Valves debug:
POST /api/valves/all_off
POST /api/valves/all_on_pulse
POST /api/valves/chase
POST /api/valves/single

Pump:
GET /api/pumps
POST /api/pumps/1/manual
POST /api/pumps/2/manual
POST /api/pumps/1/config
POST /api/pumps/2/config

Sensors:
GET /api/sensors
GET /api/sensors/raw
POST /api/sensors/calibrate

Wi-Fi:
GET /api/wifi
POST /api/wifi
POST /api/wifi/reconnect

Logs:
GET /api/logs
POST /api/logs/clear

System:
POST /api/system/reboot
POST /api/system/factory_reset
WebSocket:

Endpoint:
/ws

Server posílá:
- status_update
- sensor_update
- pump_update
- queue_update
- frame_preview
- log_event
- error_event

Příklad:

{
  "type": "sensor_update",
  "data": {
    "temp": 24.3,
    "humidity": 51.2,
    "level_low": true,
    "level_high": false,
    "pump1_current": 1.24,
    "pump2_current": 0.0
  }
}
Konfigurace:

Ukládat jako JSON do LittleFS.

config.json:

{
  "version": 1,
  "device_name": "Water Curtain",
  "wifi": {
    "mode": "ap_client",
    "ap_ssid": "WaterCurtain",
    "ap_password": "waterwater",
    "client_ssid": "",
    "client_password": "",
    "fallback_ap": true
  },
  "hardware": {
    "solenoid_count": 64,
    "shift_register_count": 8,
    "bit_order": "msb_first",
    "invert_outputs": false,
    "valve_map": [0,1,2,3,...,63]
  },
  "engine": {
    "column_period_ms": 35,
    "default_frame_duration_ms": 35,
    "pre_flush_ms": 100,
    "post_flush_ms": 100,
    "max_active_valves": 64
  },
  "exhibition": {
    "enabled": true,
    "max_queue": 50,
    "max_text_length": 32,
    "allow_bitmap": true,
    "cooldown_s": 5
  },
  "pumps": {
    "pump1": {
      "enabled": true,
      "mode": "two_level_sensors",
      "invert_output": false,
      "max_current_a": 5.0,
      "min_current_when_on_a": 0.1,
      "fill_timeout_s": 60,
      "interval_period_ms": 10000,
      "duty_percent": 40,
      "only_after_water_used": true
    },
    "pump2": {
      "enabled": true,
      "mode": "off"
    }
  },
  "sensors": {
    "level_low_invert": false,
    "level_high_invert": false,
    "level_debounce_ms": 100,
    "current_adc_scale": 1.0,
    "current_adc_offset": 0.0
  }
}
Storage:

Použít LittleFS.

Soubory:
- /config/config.json
- /config/screens.json
- /config/playlists.json
- /logs/events.log
- /web/index.html.gz
- /web/admin.html.gz
- /web/app.js.gz
- /web/admin.js.gz
- /web/style.css.gz

Požadavky:
- factory defaults při prvním bootu
- validace JSON
- fallback při poškozené konfiguraci
- export/import celé konfigurace z admin UI
Bezpečnostní logika:

Při bootu:
1) nastavit OE disabled
2) clear shift registry
3) all_off
4) inicializovat storage
5) inicializovat senzory
6) inicializovat Wi-Fi/web
7) až potom povolit engine

Emergency all_off:
- vypnout OE
- zapsat 0 do shift registrů
- vypnout čerpadla, pokud safety vyžaduje
- zalogovat důvod

Důvody:
- watchdog
- panic
- overcurrent
- sensor error
- manual emergency stop
- web command
- boot/reset
Debug přes USB:

Použít ESP_LOGI/W/E.

Logovat:
- reset reason
- firmware version
- Git commit, pokud dostupný
- Wi-Fi mode
- IP
- mount LittleFS
- načtení configu
- stav I2C zařízení
- nalezen AHT20
- nalezen DS3231
- pump state changes
- queue events
- render errors
- engine start/stop
- overcurrent
- water level changes

Makefile target:
make monitor
Build systém:

Makefile:

PORT ?= /dev/ttyACM0

build:
	idf.py build

flash:
	idf.py -p $(PORT) flash

monitor:
	idf.py -p $(PORT) monitor

fullflash:
	idf.py -p $(PORT) flash monitor

menuconfig:
	idf.py menuconfig

erase:
	idf.py -p $(PORT) erase-flash

web:
	python3 tools/pack_web.py

clean:
	idf.py clean
Acceptance criteria:

1) Projekt jde sestavit přes make build.
2) Projekt jde nahrát přes native USB ESP32-S3.
3) Po bootu jsou ventily vypnuté.
4) Po bootu vznikne AP WaterCurtain, pokud není nakonfigurovaná Wi-Fi.
5) Na http://192.168.4.1 běží guest UI.
6) Na /admin běží admin UI.
7) Admin ukazuje live dashboard.
8) Admin umí spustit single valve test.
9) Admin umí testovat čerpadla.
10) Admin ukazuje proudy čerpadel.
11) Admin ukazuje hladinové senzory.
12) Admin ukazuje AHT20 a RTC.
13) Lze vytvořit text screen.
14) Text screen podporuje {{time}}, {{temp}}, {{humidity}}.
15) Lze vytvořit bitmap screen.
16) Guest může poslat splash.
17) Splash se vloží do fronty.
18) Více hostů může posílat požadavky současně.
19) Při plné frontě API vrátí 429.
20) Pumpa v režimu 2 senzorů zapne při nízké hladině a vypne při vysoké.
21) Pumpa v režimu 1 senzoru vypne při vysoké hladině.
22) Pumpa v režimu bez senzorů umí interval/duty režim.
23) Čerpadlo se vypne při overcurrent.
24) Konfigurace přežije reboot.
25) USB monitor vypisuje smysluplné debug hlášky.

Hardware zapojení a názvy bloků:

MCU blok:
- U1 = ESP32-S3-WROOM-1-N16R8 / aktuálně ve schématu symbol ESP32-S3-WROOM-1-N4
- napájení U1: +3.3 V
- EN pin:
  - R19 5k1 pull-up na +3.3 V
  - SW1 BTN_RST na GND
  - C15 1 uF na GND
- BOOT:
  - SW2 BTN_BOOT0 na GND
- USB:
  - J13 USB_C
  - USB_D- přes R22 20R na GPIO19
  - USB_D+ přes R23 20R na GPIO20
  - R20/R21 5k1 CC rezistory na GND
  - D8 SS34 z VBUS na +5 V
Napájení:
- J1 = PWR_IN, vstup +12 V
- F1 = 20A holder / pojistka na +12 V vstupu
- D3 = SS34 ochranná/sériová dioda na +12 V větvi
- U5 = TPS5430DDA buck měnič z +12 V na +5 V
- L1 = 47 uH indukčnost bucku
- D5 = SS34 catch/freewheel dioda bucku
- C12 = 10 uF výstupní kondenzátor +5 V
- C13 = 100 uF výstupní kondenzátor +5 V
- F2 = polyfuse na +5 V
- D7 = SS34 za polyfuse na +5 V
- R14/R15/R16 = zpětnovazební dělič TPS5430 pro nastavení +5 V
- U3 = AMS1117-3.3 lineární stabilizátor z +5 V na +3.3 V
- C3 = 47 uF vstup AMS1117
- C6 = 22 uF výstup AMS1117
- C1 = 100 nF decoupling +3.3 V
- C8 = 100 uF bulk +12 V
- D4 = červená LED indikace +3.3 V, R12 220R
- D6 = červená LED indikace +12 V, R13 2k2
Shift register / ventilový modul:
- U1 na ventilové desce = 74HC595D
- napájení logiky: +3.3 V
- sériový vstup:
  - J3 pin 6 = serial_data_in
  - připojeno na DS/SER 74HC595
- hodiny:
  - J3 pin 4 = shift_clk
  - připojeno na SRCLK/SHCP
- latch:
  - J3 pin 3 = latch_clk
  - připojeno na RCLK/STCP
- clear:
  - J3 pin 5 = clear
  - připojeno na SRCLR
- enable:
  - J3 pin 2 = enable_out
  - připojeno na OE
- data out:
  - QH' z 74HC595 jde na J2 pin 6 serial_data_out
  - tím se řetězí další desky
- výstupy QA až QH ovládají 8 MOSFET bloků Mosfet0 až Mosfet7
- každá ventilová deska ovládá 8 solenoidů
- pro 64 ventilů je potřeba 8 těchto shift-register bloků v sérii
MOSFET výstup pro solenoid / pumpu:
- Q2 = ADD4184A N-MOSFET low-side switch
- gate:
  - signál PUMP_SW / výstup ze shift registru
  - R27 100R sériový gate resistor
  - R24 100k pull-down gate na GND
  - D9 + R25 indikační LED na gate signálu
- drain:
  - připojen na zápornou stranu zátěže PUMP- / ventil-
- source:
  - přes R28 R_SENSE na GND, pokud jde o měřenou pumpu
  - u ventilů může být source přímo na GND, pokud se proud neměří
- zátěž:
  - PUMP+ / ventil+ na +12 V
  - PUMP- / ventil- na drain MOSFETu
- D10 = SS54 flyback dioda přes zátěž:
  - katoda na +12 V / PUMP+
  - anoda na spínaný uzel PUMP-
- princip:
  - GPIO/shift register dá HIGH
  - otevře se MOSFET
  - proud teče +12 V → zátěž → MOSFET → R_SENSE/GND
  - při vypnutí proud indukční zátěže doběhne přes D10
Měření proudu pumpy:
- U8 = INA180A2 proudový zesilovač
- R28 = R_SENSE, měřicí odpor v low-side větvi
- vstup INA180:
  - IN+ měří stranu R_SENSE blíže k MOSFET/source
  - IN- měří stranu R_SENSE blíže k GND
- výstup:
  - OUT INA180 přes R29 100R na signál CURR_ADC
  - C19 10 nF z CURR_ADC na GND jako jednoduchý low-pass filtr
- CURR_ADC jde do ADC pinu ESP32-S3
- vzorec:
  - Vadc = I_pump * R_sense * gain_ina180
  - INA180A2 má zesílení 50 V/V
  - I_pump = Vadc / (R_sense * 50)
Pump control blok:
- existují dva bloky pump_control:
  - pump_control0 = PUMP1
  - pump_control1 = PUMP2
- každý blok má:
  - PUMP_SW řídicí signál z ESP32
  - PUMP+ / PUMP- konektor pro čerpadlo
  - CURR_ADC výstup do ADC
- konektory:
  - J5 = CONN_PUMP1
  - J12 = CONN_PUMP2
- řídicí signály:
  - SW_PUMP1
  - SW_PUMP2
- doporučení:
  - SW_PUMP1 nepoužívat na GPIO45
  - přesunout ideálně na GPIO15
Hladinové senzory:
- J6 = WATER_LEVEL_1
- J7 = WATER_LEVEL_2
- každý konektor má:
  - pin 1 = +3.3 V
  - pin 2 = signál přes 10R odpor
  - pin 3 = GND
- R7 = 10R sériově do WATER_LEVEL_1
- R8 = 10R sériově do WATER_LEVEL_2
- signály:
  - WATER_LEVEL_1 → GPIO6
  - WATER_LEVEL_2 → GPIO7
- firmware musí mít nastavitelnou polaritu:
  - active high
  - active low
- firmware musí mít debounce
I2C senzory:
- I2C sběrnice:
  - GPIO38 = I2C_SDA
  - GPIO39 = I2C_SCL
- pull-up:
  - R4/R6 10k pro AHT20 část
  - R10/R11 10k pro DS3231 část
- U2 = AHT20
  - měří teplotu a vlhkost
  - VDD na +3.3 V
  - C9 100 nF decoupling
- U6 = DS3231MZ
  - RTC reálného času
  - VCC na +3.3 V
  - VBAT na BT1
  - BT1 = CR2032 holder
  - 32KHZ nepoužito
  - INT/SQW nepoužito
  - RST nepoužito
WS2812B:
- J10 = WS2812B datový konektor
  - GND
  - OUT = WS2812B data
  - VCC
- J11 = WS2812B_PWR
  - VCC
  - GND
- signál WS2812B jde z GPIO18
- firmware má používat RMT periférii
- LED používat pro stav:
  - boot
  - Wi-Fi AP
  - Wi-Fi connected
  - error
  - playing
  - emergency stop
Externí konektory:
- J8 = I2C header
  - +3.3 V
  - I2C_SDA
  - I2C_SCL
  - GND
- J9 = UART header
  - +3.3 V
  - UART_RX
  - UART_TX
  - GND
- J2/J3 = DATA_IN/DATA_OUT pro řetězení ventilových modulů
- J4 = PWR_OUT +12 V
- J1 = PWR_IN +12 V
Věci potřebné pro ovládání ve firmware:

1) GPIO output:
- pump MOSFETy
- shift register latch
- shift register clear
- shift register enable
- WS2812B přes RMT

2) SPI:
- shift register data
- shift register clock

3) ADC:
- CURR_ADC1
- CURR_ADC2
- CURR_ADC3
- přepočet ADC raw → napětí → proud

4) I2C:
- AHT20
- DS3231
- externí I2C header

5) USB:
- native USB CDC/JTAG
- flashování
- debug log

6) Web:
- HTTP server port 80
- WebSocket
- REST API
- LittleFS pro web assets a config

7) Safety:
- výchozí stav všech výstupů OFF
- OE disabled při bootu
- clear shift registrů při bootu
- emergency all_off
- pump overcurrent shutdown
- fill timeout
- sensor debounce
Mapování logických funkcí do firmware:

#define PIN_USB_D_MINUS       19
#define PIN_USB_D_PLUS        20

#define PIN_SR_DATA           10
#define PIN_SR_SHIFT_CLK      11
#define PIN_SR_LATCH_CLK      12
#define PIN_SR_CLEAR          13
#define PIN_SR_ENABLE         14

#define PIN_I2C_SDA           38
#define PIN_I2C_SCL           39

#define PIN_WS2812B           18
#define PIN_LED_INT           41

#define PIN_WATER_LEVEL_1     6
#define PIN_WATER_LEVEL_2     7

#define PIN_CURR_ADC1         1
#define PIN_CURR_ADC2         2
#define PIN_CURR_ADC3         4

#define PIN_SW_PUMP1          15
#define PIN_SW_PUMP2          47

A ještě tam přidej toto jako důležitou poznámku:

Poznámka k HW:
Aktuální schéma má SW_PUMP1 na GPIO45. To je strapping pin ESP32-S3. Firmware má být připraven na GPIO15 jako doporučený pin. Pokud bude deska vyrobena s GPIO45, musí firmware umět pin přemapovat v board_config.h, ale je to nedoporučená varianta.
