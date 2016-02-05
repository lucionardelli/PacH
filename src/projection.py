#!/usr/bin/env python
# -*- coding: UTF-8
import numpy as np
from corrmatrix import CorrMatrix
#from kmeans import two_means
from kmeans_plus_plus import two_means

from stopwatch_wrapper import stopwatch
from config import *

def projection(func):

    @stopwatch
    def do_projection(self, points, *args, **kwargs):
        # Calculamos la matrix de correlaciones
        points = np.array(list(points))
        if self.proj_size is None:
            # Si el máximo es None es porque no se desea hacer projection
            logger.debug('Calculate hull without projection')
            qhull = func(self, points, *args, **kwargs)
        else:
            # Hacemos projection
            corr = CorrMatrix(points)
            corr2 = corr.copy()
            facets = []
            qhull = None
            projections = {}
            proj_count = 0
            logger.debug('Calculate hull with projection')
            while True:
                # Hacemos una lista de pares (valor, posicion)
                max_ev = 0
                max_idx = None
                eigen = None
                # Tomamos el eigenvector correspondiente al mayor eigenvalor
                # ya que se espera que sea el que más info tiene sobre
                # correlaciones
                for idx,val in enumerate(corr.eigenvalues):
                    if abs(val) > max_ev:
                        max_ev = abs(val)
                        max_idx = idx
                        eigen = corr.eigenvector[:,idx]
                logger.debug('Leader row # of CORR matrix %s',max_idx)
                # Si 'eigen' es None
                # es porque todos los eigen-valores eran 0
                # ya somos conexos!
                if eigen is None:
                    logger.info('The model is all projected, '\
                            'finishing projections')
                    break

                proj_count += 1
                logger.info('Projection #%s',proj_count)
                # tomamos la fila correspondiente al líder
                # (más grande en valor absoluto)
                # en la matriz de correlación
                eigen_abs = map(abs,eigen)
                leader = eigen_abs.index(max(eigen_abs))
                leader_row = corr.matrix[leader]
                #solo utilizamos el cluster de mayor correlación
                logger.debug('Calling k-means with %s',leader_row)
                cluster0, cluster1 = two_means(leader_row,max_size=self.proj_size)
                logger.debug('Cluster0: %s \n Cluster1: %s', cluster0, cluster1)
                if 0.0 in cluster1:
                    logger.error("Error getting Cluster. "\
                            " 0.0 is present in %s",cluster1)
                    raise Exception('Cannot get clusters!')
                if len(cluster1) <= 1:
                    if qhull is not None:
                        break
                    else:
                        logger.error("We couldn't  get even a single cluster!")
                        # Aunque la proyección sea mala,
                        # tenemos que hacer al menos una.
                        while len(cluster1) <= 1:
                            cluster1.append(max(cluster0))
                        logger.error('Using %s as the cluster closer to 1',cluster1)
                pts_proj, projected = self.project(points, leader_row, cluster1)
                logger.debug('We will project onto this points: %s', projected)
                projections[proj_count] = projected
                qhull = func(self, pts_proj, *args, **kwargs)
                # Extendemos a la dimensión original
                qhull.extend(leader_row, cluster1,orig_dim=self.dim)
                # Agregamos las facetas que ya calculamos
                qhull.union(facets)
                facets = qhull.facets

                #NOTE
                # Esto es para chequear que no dejando a nadia afuera
                if self.sanity_check:
                    assert qhull.all_in(self.pv_set)

                # Actualizamos la matriz poniendo en 0 los valores usados
                corr.update(projected)

                if not corr.matrix.any():
                    logger.info('The model is all projected, '\
                            'finishing projections')
                    break
            if self.proj_connected:
                # Intentamos hacer que el modelo sea conexo
                # con este algoritmo heurístico
                logger.info('Connecting projections')
                last_con_line = None
                connections_count = 0
                while True:
                    try:
                        p0,p1,cor0,cor1 = corr2.closest_points(projections)
                        logger.debug('Closer points are %s and %s', p0, p1)
                        if not (np.any(cor0) and np.any(cor1)):
                            break
                        con_line = np.concatenate((cor0,cor1))
                        if np.any(last_con_line) and np.all(last_con_line==con_line):
                            break
                        else:
                            last_con_line = con_line
                        logger.debug('Calling k-means with %s',con_line)
                        cluster0, cluster1 = two_means(con_line,max_size=self.proj_size)
                        logger.debug('Cluster0: %s \n Cluster1: %s', cluster0, cluster1)
                        if len(cluster1) <= 1:
                            break
                        if 0.0  in cluster1:
                            logger.error("Error getting Cluster. "\
                                    " 0.0 is present in %s",cluster1)
                            raise Exception('Cannot get clusters!')
                        pts_proj, projected = self.project(points, con_line, cluster1)
                        logger.debug('We will project onto this points: %s', projected)
                        qhull = func(self, pts_proj, *args, **kwargs)
                        # Extendemos a la dimensión original
                        qhull.extend(con_line, cluster1, orig_dim=self.dim)
                        # Agregamos las facetas que ya calculamos
                        qhull.union(facets)
                        facets = qhull.facets

                        #NOTE
                        # Esto es para chequear que no dejando a nadia afuera
                        if self.sanity_check:
                            assert qhull.all_in(self.pv_set)

                        # Actualizamos la matriz poniendo en 0 los valores usados
                        corr2.update(projected)
                        connections_count += 1
                    except Exception, err:
                        break
                logger.info('Succesfull connections of projections: %s',connections_count)
        return qhull
    return do_projection


