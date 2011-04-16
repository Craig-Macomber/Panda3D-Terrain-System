import math
import meshManager

class GridFactory(meshManager.MeshFactory):
    def __init__(self,scalar,gridSize):
        self.scalar=scalar
        self.gridSize=gridSize
        meshManager.MeshFactory.__init__(self)
        
    def draw(self,LOD,x0,y0,x1,y1,drawResourcesFactory):
        tile=drawResourcesFactory.getTile()
        
        grid=self.gridSize*self.scalar
        x=math.ceil(x0/grid)*grid
        while x<x1:
            y=math.ceil(y0/grid)*grid
            while y<y1:
                self.drawItem(LOD,x,y,drawResourcesFactory,tile)
                y+=grid
            x+=grid