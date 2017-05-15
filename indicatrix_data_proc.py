import sys
import pandas
import json
import matplotlib.pyplot as plt
filename = sys.argv[1]

from itertools import takewhile
header = []
comments = []
#with open('filters.dict') as f:
#	filtersDict = json.load(f)	
filtersDict = {"532": {1:1,
							'1': 1,
							"OP06": 10**-0.6,
							"OP09": 10**-0.9,
							"OP18": 10**-1.8
							}}
filtersRaw = []
WAVELENGHT = "532"


def convertRawFilter(filt,wavelenght):
	filt = filt.upper()
	filters = filt.replace(' ','').replace('\n','').replace('\t','').split(',')
	conv = [filtersDict[wavelenght][i] for i in filters]
	res = 1
	for i in conv:
		res*=i
	return res



with open(filename, 'r') as fobj:
	# takewhile returns an iterator over all the lines 
	# that start with the comment string
	for n,line in enumerate(fobj):
		if line.startswith('#'):
			#print(n, line)
			comments.append([n,line.split(';')])
		if line.startswith('#Filter:'):
			print(n, line)
			filtersRaw.append([n, convertRawFilter(line.split(':')[-1], WAVELENGHT)])
		if line.startswith('#ch'):
			header = line[1:-1].split('\t')
	#headiter = takewhile(lambda s: ss(s), fobj)
	# you may want to process the headers differently, 
	# but here we just convert it to a list
	#header = list(headiter)
df = pandas.read_csv(filename, comment='#',sep='\t',names = header)
df['filter'] = pandas.np.ones(len(df))
k = pandas.np.where(df['N']==1)[0]

for i in range(len(k)-1):
	df['filter'][k[i]:k[i+1]] = filtersRaw[i][1]

df['scat'] = df['ch3']/df['filter']
df = df[df['scat']>=0]
df.plot(x=df.index,y='scat', logy=1)
plt.show()

df.to_csv(filename+"_proc.dat")

