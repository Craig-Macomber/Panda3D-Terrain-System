class ToroidalCache(object):
    def __init__(self,size,startX=0,startY=0,hysteresis=1.0):
        self.size=size
        self.originX=startX
        self.originY=startY
        self.hysteresis=hysteresis
        self.data=[self.replaceValue(x+startX,y+startY,None) for x in xrange(size) for y in xrange(size)]
    
    def replaceValue(self,x,y,old):
        return None
    
    def updateCenter(self,x,y):
        """
        x and y can be floats or ints. If the passed x,y is further than hysteresis from
        center in either x or y, then move origin
        """
        offset=(self.size-1)/2.0
        
        xError=x-(offset+self.originX)
        if abs(xError)>self.hysteresis:
            change=round(xError)
            step=1 if change>0 else -1
            while change!=0:
                for yindex in xrange(self.originY,self.originY+self.size):
                    if step==1:
                        old=self.get(self.originX,yindex)
                        new=self.replaceValue(self.originX+self.size,yindex,old)
                        self.store(self.originX,yindex,new)
                    else:
                        old=self.get(self.originX-1,yindex)
                        new=self.replaceValue(self.originX-1,yindex,old)
                        self.store(self.originX-1,yindex,new)
                change-=step
                self.originX+=step

        yError=y-(offset+self.originY)
        if abs(yError)>self.hysteresis:
            change=round(yError)
            step=1 if change>0 else -1
            while change!=0:
                for xindex in xrange(self.originX,self.originX+self.size):
                    if step==1:
                        old=self.get(xindex,self.originY)
                        new=self.replaceValue(xindex,self.originY+self.size,old)
                        self.store(xindex,self.originY,new)
                    else:
                        old=self.get(xindex,self.originY-1)
                        new=self.replaceValue(xindex,self.originY-1,old)
                        self.store(xindex,self.originY-1,new)
                change-=step
                self.originY+=step
        
    def inbounds(self,x,y):
        """
        x and y are ints in the same coordnit system as update center and the origin
        """
        return (0<=(x-self.originX)<size) and (0<=(y-self.originY)<size)
        
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
        self.data[self._cellIndex(x,y)]=data

class Verbos(ToroidalCache):
    
    def replaceValue(self,x,y,old):
        new=(x,y)
        print old,new
        return new
        
    def __str__(self):
        s=""
        for y in range(self.originY,self.originY+self.size):
            for x in range(self.originX,self.originX+self.size):
                s+=str(self.get(x,y))
            s+='\n'
        return s