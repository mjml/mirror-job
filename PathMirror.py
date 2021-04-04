import FreeCAD as App
import Part
import PathScripts
import Sketcher
import math
from math import *

eps_tol = 1e-7

Gui = App.Gui
Print = App.Console.PrintMessage

def is_registration_sketch(obj):
    if obj.TypeId != "Sketcher::SketchObject":
        return False

    circles = [c for c in obj.Geometry if type(c) == Part.Circle]
    if len(circles) < 2:
        # Raise an exception here if we have a sketch but no circles are found.
        return False

    mirrorlines = [ f.Geometry for f in obj.GeometryFacadeList if ( f.Construction and type(f.Geometry) == Part.LineSegment ) ]
    if len(mirrorlines) != 1:
        # Raise an exception here if we have a sketch but no mirror line is found.
        return False

    return True


def is_job_object(obj):
    if (obj.TypeId != "Path::FeaturePython"):
        return False
    return hasattr(obj, 'Path') and hasattr(obj, 'Model')


def is_model_object(obj):
    return hasattr(obj, 'Objects') and hasattr(obj, 'Attacher') and hasattr('obj', 'PathResource)')


def is_stock_object(obj):
    return hasattr(obj, "StockType")


def elicit_stock_object():
    stocks = [ x for x in Gui.Selection.getSelection() if is_stock_object(x) ]
    if len(stocks) >= 1:
        return stocks[0]
    return None


def elicit_sketch_object():
    sketches = [ x for x in Gui.Selection.getSelection() if is_registration_sketch(x) ]
    if len(sketches) > 0:
        return sketches[0]
    return None


def elicit_jobs():
    return [ x for x in Gui.Selection.getSelection() if is_job_object(x) ]


def find_job_parent(inlist):
    for p in inlist:
        if is_job_object(p):
            return p
    return None


def elicit_first_job():
    jobs = elicit_jobs()
    Print("{0} jobs returned.\n".format(len(jobs)))
    if len(jobs) >= 1:
        return jobs[0]
    return None


def elicit_second_job(first_job):
    jobs = elicit_jobs()
    if len(jobs) > 0:
        j = jobs[len(jobs)-1]
        if j != first_job:
            return j

    return None


def elicit_model():
    models = [ x for x in Gui.Selection.getSelection() if is_model_object(x) ]
    if len(models) > 0:
        m = models[0]


def find_job_from_model(model):
    objs = [x for x in App.ActiveDocument.getObjectsByLabel(model.PathResource)]
    if len(objs) == 0:
        raise Exception("model.PathResource({0}) not contained in document.")
    elif len(objs) != 1:
        raise Exception("model.PathResource({0}) not unique in document.")
    model = objs[0]
    jobs = [ x for x in model.InList if is_job_object(x) ]
    if len(jobs) == 0:
        raise Exception("This model doesn't seem to be contained within a Job")
    elif len(jobs) != 1:
        raise Exception("This model seems to be contained within several Jobs. Too complicated for this script!")
    return jobs[0]


def find_job_from_stock(stock):
    if not is_stock_object(stock):
        raise Exception("Object passed in is not a Stock object.")
    n = len(stock.InList)
    if n == 0:
        raise Exception("This Stock object oddly does not have an associated Job.")
    jobs = [ x for x in stock.InList if is_job_object(x) ]
    return jobs[0]


def compute_mirror_from_stock(stock, flip_x_axis):
    origin = App.Vector()
    linenorm = App.Vector()
    bb = stock.Shape.BoundBox
    if flip_x_axis:
        origin.x = bb.XMin
        origin.y = bb.YLength/2 + bb.YMin
        linenorm = App.Vector(1,0,0)
    else:
        origin.x = bb.XLength/2 + bb.XMin
        origin.y = bb.YMin
        linenorm = App.Vector(0,1,0)
    origin.z = bb.ZLength/2 + bb.ZMin
    return (origin, linenorm )


def compute_mirror_from_sketch(rsketch, placeable):
    # Find circles (which correspond to alignment pins)
    circles = [c for c in rsketch.Geometry if type(c) is Part.Circle]
    if len(circles) != 2:  # Couldn't find the circles within the sketches
        raise Exception("Couldn't find exactly two circles within the Registration sketch")
    # Find lines (which may show the mirror axis)
    linefacs = [f for f in rsketch.GeometryFacadeList if type(f) is Sketcher.GeometryFacade and f.Construction]
    lines = [ f.Geometry for f in linefacs ]
    mirrorline = None

    # Check/warn: one line only in these sketches
    if len(lines) != 1:
        raise Exception("Mirror sketch must contain exactly one construction line to delineate the mirror axis.")

    l = lines[0]
    allmatched = True  # Assume that each circle has a match or is on the flip line until we find otherwise
    linenorm = (l.EndPoint - l.StartPoint).normalize()  # used to project each circle's center
    linenorm = abs(linenorm)
    # For each circle (i)
    for i in circles:
        matched = False
        rel_i = i.Center - l.StartPoint
        ext_i = rel_i - (linenorm.dot(rel_i) * linenorm)  # extension from line
        if ext_i.Length < eps_tol:
            continue
        else:
            # For each circle (j)
            for j in circles:
                rel_j = i.Center - l.StartPoint
                ext_j = rel_j - (linenorm.dot(rel_j) * linenorm)
                if (ext_i - ext_j).Length < eps_tol:
                    matched = True
                    break  # break from j loop, this i-j pair matches

            if not matched:
                allmatched = False
                continue  # break from i loop, continue in l loop, some l-i couldn't be aligned

    if allmatched:
        mirrorline = (l.StartPoint, linenorm)
    else:
        raise Exception("The circles used to indicate alignment pins do not match appropriately across the mirror line.")
        

    if placeable is not None:
        # Use the Model Placement to adjust the flip line
        pl = placeable.Placement
        T = pl.Matrix
        mirrorline = (T * l.StartPoint, T * linenorm)    

    return mirrorline


def check_model(src_job, tgt_job):
    # This is done during target job creation, but this method checks for consistency between the two jobs
    if len(tgt_job.Model.OutList) != len(src_job.Model.OutList):
        raise Exception("Target job seems to have a different number of base objects.")
    for (i, obj) in enumerate(src_job.Model.OutList):
        tgt_job.Model.OutList[i].Label = obj.Label


def copy_stock(src_job, tgt_job):
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


def adjust_mirror_origin(job, origin):
    z = (job.Stock.Shape.BoundBox.ZMax + job.Stock.Shape.BoundBox.ZMin) / 2
    App.Console.PrintMessage("z flip at %s\n" % (z))
    origin.z = z
    return origin


def mirror_job(src_job, tgt_job, origin, norm):

    if origin == None or norm == None:
        raise Exception("Need to have a well-defined flip line in order to create mirrored stock")

    tgt_job.Label = "Reverse{0}".format(src_job.Label)

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

    for (i, obj) in enumerate(tgt_job.Model.OutList):
        obj.Placement.Matrix = Ti * R * T * src_job.Model.OutList[i].Placement.Matrix

    tgt_job.Stock.Placement.Matrix = Ti * R * T * src_job.Stock.Placement.Matrix
    tgt_job.recompute()
