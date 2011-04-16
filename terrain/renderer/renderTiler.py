import math

from renderer import RenderNode
from terrain.bakery.bakery import loadTex
from terrain.meshManager import meshManager

from panda3d.core import *
from direct.task.Task import Task

from terrain import tileUtil

class RenderTiler(RenderNode):
    def __init__(self,path,heightScale,meshFactories):
        RenderNode.__init__(self,path,NodePath(path+"_terrainNode"),heightScale)
        
        self.meshManager=meshManager.MeshManager(meshFactories)
    
    def addTile(self, bakedTile):
        n=RenderTile(bakedTile,self)
        n.reparentTo(self.terrainNode)
        return n
        
    def addTiles(self, bakedTiles):
        """ Expects a list of lists of tiles """
        for tlist in bakedTiles:
            for t in tlist:
                self.addTile(t)
    
    def removeTile(self, renderTile):
        renderTile.removeNode()



# class RenderAutoTiler(RenderTiler):
#     def __init__(self,path,tileSource,tileScale,focus,addThreshold=1.0,removeThreshold=1.8,heightScale=300):
#         RenderTiler.__init__(self,path,heightScale)        
#         self.tileSource=tileSource
#         self.tileScale=tileScale
#         self.tilesMade=0
#         self.addThreshold=addThreshold
#         self.removeThreshold=removeThreshold
#         self.focus=focus
#         
#         self.currentGenTile=None
#         
#         # Add a task to keep updating the terrain
#         taskMgr.add(self.updateTiles, "updateTiles")
#         
#     def updateTiles(self,task):
#         
#         """Make any needed tiles and remove any unneeded"""
#         
#         # This is offset as if the tile origin was in their center!
#         # Its also scaled so the current tiles are size 1
#         camTilePos=(self.focus.getPos(self))/self.tileScale-Vec3(0.5, 0.5, 0.0)
#         camTilePos.setZ(0)
#         
#         # Figure out which tiles are needed
#         # This is done by looping by nearby tiles positions, and checking their distances
#         
#         # Stores (tile x index, tile y index) : distance
#         needTiles={}
#         
#         addRange=xrange(int(-math.ceil(self.addThreshold)),int(math.ceil(self.addThreshold)))
#         xOffset=int(math.ceil(camTilePos.getX()))
#         yOffset=int(math.ceil(camTilePos.getY()))
#         vecOffset=Vec3(xOffset,yOffset,0)
#         for x in addRange:
#             for y in addRange:
#                 vecOffset=Vec3(int(xOffset+x),int(yOffset+y),0)
#                 d=(camTilePos-vecOffset).length()
#                 if d<self.addThreshold:
#                     # Add location index tuple to needTiles
#                     needTiles[(xOffset+x,yOffset+y)]=d
#         
#         
#         # Go through existing tiles
#         # Remove them from needTiles as they are already generated
#         # Collect any tiles too far away to keep in toRemove so they can be removed later
# 
#         tiles=self.getTiles()
#         # Remove distant tiles and remove existing tiles from needTiles
#         for t in tiles:
#             if t.tileLoc in needTiles:
#                 del needTiles[t.tileLoc]
#             dist=(camTilePos-(t.getPos()/self.tileScale)).length()
#             if dist>self.removeThreshold:
#                 self.removeTile(t)
#         
#         # Add a tile if appropriate
#         if self.currentGenTile is None:
#             if len(needTiles)>0:
#                 minTile,minDist=needTiles.popitem()
#                 for k,v in needTiles.iteritems():
#                     if v<minDist:
#                         minTile=k
#                         minDist=v
#                 self.currentGenTile=minTile
#                 x=minTile[0]*self.tileScale
#                 y=minTile[1]*self.tileScale
#                 self.tileSource.asyncGetTile(x,y,self.tileScale,self._asyncTileDone)
#                 
#                
#         return task.cont
#     
#     def _asyncTileDone(self,tile):
#             t=self.addTile(tile)
#             t.tileLoc=self.currentGenTile
#             self.currentGenTile=None
#             self.tilesMade+=1
#             
#             
#     def height(self,x,y):
#         # This is inefficent. Should keep a tile dictionary around for finding the right one
#         # This has issues. It's inaccurate and has seam problems for some reason.
#         tiles=self.getTiles()
#         for t in tiles:
#             xDif=x-t.getX()
#             if xDif>=0 and xDif<=self.tileScale:
#                 yDif=y-t.getY()
#                 if yDif>=0 and yDif<=self.tileScale:
#                     
#                 
#                     # found correct tile
#                     h=t.terrain.heightfield()
#                     mapSize=h.getXSize()
#                     s=(mapSize-1)/self.tileScale
#                     xLoc=min(mapSize,max(0,xDif*s))
#                     yLoc=min(mapSize,max(0,yDif*s))
#                     
#                     return t.terrain.getElevation(xLoc,yLoc)*self.heightScale
#                     '''
#                     
#                     xLoc=min(mapSize,max(0,xDif*s))
#                     yLoc=min(mapSize,max(0,mapSize-yDif*s-1))
#                     px1=int(floor(xLoc))
#                     py1=int(floor(yLoc))
#                     px2=int(ceil(xLoc))
#                     py2=int(ceil(yLoc))
#                     xFade=xLoc-px1
#                     yFade=yLoc-py1
#                     v1=h.getRed(px2,py1)*xFade+h.getRed(px1,py1)*(1-xFade)
#                     v2=h.getRed(px2,py2)*xFade+h.getRed(px1,py2)*(1-xFade)
#                     v=v2*yFade+v1*(1-yFade)
#                     return v*self.heightScale  
#                     '''
#         #print "Find height Failed"
#         return 0
# 


