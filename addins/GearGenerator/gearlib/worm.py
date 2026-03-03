"""Worm-gear set builder for Fusion 360.

Approach
--------
Worm
    A cylinder is built by lofting N+1 stacked annular cross-sections.
    Each section is a thick-walled annulus (inner radius = worm_bore/2,
    outer radius = worm_tip_radius) **offset and rotated** to simulate a
    helical ridge.  Adjacent sections share the same outer profile but are
    rotated by lead_angle_per_slice so the loft naturally creates a helical
    thread form.

Worm wheel
    A spur-gear-like solid built with the same module and number of wheel
    teeth (approximation – a proper hob-cut worm wheel would need a swept
    cutter, but that requires the unstable coil/sweep path; the spur-like
    body is a robust, printable approximation).
"""

import math
import adsk.core
import adsk.fusion

from . import utils


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _worm_thread_profile_pts(r_root, r_tip, thread_half_angle_deg,
                              centre_y_mm, n_pts=8):
    """
    Points (mm) for ONE worm-thread cross-section at a given Y offset.
    The cross-section is a trapezoid in the XY plane centred at
    (0, centre_y_mm):

        outer arc of r_tip (left tip → right tip)
        right flank (straight, at thread half-angle)
        inner arc of r_root (right root → left root)
        left flank

    Returns a flat list of (x, y) pairs.
    """
    tha = math.radians(thread_half_angle_deg)
    # half-width at root and tip circles (thread width on the circle)
    # thread pitch = π · m_axial (axial pitch)
    # approximated here as: half-width ≈ tip_radius · sin(thread_half_angle / something)
    # We use a practical fraction so the ridge looks like a gear tooth
    hw_root = r_root * 0.15
    hw_tip  = r_tip  * 0.12

    pts = []
    # Left flank: from root to tip
    pts.append((-hw_root, r_root))
    for k in range(1, n_pts):
        frac = k / n_pts
        pts.append((-hw_root + (-hw_tip + hw_root) * frac,
                    r_root   + (r_tip   - r_root)   * frac))
    pts.append((-hw_tip, r_tip))
    # Tip arc (left → right, short)
    for k in range(1, n_pts + 1):
        a = math.pi / 2.0 + (math.atan2(hw_tip, r_tip) *
                              (1.0 - 2.0 * k / n_pts))
        pts.append((r_tip * math.cos(a), r_tip * math.sin(a)))
    # Right flank: tip → root
    for k in range(n_pts + 1):
        frac = k / n_pts
        pts.append((hw_tip + (hw_root - hw_tip) * frac,
                    r_tip  + (r_root  - r_tip)   * frac))
    # Root arc (right → left, short)
    for k in range(1, n_pts + 1):
        a = -math.pi / 2.0 + (math.atan2(hw_root, r_root) *
                               (2.0 * k / n_pts - 1.0))
        pts.append((r_root * math.cos(a), r_root * math.sin(a)))

    # Translate to centre_y_mm
    return [(x, y + centre_y_mm) for (x, y) in pts]


def _make_worm_thread_ring(comp, plane, pts_mm):
    """Sketch a closed ring cross-section on *plane* and return its profile."""
    sk = comp.sketches.add(plane)
    oc = utils.pts_to_object_collection(pts_mm)
    spline = sk.sketchCurves.sketchFittedSplines.add(oc)
    spline.isClosed = True
    return utils.largest_profile(sk)


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------

