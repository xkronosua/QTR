import scipy as sp
from scipy.optimize import leastsq


def calcImChi3(data, d=0.5, n0=1.33, Lambda=1064, exp_type="CW"):
    sp.can_cast(sp.complex128,sp.float64, casting='safe')
    X = data[:,0]
    Y = data[:,1]
    print(data.shape)
    Lambda*=10**-7
    eq = sp.polyfit(X,Y,1)[0]
    print("Sign:",eq/abs(eq))
    bSign = eq/abs(eq)*0.001
    T0 = 1
    if exp_type=="CW":
        fit_func = lambda  I, T0, bLeff: T0*sp.log(1+bLeff*I)/(bLeff*I)
        def residuals( p, y, x): 
            err = y - fit_func(x, p[0], p[1])
            err = sp.array(err, dtype='complex128')
            return err.real**2+err.imag**2
        
        params = leastsq(residuals,[0.5,bSign], args=(Y, X))
        T0, bLeff = params[0]
        print("T0 = %f, bLeff = %f"%(T0, bLeff))
        Leff = -(1. - T0)/(sp.log(T0)/d)
        print('Leff', Leff)
        beta = bLeff/Leff
        c = 2.998*10**10
        ImHi3 = (n0**2*Lambda*c*beta*10**-14)/(19.2*sp.pi**3)
        print("ImHi3", ImHi3)
        x_new = sp.linspace(X.min(), X.max(), 300)
        y_new = fit_func(x_new, T0, bLeff)
    if exp_type=="PICO":
        fit_func = lambda  I, T0, bLeff: T0*sp.log(1+bLeff*I)*(1+0.228*bLeff*I)/(bLeff*I)/(1+0.136*bLeff*I)
        def residuals( p, y, x): 
            err = y - fit_func(x, p[0], p[1])
            err = sp.array(err, dtype='complex128')
            return err.real**2+err.imag**2

        params = leastsq(residuals,[0.5,bSign], args=(Y, X))
        T0, bLeff = params[0]
        print("T0 = %f, bLeff = %f"%(T0, bLeff))
        Leff = -(1. - T0)/(sp.log(T0)/d)
        print('Leff', Leff)
        beta = bLeff/Leff
        c = 2.998*10**10
        ImHi3 = (n0**2*Lambda*c*beta*10**-14)/(19.2*sp.pi**3)
        print("ImHi3", ImHi3)
        x_new = sp.linspace(X.min(), X.max(), 300)
        y_new = fit_func(x_new, T0, bLeff)
    return (ImHi3, beta, Leff, T0, x_new, y_new)


if __name__ == "__main__":
    '''
    def func(x, a, b):
        return a*x + b

    scipy.optimize.curve_fit(func, x, y) will return a numpy array containing two arrays: the first will contain values for a and b that best fit your data, and the second will be the covariance of the optimal fit parameters.

    Here's an example for a linear fit with the data you provided.

    import numpy as np
    from scipy.optimize import curve_fit

    x = np.array([1, 2, 3, 9])
    y = np.array([1, 4, 1, 3])

    def fit_func(x, a, b):
        return a*x + b

    params = curve_fit(fit_func, x, y)

    [a, b] = params[0]
    '''

    from pylab import *
    ##In[199]=
    '''Leff calc      lengths in cm'''
    T0 = 0.7
    d = 0.5
    Leff = -(1. - T0) / (log(T0) / d)
    print('Leff', Leff)
    # Out[201]= 0.005

    # In[202]= 0.0014699999264999988`

    # Out[202]= 0.00147

    # In[203]=

    # In[204]=
    # (* beta [cm/MW] calc      using q [cm**2/MW], obtained in ORIGIN by \
    # transmittance graph approximation *)
    q = -0.0015698676884758141  # 436,8367577373*0.001#
    beta = q / Leff
    print('beta', beta)
    # Out[205]= -0.003276

    # In[206]=

    # In[207]=

    # In[208]=
    # (* Im(Hi3)[esu] calc    using beta [cm/MW] & lengths in cm *)
    n0 = 1.33
    lambd = 1064 * 10 ** -7
    c = 2.998 * 10 ** 10
    ImHi3 = (n0 ** 2 * lambd * c * beta * 10 ** -14) / (19.2 * pi ** 3)
    print("ImHi3", ImHi3)
    # During evaluation of #In[208]= Set::write: Tag Times in Hi3 Im is Protected. >>

    # Out[211]= -1.97478*10**-13

    # In[212]=

    # In[213]=

    # In[214]= (* n2 [cm/MW] calc      using fi [cm**2/MW], obtained in \
    # ORIGIN by on-axis transmittance graph approximation,lengths in cm *)
    # \
    fi = 0.00031
    n2 = (lambd) * fi / (2. * pi * Leff)
    print(n2)
    # Out[215]= 5.24957*10**-7

    # In[216]=

    # In[217]=
    ''' Re(Hi3)[esu] calc   using n2 [cm**2/MW] '''

    ReHi3 = 3 * (n0 / (4. * pi)) ** 2 * n2 * 10 ** -3

    # During evaluation of #In[217]= Set::write: Tag Times in Hi3 Re is Protected. >>

    # Out[217]= 2.24392*10**-11
    print(ReHi3)
