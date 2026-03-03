"""Helical (external) gear solid builder – stacked-slice loft approach."""

import math
import adsk.core
import adsk.fusion

from . import utils


def create_helical(comp, params):
    """
    Create a helical gear solid inside *comp* using a multi-section loft.

    Extra params keys (beyond the spur keys)
    ------------------------------------------
    helix_angle_deg : float (default 15.0)  – lead helix angle
    n_slices        : int   (default 8)     – loft cross-sections

    Returns the created BRepBody.
    """
    m     = float(params["module_mm"])
    z     = int(params["num_teeth"])
    fw    = float(params["face_width_mm"])
    bore  = float(params.get("bore_dia_mm", 0.0))
    alpha = float(params.get("pressure_angle_deg", 20.0))
    bl    = float(params.get("backlash_mm", 0.0))
    tr    = float(params.get("tip_relief_mm", 0.0))
    helix = float(params.get("helix_angle_deg", 15.0))
    n_sl  = int(params.get("n_slices", 8))

    # Total twist over the face width
    # tan(helix_angle) = lead / (π · d)  →  twist_rad = face_width · tan(helix) / (m·z/2)
    rp = m * z / 2.0
    total_twist = fw * math.tan(math.radians(helix)) / rp   # radians

    planes  = comp.constructionPlanes
    section_profiles = []

    for i in range(n_sl + 1):
        height_mm = fw * i / n_sl
        twist     = total_twist * i / n_sl

        # Offset construction plane
        plane_in = planes.createInput()
        plane_in.setByOffset(
            comp.xYConstructionPlane,
            adsk.core.ValueInput.createByReal(utils.mm_to_cm(height_mm))
        )
        plane = planes.add(plane_in)

        # Profile sketch on that plane
        sk = comp.sketches.add(plane)
        pts_mm = utils.spur_profile_pts(m, z, alpha, bl, tr)
        pts_rotated = [utils._rot(x, y, twist) for (x, y) in pts_mm]
        oc = utils.pts_to_object_collection(pts_rotated)
        spline = sk.sketchCurves.sketchFittedSplines.add(oc)
        spline.isClosed = True

        prof = utils.largest_profile(sk)
        if prof is None:
            raise RuntimeError(
                f"Helical: no valid profile at slice {i} – check parameters.")
        section_profiles.append(prof)

    # Loft through all sections
    loft_in = comp.features.loftFeatures.createInput(
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    for prof in section_profiles:
        loft_in.loftSections.add(prof)
    body = comp.features.loftFeatures.add(loft_in).bodies.item(0)

    utils.add_bore(comp, bore, fw)
    return body
