#!/usr/bin/env python
# -*- coding: UTF-8
from halfspace import Halfspace
from custom_exceptions import IncorrectOutput, CannotGetHull, LostPoints
from redirect_output import stderr_redirected
from convexhull import ConvexHull
from stopwatch import StopWatchObj
from config import logger

from pyhull import qconvex
import sys

class Qhull(ConvexHull):
    def __parse_hs_output(self, output):
        """
         input: Output string for ConvexHull
            The first line is the dimension.
            The second line is the number of facets.
            Each remaining line is the hyperplane's coefficient
                followed by its offset.
         output: (dimension,nbr_facets,[halfspaces])
        """
        try:
            dim = int(output.pop(0)) - 1
            facets_nbr = output.pop(0)
            prepare = [[float(i) for i in row.strip().split()]
                    for row in output]
            facets = [Halfspace(out[:-1],out[-1]) for out in prepare]
        except Exception, err:
            logger.error('Incorrect output of pyhull! Error: %s', err)
            raise IncorrectOutput()
        return (dim, facets_nbr, facets)

    @StopWatchObj.stopwatch
    def compute_hiperspaces(self):
        if not len(self.points) > 0:
            logger.error('No points to compute hull!')
            raise Exception('No points to compute hull!')

        # The heuristic caracteristic when searching to connect
        # different clusters does that it might fail
        # so we redirect the stdout to avoid such error
        # being visible to user
        stderr_fd = sys.stderr.fileno()
        with open('/tmp/qhull-output.log', 'w') as f, stderr_redirected(f):
            points = list(self.points)
            logger.info('Searching for hull in dimension %s based on %s points',
                    len(points[0]),len(points))
            output = qconvex('n',points)
            if len(output) == 1:
                logger.debug('Could not get Hull. Joggle input?')
        try:
            dim, facets_nbr, facets = self.__parse_hs_output(output)
        except IncorrectOutput:
            logger.error('Could not get hull')
            raise CannotGetHull()
        logger.info('Found hull in dimension %s of %s facets',
                dim,facets_nbr)
        self.dim = dim
        self.facets = facets
        return self.dim

if __name__ == '__main__':
    import sys, traceback,pdb
    from mains import qhull_main
    try:
        qhull_main()
    except Exception, err:
        logger.error('Error: %s' % err, exc_info=True)
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        #pdb.post_mortem(tb)

