from pylab import *
import cmath
from cmath import *
import sys
'''

#In[1]= (*
  - Length unit is cm,
   - Intensity unit is MW/cm2
  - [a] is measures in pixels(field)
*)

#In[2]= 

#In[3]= (*Input coeficient of On Axis Transmittance dependence \
aproximation obtained in Origin*)
'''
def calcReChi3CW(XY, m=1, a=10.5, Lambda=532, n0=1.7, d=14.46*10**(-4), z=79.1, L=12., f=8., r0=0.1):

	X, Y = XY[:,0], XY[:,1]
	X*=10**-3
	c = [float64(0.0)]*5
	#A, B1, B2, B3, B4 = [0, 0, 0, 0, 0]
	eq = np.polyfit(X, Y, m)[::-1]
	for i, j in enumerate(eq):
		print( i, j, m)
		if i > m: break
		c[i] = j
	A, B1, B2, B3, B4 = c
	print("-----\n",A,B1,B2,B3,B4)
	
	#In[8]= 

	#In[9]= '''input a in pixel obtained from gaus1.exe'''
	a *= float64(0.0025)#10.5*0.0025
	print(a)

	#In[10]= '''input Lambda in cm'''
	Lambda *= 10**(-7)
	print(Lambda)
	k = 2*pi/Lambda
	ld = k*a**2/2.
	'''input refractive index n0'''
	##n0 = 1.7
	Rfl = ((1 - n0)/(1 + n0))**2
	'''input thickness d in cm'''
	d *= 0.1
	print(d)

	#Out[10]= 0.0000532

	#Out[11]= 118105.

	#0.0000532

	#118105.

	#In[16]= 

	#In[17]= 
	alpha = 0.1

	#In[18]= ww[x_, a_, F_, ld_] = a*cmath.sqrt((1 - x/F)**2 + (x/ld)**2) 
	Rc = lambda x, rad, ld : rad*((1 - x/rad)**2 + (x/ld)**2)/(1 - x/rad*(1 + (rad/ld)**2))

	#In[20]= '''input distance PhD - Sample in cm'''
	##z = 79.1
	##r0 = 0.1
	##L = 12
	##f = 8
	r02 = r0**2
	ww = lambda x, a, F, ld : a*sqrt((1 - x/F)**2 + (x/ld)**2)
	Rc = lambda x, rad, ld: rad*((1 - x/rad)**2 + (x/ld)**2)/(1 - x/rad*(1 + (rad/ld)**2))
	'''input correct distance Sample -Lens in cm'''
	w = ww(L, a, f, ld)  
	'''input correct distance Sample -Lens in cm'''
	R = Rc(L, f, ld)
	lds = k*w**2/2
	b = -k*w**2*(1 - z/R)/(2*z)
	b2 = b**2
	ar2 = w**2*(1 + b2)*(z/lds)**2
	Norm1 = 1 - cmath.exp(-2*r02/ar2)
	wInt = w/cmath.sqrt(2)
	print("ww", w)
	#Out[25]= 0.0170141

	#Out[26]= -3.12949
	'''
	#In[33]= (* \
	T=1/(Norm1)*(Norm1+Phi/(2**(1.5))*Exp[-4*r02*(3+b2)/(ar2*(9+b2)\
	)]*cmath.sin(8*b*r02/(ar2*(9+b2))]+\[CurlyPhi)**2/(6*3**(0.5))*(Exp[-6*r02*(5+\
	b2)/(ar2*(25+b2))]*cmath.cos(24*b*r02/(ar2*(25+b2)))-Exp[-6*r02*(1+b2)/(ar2*\
	(9+b2))])+Phi**3/16*(1/3*cmath.exp(-8*r02*(7+b2)/(ar2*(49+b2)))*Sin[\
	48*r02*b/(ar2*(49+b2))]-Exp[-8*r02*(15+b2)*(1+b2)/(ar2*(25+b2)*(9+b2))\
	]*cmath.sin(16*r02*b*(1+b2)/(ar2*(25+b2)*(9+b2))) )) *)
	'''
	#In[34]= 
	Th0 = 1

	Th1 = -1/(Norm1)*exp(-4*r02*(3 + b2)/(ar2*(9 + b2)))*  sin(8*b*r02/(ar2*(9 + b2)))
	Th2 = 1/(Norm1)*(cmath.exp(-6*r02*(5 + b2)/(ar2*(25 + b2)))*
		cmath.cos(24*b*r02/(ar2*(25 + b2))) -cmath.exp(-6*r02*(1 + b2)/(ar2*(9 + b2))))

	Th3 = 1/(Norm1*8)*(1/3*cmath.exp(-8*r02*(7 + b2)/(ar2*(49 + b2)))*cmath.sin(48*r02*b/(ar2*(49 + b2))) - 
		cmath.exp(-8*r02*(15 + b2)*(1 + b2)/(ar2*(25 + b2)*(9 + b2)))*
		 cmath.sin(16*r02*b*(1 + b2)/(ar2*(25 + b2)*(9 + b2))) )
	#(*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*)

	Th4 = ((1/4.)*(1 - cmath.exp(-10*r02*(1 + b2)/(25 + b2))) -
		(1/3.)*(1 - 
		   cmath.exp(-10*r02*(1 + b2)*(21 + b2)/((9 + b2)*(49 + b2))))* 
		 cmath.cos(40*r02*b*(1 + b2)/((9 + b2)*(49 + b2))) +
		(1/12.)*(1 - cmath.exp(-10*r02*(9 + b2)/(81 + b2)))*
		 cmath.cos(80*r02*b/(81 + b2)))/(Norm1*5)
	print("Th_i: ", Th0,Th1,Th2,Th3,Th4)

	#Out[34]= 1

	#Out[35]= 0.0402903

	#Out[36]= 0.00695697

	#Out[37]= 0.000168408

	#Out[38]= -5.25015*10**-6

	#In[39]= 

	#In[40]= 
	#Phi = k*n2*Inten*(1 - Rfl)*(1 - cmath.exp(-2*Alpha]*d])/(2*Alpha]), 10)

	c1 = k*(1 - Rfl)*d
	print(c1)
	'''(1-cmath.exp(-2*Alpha]*d])/(2*Alpha))'''


	#Out[41]= 566.904

	#In[42]= 
	n21 = (Th0/Th1)*(B1/A)/c1*10**3
	n22 = cmath.sqrt((B2/A)*(Th0/Th2))/c1*10**(3)
	n23 = (Th0/Th3*(B3/A))**(1/3)/c1*10**(3)

	print(n21,n22,n23)
	#Out[42]= -1.03273*10**-9

	#Out[43]= 0.

	#Out[44]= 0.

	#In[45]= 
	hi31 = 3*abs(n21)*(n0/(4*pi))**2
	hi32 = 3*abs(n22)*(n0/(4*pi))**2
	hi33 = 3*abs(n23)*(n0/(4*pi))**2

	print(hi31,hi32,hi33)
	#Out[45]= 4.41439*10**-11

	#Out[46]= 0.

	#Out[47]= 0.
	'''
	#In[48]= 
	n201v = B1/A*Th0/(Th1*c1)*10**(3)
	n212v = B2/B1*Th1/(Th2*c1)*10**(3)
	n223v = B3/B2*Th2/(Th3*c1)*10**(3)

	#In[51]= 
	hi301 = 3*n201v*(n0/(4*pi))**2
	hi312 = 3*n212v*(n0/(4*pi))**2
	hi323 = 3*n223v*(n0/(4*pi))**2 


	print(hi301,hi312,hi323)
	#Out[51]= -4.41439*10**-11

	#Out[52]= 0.

	#During evaluation of In[51]= Power::infy: Infinite cmath.expression 1/0 encountered. >>

	#During evaluation of In[51]= Infinity::indet: Indeterminate cmath.expression 0 ComplexInfinity encountered. >>

	#Out[53]= Indeterminate

	#In[54]= 
	na1 = (abs(n21) + abs(n22) + abs(n23))*10**(3)/2
	na2 = (abs(n212v) + abs(n223v))*10**(3)/2
	nt = -0.0001*10**(3)
	T1 = lambda Inten : Th0 + Th1*(na1*c1)*Inten + Th2*(na1*c1)**2*Inten**2 +   Th3*(na1*c1)**3*Inten**3
	T2 = lambda Inten : Th0 + Th1*(na2*c1)*Inten + Th2*(na2*c1)**2*Inten**2 + Th3*(na2*c1)**3*Inten**3
	T3 = lambda Inten : Th0 + Th1*(nt*c1)*Inten + Th2*(nt*c1)**2*Inten**2 + Th3*(nt*c1)**3*Inten**3 + Th4*(nt*c1)**4* Inten**4
	Ex = lambda Inten : A + B1*Inten + B2*Inten**2 + B3*Inten**3 + B4*Inten**4 + 0.320
	'''
	'''
	Plot[{ Ex[Inten], T3[Inten]}, {Inten, 10, 40}, 
	 PlotStyle -> { Hue[0.4], Hue[0.9], Hue[0.1]}, 
	 AxesLabel -> {"Intensity[MW]", "On-ax Tr[r=0.1 cm]"}, 
	 PlotRange -> All]
	'''
	'''
	print("hi3 1-st method")
	hi3a1 = 3*na1*(n0/(4*pi))**2*10**(-3)
	print (hi3a1)
	print("hi3 2-st method") 
	hi3t = 3*na2*(n0/(4*pi))**2*10**(-3)
	print(hi3t)
	print ("hi3 fitting")
	hi3t = 3*nt*(n0/(4*pi))**2*10**(-3)
	print(hi3t)
	print("\[CapitalDelta]\[Phi] theoretical is")
	Phit = k*nt*d
	print(Phit)
	'''
	#Out[54]= 5.16365*10**-7

	#During evaluation of In[54]= Power::infy: Infinite cmath.expression 1/0 encountered. >>

	#During evaluation of In[54]= Infinity::indet: Indeterminate cmath.expression 0 ComplexInfinity encountered. >>

	#Out[55]= Indeterminate

	#Out[61]= \!\(\*
	'''
	During evaluation of In[54]= hi3 1-st method
	'''
	#Out[62]= 2.2072*10**-11

	#During evaluation of In[54]= hi3 2-st method

	#Out[63]= Indeterminate

	#During evaluation of In[54]= hi3 fitting

	#Out[64]= -0.0000128235

	#During evaluation of In[54]= \[CapitalDelta]\[Phi] theoretical is

	#Out[65]= -177.157

	#In[66]=		 


if __name__ == "__main__":
	
	
	print(len(sys.argv))
	if len(sys.argv) == 1:
		A = 1.0177#0.9753
		B1 = -1.74882*10**(-1)#0.00249
		B2 = 1.40326*10**(-4)#-0.00025
		B3 = 0
		B4 = 0
		
		eq = poly1d([B4,B3,B2,B1,A])
		x = arange(100)
		y = eq(x)
		calcReChi3CW(vstack((x,y)).T, m=2, a=49, Lambda=1064, n0=1.33, d=4,
			z=50, L=14, f=8,r0=0.1)
		#calcReChi3CW(vstack((x,y)).T, m=2, a=10.5, Lambda=532*10**-7, n0=1.7, d=14.46*10**(-4),
		#	z=79.1, L=12, f=8,r0=0.1)
	else:
		'''
		xy = loadtxt(sys.argv[1])
		r = [float(i) for i in sys.argv[2].split(',')]
		m = sys.argv[3]
		eq = poly1d(polyfit(xy[:,0], xy[:,1], m)
		calcReChi3CW(vstack(xy, m=m, a=48.02, Lambda=1064*10**-7, n0=1.7, d=0.2,
			z=54-19.7, L=19.7, f=8,r0=0.1)
		'''