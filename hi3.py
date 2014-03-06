from pylab import *



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
A = 0.77683
B1 = -1.83241*10**(-5)
B2 = 10**-50
B3 = 10**-50
B4 = 10**-50

#In[8]= 

#In[9]= '''input a in pixel obtained from gaus1.exe'''
a = 24*0.00253 

#In[10]= '''input Lambda in cm'''
Lambda = 0.532*10**(-4)
k = 2*pi/Lambda
ld = k*a**2/2
'''input refractive index n0'''
n0 = 1.5
Rfl = ((1 - n0)/(1 + n0))**2
'''input thickness d in cm'''
d = 50*10**(-4)

#Out[10]= 0.0000532

#Out[11]= 118105.

0.0000532

118105.

#In[16]= 

#In[17]= 


#In[18]= ww[x_, a_, F_, ld_] = a*sqrt((1 - x/F)**2 + (x/ld)**2) 
Rc = lambda x, rad, ld : rad*((1 - x/rad)**2 + (x/ld)**2)/(1 - x/rad*(1 + (rad/ld)**2))

#In[20]= '''input distance PhD - Sample in cm'''
z = 68
r0 = 0.1 
r02 = r0**2
ww = lambda x, a, F, ld : a*sqrt((1 - x/F)**2 + (x/ld)**2)
Rc = lambda x, rad, ld: rad*((1 - x/rad)**2 + (x/ld)**2)/(1 - x/rad*(1 + (rad/ld)**2))
'''input correct distance Sample -Lens in cm'''
w = ww(14, a, 11, ld)  
'''input correct distance Sample -Lens in cm'''
R = Rc(14, 11, ld)
lds = k*w**2/2
b = -k*w**2*(1 - z/R)/(2*z)
b2 = b**2
ar2 = w**2*(1 + b2)*(z/lds)**2
Norm1 = 1 - exp(-2*k*r02/ar2)
wInt = w/sqrt(2)

#Out[25]= 0.0170141

#Out[26]= -3.12949
'''
#In[33]= (* \
T=1/(Norm1)*(Norm1+Phi/(2**(1.5))*Exp[-4*r02*(3+b2)/(ar2*(9+b2)\
)]*sin(8*b*r02/(ar2*(9+b2))]+\[CurlyPhi)**2/(6*3**(0.5))*(Exp[-6*r02*(5+\
b2)/(ar2*(25+b2))]*cos(24*b*r02/(ar2*(25+b2)))-Exp[-6*r02*(1+b2)/(ar2*\
(9+b2))])+Phi**3/16*(1/3*exp(-8*r02*(7+b2)/(ar2*(49+b2)))*Sin[\
48*r02*b/(ar2*(49+b2))]-Exp[-8*r02*(15+b2)*(1+b2)/(ar2*(25+b2)*(9+b2))\
]*sin(16*r02*b*(1+b2)/(ar2*(25+b2)*(9+b2))) )) *)
'''
#In[34]= 
Th0 = 1

Th1 = -1/(Norm1*2**(.5))*exp(-4*r02*(3 + b2)/(ar2*(9 + b2)))*  sin(8*b*r02/(ar2*(9 + b2)))
Th2 = 1/(Norm1*3*3**(0.5))*(exp(-6*r02*(5 + b2)/(ar2*(25 + b2)))*
     cos(24*b*r02/(ar2*(25 + b2))) - 
    exp(-6*r02*(1 + b2)/(ar2*(9 + b2))))
Th3 = 1/(Norm1*8)*(1/3*exp(-8*r02*(7 + b2)/(ar2*(49 + b2)))*
     sin(48*r02*b/(ar2*(49 + b2))) - 
    exp(-8*r02*(15 + b2)*(1 + b2)/(ar2*(25 + b2)*(9 + b2)))*
     sin(16*r02*b*(1 + b2)/(ar2*(25 + b2)*(9 + b2))) )*(1/sqrt(4))

'''!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'''

