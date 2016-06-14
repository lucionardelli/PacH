#!/usr/bin/env python
# -*- coding: UTF-8

from custom_exceptions import CannotGetHull, WrongDimension, CannotIntegerify

from stopwatch import StopWatchObj
from config import logger

def sampling(func):
    @StopWatchObj.stopwatch
    def do_sampling(self, points, *args, **kwargs):
        facets = []
        for _ in xrange(self.samp_num):
            try:
                points = self.get_sample()
                qhull = func(self, points, *args, **kwargs)
                # Make union of all facets
                qhull.union(facets)
                # Not "sampled" points restrict the facet
                for outsider in self.pv_set - points:
                    qhull.restrict_to(outsider)
                facets = qhull.facets
            except Exception, err:
                logger.error('Error: %s' % err, exc_info=True)
                if self.samp_size:
                    logger.error('Cannot get MCH. Maybe doing *TOO*'\
                            ' small sampling?')
                raise err
        return qhull
    return do_sampling
