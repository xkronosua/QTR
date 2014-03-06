from pylab import *
##In[199]= 
'''Leff calc      lengths in cm'''
T0 = 0.999999999
d = 50*10**(-4)
Leff = -(1. - T0)/(log(T0)/d)

#Out[201]= 0.005

#In[202]= 0.0014699999264999988`

#Out[202]= 0.00147

#In[203]= 

#In[204]= 
#(* beta [cm/MW] calc      using q [cm**2/MW], obtained in ORIGIN by \
#transmittance graph approximation *)
q = -0.01638*0.001
beta = q/Leff

#Out[205]= -0.003276

#In[206]= 

#In[207]= 

#In[208]= 
#(* Im(Hi3)[esu] calc    using beta [cm/MW] & lengths in cm *)
n0 = 1.5
lambd = 532*10**-7
c = 2.998*10**10
ImHi3 = (n0**2*lambd*c*beta*10**-14)/(19.2*pi**3)
print(ImHi3)
#During evaluation of #In[208]= Set::write: Tag Times in Hi3 Im is Protected. >>

#Out[211]= -1.97478*10**-13

#In[212]= 

#In[213]= 

#In[214]= (* n2 [cm/MW] calc      using fi [cm**2/MW], obtained in \
#ORIGIN by on-axis transmittance graph approximation,lengths in cm *)
#\
fi = 0.00031
n2 = (lambd)*fi/(2.*pi*Leff)
print(n2)
#Out[215]= 5.24957*10**-7

#In[216]= 

#In[217]= 
''' Re(Hi3)[esu] calc   using n2 [cm**2/MW] '''

ReHi3 = 3*(n0/(4.*pi))**2*n2*10**-3

#During evaluation of #In[217]= Set::write: Tag Times in Hi3 Re is Protected. >>

#Out[217]= 2.24392*10**-11
print(ReHi3)