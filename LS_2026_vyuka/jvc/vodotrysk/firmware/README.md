# Water Curtain Firmware

První implementační kostra firmware pro ESP32-S3 water curtain controller v ESP-IDF.

Aktuálně obsahuje:
- build systém (`make build`, `make flash`, `make web`)
- základní strukturu modulů `board`, `drivers`, `engine`, `system`
- bezpečný boot se zakázanými výstupy
- SPI driver pro 74HC595 řetězec
- minimální HTTP server a REST endpoint `/api/status`
- výchozí konfiguraci a placeholder web assets

Další iterace mají doplnit JSON storage, renderování textu/bitmap, plný admin/guest UI a detailní safety logiku.

## ESP-IDF setup

`idf.py` není součástí tohoto repozitáře. Je dostupné až po instalaci ESP-IDF a načtení jeho prostředí.

Příklad instalace na Linuxu:

```bash
cd ~
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32s3
. ./export.sh
idf.py --version
```

Pro každý nový shell je pak potřeba před buildem načíst prostředí:

```bash
. ~/esp-idf/export.sh
```

Pak už v tomto projektu fungují příkazy:

```bash
make build
make flash
make monitor
```
