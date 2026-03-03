"""Bevel gear (straight) pair builder for Fusion 360.

Approach
--------
* Build a large-end spur-profile cross-section and a small-end spur-profile
  cross-section (scaled by the cone-ratio), each on its own offset plane.
* Loft between them to create a tapered gear body.
* Repeat for the mating pinion (90° shaft angle assumed).
* Both solids are created in the same component as separate bodies.
"""

import math
import adsk.core
import adsk.fusion

from . import utils


def _bevel_gear_body(comp, m_large, m_small, z, fw, alpha, bl, tr,
                     z_offset_mm, name_hint):
    """
    Create one bevel gear body by lofting a large-end and small-end
    spur profile.

    Parameters
    ----------
    m_large   : module at the large (back) face (mm)
    m_small   : module at the small (front / apex) face (mm)
    z         : number of teeth
    fw        : face width (mm)
    z_offset_mm : Z-position of the large face in the component
    """
    planes = comp.constructionPlanes

    sections = []
    for i, (m_i, z_off) in enumerate([(m_large, z_offset_mm),
                                       (m_small, z_offset_mm + fw)]):
        plane_in = planes.createInput()
        plane_in.setByOffset(
            comp.xYConstructionPlane,
            adsk.core.ValueInput.createByReal(utils.mm_to_cm(z_off))
        )
        plane = planes.add(plane_in)

        sk = comp.sketches.add(plane)
        pts = utils.spur_profile_pts(m_i, z, alpha, bl, tr)
        oc = utils.pts_to_object_collection(pts)
        spline = sk.sketchCurves.sketchFittedSplines.add(oc)
        spline.isClosed = True
        prof = utils.largest_profile(sk)
        if prof is None:
            raise RuntimeError(f"Bevel {name_hint}: no profile at section {i}.")
        sections.append(prof)

    loft_in = comp.features.loftFeatures.createInput(
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    for prof in sections:
        loft_in.loftSections.add(prof)
    body = comp.features.loftFeatures.add(loft_in).bodies.item(0)
    return body


def create_bevel(comp, params):
    """
    Create a bevel gear *pair* (gear + pinion) inside *comp*.

    params keys
    -----------
    module_mm          : float – module at large (back) face
    num_teeth          : int   – tooth count for the gear
    num_teeth_pinion   : int   – tooth count for the pinion (default = num_teeth // 2)
    face_width_mm      : float
    pressure_angle_deg : float (default 20.0)
    backlash_mm        : float (default 0.0)
    tip_relief_mm      : float (default 0.0)
    shaft_angle_deg    : float (default 90.0)
    bore_dia_mm        : float (default 0.0)

    Returns
    -------
    Tuple (gear_body, pinion_body).
    """
    m      = float(params["module_mm"])
    z_gear = int(params["num_teeth"])
    z_pin  = int(params.get("num_teeth_pinion", max(6, z_gear // 2)))
    fw     = float(params["face_width_mm"])
    alpha  = float(params.get("pressure_angle_deg", 20.0))
    bl     = float(params.get("backlash_mm", 0.0))
    tr     = float(params.get("tip_relief_mm", 0.0))
    bore   = float(params.get("bore_dia_mm", 0.0))

    # Pitch-cone half-angles
    shaft_angle = float(params.get("shaft_angle_deg", 90.0))
    pitch_cone_gear = math.degrees(
        math.atan2(math.sin(math.radians(shaft_angle)),
                   z_gear / z_pin + math.cos(math.radians(shaft_angle))))
    pitch_cone_pin = shaft_angle - pitch_cone_gear

    # Back-cone (large-end) pitch radius
    r_back_gear = m * z_gear / 2.0
    r_back_pin  = m * z_pin  / 2.0

    # Cone distance (slant height)
    cone_dist = r_back_gear / math.sin(math.radians(pitch_cone_gear))

    # Small-end module (proportional to distance from apex)
    ratio = (cone_dist - fw) / cone_dist
    m_small_gear = m * ratio
    m_small_pin  = m * ratio   # same pitch at small end

    # ── Gear body ────────────────────────────────────────────────────────────
    gear_body = _bevel_gear_body(comp, m, m_small_gear, z_gear, fw,
                                  alpha, bl, tr, 0.0, "gear")

    utils.add_bore(comp, bore, fw)

    # ── Pinion body (offset in X, rotated 90° about X axis) ─────────────────
    # Place the pinion so it appears next to the gear with correct spacing.
    # The two back-cone circles are tangent: centre distance = r_back_gear + r_back_pin
    pinion_offset_mm = r_back_gear + r_back_pin + fw * 0.5   # visual gap

    # Build pinion as a new component offset along X
    pin_body = _bevel_gear_body(comp, m, m_small_pin, z_pin, fw,
                                  alpha, bl, tr, 0.0, "pinion")

    # Move pinion body to the side
    bodies_to_move = adsk.core.ObjectCollection.create()
    bodies_to_move.add(pin_body)
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(
        utils.mm_to_cm(pinion_offset_mm), 0, 0)
    move_in = comp.features.moveFeatures.createInput(bodies_to_move, transform)
    comp.features.moveFeatures.add(move_in)

    utils.add_bore(comp, bore, fw)

    return gear_body, pin_body
