from pandac.PandaModules import *

loadPrcFile("TerrainConfig.prc")

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
import direct.directbase.DirectStart

from bakery import *
from renderer import *
from direct.filter.CommonFilters import CommonFilters
import math

from direct.task import Task
from pandac.PandaModules import PandaSystem
print PandaSystem.getVersionString()
backBinName="background"

"""

This is a test of the terrain system.


"""

# Create a bakery that uses the "bakery2" folder for its resources
b=LiveBakery(None,"bakery2")

n=RenderNode('render')
n.reparentTo(render)
i=[0]

def cameraTask(task):
    t=b.bakeTile(0,0,1)
    n.addTile(t)
    #n.removeTile(n.addTile(t))
    i[0]+=1
    print i

    return Task.cont

taskMgr.add(cameraTask, "cameraTask")

print "z"
run()