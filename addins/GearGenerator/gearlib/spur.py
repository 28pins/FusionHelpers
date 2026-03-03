"""Spur (external) gear solid builder for Fusion 360."""

import adsk.core
import adsk.fusion

from . import utils


def create_spur(comp, params):
    """
    Create an external spur gear solid inside *comp*.

    Required params keys
    --------------------
    module_mm        : float – gear module in mm
    num_teeth        : int
    face_width_mm    : float

    Optional params keys
    --------------------
    pressure_angle_deg : float (default 20.0)
    backlash_mm        : float (default 0.0)
    tip_relief_mm      : float (default 0.0)
    bore_dia_mm        : float (default 0.0 → no bore)

    Returns
    -------
    The created adsk.fusion.BRepBody.
    """
    m    = float(params["module_mm"])
    z    = int(params["num_teeth"])
    fw   = float(params["face_width_mm"])
    bore = float(params.get("bore_dia_mm", 0.0))
    alpha = float(params.get("pressure_angle_deg", 20.0))
    bl   = float(params.get("backlash_mm", 0.0))
    tr   = float(params.get("tip_relief_mm", 0.0))

    # ── 1. Build profile sketch ─────────────────────────────────────────────
    sk = comp.sketches.add(comp.xYConstructionPlane)
    pts_mm = utils.spur_profile_pts(m, z, alpha, bl, tr)
    oc = utils.pts_to_object_collection(pts_mm)
    spline = sk.sketchCurves.sketchFittedSplines.add(oc)
    spline.isClosed = True

    prof = utils.largest_profile(sk)
    if prof is None:
        raise RuntimeError("Spur: no valid profile found – check parameters.")

    # ── 2. Extrude ──────────────────────────────────────────────────────────
    dist = adsk.core.ValueInput.createByReal(utils.mm_to_cm(fw))
    ext_in = comp.features.extrudeFeatures.createInput(
        prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_in.setDistanceExtent(False, dist)
    body = comp.features.extrudeFeatures.add(ext_in).bodies.item(0)

    # ── 3. Bore ─────────────────────────────────────────────────────────────
    utils.add_bore(comp, bore, fw)

    return body
