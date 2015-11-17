#!/usr/bin/env python
# -*- coding: UTF-8
import random
import numpy as np

from config import *

class KMeans(object):
    def __init__(self, K, X):
        self.K = K
        self.X = X
        self.N = len(X)
        self.mu = None
        self.clusters = {}

    def _cluster_points(self):
        mu = self.mu
        clusters  = {}
        for x in self.X:
            bestmukey = min([(i[0], np.linalg.norm(x-mu[i[0]])) \
                             for i in enumerate(mu)], key=lambda t:t[1])[0]
            try:
                clusters[bestmukey].append(x)
            except KeyError:
                clusters[bestmukey] = [x]
        self.clusters = clusters

    def _reevaluate_centers(self):
        clusters = self.clusters
        newmu = []
        keys = sorted(self.clusters.keys())
        for k in keys:
            newmu.append(np.mean(clusters[k], axis = 0))
        self.mu = newmu

    def _has_converged(self):
        K = len(self.oldmu)
        return(set([tuple(a) for a in self.mu]) == \
               set([tuple(a) for a in self.oldmu])\
               and len(set([tuple(a) for a in self.mu])) == K)

    def init_centers(self):
        self.mu = random.sample(X, K)

    def find_centers(self, method='random'):
        X = self.X
        K = self.K
        self.init_centers()
        self.oldmu = random.sample(X, K)
        while not self._has_converged():
            self.oldmu = self.mu
            # Assign all points in X to clusters
            self._cluster_points()
            # Reevaluate centers
            self._reevaluate_centers()

class KPlusPlus(KMeans):
    def _dist_from_centers(self):
        cent = self.mu
        X = self.X
        D2 = np.array([min([np.linalg.norm(x-c)**2 for c in cent]) for x in X])
        self.D2 = D2

    def _choose_next_center(self):
        self.probs = self.D2/self.D2.sum()
        self.cumprobs = self.probs.cumsum()
        r = random.random()
        ind = np.where(self.cumprobs >= r)[0][0]
        return(self.X[ind])

    def init_centers(self):
        self.mu = random.sample(self.X, 1)
        while len(self.mu) < self.K:
            self._dist_from_centers()
            self.mu.append(self._choose_next_center())

def two_means(points,max_size=None):
    retries = KMEANS
    logger.debug('Points are: %s',points)
    kplusplus = KPlusPlus(2,[np.array([abs(x)]) for x in points])
    while len(kplusplus.clusters) == 0 and retries > 0:
        kplusplus.init_centers()
        kplusplus.find_centers()
        clu0 = kplusplus.clusters.get(0,[])
        clu0 = [x[0] for x in clu0]
        clu1 = kplusplus.clusters.get(1,[])
        clu1 = [x[0] for x in clu1]
        retries -= 1
    if len(clu1) == 0 or (len(clu0) > 0 and max(clu0) > max(clu1)):
        tmp = clu0
        clu0 = clu1
        clu1 = tmp
    if max_size and len(clu1) > max_size:
        clu1.sort()
        clu0 = clu0 + clu1[:len(clu1)-max_size]
        clu1 = clu1[len(clu1)-max_size:]
    logger.debug('Cluster 0 is: %s',clu0)
    logger.debug('Cluster 1 is: %s',clu1)
    logger.debug('Length of cluster 0 is: %s',len(clu0))
    logger.debug('Length of cluster 1 is: %s',len(clu1))
    return clu0, clu1
