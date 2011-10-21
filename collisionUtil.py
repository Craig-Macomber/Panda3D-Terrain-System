from panda3d.core import NodePath,CollisionPolygon,CollisionNode,GeomVertexReader,BitMask32

groundMask=BitMask32(0b1)


# from FenrirWolf via http://www.panda3d.org/forums/viewtopic.php?p=43705&sid=d5588e66bcedd9f7c7f51a3226ad890c
# modified by Craig Macomber
def rebuildGeomNodesToColPolys (incomingNode,relativeTo=None): 
    ''' 
    Converts GeomNodes into CollisionPolys in a straight 1-to-1 conversion 

    Returns a new NodePath containing the CollisionNodes 
    ''' 
    
    parent = NodePath('cGeomConversionParent') 
    for c in incomingNode.findAllMatches('**/+GeomNode'): 
        if relativeTo:
            xform=c.getMat(relativeTo).xformPoint
        else:
            xform=(c.getMat(incomingNode)*(incomingNode.getMat())).xformPoint
        gni = 0 
        geomNode = c.node() 
        for g in range(geomNode.getNumGeoms()): 
            geom = geomNode.getGeom(g).decompose() 
            vdata = geom.getVertexData() 
            vreader = GeomVertexReader(vdata, 'vertex') 
            cChild = CollisionNode('cGeom-%s-gni%i' % (c.getName(), gni)) 
            
            gni += 1 
            for p in range(geom.getNumPrimitives()): 
                prim = geom.getPrimitive(p) 
                for p2 in range(prim.getNumPrimitives()): 
                    s = prim.getPrimitiveStart(p2) 
                    e = prim.getPrimitiveEnd(p2) 
                    v = [] 
                    for vi in range (s, e): 
                        vreader.setRow(prim.getVertex(vi)) 
                        v.append (xform(vreader.getData3f())) 
                    colPoly = CollisionPolygon(*v) 
                    cChild.addSolid(colPoly) 

            n=parent.attachNewNode (cChild) 
            #n.show()
            
    return parent 
