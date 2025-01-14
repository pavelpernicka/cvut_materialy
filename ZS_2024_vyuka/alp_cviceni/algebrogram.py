from itertools import permutations
import re
import time

def is_valid_assignment(equations, assignment):
    # Replace letters with digits based on the assignment
    def substitute(equation):
        return ''.join(str(assignment[ch]) if ch in assignment else ch for ch in equation)

    for equation in equations:
        # Substitute and evaluate
        substituted = substitute(equation)
        try:
            left, right = substituted.split('=')
            if eval(left) != eval(right):
                return False
        except:
            return False
    return True

def solve_algebrogram(equations):
    # Extract unique letters
    letters = sorted(set(re.findall(r'[A-Z]', ''.join(equations))))
    if len(letters) > 10:
        return "NEEXISTUJE"

    for perm in permutations(range(10), len(letters)):
        assignment = dict(zip(letters, perm))
        # Ensure no leading zeroes
        if any(assignment[equation[0]] == 0 for equation in re.findall(r'\b[A-Z]+\b', ''.join(equations))):
            continue
        if is_valid_assignment(equations, assignment):
            return ''.join(str(assignment[letter]) for letter in letters)

    return "NEEXISTUJE"

# Test the solution with provided test cases
def main():
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

    for i, (input_data, expected) in enumerate(test_cases):
        start_time = time.time()
        result = solve_algebrogram(input_data)
        elapsed_time = time.time() - start_time
        print(f"Test case {i+1}: {'PASSED' if result == expected else 'FAILED'}")
        print(f"Expected: {expected}, Got: {result}, Time: {elapsed_time:.4f}s\n")

if __name__ == "__main__":
    main()



