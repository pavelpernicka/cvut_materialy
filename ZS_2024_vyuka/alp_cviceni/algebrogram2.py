from collections import deque
import time

# Simplified and corrected implementation of the solution
def parse_equations(equations):
    parsed = []
    for equation in equations:
        left, right = equation.split('=')
        for op in "+-*/":
            if op in left:
                left1, left2 = left.split(op)
                parsed.append((left1, op, left2, right))
                break
    return parsed

def evaluate(equation, mapping):
    def to_number(word):
        return int(''.join(str(mapping[c]) for c in word))

    left1, op, left2, right = equation
    try:
        num1, num2, res = to_number(left1), to_number(left2), to_number(right)
        if op == '+':
            return num1 + num2 == res
        elif op == '-':
            return num1 - num2 == res
        elif op == '*':
            return num1 * num2 == res
        elif op == '/':
            return num2 != 0 and num1 // num2 == res and num1 % num2 == 0
    except KeyError:
        return True  # Allow incomplete mappings during exploration
    return False

def solve_algebrogram(equations):
    parsed = parse_equations(equations)
    letters = sorted(set(''.join(equations)))
    if len(letters) > 10:
        return "NEEXISTUJE"  # Impossible if more than 10 letters

    # BFS queue: (current mapping, used digits)
    queue = deque([({}, set())])

    while queue:
        mapping, used = queue.popleft()

        if len(mapping) == len(letters):
            if all(evaluate(eq, mapping) for eq in parsed):
                return ''.join(str(mapping[char]) for char in letters)

        # Pick the next unmapped letter
        for char in letters:
            if char not in mapping:
                break

        # Try all possible digits
        for digit in range(10):
            if digit not in used and not (digit == 0 and char in {eq[0] for eq in parsed for eq in eq}):
                new_mapping = mapping.copy()
                new_mapping[char] = digit
                new_used = used | {digit}
                queue.append((new_mapping, new_used))

    return "NEEXISTUJE"

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

    results = []
    for i, (equations, expected) in enumerate(test_cases):
        start_time = time.time()
        result = brute_format_wrapper(solve_algebrogram(equations))
        elapsed_time = time.time() - start_time
        results.append((i + 1, expected == result, expected, result, elapsed_time))
    return results

# Run the tests
test_results = test_solve_algebrogram()

# Display test results
test_results
