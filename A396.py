#!/usr/bin/python3

import math

class A396:

  def normdev_appx(self, z):
    return (1+erf_appx(z/sqrt(2)))/2

  def a_sample_function_with_no_args():
    return 99

  def erf_appx(self, z):
# Abramowitz and Stegun 7.1.28
    a = [1, 0.0705230784, 0.0422820123, 0.0092705272, 0.0001520143, 0.0002765672, 0.0000430638]
    return sign(z)*(1 - (1/pow(sum([pow(abs(z), i)*a[i] for i in range(len(a))]),16)))

  def compare(self, a, b, e):
    return abs(a - b) < e

  def tquantile(self, n, p):
# G. W. Hill, Algorithm 396
    if n < 1 or p > 1.0 or p <= 0:
      raise ValueError("Invalid argument")
    elif n == 2:
      return math.sqrt(2.0/(p*(2.0-p))-2.0)
    else:
      if n == 1:
        return math.cos(p*math.pi/2)/math.sin(p*math.pi/2)
      else:
        a = 1/(n-0.5)
        b = 48/(a**2)
        c = (((((20700*a/b)-98)*a)-16) * a) + 96.36;
        d = ((((94.5/(b+c))-3.0)/b) + 1) * math.sqrt(a*math.pi/2) * n
        x = d * p
        y = x ** (2/n)

        if y > 0.05 + a:
#x = normdev(p*0.5)
          x = 99#lqtnorm(p*0.5)
          y = x ** 2
          if n < 5: c = c + 0.3 * (n-4.5) * (x+0.6)
          c = (((0.05*d*x-5)*x-7)*x-2)*x+b+c
          y = (((((0.5*y+6.3)*y+36)*y+94.5)/c-y-3)/b+1)*x
          y = a * (y**2)
          if y > 0.002:
            y = math.exp(y) - 1
          else:
            y = 0.5 * y**2 + y
        else:
          y = ((1/(((n+6)/(n*y)-0.089*d-0.822)*(n+2)*3)+0.5/(n+4))*y-1)*(n+1)/(n+2)+1/y

        return math.sqrt(n*y)

  def ltqnorm( p ):
    """
    Modified from the author's original perl code (original comments follow below)
    by dfield@yahoo-inc.com.  May 3, 2004.

    Lower tail quantile for standard normal distribution function.

    This function returns an approximation of the inverse cumulative
    standard normal distribution function.  I.e., given P, it returns
    an approximation to the X satisfying P = Pr{Z <= X} where Z is a
    random variable from the standard normal distribution.

    The algorithm uses a minimax approximation by rational functions
    and the result has a relative error whose absolute value is less
    than 1.15e-9.

    Author:      Peter John Acklam
    Time-stamp:  2000-07-19 18:26:14
    E-mail:      pjacklam@online.no
    WWW URL:     http://home.online.no/~pjacklam
    """

    if p <= 0 or p >= 1:
      # The original perl code exits here, we'll throw an exception instead
      raise ValueError( "Argument to ltqnorm %f must be in open interval (0,1)" % p )

    # Coefficients in rational approximations.
    a = (-3.969683028665376e+01,  2.209460984245205e+02, \
         -2.759285104469687e+02,  1.383577518672690e+02, \
         -3.066479806614716e+01,  2.506628277459239e+00)
    b = (-5.447609879822406e+01,  1.615858368580409e+02, \
         -1.556989798598866e+02,  6.680131188771972e+01, \
         -1.328068155288572e+01 )
    c = (-7.784894002430293e-03, -3.223964580411365e-01, \
         -2.400758277161838e+00, -2.549732539343734e+00, \
         4.374664141464968e+00,  2.938163982698783e+00)
    d = ( 7.784695709041462e-03,  3.224671290700398e-01, \
          2.445134137142996e+00,  3.754408661907416e+00)

    # Define break-points.
    plow  = 0.02425
    phigh = 1 - plow

    # Rational approximation for lower region:
    if p < plow:
      q  = math.sqrt(-2*math.log(p))
    return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
            ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)

    # Rational approximation for upper region:
    if phigh < p:
      q  = math.sqrt(-2*math.log(1-p))
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
             ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)

    # Rational approximation for central region:
    q = p - 0.5
    r = q*q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)

