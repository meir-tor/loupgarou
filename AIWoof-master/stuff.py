listi = [[4,5],[3,2],[3,5],[3,6]]

black = []

for pair in listi:
        if 3 in pair:
                for a in pair:
                        if a != 3:
                                black.append(a)

print(black)
