"""Internal (ring) gear solid builder for Fusion 360."""

import adsk.core
import adsk.fusion

from . import utils


def create_internal(comp, params):
    """
    Create an internal (ring) gear solid inside *comp*.

    The ring gear has inward-pointing involute teeth.

    Extra params keys
    -----------------
    ring_wall_mm : float (default 3·m)  – radial ring-wall thickness beyond root

    Returns the created BRepBody.
    """
    m     = float(params["module_mm"])
    z     = int(params["num_teeth"])
    fw    = float(params["face_width_mm"])
    alpha = float(params.get("pressure_angle_deg", 20.0))
    bl    = float(params.get("backlash_mm", 0.0))
    tr    = float(params.get("tip_relief_mm", 0.0))
    wall  = float(params.get("ring_wall_mm", 3.0 * m))

    rp      = m * z / 2.0
    r_root  = rp + 1.25 * m        # ring-gear root (outer side of teeth)
    r_outer = r_root + wall         # ring outer wall

    # ── 1. Outer circle ─────────────────────────────────────────────────────
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 0),
        utils.mm_to_cm(r_outer)
    )

    # ── 2. Inner gear profile (inward teeth) ────────────────────────────────
    pts_mm = utils.internal_profile_pts(m, z, alpha, bl, tr)
    oc     = utils.pts_to_object_collection(pts_mm)
    spline = sk.sketchCurves.sketchFittedSplines.add(oc)
    spline.isClosed = True

    # The annular region is the profile BETWEEN the outer circle and the
    # inner gear profile.  Fusion detects this as one of the profiles.
    # Pick by largest area excluding the full-disk region.
    best_prof = None
    best_area = -1.0
    full_disk_area = 3.14159 * (r_outer / 10.0) ** 2   # approx cm²
    for i in range(sk.profiles.count):
        p = sk.profiles.item(i)
        try:
            a = p.areaProperties().area
        except Exception:
            continue
        if a > best_area and a < full_disk_area * 0.99:
            best_area = a
            best_prof = p

    if best_prof is None:
        raise RuntimeError("Internal gear: could not identify annular profile.")

    # ── 3. Extrude ──────────────────────────────────────────────────────────
    dist   = adsk.core.ValueInput.createByReal(utils.mm_to_cm(fw))
    ext_in = comp.features.extrudeFeatures.createInput(
        best_prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_in.setDistanceExtent(False, dist)
    body   = comp.features.extrudeFeatures.add(ext_in).bodies.item(0)

    return body
