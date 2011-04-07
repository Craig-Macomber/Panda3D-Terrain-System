import math, random

from panda3d.core import Vec3, Quat, GeomVertexFormat

import meshManager
import gridFactory


class TreeFactory(gridFactory.GridFactory):
    def __init__(self,heightSource,barkTexture=None,leafTexture=None):
        self.scalar=2.0
        self.gridSize=2.0
        self.barkTexture=barkTexture
        self.leafTexture=leafTexture
        gridFactory.GridFactory.__init__(self,heightSource,1.0,3.0)
    
    def regesterGeomRequirements(self,LOD,collection):
        if self.barkTexture is not None:
            trunkRequirements=meshManager.GeomRequirements(
                geomVertexFormat=GeomVertexFormat.getV3n3t2(),
                texture=self.barkTexture
                )
        else:
            trunkRequirements=meshManager.GeomRequirements(
                geomVertexFormat=GeomVertexFormat.getV3n3c4(),
                )
        
        if self.leafTexture is not None:
            leafRequirements=meshManager.GeomRequirements(
                geomVertexFormat=GeomVertexFormat.getV3n3t2(),
                texture=self.leafTexture
                )
        
        else:
            leafRequirements=meshManager.GeomRequirements(
                geomVertexFormat=GeomVertexFormat.getV3n3c4(),
                )
        
        self.trunkDataIndex=collection.add(trunkRequirements)
        self.leafDataIndex=collection.add(leafRequirements)
    
    def drawItem(self,LOD,x,y,drawResourcesFactory):
        quat=Quat()
        
        heightOffset=-0.4 # make sure whole bottom of tree is in ground
        pos=Vec3(x,y,self.heightSource.height(x,y)+heightOffset)
        
        random.seed((x,y))
        self.drawTree(LOD,(pos, quat, 0, 0, 0),drawResourcesFactory)
               
    def drawTree(self,LOD,base,drawResourcesFactory):
        exists=random.random()
        if exists<.9: return
        age=random.random()**1.5
        to = 12*age
        
        if to<6: return
        
        dotCount=1#int((2/age))
        
        leafResources=drawResourcesFactory.getDrawResources(self.leafDataIndex)
        leafTri=leafResources.getGeomTriangles()
        trunkResources=drawResourcesFactory.getDrawResources(self.trunkDataIndex)
        lines = trunkResources.getGeomTristrips()
        vertWriter = trunkResources.vertexWriter
        normalWriter = trunkResources.normalWriter
        if self.barkTexture:
            texWriter = trunkResources.texcoordWriter
        else:
            colorWriter = trunkResources.colorWriter
        
        maxbend=40+random.random()*20
        
        forks=int(to/2-1)
        lengthList=[]
        numCopiesList=[]
        radiusList=[]
        currR=age*1.0*(random.random()*2+1)
        forkCount=0
        for i in xrange(forks+1):
            currR*=1/math.sqrt(2)
            endR=currR*.9*.9
            if i==forks:
                endR=0
                forkCount=0
            if i<2:
                lengthList.extend([2.0,2.0,2.0])
                numCopiesList.extend([forkCount,0,0])
                radiusList.extend([currR,currR*.9,endR])
            else:
                lengthList.extend([6.0])
                numCopiesList.extend([forkCount])
                radiusList.extend([endR])
            forkCount=2+(i%2)
                
        stack = [base]
        
        numVertices=3
        
        #cache some info needed for placeing the vertexes
        angleData=[]
        if self.barkTexture:
            vNum=numVertices+1
        else:
            vNum=numVertices
        
        for i in xrange(vNum):  #doubles the last vertex to fix UV seam
            angle=-2 * i * math.pi / numVertices
            angleData.append((math.cos(angle),math.sin(angle),1.0*i / numVertices))
        
        bottom=True
        
        while stack: 
            pos, quat, depth, previousRow, sCoord = stack.pop() 
            length = lengthList[depth]
            radius=radiusList[depth]
            
            startRow = vertWriter.getWriteRow()
            
            sCoord += length/4.0
            
            #this draws the body of the tree. This draws a ring of vertices and connects the rings with 
            #triangles to form the body. 

            currAngle = 0 
            perp1 = quat.getRight() 
            perp2 = quat.getForward()   
            #vertex information is written here 
            for cos,sin,tex in angleData:
                adjCircle = pos + (perp1 * cos + perp2 * sin) * radius * self.scalar
                normal = perp1 * cos + perp2 * sin        
                normalWriter.addData3f(normal) 
                vertWriter.addData3f(adjCircle) 
                if self.barkTexture is not None:
                    texWriter.addData2f(tex,sCoord) 
                else:
                    colorWriter.addData4f(.4,.3,.3,1)
            #we cant draw quads directly so we use Tristrips 
            
            if bottom: 
                bottom=False
            else:
                         
                for i in xrange(vNum): 
                    lines.addVertices(i + previousRow,i + startRow)
                if not self.barkTexture: lines.addVertices(previousRow,startRow)
                lines.closePrimitive()
            
            if depth + 1 < len(lengthList):
                #move foward along the right axis 
                newPos = pos + quat.getUp() * length * self.scalar
