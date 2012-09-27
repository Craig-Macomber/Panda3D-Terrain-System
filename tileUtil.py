import math
def ifloor(x): return int(math.floor(x))

class BakeryManager(object):
    """
    Invariets:
        All entries in renderCach have had render called with them, and are not None
        All entries in midCache that are not None have had render called with them
        All entries in renderCach are also in midCache
        All entries in midCache are also in tileCache
        Any entry that is None in midCache is None in tileCache
    """
    def __init__(self,bakery,tileSize,minRenderSize,maxRenderSize,maxPreGenSize,startX,startY):
        """
        
        bakery should be a bakery.bakery.FixedBakery
        
        
        """
        
        assert minRenderSize<=maxRenderSize<=maxPreGenSize
        
        self.tileSize=tileSize
        
        self.bakery=bakery
        self.asyncBaking=False # only async bake one tile at a time
        tileX=startX/tileSize
        tileY=startY/tileSize
        
        def replaceTileCacheEntry(x,y,old):
            if old:
                self.destroy(old)
            return None
            
        self.tileCache=ToroidalCache(maxPreGenSize,replaceTileCacheEntry,tileX,tileY)
        
        def replaceMidCacheEntry(x,y,old):
            if old:
                self.unrender(old)
            new=self.tileCache.get(x,y)
            if new:
                self.render(new)
            return new
            
        self.midCache=ToroidalCache(maxRenderSize,replaceMidCacheEntry,tileX,tileY)
        
        def replaceRenderTile(x,y,old):
            new=self.tileCache.get(x,y)
            if not new:
                new=self._makeTile(x,y)
                self.midCache.store(x,y,new)
                self.tileCache.store(x,y,new)
                self.render(new)
            return new
            
        self.renderCache=ToroidalCache(minRenderSize,replaceRenderTile,tileX,tileY)
        # TODO : perhaps add some some of addational cache to save things when outside pregen
        #           LRU, weighted by generation time perhaps?
    
    
    def _storeTile(self,x,y,tile):
        if not self.tileCache.inbounds(x,y):
            print "_storeTile Error: tile not inbounds in tileCache",x,y
            return
        t=self.tileCache.get(x,y)
        if t is not None:
            print "_storeTile Error: tile exists in tileCache",x,y
            return
        self.tileCache.store(x,y,tile)
        if self.midCache.inbounds(x,y):
            t=self.midCache.get(x,y)
            if t is not None:
                print "_storeTile Error: tile exists in midCache",x,y
                return
            self.midCache.store(x,y,tile)
            self.render(tile)
            if self.renderCache.inbounds(x,y):
                t=self.renderCache.get(x,y)
                if t is not None:
                    print "_storeTile Error: tile exists in renderCache",x,y
                    return
                self.renderCache.store(x,y,tile)
    
    
    def getTile(self,wx,wy):
        x=ifloor(wx/self.tileSize)
        y=ifloor(wy/self.tileSize)
        if self.tileCache.inbounds(x,y):
            return self.tileCache.get(x,y) # might be none if not generated
        return None
        
    def _makeTile(self,x,y,async=False):
        if async:
            self.asyncBaking=True
            self.bakery.asyncGetTile(x, y, self._asyncTileDone, (x,y))
        else:
            self.asyncBaking=False
            return self.bakery.getTile(x, y)
    
    def updateCenter(self,worldX,worldY):
        """
        updated the location around which rendering and caching is being done.
        
        if there are tiles withing the minRenderSize that are not ready,
        this call will block and finish them.
        
        After this call, a grid of minRenderSize*minRenderSize centered at or near the passed x,y
        is guarenteed to be rendered.
        """
        x=worldX/self.tileSize
        y=worldY/self.tileSize
        
        self.tileCache.updateCenter(x,y)
        self.midCache.updateCenter(x,y)
        self.renderCache.updateCenter(x,y)
        
        if not self.asyncBaking:
            minDistSquared=1000000
            minX=minY=None
            for iy in xrange(self.tileCache.size):
                ty=iy+self.tileCache.originY
                for ix in xrange(self.tileCache.size):
                    tx=ix+self.tileCache.originX
                    if self.tileCache.get(tx,ty) is None:
                        distSquared=(tx-x)**2+(ty-y)**2
                        if distSquared<minDistSquared:
                            minX=tx
                            minY=ty
                            minDistSquared=distSquared      
            if minX!=None:
                self._makeTile(ifloor(minX),ifloor(minY),True)
        
    
    def _asyncTileDone(self,tile,x,y):
        if not self.asyncBaking:
            print "Bake sync error"
            return
        self.asyncBaking=False
        if self.tileCache.inbounds(x,y):
            t=self.tileCache.get(x,y)
            if t is None:
                self._storeTile(x,y,tile)
    
    def render(self,tile):
        """
        tile for spec is done and should be displayed
        
        override as needed
        """
        pass
        
    def unrender(self,tile):
        """
        tile is outside rendering area, and should be hidded
        
        override as needed
        """
        pass
        
    def destroy(self,tile):
        """
        tile has been unrendered, or never was rendered, but is no longer managed by this manager
        and will not be needed again. If needed again, will be regenerated, so dispose of this tile
        
        override as needed
        """
        pass

