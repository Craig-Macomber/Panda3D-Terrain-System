from panda3d.core import NodePath, Geom, GeomNode, GeomVertexWriter, GeomVertexData, GeomVertexFormat, GeomTriangles, GeomTristrips, LODNode, Vec3, RenderState
import math

import collections
import heapq

from terrain import tileUtil

"""
This module provides a MeshManager class and its assoiated classes.

Together this creates a system for paging and LODing meshes that streams them into
minimal ammounts of Geom and NodePaths. This allows for properly chunked, paged and LODed
meshes, in a finifed system that does not create any temparart/intermeadary meshes or data,
requires no flattening works with fully procedural meshes.

Support for static meshes should be straight forward, just impliment a MeshFactory
that caches the vertex data
and geom data in a optimized manner for writing out.

for performance, most or all of this, including the factories should be ported to C++
The main performance bottleneck should be the auctual ganeration and writing on meshes
into the geoms. This is greatly slowed by both python, and the very high ammount of calls across
Panda3D's python wrapper.

However, even in pure python, reasonable performance can be achieved with this system!
"""

class _LODLevel(object):
    """
    this is very explicitly NOT threadsafe in any way,
    and makes most of the other stuff also not thread safe
    """
    def __init__(self,lod,factories):
        """
        factoriesAndLODs should be list of (LOD,MeshFactory)
        
        
        
        """
        self.factories=factories
        self.geomRequirementsCollection=GeomRequirementsCollection()
        self.lod=lod
        for f in factories:
            f.regesterGeomRequirements(lod,self.geomRequirementsCollection)
        
        self.makingTile=False
        self.drawResourcesFactory=None 
        
    def initForTile(self,tile):
        assert not self.makingTile
        self.drawResourcesFactory=self.geomRequirementsCollection.getDrawResourcesFactory(tile)
        self.makingTile=True
        
#     def doFactory(self,f,x,y,x2,y2,tileCenter):
#         assert self.makingTile
#         if self.drawResourcesFactory is not None:
#             f.draw(self.lod,x,y,x2,y2,drawResourcesFactory,tileCenter)
    
    def finishTile(self):
        assert self.makingTile
        self.node = self.drawResourcesFactory.getNodePath()
    
    def clean(self):
        assert self.makingTile
        self.makingTile=False
        self.node=None
        self.drawResourcesFactory=None
        
#     def makeTile(self,x,y,x2,y2,tile,tileCenter):
#         """
#         Returns a NodePath is geometry was needed, If empty, may return None
#         """
#         
#         drawResourcesFactory=self.geomRequirementsCollection.getDrawResourcesFactory(tile)
#         if drawResourcesFactory is None:
#             return None
#         
#         for f in factories:
#             f.draw(self.lod,x,y,x2,y2,drawResourcesFactory,tileCenter)
#         
#         nodePath=drawResourcesFactory.getNodePath()
# 
#         return nodePath


LOD=collections.namedtuple("LOD",["high","low"])
    
