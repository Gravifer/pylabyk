"""
See examples in the docstring of Cache (example_* at the bottom of this module)

USAGE 1. Use custom cache file name (good for parallel execution; recommended)
- Open cache
cache = CacheDict([(key1,value1),(key2,value2)])

- Check cache
cache.exists(key) # breaks from previous cacheutil

- Set cache
cache.setdict({key:val}) # breaks from previous cacheutil

- Get cache
val1, val2 = cache.getvalue([key1, key2]) # new
# dict = cache.getdict([key1, key2]) # not implemented yet

USAGE 2. Use a single cache file name and use locals() as the key
(old; use only when using locals() is necessary and gives too long file names)

- Open cache
cache = CacheSub(key=locals())

- Set cache
cache.setdict({subkey:val})

- Get cache
val1, val2 = cache.getvalue([subkey1, subkey2])
# dict = cache.getdict([key1, key2]) # not implemented yet

(not implemented)
"""

import os
from . import zipPickle, argsutil
from collections import OrderedDict as odict
from .argsutil import dict2fname
from .argsutil import kwdef
from .argsutil import rmkeys

def dict_except(d, keys_to_excl):
    return {k:d[k] for k in d if k not in keys_to_excl}

def obj2dict(obj, keys_to_excl=[], exclude_hidden=True):
    d = obj.__dict__
    if exclude_hidden:
        d = {k:d[k] for k in d if k[0] != '_'}
    if len(keys_to_excl) > 0:
        d = {k:d[k] for k in d if k not in keys_to_excl}
    return d

def dict2obj(d, obj):
    for k in d:
        obj.__dict__[k] = d[k]
    return obj

class Cache(object):
    """
    (Deprecated due to confusing interface. Use CacheDict or CacheSub instead.)
    Caches to file for fast retrieval.

    EXAMPLE 1 - use locals() to name the key inside a fixed cache file.
    See example_cache_fixed_file()

    EXAMPLE 2 - use custom cache file name (good for parallel execution):
    See example_cache_custom_file()
    """
    def __init__(self, fullpath='cache.pkl.zip', key=None, verbose=True,
                 ignore_key=False, hash_fname=False):
        """
        :param fullpath: use cacheutil.dict2fname(dict) for human-readable
        names, or use 'cache.zpkl' if using an old cache file.
        :param key: anything, e.g., locals(), that can serve as a key for dict.
        :param verbose: bool.
        :param ignore_key: bool.
        """
        if hash_fname:
            self.fullpath_orig = fullpath
            self.fullpath = argsutil.fname2hash(fullpath)
        else:
            self.fullpath_orig = fullpath
            self.fullpath = fullpath
        self.verbose = verbose
        self.dict = {}
        self.to_save = False
        if key is None:
            self.key = None
        else:
            self.key = self.format_key(key)
        self.ignore_key = ignore_key
        if os.path.exists(self.fullpath):
            self.dict = zipPickle.load(self.fullpath)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        try:
            self.__del__()
        except:
            raise Warning()

    def format_key(self, key):
        """
        :param key: non-None object that converts into a string, e.g., locals()
        :rtype: str
        """
        return '%s' % key

    def exists(self, key=None):
        """
        :param key: non-None object that converts into a string, e.g., locals()
        :rtype: bool
        """
        if self.ignore_key:
            return self.dict.__len__() > 0
        if key is None:
            key = self.key
        return self.format_key(key) in self.dict

    def ____DIRECT_SET_GET____(self):
        """
        Not recommended. Use getdict/setdict instead.
        :return:
        """
        pass

    def get(self, key=None, subkeys=None):
        """
        :param key: non-None object that converts into a string, e.g., locals()
        :param subkeys:if list, return a tuple of values for
                        the subkeys
        :rtype: Any
        """
        if self.ignore_key:
            key = list(self.dict.keys())[0]
        elif key is None:
            key = self.key
        if self.verbose and self.exists(key):
            if self.fullpath == self.fullpath_orig:
                print('Loaded cache from %s' % self.fullpath)
            else:
                print('Loaded cache from\n%s\n= %s'
                      % (self.fullpath, self.fullpath_orig))
        v = self.dict[self.format_key(key)]

        if subkeys is None:
            return v
        else:
            if type(subkeys) is str:
                return v[subkeys]
            else:
                return [v[k] for k in subkeys]

    def set(self, data, key=None):
        """
        Store the data in the cache.
        :param data: Use dict to allow get() and getdict() to use subkeys.
        :param key: non-None object that converts into a string, e.g., locals()
        :rtype: None
        """
        if key is None:
            # assert self.key is not None, 'default key is not specified!'
            key = self.key
        self.dict[self.format_key(key)] = data
        self.to_save = True

    def ____DICT_INTERFACE____(self):
        pass

    def getdict(self, subkeys=None, key=None):
        """
        Return a tuple of values corresponding to subkeys from default key.
        Assumes that self.dict[key] is itself a dict.
        :type subkeys: list, str
        :param subkeys: list of keys to the cached dict (self.dict[key]).
        :return: a tuple of values corresponding to subkeys from default key.
        """
        return self.get(key=key, subkeys=subkeys)

    def setdict(self, data_dict, key=None, update=True):
        """
        Updates self.dict using keys in data_dict
        :type data_dict: dict
        """
        if update:
            if self.exists(key):
                d0 = self.get(key)
            else:
                d0 = {}
            for key in data_dict.keys():
                d0[key] = data_dict[key]
        else:
            d0 = data_dict

        self.set(d0, key=key)

    def ____SAVE____(self):
        pass

    def save(self):
        pth = os.path.dirname(self.fullpath)
        if not os.path.exists(pth) and pth != '':
            os.mkdir(pth)

        self.dict['_fullpath_orig'] = self.fullpath_orig
        zipPickle.save(self.dict, self.fullpath)
        if self.verbose:
            if self.fullpath_orig == self.fullpath:
                print('Saved cache to %s'
                      % self.fullpath)
            else:
                print('Saved cache to\n%s\n= %s'
                      % (self.fullpath, self.fullpath_orig))
        # with open(self.fullpath, 'w+b') as cache_file:
        #     pickle.dump(self.dict, cache_file)
        #     if self.verbose:
        #         print('Saved cache to %s' % self.fullpath)

    def __del__(self):
        if self.to_save:
            self.save()