Th4 = ((1/4.)*(1 - exp(-10*r02*(1 + b2)/(25 + b2))) -
     (1/3.)*(1 - 
        exp(-10*r02*(1 + b2)*(21 + b2)/((9 + b2)*(49 + b2))))* 
      cos(40*r02*b*(1 + b2)/((9 + b2)*(49 + b2))) +
     (1/12.)*(1 - exp(-10*r02*(9 + b2)/(81 + b2)))*
      cos(80*r02*b/(81 + b2)))/(Norm1*5)*(1/sqrt(5))

'''!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'''


#Out[34]= 1

#Out[35]= 0.0402903

#Out[36]= 0.00695697

#Out[37]= 0.000168408

#Out[38]= -5.25015*10**-6

#In[39]= 

#In[40]= 
#Phi = k*n2*Inten*(1 - Rfl)*(1 - exp(-2*Alpha]*d])/(2*Alpha]), 10)

c1 = k*(1 - Rfl)*d
'''(1-exp(-2*Alpha]*d])/(2*Alpha))'''


#Out[41]= 566.904

#In[42]= 
n21 = (Th0/Th1)*(B1/A)*10**(-3)/c1
n22 = sqrt((B2/A)*(Th0/Th2))/c1*10**(-3)
n23 = (Th0/Th3*(B3/A))**(1/3)/c1*10**(-3)

#Out[42]= -1.03273*10**-9

#Out[43]= 0.

#Out[44]= 0.

#In[45]= 
hi31 = 3*abs(n21)*(n0/(4*pi))**2
hi31 = 3*abs(n22)*(n0/(4*pi))**2
hi33 = 3*abs(n23)*(n0/(4*pi))**2

#Out[45]= 4.41439*10**-11

#Out[46]= 0.

#Out[47]= 0.

#In[48]= 
n201v = B1/A*Th0/(Th1*c1)*10**(-3)
n212v = B2/B1*Th1/(Th2*c1)*10**(-3)
n223v = B3/B2*Th2/(Th3*c1)*10**(-3)

#In[51]= 
hi301 = 3*n201v*(n0/(4*pi))**2
hi312 = 3*n212v*(n0/(4*pi))**2
hi323 = 3*n223v*(n0/(4*pi))**2 

#Out[51]= -4.41439*10**-11

#Out[52]= 0.

#During evaluation of In[51]= Power::infy: Infinite expression 1/0 encountered. >>

#During evaluation of In[51]= Infinity::indet: Indeterminate expression 0 ComplexInfinity encountered. >>

#Out[53]= Indeterminate

#In[54]= 
na1 = (abs(n21) + abs(n22) + abs(n23))*10**(3)/2
na2 = (abs(n212v) + abs(n223v))*10**(3)/2
nt = -0.03*10**(1)
T1 = lambda Inten : Th0 + Th1*(na1*c1)*Inten + Th2*(na1*c1)**2*Inten**2 +   Th3*(na1*c1)**3*Inten**3
T2 = lambda Inten : Th0 + Th1*(na2*c1)*Inten + Th2*(na2*c1)**2*Inten**2 + Th3*(na2*c1)**3*Inten**3
T3 = lambda Inten : Th0 + Th1*(nt*c1)*Inten + Th2*(nt*c1)**2*Inten**2 + Th3*(nt*c1)**3*Inten**3 + Th4*(nt*c1)**4* Inten**4
Ex = lambda Inten : A + B1*Inten + B2*Inten**2 + B3*Inten**3 + B4*Inten**4 + 0.320

