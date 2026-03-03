"""Rack gear solid builder for Fusion 360."""

import math
import adsk.core
import adsk.fusion

from . import utils


def create_rack(comp, params):
    """
    Create a rack solid inside *comp*.

    params keys
    -----------
    module_mm        : float
    num_teeth        : int   – number of rack teeth
    face_width_mm    : float – rack width (Z direction)
    pressure_angle_deg : float (default 20.0)
    backlash_mm      : float (default 0.0)
    tip_relief_mm    : float (default 0.0)
    bore_dia_mm      : float (ignored for rack)

    Returns the created BRepBody.
    """
    m     = float(params["module_mm"])
    nt    = int(params["num_teeth"])
    fw    = float(params["face_width_mm"])
    alpha = float(params.get("pressure_angle_deg", 20.0))
    bl    = float(params.get("backlash_mm", 0.0))
    tr    = float(params.get("tip_relief_mm", 0.0))

    p     = math.pi * m            # circular pitch
    ht    = m                      # addendum
    hd    = 1.25 * m               # dedendum
    total_len = nt * p

    # ── 1. Build rack cross-section profile ─────────────────────────────────
    #   XY plane: X = along rack length, Y = tooth height direction.
    #   Pitch line at Y = 0.
    sk = comp.sketches.add(comp.xYConstructionPlane)
    lines = sk.sketchCurves.sketchLines

    # Rack boundary: rectangle from (-total_len/2, -hd) to (+total_len/2, +ht)
    # with tooth cut-outs along the top.
    # Strategy: draw bottom rectangle, then add tooth profiles on top.

    # Collect all top-profile X,Y points (the toothed edge)
    top_pts = []
    tooth_one = utils.rack_tooth_pts(m, alpha, bl, tr)
    # tooth_one spans one full pitch centred at x=0
    # tile it across nt teeth
    for i in range(nt):
        cx = -total_len / 2.0 + (i + 0.5) * p
        for (tx, ty) in tooth_one:
            top_pts.append((cx + tx, ty))

    # Build closed profile: bottom line → right side → toothed top → left side
    # Points: bottom-left, bottom-right, right-side-up, toothed-top (reversed),
    #         left-side-down.

    # Bottom-left corner
    x0 = -total_len / 2.0
    x1 =  total_len / 2.0
    y_bot = -hd

    corners = [
        (x0, y_bot),
        (x1, y_bot),
    ]
    # Traverse top_pts left to right then close
    profile_pts = corners + top_pts[::-1]   # reversed so we go right→left on top
    # Actually we need CCW: bottom-left → bottom-right → top-right → toothed-top-left-to-right is CW
    # Let's go: bottom-left (x0,y_bot) → bottom-right (x1,y_bot) → up along right side →
    #            toothed edge from right to left → down left side → back to start
    # This is CW, so reverse for CCW:

    profile_pts_ccw = []
    # Top-edge (toothed), left to right:
    profile_pts_ccw.extend(top_pts)
    # Right side down:
    profile_pts_ccw.append((x1, y_bot))
    # Bottom right to left:
    profile_pts_ccw.append((x0, y_bot))
    # Left side up is implicit (closed by the spline)

    oc = adsk.core.ObjectCollection.create()
    for (x, y) in profile_pts_ccw:
        oc.add(adsk.core.Point3D.create(utils.mm_to_cm(x), utils.mm_to_cm(y), 0.0))

    spline = sk.sketchCurves.sketchFittedSplines.add(oc)
    spline.isClosed = True

    prof = utils.largest_profile(sk)
    if prof is None:
        raise RuntimeError("Rack: no valid cross-section profile found.")

    # ── 2. Extrude in Z (face width) ────────────────────────────────────────
    dist   = adsk.core.ValueInput.createByReal(utils.mm_to_cm(fw))
    ext_in = comp.features.extrudeFeatures.createInput(
        prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_in.setDistanceExtent(False, dist)
    body   = comp.features.extrudeFeatures.add(ext_in).bodies.item(0)

    return body
