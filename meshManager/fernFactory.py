import meshManager

from panda3d.core import NodePath, Geom, GeomNode, GeomVertexWriter, GeomVertexData, GeomVertexFormat, GeomTristrips, GeomTriangles
from panda3d.core import Vec3, Quat

import math, random

class FernFactory(meshManager.MeshFactory):
    def __init__(self,heightSource):
        meshManager.MeshFactory.__init__(self)
        
        self.heightSource=heightSource
        self.scalar=.0001
        
    def regesterGeomRequirements(self,LOD,collection):
        leafTexture = base.loader.loadTexture("meshManager/models/material-10-cl.png")

        leafRequirements=meshManager.GeomRequirements(
            geomVertexFormat=GeomVertexFormat.getV3n3t2(),
            texture=leafTexture
            )
        self.leafDataIndex=collection.add(leafRequirements)
    
    def getLodThresholds(self):
        # perhaps this should also have some approximate cost stats for efficent graceful degradation
        return [] # list of values at which rendering changes somewhat
    
    def draw(self,LOD,x0,y0,x1,y1,drawResourcesFactory):
        quat=Quat()
        leafResources=drawResourcesFactory.getDrawResources(self.leafDataIndex)
        leafTri = GeomTriangles(Geom.UHStatic) 
        grid=3.0*self.scalar
        x=math.ceil(x0/grid)*grid
        while x<x1:
            y=math.ceil(y0/grid)*grid
            while y<y1:
                pos=Vec3(x,y,self.heightSource.height(x,y))
                self.drawFern(LOD,pos, quat,drawResourcesFactory,leafTri)
                y+=grid
            x+=grid
        leafResources.geom.addPrimitive(leafTri)
        
    def drawFern(self,LOD,pos,quat,drawResourcesFactory,leafTri):
        leafResources=drawResourcesFactory.getDrawResources(self.leafDataIndex)
        
        exists=random.random()
        if exists<.6: return
        scalar=random.random()
        scale=scalar**.1
        
        if scale<.3: return
        
        count=int(scalar*10)
        
        scale*=self.scalar
        
        q2=Quat()
        q3=Quat()
        
        for i in xrange(count):
            p=(random.random()**2)*60+20
            h=random.random()*360
            q2.setHpr((h,p,0))
            q3.setHpr((h,p-20-p/4,0))
            
            length1=scale*4
            length2=scale*3
            
            f=q2.getForward()*length1
            r=q2.getRight()*scale*.5
            f2=q3.getForward()*length2+f
            norm0=q2.getUp()
            norm2=q3.getUp()
            norm1=norm0+norm2
            norm1.normalize()
            
            leafRow = leafResources.vertexWriter.getWriteRow()
            
            leafResources.vertexWriter.addData3f(pos)
            leafResources.vertexWriter.addData3f(pos+f+r)
            leafResources.vertexWriter.addData3f(pos+f-r)
            leafResources.vertexWriter.addData3f(pos+f2)
            
            leafResources.normalWriter.addData3f(norm0)
            leafResources.normalWriter.addData3f(norm1) 
            leafResources.normalWriter.addData3f(norm1) 
            leafResources.normalWriter.addData3f(norm2)
            
            leafResources.texcoordWriter.addData2f(0,0)
            leafResources.texcoordWriter.addData2f(0,1)
            leafResources.texcoordWriter.addData2f(1,0)
            leafResources.texcoordWriter.addData2f(1,1)
            
            leafTri.addVertices(leafRow,leafRow+1,leafRow+2)
            leafTri.addVertices(leafRow+1,leafRow+3,leafRow+2)