'''
Plot[{ Ex[Inten], T3[Inten]}, {Inten, 10, 40}, 
 PlotStyle -> { Hue[0.4], Hue[0.9], Hue[0.1]}, 
 AxesLabel -> {"Intensity[MW]", "On-ax Tr[r=0.1 cm]"}, 
 PlotRange -> All]
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

#Out[54]= 5.16365*10**-7

#During evaluation of In[54]= Power::infy: Infinite expression 1/0 encountered. >>

#During evaluation of In[54]= Infinity::indet: Indeterminate expression 0 ComplexInfinity encountered. >>

#Out[55]= Indeterminate

#Out[61]= \!\(\*
'''
GraphicsBox[{{}, {}, 
{Hue[0.4], LineBox[CompressedData["
1:eJwV0H1M02cQB/BmZSDSoRYFNiZvKUh4mRRKBQrt0ac60KC8VBkb8jYUpEwb
ZYJDhxAjEypOnICoFQpzQxQUR31hDhAVKwMpSksKqGyYKcKAVaVQXna/Py6X
T/K9XO6ckvdE7fiARqOFY1H9PqtoJY3GggOT6uyhoimB24b45UoTFniPn9hE
uTCVzcgwZ8E/r8PtKUdc0tL7mSzY+reqfRA9uJalb3DBvKbNkvLbwDvqhE2Y
b75Wo0M7R04Ut5RivuBkjxadeyjaPNfLBbztI9160VmvfuJ8mekKM288R+6j
/+Jp42Q/r4GNwY7S22j6QNloW48bGKVlfg3oZJm6PnqVO7SIJGbVaF9XhjRI
5AFLz22rLUMLe1tS82SekHZKHlOENns0dU/V7QUu36QLctGCSyyHXcbPQPIo
fHof+qvNr2IaHb2hveN4cyr6cfMf8oGb3qAIfbklDm2/RVxuupkNw3WtqyPR
MonrlecTbPBtMEyLqP1z2TBy1Ac+4oYqAtAzq5ZMlLr7giHu7Rde6Iqt2yI2
dfrC+p2sMCd0prmLt0cSB2z1EnNr9O4N3h636H6w6LBcY46umm6u2XvWDzJ6
OvcuFE4J9OwjAToBF8YcR+z+QzuWWOSRYS50RR9eeIk+utPq8/6sdcBZyrmm
Q1vci3Gzs/OHhkSRtButOv3pD8eu+8PVwIzFu+jk45UVM6EBwJy2eXgD/Yll
0kObNwFQEO14vo6apysyk/IDId8XhJVouzyHoFhXHpy8/rv+FNrUJU4Z1cED
mvWdZwVoj+CPG7K2B8F749MzB9F7njHbN9KCYSEvLEmKHtPLtoaVB0NxUZ8h
BS1a+6AizIsPuVkvVbHoZj3PON3Nh3x61C/haImnj069QwAMK41YiF6d5TN6
2QSg9q7Skot2ZsoumkYCdL2rL3dHr4T1QcNnASItPOIc0KWN554zxwFetdI9
rdCcBI5Q5x8CprP6TjPq/oj0RkNhCKx7AtnGY1OCQ08XjWUDIaAqXhE/gW4q
6TPpchXCcNeM1Qj64Okwu9hsITCu8DVadGLv/OR394TQsuxs2p9otmJF5epl
BHrFOZw2dImyPc4mkcB0wE1GE3r5h8r+i3UEahSMplq0toofbLhMINk9NZ+y
nN9RFVZPwKmxbQtlz+z+9LGrBORt+0d/RYe+mZ1jKwmcefHCgfJhtcDpTiuB
YvumwovoyfOqXU/6CByo2J5Yjb4RGNXN0hLwd77pRfl7rc5nfz+B97VMowLN
WDFmtB0gkHmr4zRltyOWxfEvCOzuZ3dWUfelRze+HiWQYm3KrUSvMRu05o0R
cJYn0in/W52SIxsnMOzS3HOB+s/Qt6K1kwTi/aQSyuUR5ZrMdwRixbpKOTph
3JH34D0B20HObsquhbUXbAwENF+f4FH+rf122u1ZAuJ9Is15dE4i6bKYI8A0
yqspC+c72dvnCajzZ6SUl1SIS+sXCPy4VMyn/Jg7NLu4SGBzSb0F5f8BCZpX
9w==
"]]}, 
{Hue[0.9], LineBox[CompressedData["
1:eJwVjWs0lAkYgCfzjRLHDqWxq1KdoVkkM1TE8M58EqnJLU41NcyRQmdtu1p2
c6vNpWlyQqRxqSSWlWpqp2LD+5GoXAuzRNla5bZILrlk2x/Pec7z61krDfM6
pEGj0XZ94X8/Yp9dTqOx4Q7zdMMRn3jkuBxkqgg2aLT2tR07Eo+yw1ydo1ps
mB+amEqKikeP4g66Wp8NkwLZtd78eHy5kT1+04QNatknT/5kPH7c+rBF4v6l
AyJeXstKwHWeI8mVGWzoTvaMFo8lYmy0t1bsBhMYZvJvTNXLMOL9BZt94aZg
3L0rP7v/PP5t3yGWX18PNop7Pcq6C0jvujiAzRz4VetiQ6HVJZTKW0q9Dcwg
T3p+XdyDXLQ21fnewdkcqvQy72fvyUNha+Xhk3IL8HPJOR7BKMDFT8Zq6hs3
gOhsYN0iTjE6FbONg2ctocYs2jfn11LcL3rvp1xjBW9YtU0xA7exqbwit+u+
FRg7L0pvUd7F1bt9MjVFXDjeWGBWXHYP5aGmN16NcGG7yJJVGFCO1nOR8DaB
BxpX7Diq9ZX4yWDJSIaZNRS+NWtZ1o6o2OPr4f7UGs710WPRtQbDtUyszANs
YCLwUuze+lr8zsXK/AF9EyQ80o1xxnq8OlWe/0PWJliwTDoqefwMx7mn7Tqd
NsNIrnBHkkUzrknVPkn2boY3Dpo8jkErJgQt266O2AKnDHVXt2u8QO0aP46R
kS2o49oLc7a1Y336yqQzd2wh36/uDnFOjdJzVxSfXO3gt2Bzhe94J36jG1DH
GrSD5rt99LTKbtSm54UHnNoK/T2Cqp9dXqPRSWOHvab20OdsUGH3rhc1TcQq
r8f2kNaQHKaV+wbN+V/fjDjgAB3PEg8v9f4Hw3r0q3fQ+MC1vp0t2/kOh8bl
e9wy+aCnFm0Rk/3ovLFW4bbBEcokP5bGiAaxfNx+dqrREQLFJgJp0TCGWvA6
Ww45gcufoaFun0dwVQRvoIQAEHc9a+D5juE6fXmBpieAW1NcxYWiD7gctjn0
ZgG83lmT+teSj5ihzH6lPwxQzPkQFZQ1gTYSG2GnrQB0clhSXc4USj1ClNMy
AQh2v1CmD09j9IuF2YtdAmCIygpuVs/gH6ltRIOpEGR113dYpcxhVLqb0d5I
IQQzH00mXv6M/q3zo7/UCKHEMDdYx4tGcfP0rqz6ioS82iKTY/sXUamqajHL
n4SKJ9E+kWc0KCZDpS74nQQ/plbkh1t0quOqI3+6hISYFTGHbFV0Ktfx8VW3
UhKysmjS2HI6ZRGpDhm6RYI1vzKJWUunXAdn5rgqEvjGRilOXXQqrsVp7cMq
EmYlrBvNDIIazakPft5GQppgjFm1n6DubfVqZHeQcLlVbsoJIKiYjk7eT2oS
Kn2rd6cEEZSO3tCsYRcJrmfSuoOOERTntG7ywdckLPbDgdWJBOUf4q3sHyDh
VKL/IKUkqPWLX66wHyJhX3Obu8N9gvr3WuAJ+TAJhiFWlOohQUV1H3feOEpC
QRRnrLSOoDI9MtvDJ0jIWfmtuKSHoCTDa+xrJ0mw7WwIs3xLUKayosusaRJS
aTGK2/0Edbe67EjZDAkpmLap/CNBnfAnG7TnSHBfEBYIZghKOP+Ue2CehNHB
85b1CwS1ROGTUfr5y1+S1+jJYFBNm7tnFhZIeM7LTuhayqD+A8xKVqg=
"]]}},
AspectRatio->0.6180339887498948,
Axes->True,
AxesLabel->{
FormBox["\"Intensity[MW]\"", TraditionalForm], 
FormBox["\"On-ax Tr[r=0.1 cm]\"", TraditionalForm]},
AxesOrigin->{10., 0},
Method->{},
PlotRange->{All, All},
PlotRangeClipping->True,
PlotRangePadding->{Automatic, Automatic}]\)

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