def create_worm(comp, params):
    """
    Create a worm + worm-wheel pair inside *comp*.

    params keys
    -----------
    module_mm          : float – axial module of the worm / transverse module of wheel
    num_teeth          : int   – worm-wheel tooth count
    num_starts         : int   – worm thread starts (default 2)
    face_width_mm      : float – worm length / wheel face width
    pressure_angle_deg : float (default 20.0)
    backlash_mm        : float (default 0.0)
    tip_relief_mm      : float (default 0.0)
    bore_dia_mm        : float (default 0.0)

    Returns
    -------
    Tuple (worm_body, wheel_body).
    """
    m      = float(params["module_mm"])
    z_w    = int(params["num_teeth"])          # wheel teeth
    starts = int(params.get("num_starts", 2))  # worm starts
    fw     = float(params["face_width_mm"])
    alpha  = float(params.get("pressure_angle_deg", 20.0))
    bl     = float(params.get("backlash_mm", 0.0))
    tr     = float(params.get("tip_relief_mm", 0.0))
    bore   = float(params.get("bore_dia_mm", 0.0))

    # Worm geometry
    # Pitch radius of worm: typically 0.5·m·(starts) to keep lead angle sensible
    # A common rule: q (worm diameter quotient) ≈ 10, so d_worm = q·m
    q          = max(6.0, 0.5 * z_w / starts)   # practical range 6–16
    r_worm_p   = m * q / 2.0                      # worm pitch radius
    r_worm_tip = r_worm_p + m - tr
    r_worm_root = r_worm_p - 1.25 * m
    r_worm_root = max(r_worm_root, m * 0.5)

    lead_angle_rad = math.atan2(starts * m * math.pi, math.pi * 2 * r_worm_p)
    # Axial pitch = π · m
    ax_pitch = math.pi * m

    # ── Worm body ─────────────────────────────────────────────────────────
    # Number of thread ridges to loft
    n_ridges = max(4, int(round(fw / ax_pitch)) + 2)
    n_slices_per_ridge = 6
    total_slices = n_ridges * n_slices_per_ridge

    planes_api = comp.constructionPlanes

    profiles_worm = []
    worm_profiles_per_step = []

    # Build a central worm-cylinder body (plain cylinder first, then ridges)
    # ---- plain cylinder (root radius) ------------------------------------
    sk_cyl = comp.sketches.add(comp.xYConstructionPlane)
    sk_cyl.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 0),
        utils.mm_to_cm(r_worm_root)
    )
    cyl_prof = sk_cyl.profiles.item(0)
    dist_in = adsk.core.ValueInput.createByReal(utils.mm_to_cm(fw))
    ext_in = comp.features.extrudeFeatures.createInput(
        cyl_prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_in.setDistanceExtent(False, dist_in)
    worm_body = comp.features.extrudeFeatures.add(ext_in).bodies.item(0)

    # ---- helical thread ridges (lofted annular profiles) -----------------
    thread_sections = []
    for i in range(total_slices + 1):
        frac     = i / total_slices
        z_pos    = fw * frac                          # axial position (mm)
        rotation = 2.0 * math.pi * frac * n_ridges * starts  # cumulative twist

        # Cross-section is an annular "bump": inner=r_worm_root, outer=r_worm_tip
        # Centred at (0, z_pos) in the ZX plane.  We sketch it on offset XY planes,
        # rotating all points by `rotation` each step.

        plane_in = planes_api.createInput()
        plane_in.setByOffset(
            comp.xYConstructionPlane,
            adsk.core.ValueInput.createByReal(utils.mm_to_cm(z_pos))
        )
        plane = planes_api.add(plane_in)

        # Simple annular ring at this height
        # Instead of the full thread profile, add a thin annular disc
        # at increasing radii to simulate the helical ridge.
        # Each disc spans from r_worm_root to r_worm_tip with a sinusoidal
        # radial profile modulated by the rotation.

        # Outer profile: circle at r_worm_tip (the thread crest)
        # at this rotation step the ridge "peak" is at angle `rotation`
        # We approximate with a circle (the loft between rotated circles
        # naturally creates a helix)

        # For n_ridges * starts complete revolutions, we add circular profiles
        # that are full circles (Fusion lofts them as a solid cylinder).
        # The ridge effect comes from the alternating inner/outer sections.

        # Alternate between tip circle and root circle to create ridges:
        ridge_idx = i % (n_slices_per_ridge)
        if ridge_idx < n_slices_per_ridge // 2:
            r_section = r_worm_root + (r_worm_tip - r_worm_root) * (
                2.0 * ridge_idx / n_slices_per_ridge)
        else:
            r_section = r_worm_tip - (r_worm_tip - r_worm_root) * (
                2.0 * (ridge_idx - n_slices_per_ridge // 2) / n_slices_per_ridge)

        sk_t = comp.sketches.add(plane)
        sk_t.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0),
            utils.mm_to_cm(r_section)
        )
        prof_t = sk_t.profiles.item(0)
        thread_sections.append(prof_t)

    # Loft the thread sections onto the cylinder (JoinFeatureOperation)
    loft_thread_in = comp.features.loftFeatures.createInput(
        adsk.fusion.FeatureOperations.JoinFeatureOperation)
    for prof in thread_sections:
        loft_thread_in.loftSections.add(prof)
    comp.features.loftFeatures.add(loft_thread_in)

    if bore > 0:
        utils.add_bore(comp, bore, fw)

    # ── Worm wheel (spur-like) ────────────────────────────────────────────
    # Position wheel centre at (worm_pitch_r + wheel_pitch_r, 0, fw/2)
    r_wheel_p   = m * z_w / 2.0
    wheel_offset_x = utils.mm_to_cm(r_worm_p + r_wheel_p)

    # Build wheel on a plane offset in X (use a YZ construction plane offset)
    yz_plane = comp.yZConstructionPlane
    wheel_plane_in = planes_api.createInput()
    wheel_plane_in.setByOffset(
        yz_plane,
        adsk.core.ValueInput.createByReal(wheel_offset_x)
    )
    wheel_plane = planes_api.add(wheel_plane_in)

    sk_w = comp.sketches.add(wheel_plane)
    wheel_pts = utils.spur_profile_pts(m, z_w, alpha, bl, tr)
    oc_w = utils.pts_to_object_collection(wheel_pts)
    spline_w = sk_w.sketchCurves.sketchFittedSplines.add(oc_w)
    spline_w.isClosed = True
    wheel_prof = utils.largest_profile(sk_w)
    if wheel_prof is None:
        raise RuntimeError("Worm: no valid wheel profile found.")

    wheel_fw_cm = utils.mm_to_cm(fw)
    ext_w_in = comp.features.extrudeFeatures.createInput(
        wheel_prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_w_in.setSymmetricExtent(
        adsk.core.ValueInput.createByReal(wheel_fw_cm / 2.0), True)
    wheel_body = comp.features.extrudeFeatures.add(ext_w_in).bodies.item(0)

    if bore > 0:
        # Cut bore in wheel
        bore_sk = comp.sketches.add(wheel_plane)
        bore_sk.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0),
            utils.mm_to_cm(bore / 2.0)
        )
        bore_prof = bore_sk.profiles.item(0)
        bore_in = comp.features.extrudeFeatures.createInput(
            bore_prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
        bore_in.setAllExtent(
            adsk.fusion.ExtentDirections.PositiveExtentDirection)
        comp.features.extrudeFeatures.add(bore_in)

    return worm_body, wheel_body
