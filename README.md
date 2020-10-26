Two-sided CAM Job helper for FreeCAD
====================================

To use, just load PathRegister.py and bind a toolbar button to the macro PathRegister.FCMacro.


CAD Instructions
----------------

1. Create a part that would need planar milling on both of two sides.


2. Create a job for this part and provide all the required operations for milling the first side.


3. Create a Sketch at the document level. We'll call this the "Alignment Pin" sketch. This sketch must contain, at minimum:
  - A construction (blue) line indicating the position of the line that you will flip your stock over on.
	
	- A set of circles. Each circle will either a) be exactly on the flip line or b) have some other matching circle that is mirrored with itself along the flip line

The mirror constraint is obviously very helpful for creating pairs of circles that mirror each other on the flip line.

The circles are intended to be the positions of alignment pins or screws.
For example, I use M3 set screws for this purpose and so I set the diameters to be 3.0mm each.

When the stock is flipped to mill the backward side, any holes lying on the flip-line will obviously be filled with the same pin but from the opposite side.
Any holes lying off of the flip-line will be filled by the pin from its "mirror" hole on the opposite side of the flip line.


4. Click the toolbar button that you bound to PathRegister.FCMacro.

A second job will be created. You'll notice that its Stock object is a flipped version of the first Job's,
  where the flip line was the line you defined in the Alignment Pin sketch.
Its Model object will contain copies of whatever Models were in the first Job, but they will be flipped over just like the stock object,
  so you can create Operations for them.
You'll have to play with the visibility a bit since these objects will overlap each other on the screen and be messy and confusing otherwise.


5. Make a third job for alignment pin holes in your wasteboard.

If you don't already have this, you can use the Alignment Pin Sketch to produce a drilling job that will put some blind holes into your wasteboard to hold the alignment screws or pins.



CAM Guidelines
----------------

- If you use a guard rail or bench dogs to align your stock to some coordinate frame, your flip line musn't be too close to these fixture elements.
"Too close" would be a flip line that lies between an edge of the stock making contact with your fixture and the parallel midline of that stock.

![Flip Lines Example](https://github.com/mjml/path-register/doc/fliplines.png)

Otherwise when you flip the stock along that line, the opposite side will not be able to clear your fixture.
Be aware of how your stock will align with your other fixture elements when designing your flip line.

- It is possible to get very good alignments with just two pins, either on the flip line or off it.

