#!/usr/bin/env bash
set -euo pipefail

OPENOCD_BIN="${OPENOCD:-openocd}"
OPENOCD_CFG="${OPENOCD_CFG:-./openocd_rs41.cfg}"
FLASH_PROTECT_LAST="${FLASH_PROTECT_LAST:-15}"
DO_UNPROTECT=0
ELF_PATH="build/rs41.elf"

if [[ "${1:-}" == "--unprotect" ]]; then
    DO_UNPROTECT=1
    shift
fi

if [[ $# -ge 1 ]]; then
    ELF_PATH="$1"
fi

if [[ "${DO_UNPROTECT}" == "1" ]]; then
    "${OPENOCD_BIN}" -f "${OPENOCD_CFG}" -c "init; halt; flash protect 0 0 ${FLASH_PROTECT_LAST} off; exit"
fi

"${OPENOCD_BIN}" -f "${OPENOCD_CFG}" -c "program ${ELF_PATH} verify reset exit"
"${OPENOCD_BIN}" -f "${OPENOCD_CFG}" -c "init; reset; exit"
