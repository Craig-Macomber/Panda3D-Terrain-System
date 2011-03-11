import meshManager

from panda3d.core import NodePath, Geom, GeomNode, GeomVertexWriter, GeomVertexData, GeomVertexFormat, GeomTristrips, GeomTriangles
from panda3d.core import Vec3, Quat

import math, random

class TreeFactory(meshManager.MeshFactory):
    def __init__(self,heightSource):
        meshManager.MeshFactory.__init__(self)
        
        self.heightSource=heightSource
        
        self.scalar=.0002
        
    def regesterGeomRequirements(self,LOD,collection):
        """
        collection is a GeomRequirementsCollection
        
        example:
        self.trunkData=collection.add(GeomRequirements(...))
        """
        barkTexture = base.loader.loadTexture("meshManager/models/barkTexture.jpg") 
        # leafModel = base.loader.loadModel('models/tree/shrubbery') 
        leafTexture = base.loader.loadTexture("meshManager/models/material-10-cl.png")
        
        trunkRequirements=meshManager.GeomRequirements(
            geomVertexFormat=GeomVertexFormat.getV3n3t2(),
            texture=barkTexture
            )
        leafRequirements=meshManager.GeomRequirements(
            geomVertexFormat=GeomVertexFormat.getV3n3t2(),
            texture=leafTexture
            )
        self.trunkDataIndex=collection.add(trunkRequirements)
        self.leafDataIndex=collection.add(leafRequirements)
    
    def getLodThresholds(self):
        # perhaps this should also have some approximate cost stats for efficent graceful degradation
        return [] # list of values at which rendering changes somewhat
    
    def draw(self,LOD,x0,y0,x1,y1,drawResourcesFactory):
        quat=Quat()
        leafResources=drawResourcesFactory.getDrawResources(self.leafDataIndex)
        leafTri = GeomTriangles(Geom.UHStatic) 
        
        grid=10.0*self.scalar
        x=math.ceil(x0/grid)*grid
        while x<x1:
            y=math.ceil(y0/grid)*grid
            while y<y1:
                pos=Vec3(x,y,self.heightSource.height(x,y))
                self.drawTree(LOD,(pos, quat, 0, 0, 0),drawResourcesFactory,leafTri)
                y+=grid
            x+=grid
        
        leafResources.geom.addPrimitive(leafTri)
        
    def drawTree(self,LOD,base,drawResourcesFactory,leafTri):
        leafResources=drawResourcesFactory.getDrawResources(self.leafDataIndex)
        exists=random.random()
        if exists<.6: return
        age=random.random()**1.5
        to = 14*age
        
        if to<6: return
        
        maxbend=40+random.random()*20
        
        forks=int(to/2-1)
        lengthList=[]
        numCopiesList=[]
        radiusList=[]
        currR=age*1.0*(random.random()*2+1)
        for i in xrange(forks+1):
            forkCount=2+(i%2)
            currR*=1/math.sqrt(2)
            endR=currR*.9*.9
            if i==forks:
                endR=0
                forkCount=0
            if i<2:
                lengthList.extend([2.0,2.0,2.0])
                numCopiesList.extend([0,0,forkCount])
                radiusList.extend([currR,currR*.9,endR])
            else:
                lengthList.extend([6.0])
                numCopiesList.extend([forkCount])
                radiusList.extend([endR])
                
                
        stack = [base]
        #lengthList = [2.0]*to
        #numCopiesList = [0, 0, 2, 0, 0, 3]*(to/6+1)
        #radiusList = [2.0, 1.8973665961010275, 1.8, 1.8, 1.2074767078498865, 1.145512985522207, 1.145512985522207, 0.62742330208560149, 0.59522600749631227, 0.59522600749631227, 0.39928974442126608, 0.37879951161531344, 0.37879951161531344, 0.20747703728364739, 0.19683000000000003, 0.19683000000000003, 0.13203757800338509, 0.12526184496685336, 0.12526184496685336, 0.068608738083060533, 0.065087963919721756, 0.065087963919721756, 0.043662333552465453, 0.041421726595134531, 0.041421726595134531, 0.02268761402696684, 0.021523360500000002, 0.021523360500000002, 0.01443830915467016, 0.013697382747125413, 0.013697382747125413, 0.0075023655093826675, 0.0071173688546215721, 0.0071173688546215721, 0.0047744761739620962, 0.0045294658031779598, 0.0045294658031779598, 0.0024808905938488233, 0.0023535794706749996, 0.0023535794706749996, 0.0015788291060631818, 0.0014978088033981637, 0.0014978088033981637, 0.0008203836684509948, 0.00077828428425286904, 0.00077828428425286904, 0.00052208896962275522, 0.00049529708557750993, 0.00049529708557750993, 0.00027128538643736883, 0.00025736391511831119, 0.00025736391511831119, 0.00017264496274800887, 0.00016378539265158914, 0.00016378539265158914, 8.9708954145116258e-05, 8.5105386483051203e-05, 8.5105386483051203e-05, 5.7090428828248272e-05, 5.4160736307900701e-05, 5.4160736307900701e-05, 2.9665057006926284e-05, 2.8142744118187332e-05, 2.8142744118187332e-05, 1.8878726676494776e-05]
        #radiusList=[x*age*age for x in radiusList]
        ends = []
        
        trunkResources=drawResourcesFactory.getDrawResources(self.trunkDataIndex)
        vertWriter = trunkResources.vertexWriter
        normalWriter = trunkResources.normalWriter
        texWriter = trunkResources.texcoordWriter
        geom = trunkResources.geom
        
        
        
        
        
        numVertices=3
        
        #cache some info needed for placeing the vertexes
        angleData=[]
        for i in xrange(numVertices+1):  #doubles the last vertex to fix UV seam
            angle=-2 * i * math.pi / numVertices
            angleData.append((math.cos(angle),math.sin(angle),1.0*i / numVertices))
        
        bottom=True
        while stack: 
            pos, quat, depth, previousRow, sCoord = stack.pop() 
            length = lengthList[depth]
            radius=radiusList[depth]
            
            startRow = vertWriter.getWriteRow()
            #vertWriter.setRow(startRow) 
            #normalWriter.setRow(startRow)        
            #texWriter.setRow(startRow)
            
            sCoord += length/4.0
            
            #this draws the body of the tree. This draws a ring of vertices and connects the rings with 
            #triangles to form the body. 
            #this keepDrawing paramter tells the function wheter or not we're at an end 
            #if the vertices before you were an end, dont draw branches to it 
            currAngle = 0 
            perp1 = quat.getRight() 
            perp2 = quat.getForward()   
            #vertex information is written here 
            for cos,sin,tex in angleData:
                adjCircle = pos + (perp1 * cos + perp2 * sin) * radius * self.scalar
                normal = perp1 * cos + perp2 * sin        
                normalWriter.addData3f(normal) 
                vertWriter.addData3f(adjCircle) 
                texWriter.addData2f(tex,sCoord) 
            #we cant draw quads directly so we use Tristrips 
            
            if bottom: 
                bottom=False
            else:
                lines = GeomTristrips(Geom.UHStatic)         
                for i in xrange(numVertices+1): 
                    lines.addVertices(i + previousRow,i + startRow)
                lines.addVertices(previousRow,startRow)
                lines.closePrimitive()
    
                geom.addPrimitive(lines)
            
            
            
            
            
            if depth + 1 < len(lengthList):
                #move foward along the right axis 
                newPos = pos + quat.getUp() * length * self.scalar
