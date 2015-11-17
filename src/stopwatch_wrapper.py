#!/usr/bin/env python
# -*- coding: UTF-8

import time

from config import logger

def stopwatch(func):
    def do_measure(self, *args, **kwargs):
        if hasattr(self,'output') and isinstance(self.output,dict):
            times = self.output.setdefault('times',{})
            ret = func(self, *args, **kwargs)
            name = func.func_name
            start_time = time.time()
            ret = func(self, *args, **kwargs)
            elapsed_time = time.time() - start_time
            times[name] = elapsed_time
        else:
            ret = func(self, *args, **kwargs)
        return ret
    return do_measure
