a = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 1, 1, 1, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     [0, 0, 1, 0, 1, 0, 0, 0, 0, 0],
     [0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
     [0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
   ]


def step(x, b):
    for r in range(len(b)):
        for s in range(len(b[0])):
            cnt=0
            for dr in (-1,0,1):
                for ds in range(-1,2):
                    rr=r+dr
                    ss=s+ds
                    cnt+=x[rr%len(b)][ss%(len(b[0]))]
            cnt-=x[r][s]
            if (cnt==2 and x[r][s]>0) or cnt==3:
                b[r][s]=1
            else:
                b[r][s]=0
    return b, x

b=[ [0]*len(a[0]) for i in a ]
import time
for s in range(50):
    print('------------ STEP', s, '------------')
    for i in a:
        print(''.join('X' if p!=0 else ' ' for p in i))
    time.sleep(0.4)
    a, b =step(a, b)
