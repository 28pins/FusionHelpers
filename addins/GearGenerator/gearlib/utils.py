"""Shared math helpers and FDM preset data for GearGenerator."""

import math

# ---------------------------------------------------------------------------
# FDM tuning presets  (all measurements in mm)
# ---------------------------------------------------------------------------
FDM_PRESETS = {
    0.2: {"backlash": 0.12, "bore_oversize": 0.10, "tip_relief": 0.06},
    0.4: {"backlash": 0.20, "bore_oversize": 0.15, "tip_relief": 0.10},
    0.6: {"backlash": 0.28, "bore_oversize": 0.20, "tip_relief": 0.12},
    0.8: {"backlash": 0.40, "bore_oversize": 0.30, "tip_relief": 0.16},
}


def apply_fdm_preset(params, nozzle_mm):
    """Return a *copy* of params with FDM preset deltas applied."""
    preset = FDM_PRESETS.get(nozzle_mm, FDM_PRESETS[0.4])
    p = dict(params)
    p["backlash_mm"] = p.get("backlash_mm", 0.0) + preset["backlash"]
    p["bore_dia_mm"] = p.get("bore_dia_mm", 0.0) + preset["bore_oversize"]
    p["tip_relief_mm"] = preset["tip_relief"]
    return p


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------
def dp_to_module(dp):
    """Diametral-Pitch (teeth/inch) → module (mm)."""
    return 25.4 / dp


def module_to_dp(m):
    """Module (mm) → Diametral-Pitch (teeth/inch)."""
    return 25.4 / m


def mm_to_cm(mm):
    return mm / 10.0


# ---------------------------------------------------------------------------
# Low-level involute math  (all lengths in mm)
# ---------------------------------------------------------------------------
def _inv_pt(rb, t):
    """Point on the involute of circle rb at parameter t."""
    x = rb * (math.cos(t) + t * math.sin(t))
    y = rb * (math.sin(t) - t * math.cos(t))
    return x, y


def _rot(x, y, angle):
    """Rotate point (x, y) counter-clockwise by *angle* radians."""
    c, s = math.cos(angle), math.sin(angle)
    return c * x - s * y, s * x + c * y


def rotate2d(x, y, angle):
    """Public alias for _rot – rotate point (x, y) CCW by *angle* radians."""
    return _rot(x, y, angle)


