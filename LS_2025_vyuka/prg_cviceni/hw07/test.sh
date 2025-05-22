#!/bin/bash

RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
NC='\033[0m' # No color

PROGRAM=./$1
TEST_DIR="./data/$2"
IN_SUFFIX=".txt"
OUT_SUFFIX=".stdout"
TMP_OUT="tmp_output.txt"
TMP_ERR="tmp_stderr.txt"
TIME_STATS="time_stats.txt"

total_tests=0
passed_tests=0
failed_tests=0
total_time=0
total_memory=0

for infile in "$TEST_DIR"/*"$IN_SUFFIX"; do
    test_name=$(basename "$infile" "$IN_SUFFIX")
    expected_out="$TEST_DIR/$test_name$OUT_SUFFIX"

    START_TIME=$(date +%s%N)
    
    /usr/bin/time -v bash -c "$PROGRAM < '$infile' > '$TMP_OUT' 2> '$TMP_ERR'" 2> "$TIME_STATS"
    
    END_TIME=$(date +%s%N)
    EXEC_TIME=$(( (END_TIME - START_TIME) / 1000000 ))  # Convert ns to ms
    MAX_MEMORY=$(grep "Maximum resident set size" "$TIME_STATS" | awk '{print $6}')
    MAX_MEMORY=${MAX_MEMORY:-0}

    total_tests=$((total_tests + 1))
    if diff -q "$TMP_OUT" "$expected_out" >/dev/null; then
        echo -e "[${GREEN}PASS${NC}] $test_name (${CYAN}${EXEC_TIME}ms${NC}, ${YELLOW}${MAX_MEMORY} KB${NC})"
        passed_tests=$((passed_tests + 1))
    else
        echo -e "[${RED}FAIL${NC}] $test_name (${CYAN}${EXEC_TIME}ms${NC}, ${YELLOW}${MAX_MEMORY} KB${NC})"
        echo -e "  ${YELLOW}Differences in stdout:${NC}"
        diff -u "$expected_out" "$TMP_OUT"
        failed_tests=$((failed_tests + 1))
    fi

    total_time=$((total_time + EXEC_TIME))
    total_memory=$((total_memory + MAX_MEMORY))
done

avg_time=$((total_tests ? total_time / total_tests : 0))
avg_memory=$((total_tests ? total_memory / total_tests : 0))

echo -e "\n${CYAN}========== Test Summary ==========${NC}"
echo -e "Total tests: ${total_tests}"
echo -e "Passed: ${GREEN}${passed_tests}${NC}, Failed: ${RED}${failed_tests}${NC}"
echo -e "Average execution time: ${CYAN}${avg_time}ms${NC}"
echo -e "Average memory usage: ${YELLOW}${avg_memory} KB${NC}"

rm -f "$TMP_OUT" "$TMP_ERR" "$TIME_STATS"

