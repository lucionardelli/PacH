#!/usr/bin/env python
# -*- coding: UTF-8
import numpy as np
import random
from custom_exceptions import CannotGetClusters

from config import *

def cluster_points(X, mu):
    clusters  = {}
    for x in X:
        bestmukey = min([(i[0], np.linalg.norm(x-mu[i[0]])) \
                    for i in enumerate(mu)], key=lambda t:t[1])[0]
        cluster = clusters.setdefault(bestmukey,[])
        cluster.append(x)
    return clusters

def reevaluate_centers(mu, clusters):
    newmu = []
    keys = sorted(clusters.keys())
    for k in keys:
        newmu.append(np.mean(clusters[k], axis = 0))
    return newmu

def has_converged(mu, oldmu):
    return set(mu) == set(oldmu) and len(set(mu)) == len(oldmu)

def find_centers(X, K, oldmu=None, mu=None):
    # X tiene que ser una lista de np.array
    # K es el número de clusters a generar
    # Initialize to K random centers
    if oldmu is None:
        oldmu = random.sample(X, K)
    if mu is None:
        mu = random.sample(X, K)
    clusters = {}
    while not has_converged(mu, oldmu):
        oldmu = mu
        # Assign all points in X to clusters
        clusters = cluster_points(X, mu)
        # Reevaluate centers
        mu = reevaluate_centers(oldmu, clusters)
    return(mu, clusters)

def two_means(points,max_size=None,min_size=None):
    points = [abs(x) for x in points]
    # Como comenzamos con centroides random, puede fallar
    retries = KMEANS
    clusters = []
    logger.debug('Points are: %s',points)
    while len(clusters) == 0 and retries > 0:
        logger.debug('Try %s of %s for k-means',(KMEANS+1-retries),retries)
        mu, clusters = find_centers(points, 2)
        retries -= 1
    if len(clusters) == 0:
        logger.error('Cannot get clusters with k-means for points %s',points)
        raise CannotGetClusters()
    clu0 = clusters.get(0,[])
    clu1 = clusters.get(1,[])
    if len(clu1) == 0 or (len(clu0) > 0 and max(clu0) > max(clu1)):
        tmp = clu0
        clu0 = clu1
        clu1 = tmp
    if max_size and len(clu1) > max_size:
        clu1.sort()
        clu0 = clu0 + clu1[:len(clu1)-max_size]
        clu1 = clu1[len(clu1)-max_size:]
    if min_size and len(clu0) and len(clu1) <= min_size:
        clu0.sort()
        clu1 = clu0[:-1*len(clu1)-min_size] + clu1
        clu0 = clu0[len(clu1)-min_size:]
    logger.info('Length of cluster 0 is: %s',len(clu0))
    logger.info('Length of cluster 1 is: %s',len(clu1))
    logger.debug('Cluster 0 is: %s',clu0)
    logger.debug('Cluster 1 is: %s',clu1)
    return clu0, clu1
