#!/bin/bash

# Cesta ke složce s příklady
EXAMPLES_DIR="examples/examples-hard"
SCRIPT="cards_hard.py"

# Kontrola, jestli skript existuje
if [[ ! -f $SCRIPT ]]; then
  echo "Pythoní skript $SCRIPT nenalezen."
  exit 1
fi

# Počítadla pro statistiky
total_tests=0
successful_tests=0
failed_tests=0

# Iterace přes všechny zadání
for input_file in "$EXAMPLES_DIR"/hard-*.txt; do
  echo "Testuji soubor: $input_file"
  total_tests=$((total_tests + 1))
  
  # Spuštění skriptu s aktuálním zadáním
  start_time=$(date +%s%3N)  
  output=$(python3 "$SCRIPT" "$input_file" | tail -n 1)
  end_time=$(date +%s%3N)  # # end time in milliseconds
  duration_ms=$((end_time - start_time))  # duration in milliseconds 

  # Najdi odpovídající .sol soubory
  base_name=$(basename "$input_file" .txt)
  sol_files=("$EXAMPLES_DIR/$base_name"-sol-*.sol)

  if [[ ${#sol_files[@]} -eq 0 || ! -e "${sol_files[0]}" ]]; then
    # Pokud žádný .sol soubor neexistuje, očekává se NOSOLUTION
    if [[ "$output" == "NOSOLUTION" ]]; then
      if [ "${duration_ms}" -lt 1000 ]; then 
        echo "  ✔️  Výstup je správný (NOSOLUTION), trvání: $duration_ms"
      else
        echo "  ❌ Timeouted, trvání: $duration_ms"
      fi
      successful_tests=$((successful_tests + 1))
    else
      echo "  ❌ Výstup není NOSOLUTION: $output"
      failed_tests=$((failed_tests + 1))
    fi
  else
    # Porovnání s .sol soubory
    valid=false
    for sol_file in "${sol_files[@]}"; do
      # Načti očekávané řešení z .sol souboru
      expected=$(sed -n "s/^'\(.*\)'$/\1/p" "$sol_file")
      
      # Porovnání výstupu skriptu s očekávaným řešením
      if [[ "$output" == "$expected" ]]; then
        if [ "${duration_ms}" -lt 1000 ]; then 
          echo "  ✔️  Výstup odpovídá řešení, trvání: $duration_ms"
        else
          echo "  ❌ Timeouted, trvání: $duration_ms"
        fi
        valid=true
        successful_tests=$((successful_tests + 1))
        break
      fi
    done

    # Pokud neodpovídá žádnému řešení
    if [[ $valid == false ]]; then
      echo "  ❌ Výstup neodpovídá žádnému řešení pro $input_file"
      failed_tests=$((failed_tests + 1))
    fi
  fi
done

# Výpis statistik
echo "--------------------------------"
echo "Celkové statistiky testování:"
echo "  Celkem testů: $total_tests"
echo "  Úspěšné testy: $successful_tests"
echo "  Neúspěšné testy: $failed_tests"

