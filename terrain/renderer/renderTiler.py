import math

from renderer import RenderNode
from terrain.bakery.bakery import loadTex
from terrain.meshManager import meshManager

from panda3d.core import *
from direct.task.Task import Task

from terrain import tileUtil

from terrain.bakery.bakery import FixedBakery,FixWrapped


class RenderNodeTiler(NodePath):
    def __init__(self,renderTileSource,tileSize,focus,forceRenderedCount=2,maxRenderedCount=4):
        NodePath.__init__(self,"RenderNodeTiler")        
        self.tileSize=tileSize
        self.forceRenderedCount=forceRenderedCount
        self.maxRenderedCount=maxRenderedCount
        self.focus=focus
        
        self.renderTileBakery=renderTileSource
        
        cacheSize=maxRenderedCount
        x,y=self.focuseLoc()
        self.bakeryManager=tileUtil.NodePathBakeryManager(self,
            self.renderTileBakery,tileSize,
            forceRenderedCount,maxRenderedCount,cacheSize,
            x,y)
        
        # Add a task to keep updating the terrain
        taskMgr.add(self.updateTiles, "updateTiles")
    def focuseLoc(self):
        p=self.focus.getPos(self)
        return p.getX(),p.getY()
    
    def updateTiles(self,task):
        self.bakeryManager.updateCenter(*self.focuseLoc())
        return Task.cont 
            
    def height(self,x,y):
        return self.bakeryManager.getTile(x,y).height(x,y)



class RenderTileBakery(FixedBakery):
    """
    A class the wraps a bakery to produce RenderTiles instead of baked tiles
    """
    def __init__(self,bakery,tileSize,meshManager,heightScale):
        self.bakery=FixWrapped(bakery,tileSize)
        self.hasTile=bakery.hasTile
        self.makeTile=meshManager.tileFactory(tileSize)#maxDistance=float('inf'),minDistance=0,collision=False)
        self.heightScale=heightScale
        
    def getTile(self, x, y):
        return RenderTile(self.bakery.getTile(x, y),self.makeTile,self.heightScale)
    
    def asyncGetTile(self, x, y, callback, callbackParams=()):
        self.bakery.asyncGetTile(x, y, self._asyncTileDone, (callback,callbackParams))
        
    def _asyncTileDone(self,tile,callback,callbackParams):
        callback(RenderTile(tile,self.makeTile,self.heightScale),*callbackParams)

class RenderTile(NodePath):
    """
    Currently this calss gets it's height(x,y) method added to it by a GroundFactory
    
    It could sample its height map instead, but it does not know the height scale.
    """
    def __init__(self,bakedTile,makeTile,heightScale):
        """
        node = the renderNode this is for
        """
        self.heightScale=heightScale
        
        
        self.bakedTile=bakedTile
        
        NodePath.__init__(self,"renderTile")
        self.setPythonTag("subclass", self)
        
        
        
        self.tileScale=bakedTile.scale
        
        # Save a center because some things might want to know it.
        self.center=Vec3(bakedTile.x+self.tileScale/2.0,bakedTile.y+self.tileScale/2.0,0)
        
        renderMaps=bakedTile.renderMaps
        
        # generate meshes on it
        x=bakedTile.x
        y=bakedTile.y
        x2=x+bakedTile.scale
        y2=y+bakedTile.scale
        
        
        self.meshes=makeTile(x,y,self)
        
        if self.meshes is None:
            self.meshes=NodePath("EmptyMeshes")
        self.meshes.reparentTo(self)
        
    def update(self,focus):
        self.meshes.update(focus)
    
    def height(self,x,y):
        h=self.sampleMap('height',x,y,extraPx=True)
        return self.heightScale*(h.getX()+h.getY()/(256.0)+h.getZ()/(256.0**2))
    
    def sampleMap(self,mapName,x,y,extraPx=True):
        """
        
        x,y in world space
        
        extraPx=True means corners of tile are mapped to centers of corner pixels of map,
        as is the case with the height maps. Good for avoiding seams.
        
        extraPx=False not tested for accuracy
        
        """
        
        map=self.bakedTile.renderMaps[mapName]
    
        peeker=map.tex.peek()
        
        if peeker is None:
            print "Error: sampleMap "+mapName+" failed"
            return 0
        
        tx=(x-self.bakedTile.x)/self.tileScale
        ty=(y-self.bakedTile.y)/self.tileScale
        
        sx=peeker.getXSize()
        sy=peeker.getYSize()
        
        if extraPx:
            px=((sx-1)*tx)
            py=((sy-1)*ty)
        else:
            px=(sx*tx)
            py=(sy*ty)
        
        
        ix=math.floor(px)
        iy=math.floor(py)
        fu=px-ix
        fv=py-iy

        
        
        #peeker.lookup(c,u,v)
        def getH(x,y):
            x=float(max(min(sx,x),0))
            y=float(max(min(sy,y),0))
            if extraPx:
                x+=.5
                y+=.5
            c=Vec4()
            peeker.lookup(c,x/sx,y/sy)
            return c
        h=(getH(ix+1,iy+1)*fu+getH(ix,iy+1)*(1-fu))*fv+(getH(ix+1,iy)*fu+getH(ix,iy)*(1-fu))*(1-fv)
        return h
    