class MeshManager(NodePath):
    """
    A NodePath that will fill it self with meshes, with proper blocking and LOD
    
    meshes come from passed in factories
    
    this is optimized around a high number of factories, meaning that if LOD transitions line up
    it may produce less than one geom per factory per tile
    (aka, it draws all compataible factories into the same geoms)
    
    """
    def __init__(self,factories):

        self.factories=factories
        
        # collect all LODs in a useful data structure
        LODtoFact=collections.defaultdict(set)
        for f in factories:
            LODs=f.getLODs()
            for l in LODs:
                LODtoFact[l].add(f)
        
        # make the _LODLevels
        LODtoLevel={}
        for lod,facs in LODtoFact.iteritems():
            LODtoLevel[lod]=_LODLevel(lod,facs)
        
        
        # we could render everything just using the _LODLevels
        # but this would require lots of LOD nodes at the top level
        # so the rest of this init code takes all of these potentially overlapping LOD ranges
        # and makes a list of LOD ranges and the levels they contain
        # this means one top level LOD node. It may have a few nodes under it,
        # but this keeps the critical case of rendering low LODs with few nodes very optimal,
        # and takes advantage factories that don't have LOD levels out to the max distance
        
        # some constants for clarity
        # high sorts before low when the values are the same
        high=0 # reffers to distance, not LOD level
        low=1  # reffers to distance, not LOD level
        
        end=collections.namedtuple("end",["value","end","lod"])
        ends=[] # list of (value,high/low,lod)
        
        for lod in LODtoFact.iterkeys():
            ends.append(end(lod.high,high,lod))
            ends.append(end(lod.low,low,lod))
        
        ends.sort()
        
        
        
        # list of (LOD,set of _LODLevels) that should be rendered
        # during that range
        # overall list is in closer to further order
        self.LODtoLevels=[]
        
        
        # walk up ends, creating all the LOD levels needed
        # a somewhat confusing but interesting and efficent algorithm
        activeSet=set() # set of LODs
        lastEnd=(0,low,None)
        currentStart=0
        i=0
        while i<len(ends):
            
            # add all LOD ranges starting at the currentStart
            while ends[i].end==low and ends[i].value==currentStart:
                activeSet.add(ends[i].lod)
                i+=1
            
            # save LOD range if appropriate 
            if len(activeSet)>0: 
                levels=set(LODtoLevel[lod] for lod in set(activeSet))
                self.LODtoLevels.append((LOD(ends[i].value,currentStart),levels))
            
            # remove all LODs (if any) ending at the end of the LOD span we just saved
            currentStart=ends[i].value
            while i<len(ends) and ends[i].end==high and ends[i].value==currentStart:
                activeSet.discard(ends[i].lod)
                i+=1
        
    def tileFactory(self,size,maxDistance=float('inf'),minDistance=0,collision=False):
        """
        maxDistance=max view distance (for minimum LOD)
        minDistance=min view distance (for maximum LOD)
        """
        levels=set()
        # self.LODtoLevels is ordered, so this could be speed up a bit, but the time it takes
        # is insignificant, and is only part of setup.
        LODAndLevelList=[]
        for lod,levelSet in self.LODtoLevels:
            if lod.high>minDistance and lod.low<maxDistance:
                levels.update(levelSet)
                LODAndLevelList.append((lod,list(levelSet)))
        
        
        
        factoryToLevels=collections.defaultdict(list)
        for l in levels:
            for f in l.factories:
                factoryToLevels[f].append(l)
        
        # subTileFactories are makeTile closures made for smaller tiles
        # smaller sub tiles are needed for LOD to work properly for distances
        # on the scale of and smaller than the tile size
        # so the LODs can transition on part of the parent tile at a time
        
        # TODO : use sub tile factories!
        subTileFactories=[]
        LODtoSubTileFactoryIndexs={}
        
        def makeTile(x,y,tile):
            # the idea here is to make
            # all the needed nodes,
            # then instance them to all the LODNode's children that show them
            
            x2=x+size
            y2=y+size
            
            tileCenter=Vec3(x+x2,y+y2,0)/2
            
            collisionNode=NodePath("tile_collisionNode") if collision else None
            
            for l in levels: l.initForTile(tile)
            for f,levs in factoryToLevels.iteritems():
                f.draw(dict((l.lod,l.drawResourcesFactory) for l in levs),x,y,x2,y2,tileCenter,collisionNode)
                
            
            lodNode=LODNode('tile_lod')
            lodNodePath=NodePath(lodNode)
            
            subTileNodeLists=[]
            s=size/2
            for f in subTileFactories:
                nodeList=[f(x,y,tile),f(x+s,y,tile),f(x,y+s,tile),f(x+s,y+s,tile)]
                subTileNodeLists.append(nodeList)
            
            for l in levels: l.finishTile()
            
            lodNodePath.setPos(tileCenter)
            if collision: collisionNode.setPos(tileCenter)
            for lod,levs in LODAndLevelList:
                holder=NodePath("holder")
                # instance regular meshes 
                for l in levs:
                    n=l.node
                    if n is not None:
                        n.instanceTo(holder)
                # instance subtile LOD nodes 
                if lod in LODtoSubTileFactoryIndexs:
                    for i in LODtoSubTileFactoryIndexs[lod]:
                        for n in subTileNodeLists[i]:
                            instanceTo(holder)
                            
                holder.reparentTo(lodNodePath)
                lodNode.addSwitch(lod.high,lod.low)
            
            # TODO, better center LOD Node using bounds
            # lodNode.setCenter()
            
            for l in levels: l.clean()
            
            if collision:
                tileHolder=NodePath("tile_holder")
                collisionNode.reparentTo(tileHolder)
                lodNodePath.reparentTo(tileHolder)
                return tileHolder
            else:
                return lodNodePath
        return makeTile

        
class MeshFactory(object):
    def regesterGeomRequirements(self,LOD,collection):
        """
        collection is a GeomRequirementsCollection
        
        example:
        self.trunkData=collection.add(GeomRequirements(...))
        """
        raise NotImplementedError()
    
    def getLODs(self):
        raise NotImplementedError()
        #return [] # list of values at which rendering changes somewhat
    
    def draw(self,drawResourcesFactories,x,y,x1,y1,tileCenter):
        raise NotImplementedError()#pass # gets called with all entries in getGeomRequirements(LOD)
    
    
# TODO : consider palletizing textures
class GeomRequirements(object):
    """
    a set of requirements for one part of mesh.
    this will get translated to a single geom, or a nodePath as needed,
    and merged with matching requirements
    """
    def __init__(self,geomVertexFormat,renderState=RenderState.makeEmpty()):
        self.geomVertexFormat=geomVertexFormat
        self.renderState=renderState
    def __eq__(self,other):
         return (self.renderState.getUnique()==other.renderState.getUnique()
                and self.geomVertexFormat==other.geomVertexFormat)

    
