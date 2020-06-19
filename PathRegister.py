import FreeCAD as App
import Part
import PathScripts
import math
from math import *

eps_tol = 1e-7

def validate_midline (rlabel, flip_x_axis):

    # Gives parallel direction of the flip axis. For planar milling, the Z-coordinate should always be zero.
    flip_axis  = App.Vector(1,0,0)
    ortho_axis = App.Vector(0,1,0)
    if not flip_x_axis:
        flip_axis  = App.Vector(0,1,0)
        ortho_axis = App.Vector(1,0,0)

    # Find the Registration sketch
    objs = App.ActiveDocument.Objects
    reg = [ x for x in objs if x.TypeId == 'Sketcher::SketchObject' and x.Label == rlabel ]
    circles = [ c for c in reg[0].Geometry if type(c) is Part.Circle ]

    # Project each circle onto the flip axis to validate them all and to determine the midpoint
    cs = []
    for c in circles:
        App.Console.PrintMessage("Circle " + str(c) + "\n")
        cs.append(type('',(object,),{ 
                    "proj": c.Location.dot(flip_axis), 
                    "off": c.Location.dot(ortho_axis), 
                    "c": c })())

    sorted_circles = sorted(cs, key=lambda a: a.off)
    
    # Bin the circles according to their projection onto the flip axis
    bins = []
    for c in sorted_circles:
        if len(bins) == 0:
            bins.append([c])
        elif isclose(c.off, bins[-1][0].off, abs_tol=eps_tol):
            bins[-1].append(c)
        else:
            bins.append([c])

    # Pair the circles in each bin by their orthogonal projection ("off")
    midline = inf  # the orthogonal axis coordinate of the flip line
    App.Console.PrintMessage("There are " + str(len(bins)) + " bins\n")
    for b in bins:
        sorted_circles = sorted(b, key=lambda x: x.off)
        i=0
        while i < floor(len(b)/2):
            c1 = b[i]
            c2 = b[-1-i]
            m = (c1.off + c2.off)/2
            if isinf(midline):
                midline = m
            elif not isclose(midline, m, abs_tol=eps_tol):
                raise Exception("Registration pin pair mismatches another pair on proposed flip line at dot(v,ortho_axis) == " + str(midline) + " ≠ " + str(m) + "\n")
            i=i+1
        if i == floor(len(b)/2) + 1:
            if isinf(midline):
                midline = b[i].off
            elif isclose(midline, b[i].off, abs_tol=eps_tol):
                raise Exception("Middle registration pin at " + str(b[i].c) + " doesn't coincide with proposed midline\n")

    # Intercept of midline along orthogonal axis
    return midline, ortho_axis

        
def copy_model (src_job, tgt_job):
    tgt_job.Placement.Matrix = App.Matrix(src_job.Placement.Matrix)


def copy_stock (src_job, tgt_job):
    bb = src_job.Stock.Shape.BoundBox
    if src_job.Stock.StockType == 'CreateBox':
        tst = PathScripts.PathStock.CreateBox(tgt_job, 
                extent=App.Vector(bb.XLength, bb.YLength, bb.ZLength), 
                placement=App.Placement(src_job.Placement))
    elif src_job.Stock.StockType == 'FromBase':
        sst = src_job.Stock
        tst = PathScripts.PathStock.CreateFromBase(tgt_job,
                neg=App.Vector(sst.ExtXNeg, sst.ExtYNeg, sst.ExtZNeg),
                pos=App.Vector(sst.ExtXPos, sst.ExtYPos, sst.ExtZPos),
                placement=App.Placement(src_job.Placement))
    else:
        raise Exception("Two-sided registration can only work with Box and Base (boundbox) Stock types for now.\n")
    
    oldlbl = tgt_job.Stock.Label
    tgt_job.Stock = tst
    App.ActiveDocument.removeObject(oldlbl)
    #tgt_job.Stock.Label = oldlbl


def rotate_job (src_job, tgt_job, flip_x_axis, midline):
    if midline == math.inf:
        raise Exception("Can't rotate job without midline!")
    R = App.Matrix()
    R.unity()
    T = App.Matrix()
    T.unity()
    if math.fabs(tgt_job.Stock.Shape.BoundBox.ZMin) < eps_tol:
        App.Console.PrintError("Warning: stock object for two-sided job is not sitting on Z=0\n")
    bb = tgt_job.Stock.Shape.BoundBox
    if flip_x_axis:
        #T.A24 = -(bb.YMax - bb.YMin)/2
        if midline != (bb.YMax - bb.YMin)/2:
            App.Console.PrintError("Warning: midline does not pass through the center of the stock along the flip axis (X)\n")
        T.A24 = -midline
        T.A34 = -(bb.ZMax - bb.ZMin)/2
        R.rotateX(math.pi)
    else:
        #T.A14 = -(bb.XMax - bb.XMin)/2
        if midline != (bb.XMax - bb.XMin)/2:
            App.Console.PrintError("Warning: midline does not pass through the center of the stock along the flip axis (Y)\n")
        T.A24 = -midline
        T.A34 = -(bb.ZMax - bb.ZMin)/2
        R.rotateY(math.pi)

    App.Console.PrintMessage(str(T) + "\n")
    Ti = T.inverse()
    # Quintic but usually these lists have a single element
    for a in tgt_job.Model.OutList:
        for b in src_job.Model.OutList:
            p = a.Objects[0]
            q = b.Objects[0]
            if p.ID == q.ID:
                a.Placement.Matrix = Ti * R * T * b.Placement.Matrix

    tgt_job.Stock.Placement.Matrix = Ti * R * T
    
    