# ---------------------------------------------------------------------------
# Complete spur-gear profile (all N teeth, CCW, mm)
# ---------------------------------------------------------------------------
def spur_profile_pts(m, z, alpha_deg=20.0, backlash=0.0, tip_relief=0.0,
                     n_inv=10, n_arc=4):
    """
    Return [(x, y), …] in **mm** forming a closed CCW spur-gear outline
    with *z* teeth.  Suitable for SketchFittedSplines.add() with
    isClosed = True.

    Parameters
    ----------
    m          : module (mm)
    z          : number of teeth
    alpha_deg  : pressure angle (°)
    backlash   : total backlash reduction applied to tooth thickness (mm)
    tip_relief : radial tip relief shortening the addendum (mm)
    n_inv      : involute sample count per flank
    n_arc      : arc sample count for tip / root arcs
    """
    alpha = math.radians(alpha_deg)
    rp = m * z / 2.0
    rb = rp * math.cos(alpha)
    rt = rp + m - tip_relief           # tip   (addendum) radius
    rr = rp - 1.25 * m                 # root  (dedendum) radius
    rr_eff = max(rr, 0.3 * m)          # guard against very few teeth

    # Involute parameter at the start (base-circle edge or root, whichever
    # is larger so the flank is always a true involute curve)
    if rr_eff >= rb:
        t_base = math.sqrt((rr_eff / rb) ** 2 - 1)
    else:
        # Root is inside base circle – start involute at base circle and
        # treat base circle as effective root (slight simplification, fine
        # for 3-D printing)
        t_base = 0.0
        rr_eff = rb

    t_tip = math.sqrt(max(0.0, (rt / rb) ** 2 - 1))

    # Angle of the natural involute at the pitch circle  (≈ tan α − α)
    tp = math.tan(alpha)
    xp, yp = _inv_pt(rb, tp)
    inv_a = math.atan2(yp, xp)

    # Half tooth angle at the pitch circle (reduced by backlash)
    tooth_thick = math.pi * m / 2.0 - backlash
    ha = tooth_thick / (2.0 * rp)

    # Rotation constants so flanks land at ±ha from tooth centre
    rot_r = -(ha - inv_a)   # right flank  (uses mirrored involute)
    rot_l = +(ha - inv_a)   # left  flank  (uses natural involute)

    pitch = 2.0 * math.pi / z
    pts = []
    first_right_root = None
    prev_left_root = None

    for i in range(z):
        theta = i * pitch

        # ── right-flank root point (start of this tooth)
        xr_b, yr_b = _inv_pt(rb, t_base)
        right_root = _rot(xr_b, -yr_b, rot_r + theta)

        if prev_left_root is None:
            first_right_root = right_root
        else:
            # Root arc: prev left-root → this right-root  (CCW)
            a0 = math.atan2(prev_left_root[1], prev_left_root[0])
            a1 = math.atan2(right_root[1], right_root[0])
            da = a1 - a0
            if da < 0:
                da += 2.0 * math.pi
            for k in range(1, n_arc + 1):
                a = a0 + da * k / n_arc
                pts.append((rr_eff * math.cos(a), rr_eff * math.sin(a)))

        # ── right flank: base → tip  (mirror involute, rotated)
        for j in range(n_inv + 1):
            t = t_base + (t_tip - t_base) * j / n_inv
            x, y = _inv_pt(rb, t)
            pts.append(_rot(x, -y, rot_r + theta))

        # ── tip arc: right tip → left tip  (CCW)
        xrt, yrt = pts[-1]
        a_rt = math.atan2(yrt, xrt)
        xl_t, yl_t = _inv_pt(rb, t_tip)
        xl_t, yl_t = _rot(xl_t, yl_t, rot_l + theta)
        a_lt = math.atan2(yl_t, xl_t)
        da_tip = a_lt - a_rt
        if da_tip < 0:
            da_tip += 2.0 * math.pi
        if da_tip > math.pi:          # safety: take short arc
            da_tip -= 2.0 * math.pi
        for k in range(1, n_arc + 1):
            a = a_rt + da_tip * k / n_arc
            pts.append((rt * math.cos(a), rt * math.sin(a)))

        # ── left flank: tip → base  (natural involute, rotated)
        for j in range(n_inv + 1):
            t = t_tip - (t_tip - t_base) * j / n_inv
            x, y = _inv_pt(rb, t)
            pts.append(_rot(x, y, rot_l + theta))

        prev_left_root = pts[-1]

    # ── closing root arc: last left-root → first right-root
    if prev_left_root is not None and first_right_root is not None:
        a0 = math.atan2(prev_left_root[1], prev_left_root[0])
        a1 = math.atan2(first_right_root[1], first_right_root[0])
        da = a1 - a0
        if da < 0:
            da += 2.0 * math.pi
        for k in range(1, n_arc + 1):
            a = a0 + da * k / n_arc
            pts.append((rr_eff * math.cos(a), rr_eff * math.sin(a)))

    return pts


