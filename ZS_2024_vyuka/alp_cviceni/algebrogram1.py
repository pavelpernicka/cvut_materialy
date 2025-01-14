#!/usr/bin/env python3
import sys
import time

ODEVZDAVAT = False

def read_input():
    equations = []
    for line in sys.stdin:
        equations.append(line.strip())
    return equations

class Algebrogram:
    def __init__(self, equation_str):
        self.equation_string = equation_str
        self.operator = None
        self.first = []
        self.second = []
        self.result = []
        self.error = not self._parse_equation(equation_str)
        self.exclude_dict = self.exclude()

    def _parse_equation(self, equation_str):
        valid_operators = ['+', '-', '*', '/']
        
        if '=' not in equation_str:
            return False
        
        left_side, right_side = equation_str.split('=')
        right_side = right_side.strip()

        for op in valid_operators:
            if op in left_side:
                self.operator = op
                first_part, second_part = map(str.strip, left_side.split(op))
                if not first_part or not second_part:
                    return False
                
                self.first = list(first_part)
                self.second = list(second_part)
                self.result = list(right_side)
                return True
        
        return False

    def exclude(self):
        exclusions = {}

        def add_exclusion(letter, value):
            if letter not in exclusions:
                exclusions[letter] = []
            if value not in exclusions[letter]:
                exclusions[letter].append(value)

        # Nezačíná nulou
        if self.first[0].isalpha():
            add_exclusion(self.first[0], 0)
        if self.second[0].isalpha():
            add_exclusion(self.second[0], 0)
        if self.result[0].isalpha():
            add_exclusion(self.result[0], 0)

        # Sčítání/odčítání 0 nebo 9
        if self.operator in ('+', '-'):
            if len(self.first) == len(self.second) == len(self.result):
                if self.first[-1] == self.second[-1] == self.result[-1] and self.first[-1].isalpha():
                    for i in range(1, 10):
                        add_exclusion(self.first[-1], i)

            if len(self.first) == 3 and len(self.second) == 3 and len(self.result) == 3:
                if self.first[1] == self.result[1] and self.first[1].isalpha():
                    add_exclusion(self.first[1], 0)
                    add_exclusion(self.first[1], 9)
                if self.first[1] == self.second[1] and self.second[1] != self.result[1] and self.first[1].isalpha():
                    add_exclusion(self.first[1], 0)
                    add_exclusion(self.result[1], 9)

        if self.operator in ('+', '-') and len(self.first) == 3 and len(self.second) == 3 and len(self.result) == 4:
            if self.result[0].isalpha():
                add_exclusion(self.result[0], 1)

        if self.operator == '*':
            if self.first == self.second:
                for letter in self.first:
                    if letter.isalpha():
                        add_exclusion(letter, 0)
                        add_exclusion(letter, 1)
                        add_exclusion(letter, 5)
        return exclusions

    def test_values(self, mapping):
        if self.error:
            return False

        def evaluate(chars):
            return int(''.join(str(mapping[char]) for char in chars))
        
        first_value = evaluate(self.first)
        second_value = evaluate(self.second)
        result_value = evaluate(self.result)
        
        if self.operator == '+':
            return first_value + second_value == result_value
        elif self.operator == '-':
            return first_value - second_value == result_value
        elif self.operator == '*':
            return first_value * second_value == result_value
        elif self.operator == '/':
            return second_value != 0 and first_value / second_value == result_value
        
        return None

def merge_excludes(algebrograms):
    merged_excludes = {}
    for alg_instance in algebrograms:
        exclude = alg_instance.exclude_dict
        for letter, values in exclude.items():
            if letter not in merged_excludes:
                merged_excludes[letter] = []
            for value in values:
                if value not in merged_excludes[letter]:
                    merged_excludes[letter].append(value)

    return merged_excludes

def solve_algebrogram(equations):
    algebrograms = []
    
    for equation in equations:
        algebrogram = Algebrogram(equation)
        if not algebrogram.error:
            algebrograms.append(algebrogram)
        else:
            return None

    all_letters = set()
    for algebrogram in algebrograms:
        all_letters.update(algebrogram.first + algebrogram.second + algebrogram.result)
    
    all_letters = list(all_letters)
    exclude_dict = merge_excludes(algebrograms)

    def backtrack(letter_index, current_mapping, used_digits):
        if letter_index == len(all_letters):
            if all(algebrogram.test_values(current_mapping) for algebrogram in algebrograms):
                return ' '.join(str(current_mapping[letter]) for letter in sorted(current_mapping))
            return None
            
        current_letter = all_letters[letter_index]
        available_digits = [d for d in range(10) if d not in exclude_dict.get(current_letter, [])]

        for digit in available_digits:
            if digit not in used_digits:
                current_mapping[current_letter] = digit
                used_digits.add(digit)
                
                result = backtrack(letter_index + 1, current_mapping, used_digits)
                if result:
                    return result
                
                used_digits.remove(digit)
                del current_mapping[current_letter]
        return None

    result = backtrack(0, {}, set())
    return result

def brute_format_wrapper(results):
    return "NEEXISTUJE" if results is None else results

def test_solve_algebrogram():
    test_cases = [
        (["TO+GO=OUT"], "8 1 2 0"),
        (["WCW-SMY=CSW", "SMXSSM/XWM=WCC"], "1 8 3 5 7 0"),
        (["AR-BF=GP", "PA*HB=PPGO", "PYI-PH=OA", "BI*HP=PIBI"], "9 2 3 7 6 5 8 1 4 0"),
        (["PWY-TQ=RR", "PP*DR=ZWD", "QR-RW=PZ", "RS*RQ=YPDS", "PWZ-NQ=NN"], "NEEXISTUJE"),
        (["MK+XJ=KK", "PX*XM=QKPP", "XQ+QP=MJ"], "0 9 6 8 2 3"),
        (["GP-RJ=WS", "RJJS/GS=RW", "RS*SW=GSS", "RS+PP=RRJ"], "8 4 9 1 5 7"),
        (["LW+NC=CL", "HZ*CL=ZLZZ", "HU-ZM=NW", "MWZD/ZD=OZ"], "6 0 8 3 4 2 9 1 7 5"),
        (["UM+QM=UYY", "UCCK/CD=CA", "UYQ-KY=QQ", "ACUY/QD=QM", "QY-SA=CC"], "7 3 6 2 5 8 4 1 0")
    ]
    
    for i, (equations, expected) in enumerate(test_cases):
        time_start = time.time_ns()
        result = brute_format_wrapper(solve_algebrogram(equations))
        stop_time = time.time_ns()
        duration = stop_time - time_start
        if(result != expected):
            print(f"Test {i + 1} selhal: očekáváno {expected}, ale získáno {result}")
        else:
            print(f"Test {i + 1} prošel. Trvání: {duration/1000000000}s")

if(not ODEVZDAVAT):
    test_solve_algebrogram()
else:
    equations = read_input()
    print(brute_format_wrapper(solve_algebrogram(equations)))
