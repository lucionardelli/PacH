#!/usr/bin/env python
# -*- coding: UTF-8
import numpy as np
from config import logger

class CorrMatrix(object):
    """
    The correlation Matrix as defined in the paper
    "Process Discovery Algorithms Using Numerical
        Abstract Domains"
    """

    def __init__(self, pv_array):
        if pv_array is not None:
            # Standard deviation
            self.std_dev = pv_array.std(axis=0)
            # Mean deviation
            self.mean_dev = pv_array.mean(axis=0)
            # This function actually computes everything
            self._make_corr_matrix(pv_array)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.matrix.__str__()

    def __getitem__(self, idx):
        return self.matrix[idx]

    def copy(self):
        matrix = CorrMatrix(None)
        matrix.std_dev = self.std_dev.copy()
        matrix.mean_dev = self.mean_dev.copy()
        matrix.dim = self.dim
        matrix.matrix = self.matrix.copy()
        matrix.eigenvalues =  self.eigenvalues.copy()
        matrix.eigenvector = self.eigenvector.copy()
        return matrix

    def _make_corr_matrix(self, pv_array):
        """
            make Correlation Matrix for all pair of events
        """
        dim = len(pv_array) > 0 and len(pv_array[0]) or 0
        self.dim = dim
        matrix = np.zeros((dim,dim))
        aux = np.add(pv_array,-1 * self.mean_dev).T
        len_m1 = len(pv_array) -1
        for x_axis in xrange(dim):
            for y_axis in xrange(dim):
                numerator = aux[x_axis].dot(aux[y_axis])
                denominator = len_m1 * self.std_dev[x_axis] * self.std_dev[y_axis]
                if denominator == 0:
                    matrix[x_axis][y_axis] = 0
                else:
                    matrix[x_axis][y_axis] = np.divide(numerator,denominator)
        self.matrix = matrix
        self.eigenvalues, self.eigenvector = np.linalg.eig(matrix)
        return True

    def to_zero(self, positions):
        for x in positions:
            self.matrix[:,x] = np.zeros(self.dim)
            self.matrix[x,:] = np.zeros(self.dim)
        self.eigenvalues, self.eigenvector = np.linalg.eig(self.matrix)

    def closest_points(self,clusters):
        rel = {}
        closest_tuple = (None,None)
        max_all = 0
        seen = {}
        for key,cluster in clusters.items():
            for point in cluster:
                # Which cluster contains this point
                seen[point] = key
                corr_list = rel.setdefault(point,[])
                for idx,corr in enumerate(self[point,:]):
                    corr = abs(corr)
                    corr_list.append(corr)
                    if idx in cluster:
                        continue
                    if max_all < corr:
                        closest = idx
                        max_all = corr
                        closest_tuple = (point,idx)
        p0,p1 = closest_tuple
        if p0 and p1:
            for pnbr,p in enumerate([p0,p1]):
                if p in seen:
                    logger.info('Closests point p%d is from cluster %s',
                            pnbr, seen[p])
                else:
                    logger.info('Closests point p%d was disconected',pnbr)
            cor0 = np.array(rel.get(p0,self[p0,:]))
            cor1 = np.array(rel.get(p1,self[p1,:]))
        else:
            cor0 = cor1 = None
        return  p0,p1,cor0,cor1
