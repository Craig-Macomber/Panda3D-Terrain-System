import math

from renderer import RenderNode
from terrain.bakery.gpuBakery import tileMapSize
from terrain.bakery.bakery import loadTex

from panda3d.core import *
#from terrain.textureRenderer import *


class GeoClipMapper(RenderNode):
    def __init__(self,path,tileSource,minScale,focus):
        RenderNode.__init__(self,path,NodePath(path+"_terrainNode"),heightScale=300.0)
        
        heightMapName=self.specialMaps['height']
        self.heightMapRez=0
        for s in tileSource.shaders:
            if s.name==heightMapName:
                self.heightMapRez=s.getRez(tileMapSize)
                break
        
        if self.heightMapRez==0: print 'Failed to determain height map resolution'
        
        self.setShaderInput("heightMapRez",self.heightMapRez,0,0,0)
        
        self.focus=focus
        self.minScale=minScale
        self.tileSource=tileSource
        self.heightStage=TextureStage("height")
        
        rezFactor=50
        n=rezFactor*4-1
        
        if n+4>=self.heightMapRez:
            print 'Error: Can not have geoClipMap rez higher than height map rez'
        
        self.rez=n
        m=(n+1)/4
        
        self.baseTileScale=minScale/n*self.heightMapRez
        scale=minScale/(n-1)
        self.terrainNode.setScale(scale,scale,scale)
        self.shaderHeightScale=self.heightScale/scale
        self.terrainNode.setShaderInput("heightScale",self.shaderHeightScale,0,0)
        self.terrainNode.setShader(loader.loadShader("geoClip.sha"))
        
        def makeGrid(xSize,ySize):
            """ Size is in verts, not squares """
            
            format=GeomVertexFormat.getV3()
            vdata=GeomVertexData('grid', format, Geom.UHStatic)
            vertex=GeomVertexWriter(vdata, 'vertex')
            grid=Geom(vdata)
            #snode=GeomNode('grid')
            
            for x in xrange(xSize):
                for y in xrange(ySize):
                    vertex.addData3f(x,y,0)
            
            tri=GeomTristrips(Geom.UHStatic)
            def index(lx,ly):
                return ly+lx*(ySize)
                
            for x in xrange(xSize-1):
                for y in xrange(ySize):
                    tri.addVertex(index(x,y))
                    tri.addVertex(index(x+1,y))
                tri.closePrimitive()
        
            grid.addPrimitive(tri)
            
            grid.setBoundsType(BoundingVolume.BTBox)
            grid.setBounds(BoundingBox(Point3(0,0,0),Point3(xSize-1,ySize-1,self.shaderHeightScale)))
            #snode.addGeom(grid)
            #snode.setBoundsType(BoundingVolume.BTBox)
            #snode.setBounds(BoundingBox(Point3(0,0,0),Point3(xSize-1,ySize-1,self.shaderHeightScale)))
            #snode.setFinal(True)
            return grid
        
        
        
        
        nxn=makeGrid(n,n)
        mxm=makeGrid(m,m)
        mx3=makeGrid(m,3)
        x3xm=makeGrid(3,m)
        m2x2=makeGrid(2*m+1,2)

        cNode=GeomNode('center')
        cGeom=nxn.makeCopy()
        cGeom.transformVertices(Mat4.translateMat(-n/2,-n/2,0))
        cNode.addGeom(cGeom)
        cGeom.setBoundsType(BoundingVolume.BTBox)
        cGeom.setBounds(BoundingBox(Point3(-n/2,-n/2,0),Point3(n/2-1,n/2-1,self.shaderHeightScale)))
        cNode.setBoundsType(BoundingVolume.BTBox)
        center=_GeoClipLevel(0,self,cNode)
        
        
        
        #NodePath(nxn).instanceTo(center).setPos(-n/2,-n/2,0)
        center.reparentTo(self.terrainNode)
        
        halfOffset=n/2
        
        #ring=NodePath("Ring")
        ring=GeomNode('ring')
        def doCorner(x,y):
            xd=x*n/2-(x+1)*m/2
            yd=y*n/2-(y+1)*m/2
            def doGeom(g,x,y):
                cGeom=(g).makeCopy()
                cGeom.transformVertices(Mat4.translateMat(x,y,0))
                cGeom.setBoundsType(BoundingVolume.BTBox)
                b=g.getBounds()
                p=b.getPoint(7)
                cGeom.setBounds(BoundingBox(Point3(x,y,0),Point3(p.getX()+x,p.getY()+y,self.shaderHeightScale)))
                ring.addGeom(cGeom)
            doGeom(mxm,xd,yd)
            doGeom(mxm,xd,yd-y*(m-1))
            doGeom(mxm,xd-x*(m-1),yd)
            #NodePath(mxm).copyTo(ring).setPos(xd,yd,0)
            #NodePath(mxm).copyTo(ring).setPos(xd,yd-y*(m-1),0)
            #NodePath(mxm).copyTo(ring).setPos(xd-x*(m-1),yd,0)
            
            if x==-1:
                if y==1:
                    doGeom(mx3,xd,yd-y*(m+1))
                    #NodePath(mx3).copyTo(ring).setPos(xd,yd-y*(m+1),0)
                else:
                    xd2=n/2-m
                    doGeom(mx3,xd2,yd+2*m-2)
                    #NodePath(mx3).copyTo(ring).setPos(xd2,yd+2*m-2,0)
            else:
                doGeom(x3xm,xd-x*(m+1),yd)
                #NodePath(x3xm).copyTo(ring).setPos(xd-x*(m+1),yd,0)
        
        doCorner(-1,-1)
        doCorner(1,-1)
        doCorner(-1,1)
        doCorner(1,1)
        
        ring.setBoundsType(BoundingVolume.BTBox)
        
        ringCount=4
        
        
        
        self.levels=[center]
        for i in xrange(ringCount):
            cNode=GeomNode('ring'+str(i))
            cNode.addGeomsFrom(ring)
            '''for c in ring.getChildren():
                x=c.copyTo(r)
                #v1=Point3()
                #v2=Point3()
                #x.calcTightBounds(v1,v2)
                #v2.setZ(1)
                node=x.node()
                node.setBoundsType(BoundingVolume.BTBox)
                node.setBounds(c.node().getBounds())#(BoundingBox(v1,v2))
                node.setFinal(1)
                x.showBounds()'''
            #r.showBounds()
            r=_GeoClipLevel(i+1,self,cNode)
            r.reparentTo(self.terrainNode)
            r.node().setBoundsType(BoundingVolume.BTBox)
            #r.showBounds()
            self.levels.append(r)
        
        
        self.terrainNode.setShaderInput("n",n,0,0,0)
        # Add a task to keep updating the terrain
        taskMgr.add(self.update, "update")
        
        
        self.grass=self.setUpGrass(center,n)
        grassTex = loadTex("grassSheet",True)
        self.grass.setShaderInput("grassSheet",grassTex)
        grassTex.setWrapU(Texture.WMClamp)
        grassTex.setWrapV(Texture.WMClamp)
    
        self.terrainNode.setShaderInput("offset",0,0,0,0)
        
        #for r in self.levels:
        #    for node in r.getChildren():
        #        node.setShaderInput("offset",node.getX()+halfOffset,node.getY()+halfOffset,0,0)
        
        self.centerTile=None
        
    def setUpGrass(self,node,rez):
        # create a mesh thats a bunch of disconnected rectangles, 1 tall, 0.5 wide, at every grid point
        format=GeomVertexFormat.getV3()
        snode=GeomNode('grass')
        grass=NodePath(snode)
        grass.reparentTo(node)
        grass.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullNone))
        grass.setShader(loader.loadShader("geoClipGrass.sha"))
        
        cullmargin=3
        
        def makeGrid(ofx,ofy,xStart,yStart,xEnd,yEnd):
            # does not include end values, but does include start ones
            vdata=GeomVertexData('grid', format, Geom.UHStatic)
            vertex=GeomVertexWriter(vdata, 'vertex')
            grid=Geom(vdata)
            snode.setBoundsType(BoundingVolume.BTBox)
            for x in xrange(xStart,xEnd):
                for y in xrange(yStart,yEnd):
                    xp=x-ofx-.25-1
                    yp=y-ofy-1
                    vertex.addData3f(xp,yp,0)
                    vertex.addData3f(xp+.5,yp,0)
                    vertex.addData3f(xp,yp,1)
                    vertex.addData3f(xp+.5,yp,1)
                
            tri=GeomTristrips(Geom.UHStatic)
            
            def index(lx,ly):
                return ((ly-yStart)+(lx-xStart)*(yEnd-yStart))*4
                
            for x in xrange(xStart,xEnd):
                for y in xrange(yStart,yEnd):
                    i=index(x,y)
                    tri.addVertex(i)
                    tri.addVertex(i+1)
                    
                    tri.addVertex(i+2)
                    tri.addVertex(i+3)
                    tri.closePrimitive()
            grid.addPrimitive(tri)
            snode.addGeom(grid)
            #block=NodePath(snode)
            #block.reparentTo(grass)
            grid.setBoundsType(BoundingVolume.BTBox)
            grid.setBounds(BoundingBox(Point3(xStart-cullmargin-ofx,yStart-cullmargin-ofy,0),Point3(xEnd-1+cullmargin-ofx,yEnd-1+cullmargin-ofy,self.shaderHeightScale+cullmargin)))
            #block.node().setFinal(True)
            #
            
        #grass.showBounds()
        #makeGrid(rez/2,rez/2,0,0,rez,rez)
        c=5
        for x in xrange(c):
            for y in xrange(c):
                makeGrid(rez/2,rez/2,x*rez//c,y*rez//c,(x+1)*rez//c,(y+1)*rez//c)
        grass.node().setBoundsType(BoundingVolume.BTBox)
        #grass.showBounds()
        return grass
    
    def height(self,x,y):
        if self.centerTile is None: return 0
        #print 'y'
        tile=self.centerTile
        peeker=self.heightPeeker
        tx=(x-tile.x)/tile.scale
        ty=(y-tile.y)/tile.scale
        c=Vec4()
        sx=peeker.getXSize()
        sy=peeker.getYSize()
        px=(sx*tx)
        py=(sy*ty)
        
        
        #u=math.floor(px)/sx
        #v=math.floor(py)/sy
        fu=px-math.floor(px)
        fv=py-math.floor(py)
        #u2=math.floor(px+1)/sx
        #v2=math.floor(py)/sy
        px=math.floor(px)
        py=math.floor(py)
        
        #peeker.lookup(c,u,v)
        def getH(x,y):
            peeker.lookup(c,x/sx,y/sy)
            return c.getX()+c.getY()/256+c.getZ()/(256*256)
        h=(getH(px+1,py+1)*fu+getH(px,py+1)*(1-fu))*fv+(getH(px+1,py)*fu+getH(px,py)*(1-fu))*(1-fv)
        
        #peeker.filterRect(c,px/sx,py/sy,px/sx,py/sy)
        #h=c.getX()+c.getY()/256+c.getZ()/(256*256)
        return h*self.heightScale
        
    def update(self,task):
        center=self.levels[0]
        if center.lastTile:
            maps=center.lastTile.renderMaps
            t=maps[self.specialMaps['height']].tex
            if self.centerTile is not center.lastTile: # new height tex!
                self.heightPeeker=t.peek()
                self.centerTile=center.lastTile
        for i in xrange(len(self.levels),0,-1):
            self.levels[i-1].update(self.levels[i] if i<len(self.levels) else None)
        return task.cont
        
        
    #def height(self,x,y): return 0        
        
class _GeoClipLevel(NodePath):
    def __init__(self,level,geoClipMapper,node=None):
        """
        level starts at 0 in center
        scale is 2**level
        """
        if node:
            NodePath.__init__(self,node)
        else:
            NodePath.__init__(self,"GeoClipLevel_"+str(level))
        self.level=level
        self.geoClipMapper=geoClipMapper
        
        self.heightTex=loadTex("renderData/textures/grass") # some texture as place holder before map is made.
        self.setShaderInput("height",self.heightTex)
        
        scale=2**(level)
        self.setScale(scale,scale,1)
        
        self.lastTile=None
        
        self.tileScale=geoClipMapper.baseTileScale*scale
        
        self.makingTile=False
        
        self.setShaderInput("tileOffset",0,0,0,0)
        self.setShaderInput("tilePos",0,0,0,0)
    def update(self,bigger):
        """ bigger is next larger _GeoClipLevel, or None is self is biggest """
        
        # Place me!
        s=int(self.getScale().getX())*2
        fx=self.geoClipMapper.focus.getX(self.geoClipMapper.terrainNode)
        fy=self.geoClipMapper.focus.getY(self.geoClipMapper.terrainNode)
        x=int(fx)/s+1
        y=int(fy)/s+1
        self.setPos(x*s,y*s,0)
        
        # Tex Offset
        #node.setShaderInput("texOffset",node.getX()+halfOffset,node.getY()+halfOffset,0,0)

        
        if self.lastTile is not None:
            # get dist from center of self.lastTile to focuse
            tx=(self.lastTile.x+self.tileScale/2.0)/self.geoClipMapper.terrainNode.getSx()
            ty=(self.lastTile.y+self.tileScale/2.0)/self.geoClipMapper.terrainNode.getSy()
            dx=self.getX()-tx
            dy=self.getY()-ty
            
            # convert dx and dy to current level scale
            dx/=self.getSx()
            dy/=self.getSy()
            
            
            # get margin in px between current tile edge and level edge
            s=self.geoClipMapper.heightMapRez
            
            mx=s/2-abs(dx)-self.geoClipMapper.rez/2
            my=s/2-abs(dy)-self.geoClipMapper.rez/2
            
            ox=dx+s/2
            oy=dy+s/2
            self.setShaderInput("tileOffset",ox,oy,0,0)
            self.setShaderInput("tilePos",self.lastTile.x,self.lastTile.y,self.lastTile.scale,0)
            self.setShaderInput("grassData",self.lastTile.renderMaps[self.geoClipMapper.specialMaps['grassData']].tex)
            self.setShaderInput("grassData2",self.lastTile.renderMaps[self.geoClipMapper.specialMaps['grassData2']].tex)
            
            m=min(mx,my)
                

        if (not self.makingTile) and (self.lastTile is None or m<2):
            self.makingTile=True
            x=self.geoClipMapper.focus.getX(self.geoClipMapper)-self.tileScale/2
            y=self.geoClipMapper.focus.getY(self.geoClipMapper)-self.tileScale/2
            self.geoClipMapper.tileSource.asyncGetTile(x,y,self.tileScale,self.asyncTileDone)
            
    def asyncTileDone(self,tile):
        self.lastTile=tile
        print "Tile Level: "+str(self.level)
        self.makingTile=False
        tex=self.lastTile.renderMaps[self.geoClipMapper.specialMaps['height']].tex
        tex.setMinfilter(Texture.FTNearest)
        tex.setMagfilter(Texture.FTNearest)
        self.setShaderInput("height",tex)
        
 