class DrawResources(object):
    """
    this provides the needed objects for outputting meshes.
    the resources provided match the corosponding GeomRequirements this was constructed with
    """
    def __init__(self,geomNodePath,geomRequirements):
        self.geom=None
        self.nodePath=geomNodePath
        self.node=geomNodePath.node()
        self.geomRequirements=geomRequirements
        
        self.writers={}
        
        self._geomTriangles = None
        self._geomTristrips = None
    
    def _getGeom(self):
        if self.geom is None:
            self.vdata = GeomVertexData("verts", self.geomRequirements.geomVertexFormat, Geom.UHStatic) 
            self.node.addGeom(Geom(self.vdata))
            self.geom=self.node.modifyGeom(self.node.getNumGeoms()-1)
        return self.geom
    
    def getWriter(self,name):
        if name not in self.writers:
            g=self._getGeom()
            self.writers[name] = GeomVertexWriter(self.vdata, name)
        return self.writers[name]
    
    def attachNode(self,nodePath):
        nodePath.reparentTo(self.nodePath)
    
    def getGeomTriangles(self):
        if self._geomTriangles is None:
            self._geomTriangles = GeomTriangles(Geom.UHStatic)
        return self._geomTriangles
    
    def getGeomTristrips(self):
        if self._geomTristrips is None:
            self._geomTristrips = GeomTristrips(Geom.UHStatic)
        return self._geomTristrips
    
    def finalize(self):
        if self._geomTriangles is not None:
            g=self._getGeom()
            g.addPrimitive(self._geomTriangles)
        if self._geomTristrips is not None:
            g=self._getGeom()
            g.addPrimitive(self._geomTristrips)


# TODO : remove this infavor of using per geom renderStates
class _DrawNodeSpec(object):
    """
    spec for what properties are needed on the
    NodePath assoiated with a DrawResources/GeomRequirements
    """
    def __init__(self,parentIndex,renderState=RenderState.makeEmpty()):
        # parentIndex of -1 == root
        self.renderState=renderState
        self.parentIndex=parentIndex


class GeomRequirementsCollection(object):
    """
    a collection of unique GeomRequirements objects.
    
    identical entries are merged
    """
    def __init__(self):
        self.entries=[]
        self.drawNodeSpecs=None
        self.entryTodrawNodeSpec=None # entries[i]'s drawNode is entryTodrawNodeSpec[i]

    def add(self,entry):
        """
        entry should be a GeomRequirements
        returns index added at, used to get DrawResources from result of getDrawResourcesFactory
        """
        for i,e in enumerate(self.entries):
            if e==entry: return i
        self.entries.append(entry)
        self.drawNodeSpecs=None
        return len(self.entries)-1

    def getDrawResourcesFactory(self,tile):
        if len(self.entries) == 0: return None
        if self.drawNodeSpecs is None:
            
            # this is a temp basic non optimal drawNodeSpecs setup
            # TODO : analize requirements on nodes and design hierarchy to minimize state transitions
            self.drawNodeSpecs=[_DrawNodeSpec(-1)]
            for e in self.entries:
                self.drawNodeSpecs.append(_DrawNodeSpec(0,renderState=e.renderState))
           
            self.entryTodrawNodeSpec=range(1,len(self.entries)+1)
            
            
        return DrawResourcesFactory(self.entries,self.entryTodrawNodeSpec,self.drawNodeSpecs,tile)


class DrawResourcesFactory(object):
    """
    produced by GeomRequirementsCollection
    
    provides DrawResources objects corresponding to a GeomRequirements
    indexed by return value from GeomRequirementsCollection.add
    """
    def __init__(self,requirements,entryTodrawNodeSpec,drawNodeSpecs,tile):
        self.requirements=requirements
        self.entryTodrawNodeSpec=entryTodrawNodeSpec
        self.drawNodeSpecs=drawNodeSpecs
        self.nodePaths=[None]*len(self.drawNodeSpecs)
        self.resources=[None]*len(self.requirements)
        self.np=None
        self.tile=tile

    def getNodePath(self):
        """
        returns None if nothing drawn, else returns a NodePath
        
        finalizes resources
        """
        for r in self.resources:
            if r is not None:
                r.finalize()
        return self.np

    def _getNodePath(self,nodeIndex):
        np=self.nodePaths[nodeIndex]
        if np is not None: return np
        
        s=self.drawNodeSpecs[nodeIndex]
        
        node=GeomNode("DrawResourcesFactoryGeomNode")
        if s.parentIndex==-1:
            np=NodePath(node)
            self.np=np
        else:
            np=self._getNodePath(s.parentIndex).attachNewNode(node)
        self.nodePaths[nodeIndex]=np
        
        # setup render atributes on np here:
        np.setState(s.renderState)
        
        return np
        
    def getDrawResources(self,index):
        """
        returns corresponding DrawResources instance
        """
    
        r=self.resources[index]
        if r is not None: return r
        
        nodeIndex=self.entryTodrawNodeSpec[index]
        nodePath=self._getNodePath(nodeIndex)
        r=DrawResources(nodePath,self.requirements[index])
        self.resources[index]=r
        
        return r
    
    def getTile(self):
        return self.tile
        