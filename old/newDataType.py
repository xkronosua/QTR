#!/usr/bin/env python3
import scipy as sp

class Array(sp.ndarray):

    def __new__(cls, input_array, scale=[None,None]):
        # Input array is an already formed ndarray instance
        # We first cast to be our class type
        obj = sp.asarray(input_array).view(cls)
        # add the new attribute to the created instance
        obj.scale = scale
        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self, obj):
        # see InfoArray.__array_finalize__ for comments
        if obj is None: return
        self.scale = getattr(obj, 'scale', [None,None])