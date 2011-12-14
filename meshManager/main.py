# A simple demo of the mesh manager.
# Generates and renders a single tile with some ferns and trees
#
# INSTRUCTIONS:
#
# Launch from outside terrain, meaning launch with:
# python terrain/meshManager/main.py

import sys
sys.path.append(".")

from panda3d.core import *

from panda3d.core import Light,AmbientLight,DirectionalLight
from panda3d.core import NodePath
from panda3d.core import Vec3,Vec4,Mat4,VBase4,Point3
from direct.task.Task import Task

from direct.showbase.ShowBase import ShowBase 

from terrain.meshManager import meshManager
from terrain.meshManager import treeFactory
from terrain.meshManager import fernFactory

base = ShowBase() 
base.disableMouse()

class Flat():
    def height(self,x,y): return 0

factories=[treeFactory.TreeFactory(),fernFactory.FernFactory()]
t=meshManager.MeshManager(factories)


tf=treeFactory.TreeFactory()
ff=fernFactory.FernFactory()

factories=[tf,ff]

meshManager=meshManager.MeshManager(factories)

size=600.0

tileFactory=meshManager.tileFactory(size)
x=0.0
y=0.0
tile=Flat()
tileNode=tileFactory(x,y,tile)


tileNode.reparentTo(base.render) 


dlight = DirectionalLight('dlight')

dlnp = render.attachNewNode(dlight)
dlnp.setHpr(0, 0, 0)
render.setLight(dlnp)

alight = AmbientLight('alight')

alnp = render.attachNewNode(alight)
render.setLight(alnp)

#rotating light to show that normals are calculated correctly
def updateLight(task):
    base.camera.setHpr(task.time/50.0*360,0,0)
    
    #base.camera.setP(0)
    base.camera.setPos(size/2,size/2,5)
    #base.camera.setPos(tileNode,2,task.time*4,5)
    base.camera.setP(8)
    
    #t.update(base.camera)
    
    h=task.time/20.0*360+180
    
    dlnp.setHpr(0,h,0)
    h=h+90
    h=h%360
    h=min(h,360-h)
    #h is now angle from straight up
    hv=h/180.0
    hv=1-hv
    sunset=max(0,1.0-abs(hv-.5)*8)
    sunset=min(1,sunset)
    if hv>.5: sunset=1
    #sunset=sunset**.2
    sunset=VBase4(0.8, 0.5, 0.0, 1)*sunset
    sun=max(0,hv-.5)*2*4
    sun=min(sun,1)
    dColor=(VBase4(0.8, 0.7, 0.7, 1)*sun*2+sunset)
    dlight.setColor(dColor)
    aColor=VBase4(0.1, 0.3, 0.8, 1)*sun*2.6+VBase4(0.2, 0.2, 0.3, 1)*2.0
    alight.setColor(aColor*(5-dColor.length())*(1.0/5))
    return Task.cont    

taskMgr.add(updateLight, "rotating Light")

base.run()