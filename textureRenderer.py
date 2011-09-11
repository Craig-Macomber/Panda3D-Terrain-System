from panda3d.core import Texture
from panda3d.core import GraphicsOutput
from direct.task.Task import Task
from panda3d.core import FrameBufferProperties

import collections
"""

This is intended to serve is a queueing system for one shot rendering to textures.

"""

def dispose(nodePath):
    def kill(n):
        for p in n.getChildren():
            kill(p)
        n.removeNode()
    kill(nodePath.getTop())

class QueueItem:
    def __init__(self, width, height, callback, getCam, callbackParams=(), getCamParams=(), cleanUpCamCall=dispose,toRam=False, texture=None):
        self.cleanUpCamCall=cleanUpCamCall
        self.width=width
        self.height=height
        self.callbackProp=callback
        self.getCamMethod=getCam
        self.getCamParams=getCamParams
        self.toRam=toRam
        self.callbackParams=callbackParams
        self.texture=texture if texture is not None else Texture()
    def callback(self,tex):
        self.callbackProp(tex,*self.callbackParams)
    def getCam(self):
        return self.getCamMethod(*self.getCamParams)
    
    
class SimpleQueueItem(QueueItem):
    """
    
    cam is passed to __init__ instead of getCam, thus, scene must be pregenerated, rather than assemblerd when needed.
    Use QueueItem instead to dynamically build the scene at the last possible moment with getCam to save space/memory or
    to spread scene assembly time out using queue.
    
    """
    def __init__(self, width, height, callback, cam, toRam=False, texture=None):
        self.cam=cam
        QueueItem.__init__(self, width, height, callback,getCam=None, toRam=toRam, texture=texture)
    def getCam(self):
        return self.cam

class Queue:
    def __init__(self):
        self.buffs={}
        self.queue=collections.deque()
        self.currentItem=None
        self.displayRegions={}
        self.currentBuff=None
        self.renderFrame=0
        
        taskMgr.add(self.processQueue,"processRenderTexQueue")
    
    def flush(self):
        """
        force the processing of all current items in a blocking manner
        """
        allBuffers=base.graphicsEngine.getWindows()
        toActivate=[]
        for b in allBuffers:
            if b.isActive() and b is not self.currentBuff:
                b.setActive(False)
                toActivate.append(b)
                
        while self.queue or self.currentItem:
            base.graphicsEngine.renderFrame()
            self.processQueue()
        
        for b in toActivate:
            b.setActive(True)
    
    def processQueue(self,task=None):
        self.renderFrame+=1
        
        if self.currentItem is None:
            if len(self.queue) > 0:
                # Process a queue item!
                self.currentItem=self.queue.popleft()
                self.renderFrame=0

                self.currentBuff=self.getBuff(self.currentItem.width,self.currentItem.height)
                self.currentBuff.setActive(True)
                    
                # maybe should use RTMCopyTexture?
                mode=GraphicsOutput.RTMCopyRam if self.currentItem.toRam else GraphicsOutput.RTMBindOrCopy
                self.currentBuff.addRenderTexture(self.currentItem.texture,mode)
                
                self.cam=self.currentItem.getCam()

                self.displayRegions[self.currentBuff].setCamera(self.cam)
                self.displayRegions[self.currentBuff].setActive(True)

        elif self.renderFrame>0:
            # Should be rendered by now. Could potentially add extra wait here.
            tex = self.currentBuff.getTexture()
            #print tex.getFormat()
            self.currentBuff.setActive(False)
            self.displayRegions[self.currentBuff].setActive(False)
            self.currentBuff.clearRenderTextures()
            self.currentItem.callback(tex)
            
            self.currentItem.cleanUpCamCall(self.cam)
            del self.cam
            self.currentItem=None
                
        
        return Task.cont
        
    def removeBuffers(self):
        for s in self.buffs:
            base.graphicsEngine.removeWindow(self.buffs[s])
        self.buffs={}
    
    def getBuff(self,width,height):
        size=(width,height)
        
        if size in self.buffs:
            buff=self.buffs[size]
        else:
            mainWindow=base.win
            fbp=FrameBufferProperties(mainWindow.getFbProperties())
            #print fbp.getColorBits()
            fbp.setColorBits(24*2)
            fbp.setDepthBits(0)
            fbp.setAlphaBits(0)
            buff=mainWindow.makeTextureBuffer('QueueBuff'+str(size),width,height,Texture(),True)
            dr=buff.makeDisplayRegion(0, 1, 0, 1)
            self.buffs[size]=buff
            self.displayRegions[buff]=dr
            print "saved buffer "+str(size)
            
        return buff