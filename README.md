``Two-sided CAM Job helper for FreeCAD``
========================================

To use, just load PathRegister.py and bind a toolbar button to the macro PathRegister.FCMacro.


``Instructions``

Create a part that would need milling on two sides.

Create a job for this part and provide all the required operations for milling the first side.

Now create a Sketch at the document level. This sketch must contain, at minimum:
  - A construction (blue) line indicating the position of the line that you will flip your stock over on
	- A set of circles. Each circle will either a) be exactly on the flip line or b) have some other matching circle that is mirrored with itself along the flip line

The mirror constraint is obviously very helpful for creating pairs of circles that mirror each other on the flip line.

The circles are intended to be the positions of registration pins or alignment screws. For example, I use an M3 screw for this purpose and so I set the diameters to be 3.0mm each.

When the stock is flipped to mill the backward side, any holes lying on the flip line will obviously be filled with the same pin but from the opposite side.

Any holes lying off of the flip line will be pinned by the pin from its "mirror" hole on the opposite side of the flip line.
 