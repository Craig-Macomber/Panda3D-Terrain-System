import math
import meshManager

class GridFactory(meshManager.MeshFactory):
    def __init__(self,heightSource):
        meshManager.MeshFactory.__init__(self)
        
        self.heightSource=heightSource
        
        self.scalar=1.0
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