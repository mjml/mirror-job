import FreeCAD
import math

curdoc = FreeCAD.activeDocument()

# Variables

# Gives parallel direction of the flip axis. For planar milling, the Z-coordinate should always be zero.
flip_axis = FreeCAD.Vector(1,0,0).normalize()
ortho_axis = FreeCAD.Vector(0,1,0).normalize()

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

sorted_circles = sorted(cs,key=lambda a: a[0])

bins = []
for c in sorted_circles:
    if len(bins) == 0:
        bins.append([c])
    elif math.isclose(c.proj, bins[-1][0].proj, abs_tol=1e-9):
        bins[-1].append(c)
    else:
        bins.append([c])

i=0
pairs = []
unpaired = 0
midline = math.inf  # the orthogonal axis coordinate of the flip line
while i < math.floor(len(bins)/2):
    a = bins[i]
    b = bins[-1-i]
    for p in a:
        for q in b:
            if (math.isclose(p.proj, q.proj, abs_tol=1e-9)):
                pairs.append((p,q))
                a.remove(p)
                b.remove(q)
                m = (p.off+q.off)/2
                if math.isinf(midline):
                    midline = m
                elif not math.isclose(midline, m, abs_tol=1e-9):
                    FreeCAD.Console.PrintError("Pairs of registration holes do not agree on the midpoint.")

    if a.count == 0:
        bins.remove(a)
    else:
        FreeCAD.Console.PrintError("Found unpaired registration holes: " + str([ x.c.Location for x in a ]))
        unpaired = unpaired+1
    if b.count == 0:
        bins.remove(b)
    else:
        FreeCAD.Console.PrintError("Found unpaired registration holes: " + str([ x.c.Location for x in b ]))
        unpaired = unpaired+1

if len(bins) > 0:
    if len(bins) == 1:
        for p in bins[0]:
            if math.isinf(midline):
                midline = p.off
            elif not math.isclose(midline, p.off):
                FreeCAD.Console.PrintError("Found misaligned registration hole: " + str(p.circle.Location))
            
    else:
        FreeCAD.Console.PrintError("Too many unpaired registration holes, aborting registration.\n")

if math.isinf(midline):
    FreeCAD.Console.PrintError("Couldn't find registration midline.\n")

    

