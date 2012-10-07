
import random
import math
import numpy as np

data=[]

for line in open('douban.dat'):
  substrs = line.split('::')
  
  data.append((substrs[0], substrs[1], float(substrs[2])))

data = data[:20000]

def InitLFM(datas, F):
  p = dict()
  q = dict()
  for u, i, rui in datas:
    if not u in p:
      p[u] = np.random.rand(F) / math.sqrt(F)
    if not i in q:
      q[i] = np.random.rand(F) / math.sqrt(F)
  
  return (p,q)

def Predict(u, i, p, q, F):
  return np.dot(p[u], q[i])

def LearningLFM(train, F, n, alpha, lam):
  (p,q) = InitLFM(data, F)
  for step in range(0, n):
    totalerror = 0.0
    for u, i, rui in train:
      pui = Predict(u, i, p, q, F)
      eui = rui - pui
      totalerror += np.abs(eui)
      p[u] += alpha * (q[i] * eui - lam * p[u])
      q[i] += alpha * (p[u] * eui - lam * q[i])
    print totalerror
    alpha *= 0.9
  
  return (p,q)

(p,q) = LearningLFM(data, 100, 100, 0.07, 0.01)
for u, i, rui in data[:10]:
  pui = Predict(u, i, p, q, 10)
  print rui - pui
