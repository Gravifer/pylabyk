#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 12 10:28:15 2018

@author: yulkang
"""
import numpy as np
import torch
import scipy
from scipy import stats
import numpy_groupies as npg
import pandas as pd
from . import numpytorch

npt = numpytorch.npt_torch # choose between torch and np

#%% Shape
def ____SHAPE____():
    pass

def cat(arrays0, dim=0, add_dim=True):
    """
    @type arrays0: list
    """
    arrays = []
    if add_dim:
        for ii in range(len(arrays0)):
            arrays.append(np.expand_dims(arrays0[ii], dim))
    return np.concatenate(arrays, dim)

def vec_on(arr, dim, n_dim=None):
    arr = np.array(arr)
    if n_dim is None:
        n_dim = np.amax([arr.ndim, dim + 1])
    
#    if dim >= n_dim:
#        raise ValueError('dim=%d must be less than n_dim=%d' % (dim, n_dim))
    
    sh = [1] * n_dim
    sh[dim] = -1
    return np.reshape(arr, sh)

def cell2mat2(l, max_len=None):
    """
    INPUT: a list containing vectors
    OUTPUT: a matrix with NaN filled to the longest
    """
    if max_len is None:
        max_len = np.amax([len(l1) for l1 in l])
        
    n = len(l)
    m = np.zeros([n, max_len]) + np.nan
    
    for ii in range(n):
        l1 = l[ii]
        if len(l1) > max_len:
            m[ii,:] = l1[:max_len]
        elif len(l1) < max_len:
            m[ii,:len(l1)] = l1
        else:
            m[ii,:] = l1

    return m     

def dict_shapes(d):
    sh = {}
    for k in d.keys():
        v = d[k]
        if type(v) is list:
            sh1 = len(v)
            if sh1 == 0:
                compo = None
            else:
                compo = type(v[0])
        elif type(v) is np.ndarray:
            sh1 = v.shape
            compo = v.dtype.type
        elif torch.is_tensor(v):
            sh1 = tuple(v.shape)
            compo = v.dtype
        elif v is None:
            sh1 = 0
            compo = None
        else:
            sh1 = 1
            compo = None
        sh[k] = (type(v), compo, sh1)
    return sh

def DataFrame(dat):
    """
    Converts dict with 1- or 2-D np.ndarrays into DataFrame
    with 2-level MultiIndex of (name, column index)
    where all values are 2-D.
    :param dat: a dict()
    :return: pd.DataFrame
    """
    keys = dat.keys()
    l = []
    for key in keys:
        v = dat[key]
        assert type(v) is np.ndarray and v.ndim <= 2 and v.ndim >= 1, \
            '%s must be np.ndarray with 1 <= ndim <= 2 !' % key

        if v.ndim == 1:
            ix = pd.MultiIndex.from_product([[key]] + [[0]])
            l.append(pd.DataFrame(v[:,np.newaxis], columns=ix))
        else:
            ix = pd.MultiIndex.from_product([[key]] + [
                np.arange(s) for s in v.shape[1:]
            ])
            l.append(pd.DataFrame(v, columns=ix))
    return pd.concat(l, axis=1)

#%%
def ____BATCH____():
    pass

def meshfun(list_args, fun, n_out=1):
    """
    EXAMPLE:
    out[i,j] = fun(list_args[0][i], list_args[1][j])
    @type list_args: Iterable[Iterable]
    @type fun: function
    @rtype: np.ndarray
    """
    shape_all = ()
    list_args1 = []
    for arg in list_args:
        try:
            shape_all += arg.shape
            list_args1 += [arg.flatten()]
        except:
            shape_all += (len(arg),)
            list_args1 += [arg]
    shape_all += (n_out,)
    list_args1 = np.meshgrid(*list_args1, indexing='ij')
    for i in range(len(list_args1)):
        list_args1[i] = list_args1[i].flatten()
    res = []
    for args in zip(*list_args1):
        res.append(fun(*args))
    try:
        shape_each = res[0].shape[1:]
    except:
        shape_each = ()
        pass
    # shape_all += res[0].shape[1:]
    out = np.transpose(
        np.array(res).reshape(shape_all + shape_each, order='C'),
        (
                [len(shape_all) - 1]
                + list(np.arange(len(shape_all) - 1))
                + list(len(shape_all) + np.arange(len(shape_each)))
        )
    )
    return out

def demo_meshfun():
    out = meshfun([(1,2), (10, 20, 30)], lambda a, b: a + b * 10)
    # out[i,j] = fun(arg0[i], arg1[j])
    print(out)

    out1, out2 = meshfun(
        [(1,2), (10, 20, 30)],
        lambda a, b: (a + b * 10, a + b),
        n_out=2
    )
    # out1[i,j], out2[i,j] = fun(arg0[i], arg1[j])
    print(out1)
    print(out2)

    return out, out1, out2

#%% Type
def ____TYPE____():
    pass

def is_None(v):
    return v is None or (type(v) is np.ndarray and v.ndim == 0)

def is_iter(v):
    return hasattr(v, '__iter__')

#%% Stat
def ____STAT____():
    pass

def sem(v, axis=0):
    v = np.array(v)
    if v.ndim == 1:
        return np.std(v) / np.sqrt(v.size)
    else:
        return np.std(v, axis=axis) / np.sqrt(v.shape[axis])
    
def quantilize(v, n_quantile=5, return_summary=False, fallback_to_unique=True):
    """Quantile starting from 0. Array is flattened first."""

    v = np.array(v)

    if fallback_to_unique:
        x, ix = uniquetol(v, return_inverse=True)
    
    if (not fallback_to_unique) or len(x) > n_quantile:
        n = v.size
        ix = np.int32(np.ceil((stats.rankdata(v, method='ordinal') + 0.) \
                              / n * n_quantile) - 1)
    
    if return_summary:
        x = npg.aggregate(ix, v, func='mean')
        return ix, x
    else:   
        return ix
    
def discretize(v, cutoff):
    """
    Discretize given cutoff.
    
    ix[i] = 0 if v[i] < cutoff[0]
    ix[i] = k if cutoff[k - 1] <= v[i] < cutoff[k]
    v[i] = len(cutoff) if v[i] >= cutoff[-1]
    """
    v = np.array(v)
    ix = np.zeros(v.shape, dtype=np.long)
    
    cutoff = list(cutoff)
    cutoff.append(np.inf)
    n = len(cutoff)
    
    for ii in range(1,n):
        ix[(v >= cutoff[ii - 1]) & (v < cutoff[ii])] = ii
    
    ix[v >= cutoff[-1]] = n - 1    
    return ix
    
def uniquetol(v, tol=1e-6, return_inverse=False, **kwargs):
    return np.unique(np.round(np.array(v) / tol) * tol, 
                     return_inverse=return_inverse, **kwargs)

def ecdf(x0):
    """
    Empirical distribution.
    INPUT:
    x0: a vector or a list
    OUTPUT: 
    p[i] = Pr(x0 <= x[i])
    x: sorted x0
    """
    
    n = len(x0)
    p = np.arange(1.,n+1.) / n
    x = np.sort(x0)
    return p, x

def argmax_margin(v, margin=0.1, margin_from='second', 
                  fillvalue=-1, axis=None, out=None):
    """
    argmax with margin; If within margin, use fillvalue instead.
    margin_from: 'second' or 'last'.
    """
    
    assert out is None, "'out' input argument is not supported yet!"

    if type(v) is not np.ndarray:
        v = np.array(v)
        
    if axis is None:
        r = np.reshape(v, v.size)
    else:
        dims = [axis] + list(set(range(v.ndim)) - set([axis]))
        r = np.transpose(v, dims)
        
    a = np.argmax(r, axis=0)
    s = np.sort(r, axis=0)
    
    if margin_from == 'second':
        m = s[-1, ...] - s[-2, ...]
    else:
        m = s[-1, ...] - s[0, ...]
        
    not_enough_margin = m < margin
    a[not_enough_margin] = fillvalue
    return a

def argmin_margin(v, **kw):
    """argmin with margin. See argmax_margin for details."""
    return argmax_margin(-v, **kw)

def sumto1(v, axis=None, ignore_nan=True):
    if ignore_nan:
        if type(v) is np.ndarray:
            return v / np.nansum(v, axis=axis, keepdims=True)
        else:  # v is torch.Tensor
            return v / v.nansum(axis, keepdim=True)
    else:
        if type(v) is np.ndarray:
            return v / v.sum(axis=axis, keepdims=True)
        else: # v is torch.Tensor
            return v / v.sum(axis, keepdim=True)

def nansem(v, axis=None, **kwargs):
    s = np.nanstd(v, axis=axis, **kwargs)
    n = np.sum(~np.isnan(v), axis=axis, **kwargs)
    return s / np.sqrt(n)

def wpercentile(w, prct, axis=None):
    """
    :type v: np.ndarray
    """
    if axis is not None:
        raise NotImplementedError()
    cw = np.concatenate([np.zeros(1), np.cumsum(w)])
    cw /= cw[-1]
    f = scipy.interpolate.interp1d(cw, np.arange(len(cw)) - .5)
    return f(prct/100.)

    # if axis is None:
    #     axis = 0
    #     v = v.flatten()
    #     w = w.flatten()
    # z = vec_on(np.zeros(v.shape[axis]), axis, v.ndim)
    # cv = np.cumsum(v, axis)
    # cv = np.concatenate([z, cv], axis)
    # cw = np.cumsum(w, axis)
    # cw = np.concatenate
    # f = stats.interpolate.interp1d(w, cv)

def wmedian(w, axis=None):
    return wpercentile(w, prct=50, axis=axis)


#%% Distribution
def ____DISTRIBUTION____():
    pass

def pdf_trapezoid(x, center, width_top, width_bottom):
    height = 1. / ((width_top + width_bottom) / 2.)
    proportion_between = ((width_bottom - width_top) / width_bottom)
    width2height = height / proportion_between

    p = (1. - npt.abs(x - center) / (width_bottom / 2.)) * width2height
    p[p > height] = height
    p[p < 0] = 0
    return p

#%% Circular stats
def ____CIRCSTAT____():
    pass

def circdiff(angle1, angle2, maxangle=None):
    """
    :param angle1: angle scaled to be between 0 and maxangle
    :param angle2: angle scaled to be between 0 and maxangle
    :param maxangle: max angle. defaults to 2 * pi.
    :return: angular difference, between -.5 and +.5 * maxangle
    """
    if maxangle is None:
        maxangle = np.pi * 2
    return (((angle1 / maxangle)
             - (angle2 / maxangle) + .5) % 1. - .5) * maxangle

#%% Transform
def ____TRANSFORM____():
    pass

def logit(v):
    """logit function"""
    return np.log(v) - np.log(1 - v)

def logistic(v):
    """inverse logit function"""
    return 1 / (np.exp(-v) + 1)

def softmax(dv):
    if type(dv) is torch.Tensor:
        edv = torch.exp(dv)
        p = edv / torch.sum(edv)
    else:
        edv = np.exp(dv)
        p = edv / np.sum(edv)
        
    return p

def softargmax(dv):
    p = softmax(dv)
    a = np.nonzero(np.random.multinomial(1, p))[0][0]
    return a

def project(a, b, axis=None, scalar_proj=False):
    """
    Project vector a onto b (vector dimensions are along axis).
    :type a: np.array
    :type b: np.array
    :type axis: None, int
    :rtype: np.array
    """
    proj = np.sum(a * b, axis) / np.sum(b**2, axis)
    if scalar_proj:
        return proj
    else:
        return proj * b

#%% Binary operations
def ____BINARY_OPS____():
    pass

def conv_circ( signal, ker ):
    '''
        signal: real 1D array
        ker: real 1D array
        signal and ker must have same shape
        
        from https://stackoverflow.com/a/38034801/2565317
    '''
    return np.real(np.fft.ifft( np.fft.fft(signal)*np.fft.fft(ker) ))

#%% Image
def ____IMAGE____():
    pass

def nansmooth(u, sigma=1.):
    from scipy import ndimage

    isnan = np.isnan(u)

    v = u.copy()
    v[isnan] = 0.
    vv = ndimage.gaussian_filter(v, sigma=sigma)

    w = 1. - isnan
    ww = ndimage.gaussian_filter(w, sigma=sigma)

    r = vv / ww
    r[isnan] = np.nan

    return r


def convolve_time(src, kernel, dim_time=0, mode='same'):
    """
    @type src: np.ndarray
    @type kernel: np.ndarray
    @type dim_time: int
    @rtype: np.ndarray
    """
    if kernel.ndim == 1 and kernel.ndim < dim_time + 1:
        kernel = vec_on(kernel, dim_time, src.ndim)
    if kernel.ndim < src.ndim:
        kernel = np.expand_dims(
            kernel,
            np.arange(kernel.ndim, src.ndim)
        )
    if np.mod(kernel.shape[dim_time], 2) != 1:
        pad_width = np.zeros((kernel.ndim, 2), dtype=np.long)
        pad_width[dim_time, 1] = 1
        kernel = np.pad(kernel, pad_width, mode='constant')

    len_kernel_half = (kernel.shape[dim_time] - 1) // 2
    pad_width = np.zeros((src.ndim, 2), dtype=np.long)
    pad_width[dim_time, :] = len_kernel_half
    src = np.pad(src, pad_width, mode='constant')

    from scipy import ndimage
    dst = ndimage.convolve(src, kernel, mode='constant')
    dst = np.moveaxis(dst, dim_time, 0)

    if mode == 'same':
        dst = dst[:-(len_kernel_half * 2)]
    elif mode == 'full':
        pass
    else:
        raise ValueError('Unsupported mode=%s' % mode)
    dst = np.moveaxis(dst, 0, dim_time)
    return dst


def demo_convolve_time():
    # src = np.ones(3)
    src = np.array([1., 0., 0., 0., 0.])
    kernel = np.array([2., 3., 1., 0.])
    res = convolve_time(src, kernel, mode='same')

    from matplotlib import pyplot as plt
    plt.plot(kernel, 'b-')
    plt.plot(res, 'ro')
    plt.show()
    print(res)
    print((src.shape, kernel.shape, res.shape))

    src2 = vec_on(src, 2, 3)
    res = convolve_time(src2, kernel, dim_time=2)

    plt.plot(kernel, 'b-')
    plt.plot(res.flatten(), 'ro')
    plt.show()
    print(res)
    print((src2.shape, kernel.shape, res.shape))

    pass