#                if makeColl: 
#                    self.makeColl(pos, newPos, radiusList[depth]) 
                
                numCopies = numCopiesList[depth]  
                if numCopies:
                    angleOffset=random.random()*2*math.pi
                    for i in xrange(numCopies): 
                        stack.append((newPos, _angleRandomAxis(quat, 2 * math.pi * i / numCopies+angleOffset, maxbend), depth + 1, startRow, sCoord))
                else: 
                    #just make another branch connected to this one with a small variation in direction 
                    stack.append((newPos, _randomBend(quat, 20), depth + 1, startRow, sCoord))
            else:
                #ends.append((pos, quat, depth, startRow)) 
                #self.drawLeaf(pos, quat) 
                leafRow = leafResources.vertexWriter.getWriteRow()
                up=quat.getUp()
                s=1.0*self.scalar
                dir1=perp1*s
                dir2=perp2*s
                bend=-up*(s/8.0)
                
                # TODO: fix backsides get upwards normals!
                
                leafResources.vertexWriter.addData3f(pos+dir1)
                leafResources.vertexWriter.addData3f(pos+dir2+bend)
                leafResources.vertexWriter.addData3f(pos-dir1)
                leafResources.vertexWriter.addData3f(pos-dir2+bend)
                leafResources.normalWriter.addData3f(up)
                n=dir1.cross(dir2+bend)
                n.normalize
                leafResources.normalWriter.addData3f(n) 
                leafResources.normalWriter.addData3f(up) 
                n=dir1.cross(dir2-bend)
                n.normalize
                leafResources.normalWriter.addData3f(n)
                leafResources.texcoordWriter.addData2f(0,0)
                leafResources.texcoordWriter.addData2f(0,1)
                leafResources.texcoordWriter.addData2f(1,1)
                leafResources.texcoordWriter.addData2f(1,0)
                
                leafTri.addVertices(leafRow,leafRow+1,leafRow+2)
                leafTri.addVertices(leafRow,leafRow+2,leafRow+3)
                leafTri.addVertices(leafRow+1,leafRow,leafRow+2)
                leafTri.addVertices(leafRow+2,leafRow,leafRow+3)
                
        

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
    #power of 2 here makes distrobution even withint a circle
    # (makes larger bends are more likley as they are further spread) 
    ammount=(random.random()**(1.0/2))*maxAngle
    q.setHpr((math.sin(nangle)*ammount,math.cos(nangle)*ammount,0))
    return inQuat*q
