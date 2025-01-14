#!/usr/bin/env python3
def calculate_scores(p1, p2, p3):
    if len(p1) != len(p2) or len(p2) != len(p3):
        return "ERROR"
    if any(x < 0 for x in p1 + p2 + p3):
        return "ERROR"
    
    scores = [0, 0, 0]
    hrom = 0

    for i in range(len(p1)):
        cards = [p1[i], p2[i], p3[i]]
        max_card = max(cards)

        # kolikrát max_card
        max_count = 0
        winner = -1
        for idx in range(3):
            if cards[idx] == max_card:
                max_count += 1
                winner = idx

        if max_count == 1:
            scores[winner] += 3 + hrom
            hrom = 0
        else:
            hrom += 3

    return " ".join(map(str, scores))

p1 = list(map(int, input().split()))
p2 = list(map(int, input().split()))
p3 = list(map(int, input().split()))
print(calculate_scores(p1, p2, p3))
