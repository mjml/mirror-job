import FreeCAD
from math import *

def validate_midline (flip_axis):
    # Variables

    # Gives parallel direction of the flip axis. For planar milling, the Z-coordinate should always be zero.
    #flip_axis = FreeCAD.Vector(1,0,0).normalize()
    flip_axis.normalize()
    R = FreeCAD.Matrix()
    R.rotateZ(pi/2)
    ortho_axis = (R * flip_axis).normalize()

    # Find the Registration sketch
    objs = FreeCAD.ActiveDocument.Objects
    reg = [ x for x in objs if x.TypeId == 'Sketcher::SketchObject' and x.Label == 'Registration1' ]
    circles = [ c for c in reg if type(c) is Part.Circle ]

    # Project each circle onto the flip axis to validate them all and to determine the midpoint
    cs = []
    for c in circles:
        cs.append(type('',(object,),{ "proj": c.Location.dot(flip_axis), 
                    "off": c.Location.dot(ortho_axis), 
                    "c": c })())

    sorted_circles = sorted(cs, key=lambda a: a[0])
    FreeCAD.Console.Print("Found " + len(sorted_circles) + " circles")

    # Bin the circles according to their projection onto the flip axis
    bins = []
    for c in sorted_circles:
        if len(bins) == 0:
            bins.append([c])
        elif isclose(c.proj, bins[-1][0].proj, abs_tol=1e-9):
            bins[-1].append(c)
        else:
            bins.append([c])

    FreeCAD.Console.Print("Found " + len(bins) + " bins")

    # Pair the circles in each bin by their offset
    midline = inf  # the orthogonal axis coordinate of the flip line
    for b in bins:
        sorted_circles = sorted(b, key=lambda x: x.off)
        i=0
        while i < floor(len(b)/2):
            c1 = b[i]
            c2 = b[-1-i]
            m = (c1.off + c2.off)/2
            if isinf(midline):
                midline = m
            elif not isclose(midline, m, abs_tol=1e-9):
                FreeCAD.Console.PrintError("Registration pin pair mismatches another pair on proposed flip line at dot(v,ortho_axis) == " + midline + " ≠ " + m)
            i=i+1
        if i == floor(len(b)/2) + 1:
            if isinf(midline):
                midline = b[i].off
            elif isclose(midline, b[i].off, abs_tol=1e-9):
                FreeCAD.Console.PrintError("Middle registration pin at " + str(b[i].c) + " doesn't coincide with proposed midline")

    if isinf(midline):
        FreeCAD.Console.PrintError("Couldn't find registration midline.\n")

    # Intercept of midline along orthogonal axis
    return midline

        