# ---------------------------------------------------------------------------
# Internal-gear profile (ring with N inward teeth, CCW inner boundary)
# ---------------------------------------------------------------------------
def internal_profile_pts(m, z, alpha_deg=20.0, backlash=0.0, tip_relief=0.0,
                          n_inv=10, n_arc=4):
    """
    Return [(x, y), …] in **mm** for the *inner* boundary of a ring gear
    with *z* inward-pointing teeth.  Draw this plus an outer circle, then
    extrude the annular region.

    Convention for internal gear:
        tip   radius = rp − m          (teeth point inward)
        root  radius = rp + 1.25·m    (root on the outside)
    """
    alpha = math.radians(alpha_deg)
    rp = m * z / 2.0
    rb = rp * math.cos(alpha)
    rt_int = rp - m + tip_relief       # tip  (inner, addendum subtracted)
    rr_int = rp + 1.25 * m            # root (outer)

    rt_int = max(rt_int, 0.5 * m)     # safety

    # Involute parameter range
    t_tip_int = math.sqrt(max(0.0, (rt_int / rb) ** 2 - 1)) if rt_int >= rb else 0.0
    t_root_int = math.sqrt(max(0.0, (rr_int / rb) ** 2 - 1))

    # Use same rotation constants as spur (teeth have same half-angle)
    tp = math.tan(alpha)
    xp, yp = _inv_pt(rb, tp)
    inv_a = math.atan2(yp, xp)
    tooth_thick = math.pi * m / 2.0 - backlash
    ha = tooth_thick / (2.0 * rp)
    rot_r = -(ha - inv_a)
    rot_l = +(ha - inv_a)

    pitch = 2.0 * math.pi / z
    pts = []
    first_right_root = None
    prev_left_root = None

    for i in range(z):
        theta = i * pitch

        # right-flank root (at r_root_int, large radius)
        xr_b, yr_b = _inv_pt(rb, t_root_int)
        right_root = _rot(xr_b, -yr_b, rot_r + theta)

        if prev_left_root is None:
            first_right_root = right_root
        else:
            # Root arc at r_root_int (CCW, at the outer/root radius)
            a0 = math.atan2(prev_left_root[1], prev_left_root[0])
            a1 = math.atan2(right_root[1], right_root[0])
            da = a1 - a0
            if da < 0:
                da += 2.0 * math.pi
            for k in range(1, n_arc + 1):
                a = a0 + da * k / n_arc
                pts.append((rr_int * math.cos(a), rr_int * math.sin(a)))

        # right flank: root → tip  (decreasing radius for internal gear)
        # t goes from t_root_int (large) down to t_tip_int (small)
        for j in range(n_inv + 1):
            t = t_root_int - (t_root_int - t_tip_int) * j / n_inv
            x, y = _inv_pt(rb, t)
            pts.append(_rot(x, -y, rot_r + theta))

        # tip arc at r_tip_int (CCW, inner/tip radius)
        xrt, yrt = pts[-1]
        a_rt = math.atan2(yrt, xrt)
        xl_t, yl_t = _inv_pt(rb, t_tip_int)
        xl_t, yl_t = _rot(xl_t, yl_t, rot_l + theta)
        a_lt = math.atan2(yl_t, xl_t)
        da_tip = a_lt - a_rt
        if da_tip < 0:
            da_tip += 2.0 * math.pi
        if da_tip > math.pi:
            da_tip -= 2.0 * math.pi
        for k in range(1, n_arc + 1):
            a = a_rt + da_tip * k / n_arc
            pts.append((rt_int * math.cos(a), rt_int * math.sin(a)))

        # left flank: tip → root  (increasing radius)
        for j in range(n_inv + 1):
            t = t_tip_int + (t_root_int - t_tip_int) * j / n_inv
            x, y = _inv_pt(rb, t)
            pts.append(_rot(x, y, rot_l + theta))

        prev_left_root = pts[-1]

    # closing root arc
    if prev_left_root is not None and first_right_root is not None:
        a0 = math.atan2(prev_left_root[1], prev_left_root[0])
        a1 = math.atan2(first_right_root[1], first_right_root[0])
        da = a1 - a0
        if da < 0:
            da += 2.0 * math.pi
        for k in range(1, n_arc + 1):
            a = a0 + da * k / n_arc
            pts.append((rr_int * math.cos(a), rr_int * math.sin(a)))

    return pts


