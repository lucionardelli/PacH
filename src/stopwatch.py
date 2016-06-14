#!/usr/bin/env python
# -*- coding: UTF-8

import time
class StopWatchObj(object):

    def __init__(self,*args,**kwargs):
        self.output = {'times': {}}

    @classmethod
    def stopwatch(cls, func):
        def do_measure(self, *args, **kwargs):
            times = self.output.setdefault('times',{})
            name = func.func_name
            start_time = time.time()
            ret = func(self, *args, **kwargs)
            elapsed_time = time.time() - start_time
            times[name] = elapsed_time
            return ret
        return do_measure

    def pout(self):
        for k,v in self.output.items():
            print '%s -> %s'%(k,v)
