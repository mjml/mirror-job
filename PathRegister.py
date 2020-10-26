import FreeCAD as App
import Part
import PathScripts
import math
from math import *

eps_tol = 1e-7

def determine_flipline (rsketch, flip_x_axis):

    # Gives parallel direction of the flip axis. For planar milling, the Z-coordinate should always be zero.
    flip_axis  = App.Vector(1,0,0)
    ortho_axis = App.Vector(0,1,0)
    if not flip_x_axis:
        flip_axis  = App.Vector(0,1,0)
        ortho_axis = App.Vector(1,0,0)

    # Find circles (which correspond to alignment pins)
    circles = [ c for c in rsketch.Geometry if type(c) is Part.Circle ]
    if len(circles) != 2: # Couldn't find the circles within the sketches
        raise Exception("Couldn't find exactly two circles within the Registration sketch")

    lines = [ l for l in rsketch.Geometry if type(l) is Part.LineSegment and l.Construction ]
    flipline = None

    # For each construction line, try to project / match all circles
    for l in lines:
        allmatched = True # Assume that each circle has a match or is on the flip line until we find otherwise
        linenorm = (l.EndPoint - l.StartPoint).normalize() # used to project each circle's center
        # For each circle (i)
        for i in circles:
            matched = False
            rel_i = i.Center - l.StartPoint
            ext_i = rel_i - (linenorm.dot(rel_i) * linenorm) # extension from line
            if ext_i.Length < eps_tol:
                continue;
            else:
                # For each circle (j)
                for j in circles:
                    rel_j = i.Center - l.StartPoint
                    ext_j = rel_j - (linenorm.dot(rel_j) * linenorm)
                    if (ext_i - ext_j).Length < eps_tol:
                        matched = True
                        break # break from j loop, this i-j pair matches

                if not matched:
                    allmatched = False
                    continue # break from i loop, continue in l loop, some l-i couldn't be aligned
        
        if allmatched:
            flipline = ( l.StartPoint, linenorm )
            break # if each circle had a match or was on the flip line, great! this line is our flip line.

    return flipline


def copy_model (src_job, tgt_job):
    if len(tgt_job.Model.OutList) != len(src_job.Model.OutList):
        raise Exception("Target job seems to have a different number of base objects.")
    for (i,obj) in enumerate(src_job.Model.OutList):
        tgt_job.Model.OutList[i].Label = obj.Label


def copy_stock (src_job, tgt_job):
    bb = src_job.Stock.Shape.BoundBox
    if src_job.Stock.StockType == 'CreateBox':
        tst = PathScripts.PathStock.CreateBox(tgt_job, 
                extent=App.Vector(bb.XLength, bb.YLength, bb.ZLength), 
                placement=App.Placement(src_job.Placement))
    elif src_job.Stock.StockType == 'FromBase':
        sst = src_job.Stock
        tst = PathScripts.PathStock.CreateFromBase(tgt_job,
                neg=App.Vector(sst.ExtXneg, sst.ExtYneg, sst.ExtZneg),
                pos=App.Vector(sst.ExtXpos, sst.ExtYpos, sst.ExtZpos),
                placement=App.Placement(src_job.Placement))
    else:
        raise Exception("Two-sided registration can only work with Box and Base (boundbox) Stock types for now.\n")
    
    oldlbl = tgt_job.Stock.Label
    tgt_job.Stock = tst
    App.ActiveDocument.removeObject(oldlbl)


def adjust_flip_origin(job, origin):
    z = (job.Stock.Shape.BoundBox.ZMax + job.Stock.Shape.BoundBox.ZMin) / 2
    App.Console.PrintMessage("z flip at %s\n" % (z))
    origin.z = z
    return origin


def flip_job (src_job, tgt_job, origin, norm):

    if origin == None or norm == None:
        raise Exception("Need to have a well-defined flip line in order to create mirrored stock")

    R = App.Matrix() 
    R.unity()
    T = App.Matrix()
    T.unity()

    # Flip along norm 
    T.A14 = -origin.x
    T.A24 = -origin.y
    T.A34 = -origin.z

    R.A11 = 2 * norm.x * norm.x - 1
    R.A12 = 2 * norm.x * norm.y 
    R.A13 = 2 * norm.x * norm.z

    R.A21 = 2 * norm.x * norm.y
    R.A22 = 2 * norm.y * norm.y - 1
    R.A23 = 2 * norm.y * norm.z

    R.A31 = 2 * norm.z * norm.x
    R.A32 = 2 * norm.z * norm.y
    R.A33 = 2 * norm.z * norm.z - 1

    Ti = T.inverse()

    for (i,obj) in enumerate(tgt_job.Model.OutList):
        obj.Placement.Matrix =  Ti * R * T * src_job.Model.OutList[i].Placement.Matrix

    tgt_job.Stock.Placement.Matrix = Ti * R * T * src_job.Stock.Placement.Matrix
    tgt_job.recompute()
    
    