# ---------------------------------------------------------------------------
# Rack tooth profile  (one period, centred on X-axis, mm)
# ---------------------------------------------------------------------------
def rack_tooth_pts(m, alpha_deg=20.0, backlash=0.0, tip_relief=0.0, n_pts=6):
    """
    Return [(x, y)] for ONE rack tooth period.  Rack is horizontal,
    teeth point in +Y direction.  x spans one full circular pitch.

    Profile order: bottom-left → left flank up → tip → right flank down
    → bottom-right.  Caller tiles these end-to-end for the full rack.
    """
    alpha = math.radians(alpha_deg)
    p = math.pi * m                    # circular pitch
    ht = m                             # addendum height
    hd = 1.25 * m                      # dedendum depth (below pitch line)
    tb = p / 2.0 - backlash            # tooth bottom width (at root)

    # half-pitch
    hp = p / 2.0

    # Width at tip (reduced by tip relief and pressure angle geometry)
    tw_tip = tb - 2.0 * (ht - tip_relief) * math.tan(alpha)
    tw_tip = max(tw_tip, 0.05 * m)

    # Width at root
    tw_root = tb + 2.0 * hd * math.tan(alpha)

    # x positions (centred at 0)
    x_root_r = tw_root / 2.0
    x_root_l = -tw_root / 2.0
    x_tip_r  = tw_tip / 2.0
    x_tip_l  = -tw_tip / 2.0

    # y positions
    y_root = -hd               # below pitch line (dedendum)
    y_tip  = ht - tip_relief   # above pitch line (addendum)

    pts = [
        (x_root_l - (hp - tw_root / 2.0), y_root),   # bottom-left space
        (x_root_l,  y_root),
    ]
    # Left flank (straight, pressure angle)
    for k in range(1, n_pts):
        frac = k / n_pts
        pts.append((x_root_l + (x_tip_l - x_root_l) * frac,
                    y_root   + (y_tip   - y_root)    * frac))
    pts += [
        (x_tip_l,  y_tip),
        (x_tip_r,  y_tip),
    ]
    # Right flank
    for k in range(1, n_pts):
        frac = k / n_pts
        pts.append((x_tip_r + (x_root_r - x_tip_r) * frac,
                    y_tip   + (y_root   - y_tip)    * frac))
    pts += [
        (x_root_r, y_root),
        (x_root_r + (hp - tw_root / 2.0), y_root),  # bottom-right space
    ]
    return pts


# ---------------------------------------------------------------------------
# Fusion sketch helpers  (depend on adsk – imported lazily)
# ---------------------------------------------------------------------------
def _p3(x_mm, y_mm, z_mm=0.0):
    """adsk.core.Point3D from mm coordinates."""
    import adsk.core
    return adsk.core.Point3D.create(x_mm / 10.0, y_mm / 10.0, z_mm / 10.0)


def pts_to_object_collection(pts_mm):
    """Convert [(x, y), …] (mm) to adsk.core.ObjectCollection of Point3D."""
    import adsk.core
    oc = adsk.core.ObjectCollection.create()
    for (x, y) in pts_mm:
        oc.add(adsk.core.Point3D.create(x / 10.0, y / 10.0, 0.0))
    return oc


def largest_profile(sketch):
    """Return the sketch profile with the greatest area."""
    best, best_area = None, -1.0
    for i in range(sketch.profiles.count):
        p = sketch.profiles.item(i)
        try:
            area = p.areaProperties().area
        except Exception:
            area = 0.0
        if area > best_area:
            best_area = area
            best = p
    return best


def add_bore(comp, bore_dia_mm, face_width_mm):
    """Cut a concentric bore through the most-recently-created body."""
    if bore_dia_mm <= 0.0:
        return
    import adsk.core, adsk.fusion
    xyp = comp.xYConstructionPlane
    sk = comp.sketches.add(xyp)
    sk.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 0),
        bore_dia_mm / 20.0   # radius in cm
    )
    prof = sk.profiles.item(0)
    ext_in = comp.features.extrudeFeatures.createInput(
        prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
    ext_in.setAllExtent(adsk.fusion.ExtentDirections.PositiveExtentDirection)
    comp.features.extrudeFeatures.add(ext_in)
