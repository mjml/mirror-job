Two-sided CAM Job helper for FreeCAD
====================================

This little script helps you create two-sided milling jobs for FreeCAD.

You create the front side milling job as you would normally.
This script then helps you configure the reverse side job so that 
  milling operations of the reverse side line up 
  perfectly with the first to create your part.

Installation
------------

Clone this repo to a directory and ensure that this directory is part of your FreeCAD Python Path.

Example:
``$ git clone https://github.com/mjml/mirror-job 
$ FreeCAD -P mirror-job``

It's really just two files. `PathMirror.py` and `PathMirror.FCMacro`.

Copy or symlink `PathMirror.FCMacro` to your user scripts directory (.FreeCAD on Linux)

The macro will work as long as `PathMirror.py` is in your FreeCAD path. Otherwise, it will complain that it can't 'import PathMirror'.

Setup
-----

Go to Customize -> Macros and create a macro.

Choose PathMirror, then give it the name "Mirror Job". If you want a description, "Create or Update Reverse Side Job".
You should give it an icon also, I use the double-pins icon to symbolize alignment pins.

Now go to Customize -> Toolbars and on the right side, choose the Path workbench and
  create a subtoolbar with a name like "Mirroring".
On the left side where you see the available buttons, choose "Macros" from the drop-down list.
You should see the Mirror Job macro that you just created. Use the right arrow to place it inside the Mirroring subtoolbar.

Now when you enter the Path workbench, your Mirroring subtoolbar should appear with its one Mirror Job button in the toolbar.


Usage 
-----

There are two different methods for aligning your reverse-side job that depend on your fixture.

Briefly, the first method uses a CNC vise and only requires you to flip the stock over in the same direction as the vise screw.
The second method uses at least two alignment pins. These pins are equidistant from a "flip line" that travels through your stock.

Method 1: Just flip the stock against a fixed vise jaw and Y-axis locator.
--------------------------------------------------------------------------

Instead of pins, this method relies on your ability to register the stock up against a vise or L-bracket so that the lower left
  corner of the stock is in the same exact place for both the first side and the reverse side.

This method is faster since you do not need to mill or drill alignment holes in wasteboard or anywhere else,
  but its drawback is that it requires you to measure the width of your stock rather precisely.
If you get the stock width measurement wrong, your top and bottom jobs will not be aligned, resulting in a poorly machined part.
Similarly, if you stock is not flat against the fixed jaw of the vise or if it is out of square, you will see deviations where the
  top and bottom jobs do not align perfectly.

For wood, the standard methods that you use to square off stock are usually sufficient for obtaining roughly 0.5-millimeter accuracy and
  agreement between your top and bottom jobs.

If you need better accuracy than this, you should instead use the alignment pin method described below.


Method 2: Flip the stock along an axis that you define, secured in place using alignment pins.
----------------------------------------------------------------------------------------------

For this method, this script requires you to make a small sketch at either Document or PartBody level that identifies where in the XY plane
  the alignment pins (circles) are and where the flip line is.
These circles do not have to be of the same size, although they should all match some counterpart on the other side of the flip line.
Circles that lie "on" the flip line are matched to themselves since the same pin will fit into the same hole from either side.

This sketch will be in the XY plane and does not necessarily need an attachment.
The circles should be standard non-construction white circles and the flip line should be a blue construction line.

The circles are meant to indicate the full diameter of the pin hole, not indicators of the milling path.
To be clear, when you pocket or helix-mill these holes, you'll be configuring the job as a standard pocket so that the
path is offset toward the center of the hole by half the tool width.



Guidelines
----------

- It is possible to get very good alignments with just two pins, either on the flip line or off it.

- If you use physical fixtures like a guard rail or bench dogs to align your stock to some coordinate frame,
  your flip line musn't be too close to these fixture elements.
"Too close" would be a flip line that lies between an edge of the stock making contact with your fixture and the parallel midline of that stock.
![Flip Lines Example](https://github.com/mjml/path-register/blob/master/doc/fliplines.png)
Otherwise when you flip the stock along that line, the opposite side will not be able to clear your fixture.
Be aware of how your stock will align with your other fixture elements when designing your flip line.

- Don't forget to create a separate Job for milling of the alignment pin holes from the first side.
This must be performed manually since the blind hole depths must be deep enough to provide purchase for clamping,
  but not so deep that they go through the wasteboard into the gantry.



Enjoy!

mike@michaeljoya.com (mjml@github)
