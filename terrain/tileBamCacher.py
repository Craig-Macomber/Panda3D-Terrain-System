"""

This acts very much like a renderer, except instead of rendering to screen,
it ouputs bam files, one per tile with all the LOD and such packed in

"""

import os
import os.path

import json

import bakery.bakery
import bakery.gpuBakery

from renderer.renderTiler import RenderNodeTiler

from panda3d.core import NodePath

def nameTile(x,y):
    return str(x)+"_"+str(y)

dataFile="data.txt"

def exportTile(dstDir,name,tile):
    tile.writeBamFile(os.path.join(dstDir,name+".bam"))

def importTile(srcDir,name,callback=None):
    def done(model):
        callback(RenderTile(model))
    path=os.path.join(srcDir,name+".bam")
    if callback:
        loader.loadModel(path,callback=done)
    else:
        return RenderTile(loader.loadModel(path))

class RenderTile(NodePath):
    def __init__(self,tile):
        NodePath.__init__(self,tile.node())
    def height(self,x,y):
        return 0

def getRenderer(dir,focus,importer=importTile):
    b=CachedNodeBakery(dir,importer)
    scale=b.tileSize
    return RenderNodeTiler(b,scale,focus)

def cache(dir,renderTileBakery,size,startX,startY,xCount,yCount,defaultX,defaultY,exporter=exportTile,originX=0,originY=0):
    x=object()
    class thingy:
        def getTile(self,x, y):
            tile=renderTileBakery.getTile(x,y)
            #tile.meshes.flattenStrong()
            return tile.meshes
    
    fbak=thingy()
    
    extraInfo={
        'size':size,
        'originX':originX,
        'originY':originY,
        }
    b=Bammer(fbak,dir,exporter=exporter,extraInfo=extraInfo)
    b.processGrid(startX,startY,xCount,yCount)
    b.setDefaultTile(defaultX,defaultY)
    b.finish()
    

        
class CachedNodeBakery:
    def __init__(self,dir,importer):
        path=os.path.join(dir,dataFile)
        d=json.load(open(path,'r'))
        self.default=d['default']
        extraInfo=d['extraInfo']
        self.tileSize=extraInfo['size']
        self.originX=extraInfo['originX']
        self.originY=extraInfo['originY']
        self.tiles=set(tuple(t) for t in d['tiles'])
        self.dir=dir
        self.importer=importer
        
    
    def _getName(self, x, y):
        t=(x, y)
        if t in self.tiles:
            return nameTile(*t)
        else:
            return nameTile(*self.default)
    
    def getTile(self, x, y):
        return self.importer(self.dir,self._getName(x, y))
    
    def asyncGetTile(self, x, y, callback, callbackParams=()):
        def done(model):
            callback(model,*callbackParams)
        self.importer(self.dir,self._getName(x, y),callback=done)
    


class Bammer:
    def __init__(self,nodeBakery,dstDir,exporter,extraInfo={}):
        """
        nodeBakery is a bakery.FixedBakery that produces NodePaths
        
        dstDir is where tiles will be saved, os specific style filepath
        """
        self.nodeBakery=nodeBakery
        
        self.processed=set()
        
        self.default=None
        
        self.dstDir=dstDir
        
        self.extraInfo=extraInfo
        
        self.exporter=exporter
        
    def processGrid(self,startX,startY,xCount,yCount):
        for x in xrange(xCount):
            for y in xrange(yCount):
                self.processTile(startX+x,startY+y)
    
    def processTile(self,x,y):
        t=(x,y)
        if t not in self.processed:
            node=self.nodeBakery.getTile(x,y)
            self.exporter(self.dstDir,nameTile(*t),node)
            self.processed.add(t)
        else:
            print "skipping redundant tile "+str(t)
    
    def setDefaultTile(self,x,y):
        self.processTile(x,y)
        self.default=(x,y)
        
    def finish(self):
        f=open(os.path.join(self.dstDir,dataFile),"w")
        d={"default":self.default,
            "extraInfo":self.extraInfo,
            "tiles":list(self.processed)
        }
        json.dump(d,f)
        f.close()