def kw2fname(kw, kw_def=None, dir='Data/cache', sort_kw=True):
    sort_kw = True
    name_cache = dict2fname(kwdef(kw, kw_def, sort_merged=sort_kw))
    fullpath = os.path.join(dir, name_cache + '.pkl.zip')
    return fullpath, name_cache

class CacheDict(object):
    """Defaults to directly addressing dict"""
    def __init__(self, fullpath='cache.',
                 **kwargs):
        self.cache = Cache(fullpath=fullpath, **kwargs)

    def exists(self, key=None):
        if key is None:
            return self.cache.exists()
        else:
            return key in self.cache.dict.keys()

    def setdict(self, d, update=True):
        if update:
            d0 = self.cache.dict
            for key in d.keys():
                d0[key] = d[key]
            self.cache.dict = d0
        else:
            self.cache.dict = d

    def getdict(self, keys=None):
        if keys is None:
            return self.cache.dict
        else:
            return {k:self.cache.dict[k] for k in keys}

    def getvalue(self, keys):
        if type(keys) is str:
            return self.cache.dict[keys]
        else:
            return [self.cache.dict[k] for k in keys]

    def save(self):
        self.cache.save()

class CacheSub(object):
    """Defaults to using a single cache file"""
    def __init__(self, key=None, **kwargs):
        self.cache = Cache(key=key, **kwargs)
        raise NotImplementedError()

def example_cache_fixed_file():
    def fun(test_param=1, to_recompute=False):
        cache = Cache(
            os.path.join('cache.pkl.zip'),
            locals()
        )
        if cache.exists() and not to_recompute:
            a, b = cache.getdict([
                'a', 'b'
            ])
        else:
            a = 10 * test_param
            b = 100 * test_param

            cache.update_dict({
                'a': a,
                'b': b
            })
        print('test_param: %d, a: %d, b:%d' % (test_param, a, b))

    for test_param_main in range(5):
        fun(test_param_main)

def example_cache_custom_file():
    pth_cache = 'Data/cache_example'
    def get_cache(subj, kw_model=None):
        # name_cache: to name corresponding figures
        if kw_model is None:
            kw_model = {}
        name_cache = dict2fname(kwdef( # cacheutil.dict2fname, argsutil.kwdef
            kw_model,
            odict([
                ('fit', 'gaze_emission'),
                ('sbj', subj),
            ])
        ))
        fit_file = os.path.join(pth_cache, name_cache + '.pkl.zip')
        cache = Cache(fit_file) # cacheutil.Cache
        return cache, name_cache

    # Key to find the cache
    subj = 'test_cache'
    kw_model = odict([
        ('field1', 1),
        ('field2', 'value2')
    ])

    # Set cache
    cache, name_cache = get_cache(subj, kw_model)
    cache.set({
        'key1': 10,
        'key2': 'value20'
    })
    cache.save()

    # Load cache
    cache2, name_cache = get_cache(subj, kw_model)
    val1, val2 = cache2.getdict(['key1', 'key2'])
    print(val1, val2)

# if __name__ == '__main__':
#     def fun(test_param=1, to_recompute=False):
#         cache = Cache(
#             os.path.join('cache.pkl'),
#             locals()
#         )
#         if cache.exists() and not to_recompute:
#             a, b = cache.getdict([
#                 'a', 'b'
#             ])
#         else:
#             a = 10 * test_param
#             b = 100 * test_param
#
#             cache.set({
#                 'a': a,
#                 'b': b
#             })
#         print('test_param: %d, a: %d, b:%d' % (test_param, a, b))
#
#     for test_param_main in range(5):
#         fun(test_param_main)