class NodePathBakeryManager(BakeryManager):
    def __init__(self,parentNodePath,*args,**kargs):
        self.parentNodePath=parentNodePath
        BakeryManager.__init__(self,*args,**kargs)
    
    def render(self,tile):
        """
        tile for spec is done and should be displayed
        """
        tile.reparentTo(self.parentNodePath)
        
    def unrender(self,tile):
        """
        tile is outside rendering area, and should be hidded
        """
        tile.detachNode()
        
    def destroy(self,tile):
        """
        tile has been unrendered, or never was rendered, but is no longer managed by this manager
        and will not be needed again. If needed again, will be regenerated, so dispose of this tile
        """
        tile.removeNode()

class ToroidalCache(object):
    def __init__(self,size,replaceValue,startX=0,startY=0,hysteresis=0.1):
        """
        replaceValue(x,y,old) where old is the previous tile, or None it there was none
        startX and startX locate the center for starting, much like the x and y for updateCenter
        see updateCenter for info about hysteresis
        """
        self.size=size
        self.originX=ifloor(startX+.5-size/2.0)
        self.originY=ifloor(startY+.5-size/2.0)
        self.hysteresis=hysteresis
        self.replaceValue=replaceValue
        self.data=[None]*(size**2)
        for x in xrange(size):
            for y in xrange(size):
                tx=x+self.originX
                ty=y+self.originY
                self.store(tx,ty,self.replaceValue(tx,ty,None))
                
        
    def updateCenter(self,x,y):
        """
        x and y can be floats or ints. If the passed x,y is further than hysteresis+0.5 from
        center in either x or y, then move origin
        
        """
        offset=self.size/2.0
        
        tolarance=self.hysteresis+0.5
        
        xError=x-(offset+self.originX)
        yError=y-(offset+self.originY)
        xChange=int(round(xError)) if abs(xError)>tolarance else 0
        yChange=int(round(yError)) if abs(yError)>tolarance else 0
        if xChange or yChange:
            originX=self.originX+xChange
            originY=self.originY+yChange
            # check all the tiles to see if they need to be replaced
            # this could be opimized to only check the ones that may have changed,
            # but size is usally small, so this is quick and simpler
            for yindex in xrange(originY,originY+self.size):
                for xindex in xrange(originX,originX+self.size):
                    if not self.inbounds(xindex,yindex):
                        old=self.get(xindex,yindex)
                        new=self.replaceValue(xindex,yindex,old)
                        self.store(xindex,yindex,new)
                    
            self.originX=originX
            self.originY=originY
        
    def inbounds(self,x,y):
        """
        x and y are ints in the same coordnit system as update center and the origin
        """
        return (0<=(x-self.originX)<self.size) and (0<=(y-self.originY)<self.size)
        
    def get(self,x,y):
        """
        x and y are ints in the same coordnit system as update center and the origin
        """
        return self.data[self._cellIndex(x,y)]
        
    def _cellIndex(self,x,y):
        col=x%self.size
        row=y%self.size
        return col+row*self.size
        
    def store(self,x,y,data):
        """
        save entry in cache.
        if x,y is not inbounds, this will overwite some other location in the cache!
        """
        self.data[self._cellIndex(x,y)]=data