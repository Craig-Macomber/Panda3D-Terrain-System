import math, random

from panda3d.core import Vec3, Quat, GeomVertexFormat, NodePath

import meshManager
import gridFactory

noFerns=1

class FernFactory(gridFactory.GridFactory):
    def __init__(self,leafTexture=None,scalar=.25,gridSize=30.0):
        self.leafTexture=leafTexture
        gridFactory.GridFactory.__init__(self,scalar=scalar,gridSize=gridSize)
        
        self.leafDataIndex={}
        self.lowLOD=meshManager.LOD(1200,000)
        self.midLOD=meshManager.LOD(800,000)
        
    def getLODs(self):
        return [self.lowLOD,self.midLOD]
        
    def regesterGeomRequirements(self,LOD,collection):
        
        n=NodePath('tmp')
        
        if self.leafTexture is not None:
            n.setTexture(self.leafTexture)
            n.setShaderInput('diffTex',self.leafTexture)
            format=GeomVertexFormat.getV3n3t2()
        else:
            n.setColor(.1,.3,.1,1)
            format=GeomVertexFormat.getV3n3()

        #n.setShader(customLoader.makeShader(n,debugCodePrefix="fern",debugGraphPrefix="fern"))
        
        leafRequirements=meshManager.GeomRequirements(
                geomVertexFormat=format,
                renderState=n.getState(),
                )
        
        self.leafDataIndex[LOD]=collection.add(leafRequirements)
        
    def drawItem(self,LOD,x,y,drawResourcesFactory,tile,tileCenter,collision,seed=True,scale=1.0):
        if seed: random.seed((x,y))
        exists=random.random()
        if exists<.6: return
        quat=Quat()
        
        height=tile.height(x,y)
        if height is None: return
        
        pos=Vec3(x,y,height)-tileCenter
        self.drawFern(LOD,pos, quat,drawResourcesFactory,scale=scale)    
    
    def drawFern(self,LOD,pos,quat,drawResourcesFactory,scale=1.0):
        scalar=random.random()
        scale*=scalar
        
        if scale<.3: return
        
        count=int((scalar**.7)*12)
        
        if scale<.8:
            if LOD==self.lowLOD: return
        else:
            if LOD==self.midLOD: return
        
        
        leafResources=drawResourcesFactory.getDrawResources(self.leafDataIndex[LOD])
        leafTri=leafResources.getGeomTriangles()
        vertexWriter=leafResources.getWriter("vertex")
        normalWriter=leafResources.getWriter("normal")
        
        if self.leafTexture:
            texcoordWriter = leafResources.getWriter("texcoord")
        
        
        
        scale*=self.scalar*3
        
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
                leafRow = vertexWriter.getWriteRow()
            
                vertexWriter.addData3f(pos)
                vertexWriter.addData3f(pos+f+r)
                vertexWriter.addData3f(pos+f-r)
                vertexWriter.addData3f(pos+f2)
                
                
                if self.leafTexture:
                    texcoordWriter.addData2f(0,0)
                    texcoordWriter.addData2f(0,1)
                    texcoordWriter.addData2f(1,0)
                    texcoordWriter.addData2f(1,1)
            
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
                    
                normalWriter.addData3f(norm0)
                normalWriter.addData3f(norm1) 
                normalWriter.addData3f(norm1) 
                normalWriter.addData3f(norm2)