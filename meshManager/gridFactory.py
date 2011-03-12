import meshManager

from panda3d.core import NodePath, Geom, GeomNode, GeomVertexWriter, GeomVertexData, GeomVertexFormat, GeomTristrips, GeomTriangles
from panda3d.core import Vec3, Quat

import math, random

class GridFactory(meshManager.MeshFactory):
    def __init__(self,heightSource):
        meshManager.MeshFactory.__init__(self)
        
        self.heightSource=heightSource
        
        self.scalar=.0002
        self.gridSize=10.0
        
    def draw(self,LOD,x0,y0,x1,y1,drawResourcesFactory):
        grid=self.gridSize*self.scalar
        x=math.ceil(x0/grid)*grid
        while x<x1:
            y=math.ceil(y0/grid)*grid
            while y<y1:
                self.drawItem(LOD,x,y,drawResourcesFactory)
                y+=grid
            x+=grid