#                if makeColl: 
#                    self.makeColl(pos, newPos, radiusList[depth]) 
                
                numCopies = numCopiesList[depth]  
                if numCopies:
                    angleOffset=random.random()*2*math.pi
                    
                    for i in xrange(numCopies): 
                        newQuat= _angleRandomAxis(quat, 2 * math.pi * i / numCopies+angleOffset, maxbend)
                        newPos2=pos + newQuat.getUp() * length * self.scalar
                        stack.append((newPos2,newQuat, depth + 1, startRow, sCoord))
                else: 
                    #just make another branch connected to this one with a small variation in direction 
                    stack.append((newPos, _randomBend(quat, 20), depth + 1, startRow, sCoord))
            else:
                q=Quat()
                q.setHpr((random.random()*2*math.pi,0,0))
                quat=quat*q
                up=quat.getUp()
                s=10.0*self.scalar
                dir1=perp1*s
                dir2=perp2*s
                bend=-up*(s/4.0)
                
                v0=pos+dir1
                v1=pos+dir2+bend
                v2=pos-dir1
                v3=pos-dir2+bend
                
                norm1=dir1.cross(dir2+bend)
                norm1.normalize()
                norm2=dir1.cross(dir2-bend)
                norm2.normalize()
                
                for x in range(2):
                    leafRow = leafResources.vertexWriter.getWriteRow()
                    leafResources.vertexWriter.addData3f(v0)
                    leafResources.vertexWriter.addData3f(v1)
                    leafResources.vertexWriter.addData3f(v2)
                    leafResources.vertexWriter.addData3f(v3)
                    if self.leafTexture is not None:
                        n=dotCount
                        leafResources.texcoordWriter.addData2f(0,0)
                        leafResources.texcoordWriter.addData2f(0,n)
                        leafResources.texcoordWriter.addData2f(n,n)
                        leafResources.texcoordWriter.addData2f(n,0)
                    else:
                        leafResources.colorWriter.addData4f(.5,.4,.0,1)
                        leafResources.colorWriter.addData4f(.0,.4,.0,1)
                        leafResources.colorWriter.addData4f(.5,.4,.0,1)
                        leafResources.colorWriter.addData4f(.0,.4,.0,1)
                    
                    if x==1:
                        # back sides
                        up=-up
                        norm1=-norm1
                        norm2=-norm2
                        leafTri.addVertices(leafRow+1,leafRow,leafRow+2)
                        leafTri.addVertices(leafRow+2,leafRow,leafRow+3)
                    else:
                        leafTri.addVertices(leafRow,leafRow+1,leafRow+2)
                        leafTri.addVertices(leafRow,leafRow+2,leafRow+3)
                        
                    leafResources.normalWriter.addData3f(up)
                    leafResources.normalWriter.addData3f(norm1) 
                    leafResources.normalWriter.addData3f(up) 
                    leafResources.normalWriter.addData3f(norm2)

#this is for making the tree not too straight 
def _randomBend(inQuat, maxAngle=20):
    q=Quat()
    angle=random.random()*2*math.pi
    
    #power of 1/2 here makes distrobution even withint a circle
    # (makes larger bends are more likley as they are further spread) 
    ammount=(math.sqrt(random.random()))*maxAngle
    q.setHpr((math.sin(angle)*ammount,math.cos(angle)*ammount,0))
    return inQuat*q


def _angleRandomAxis(inQuat, angle, maxAngle): 
    q=Quat()
    angleRange=0.125
    nangle = angle + math.pi * (angleRange * random.random() - angleRange/2) 
    #power of 1/2 here makes distrobution even withint a circle
    # (makes larger bends are more likley as they are further spread) 
    ammount=(random.random()**(1.0/2))*maxAngle
    q.setHpr((math.sin(nangle)*ammount,math.cos(nangle)*ammount,0))
    return inQuat*q
