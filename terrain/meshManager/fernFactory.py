import math, random

from panda3d.core import Vec3, Quat, GeomVertexFormat

import meshManager
import gridFactory


class FernFactory(gridFactory.GridFactory):
    def __init__(self,heightSource,leafTexture=None):
        self.leafTexture=leafTexture
        gridFactory.GridFactory.__init__(self,heightSource,.2,12.0)
        
    def regesterGeomRequirements(self,LOD,collection):
        if self.leafTexture:
            leafRequirements=meshManager.GeomRequirements(
                geomVertexFormat=GeomVertexFormat.getV3n3t2(),
                texture=leafTexture
                )
        else:
            leafRequirements=meshManager.GeomRequirements(
                geomVertexFormat=GeomVertexFormat.getV3n3c4(),
                )
        
        
        self.leafDataIndex=collection.add(leafRequirements)
    
    def drawItem(self,LOD,x,y,drawResourcesFactory):
        quat=Quat()
        
        pos=Vec3(x,y,self.heightSource.height(x,y))
        
        random.seed((x,y))
        self.drawFern(LOD,pos, quat,drawResourcesFactory)    
    
    def drawFern(self,LOD,pos,quat,drawResourcesFactory):
        exists=random.random()
        if exists<.8: return
        scalar=random.random()
        scale=scalar**.3
        
        if scale<.3: return
        
        leafResources=drawResourcesFactory.getDrawResources(self.leafDataIndex)
        leafTri=leafResources.getGeomTriangles()
        
        count=int((scalar**.7)*12)
        
        scale*=self.scalar*2
        
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
            
            for x in range(2):
                leafRow = leafResources.vertexWriter.getWriteRow()
            
                leafResources.vertexWriter.addData3f(pos)
                leafResources.vertexWriter.addData3f(pos+f+r)
                leafResources.vertexWriter.addData3f(pos+f-r)
                leafResources.vertexWriter.addData3f(pos+f2)
                
                
                if self.leafTexture:
                    leafResources.texcoordWriter.addData2f(0,0)
                    leafResources.texcoordWriter.addData2f(0,1)
                    leafResources.texcoordWriter.addData2f(1,0)
                    leafResources.texcoordWriter.addData2f(1,1)
                else:
                    leafResources.colorWriter.addData4f(.1,.3,.1,1)
                    leafResources.colorWriter.addData4f(.1,.3,.1,1)
                    leafResources.colorWriter.addData4f(.1,.3,.1,1)
                    leafResources.colorWriter.addData4f(.1,.3,.1,1)
            
                if x==1:
                    # back sides
                    norm0=-norm0
                    norm1=-norm1
                    norm2=-norm2
                    leafTri.addVertices(leafRow+1,leafRow,leafRow+2)
                    leafTri.addVertices(leafRow+3,leafRow+1,leafRow+2)
                else:
                    leafTri.addVertices(leafRow,leafRow+1,leafRow+2)
                    leafTri.addVertices(leafRow+1,leafRow+3,leafRow+2)
                    
                leafResources.normalWriter.addData3f(norm0)
                leafResources.normalWriter.addData3f(norm1) 
                leafResources.normalWriter.addData3f(norm1) 
                leafResources.normalWriter.addData3f(norm2)