class RenderAutoTiler2(RenderTiler):
    def __init__(self,path,tileSource,tileScale,focus,meshFactories,forceRenderedCount=2,maxRenderedCount=4,heightScale=100):
        RenderTiler.__init__(self,path,heightScale,meshFactories)        
        self.tileSource=tileSource
        self.tileScale=tileScale
        self.tilesMade=0
        self.forceRenderedCount=forceRenderedCount
        self.maxRenderedCount=maxRenderedCount
        self.focus=focus
        
        self.renderTileBakery=RenderTileBakery(tileSource,self)
        
        cacheSize=maxRenderedCount
        x,y=self.focuseLoc()
        self.bakeryManager=tileUtil.NodePathBakeryManager(self.terrainNode,
            self.renderTileBakery,tileScale,
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


class RenderTileBakery(object):
    """
    A class the wraps a bakery to produce RenderTiles instead of baked tiles
    """
    def __init__(self,bakery,renderNode):
        self.bakery=bakery
        self.hasTile=bakery.hasTile
        self.renderNode=renderNode
        
    def getTile(self, xStart, yStart, tileSize):
        return RenderTile(self.bakery.getTile(xStart, yStart, tileSize),self.renderNode)
    
    def asyncGetTile(self, xStart, yStart, tileSize, callback, callbackParams=()):
        self.bakery.asyncGetTile(xStart, yStart, tileSize, self._asyncTileDone, (callback,callbackParams))
        
    def _asyncTileDone(self,tile,callback,callbackParams):
        callback(RenderTile(tile,self.renderNode),*callbackParams)

class RenderTile(NodePath):
    def __init__(self,bakedTile,node):
        """
        node = the renderNode this is for
        """
        self.bakedTile=bakedTile
        
        NodePath.__init__(self,"renderTile")
        self.setPythonTag("subclass", self)
        
        self.renderNode=node
        
        
        self.tileScale=bakedTile.scale
        
        # Save a center because some things might want to know it.
        self.center=Vec3(bakedTile.x+self.tileScale/2.0,bakedTile.y+self.tileScale/2.0,0)
        
        renderMaps=bakedTile.renderMaps
        
        
              
        
        
        
        # generate meshes on it
        x=bakedTile.x
        y=bakedTile.y
        x2=x+bakedTile.scale
        y2=y+bakedTile.scale
        
        self.heightScale=node.heightScale
        
        self.meshes=node.meshManager.getLODLevel(0).makeTile(x,y,x2,y2,self)
        self.meshes.reparentTo(self)
        
    def update(self,focus):
        self.meshes.update(focus)
        
    def height(self,x,y):
        t=self
        xDif=x-self.bakedTile.x
        if xDif>=0 and xDif<=self.tileScale:
            yDif=y-self.bakedTile.y
            if yDif>=0 and yDif<=self.tileScale:
    
                # found correct tile
                h=t.terrain.heightfield()
                mapSize=h.getXSize()
                s=(mapSize-1)/self.tileScale
                xLoc=min(mapSize,max(0,xDif*s))
                yLoc=min(mapSize,max(0,yDif*s))
                
                return t.terrain.getElevation(xLoc,yLoc)*self.heightScale

        #print "Find height Failed"
        return 0.0
