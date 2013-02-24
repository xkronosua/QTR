from pylab import *
import scipy.interpolate as interp
import sys

def F(name,k=3,s=0.00001,N=2000,l=-1,r=0):
    a=loadtxt(name+'_1', delimiter=',')
    b=loadtxt(name+'_2', delimiter=',')
    A=concatenate((a,b[5:]))
    A=A[A[:,0].argsort()]
    x=A[:,0]
    y=A[:,1]
    xnew=linspace(x.min(),x.max(),N)
    ynew=interp.UnivariateSpline(x,y,k=3,s=0.00001)(xnew)
    out=array([xnew,ynew]).T
    plot(x,y,'o',xnew,ynew,'.')
    savetxt("./interp/"+name,out)
    show()
    return out

if __name__ == '__main__':
	p=sys.argv[1:]
	F(p[0],p[1],p[2],p[3],p[4],p[5])
	
