"""
GearGenerator – Fusion 360 Add-In
==================================
Parametric gear generator supporting:
    • Spur (external)     • Helical (external)
    • Internal (ring)     • Rack
    • Bevel (straight)    • Worm set

Includes optional FDM 3-D-printing optimisation with four nozzle presets.

Author : 28pins
License: MIT + NoAI  (see LICENSE)
"""

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import os
import sys

# ── ensure local package is importable ──────────────────────────────────────
_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)

from gearlib import utils, spur, helical, internal, rack, bevel, worm

# ── globals ──────────────────────────────────────────────────────────────────
_app      = None
_ui       = None
_handlers = []

_CMD_ID   = "GearGenerator_28pins"
_PANEL_ID = "SolidCreatePanel"

GEAR_TYPES = [
    "Spur (External)",
    "Helical (External)",
    "Internal (Ring)",
    "Rack",
    "Bevel (Straight)",
    "Worm Set",
]

NOZZLE_LABELS  = ["0.2 mm", "0.4 mm", "0.6 mm", "0.8 mm"]
NOZZLE_VALUES  = [0.2,      0.4,      0.6,      0.8]

# Default diametral pitch (imperial) and its metric equivalent
DEFAULT_DP     = 20.0           # teeth / inch
DEFAULT_MODULE = utils.dp_to_module(DEFAULT_DP)   # ≈ 1.27 mm


# ============================================================================
#  run / stop
# ============================================================================

def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface

        # Clean up any stale definition
        if _ui.commandDefinitions.itemById(_CMD_ID):
            _ui.commandDefinitions.itemById(_CMD_ID).deleteMe()

        cmd_def = _ui.commandDefinitions.addButtonDefinition(
            _CMD_ID,
            "Gear Generator",
            "Generate parametric spur, helical, internal, rack, bevel or worm gears\n"
            "with optional FDM 3-D printing optimisation.",
            os.path.join(_dir, "resources"),
        )

        on_created = _CommandCreatedHandler()
        cmd_def.commandCreated.add(on_created)
        _handlers.append(on_created)

        # Add to the Create panel
        panel = _ui.allToolbarPanels.itemById(_PANEL_ID)
        if panel:
            ctrl = panel.controls.addCommand(cmd_def)
            ctrl.isPromotedByDefault = False

        cmd_def.execute()
        adsk.autoTerminate(False)

    except Exception:
        if _ui:
            _ui.messageBox(
                "GearGenerator failed to start:\n" + traceback.format_exc())


def stop(context):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        panel = ui.allToolbarPanels.itemById(_PANEL_ID)
        if panel:
            ctrl = panel.controls.itemById(_CMD_ID)
            if ctrl:
                ctrl.deleteMe()
        defn = ui.commandDefinitions.itemById(_CMD_ID)
        if defn:
            defn.deleteMe()
    except Exception:
        pass


# ============================================================================
#  Command-created handler  (builds the dialog)
# ============================================================================

class _CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd    = args.command
            inputs = cmd.commandInputs

            # ── Gear type ────────────────────────────────────────────────
            gear_type_in = inputs.addDropDownCommandInput(
                "gear_type", "Gear Type",
                adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            for gt in GEAR_TYPES:
                gear_type_in.listItems.add(gt, gt == "Spur (External)", "")

            # ── Units ────────────────────────────────────────────────────
            units_in = inputs.addButtonRowCommandInput(
                "units", "Units", False)
            units_in.listItems.add("Imperial", True,  "")
            units_in.listItems.add("Metric",   False, "")

            # ── Module / Diametral-Pitch ──────────────────────────────────
            inputs.addValueInput(
                "diametral_pitch", "Diametral Pitch (teeth/in)",
                "",
                adsk.core.ValueInput.createByReal(DEFAULT_DP))
            inputs.addValueInput(
                "module_mm", "Module (mm)",
                "mm",
                adsk.core.ValueInput.createByReal(DEFAULT_MODULE))

            # ── Common tooth parameters ───────────────────────────────────
            inputs.addIntegerSpinnerCommandInput(
                "num_teeth", "Number of Teeth", 6, 500, 1, 20)
            inputs.addValueInput(
                "face_width", "Face Width",
                "mm",
                adsk.core.ValueInput.createByReal(utils.mm_to_cm(10.0)))
            inputs.addValueInput(
                "pressure_angle", "Pressure Angle (°)",
                "deg",
                adsk.core.ValueInput.createByReal(20.0))
            inputs.addValueInput(
                "bore_dia", "Bore Diameter",
                "mm",
                adsk.core.ValueInput.createByReal(0.0))
            inputs.addValueInput(
                "backlash", "Backlash",
                "mm",
                adsk.core.ValueInput.createByReal(0.0))

            # ── Helical-specific ─────────────────────────────────────────
            helix_in = inputs.addValueInput(
                "helix_angle", "Helix Angle (°)",
                "deg",
                adsk.core.ValueInput.createByReal(15.0))
            helix_in.tooltip = "Lead helix angle for helical gears only."

            # ── Worm-specific ────────────────────────────────────────────
            starts_in = inputs.addIntegerSpinnerCommandInput(
                "num_starts", "Worm Starts", 1, 12, 1, 2)
            starts_in.tooltip = "Number of thread starts on the worm."

            # ── Bevel pinion ─────────────────────────────────────────────
            pinion_in = inputs.addIntegerSpinnerCommandInput(
                "num_teeth_pinion", "Pinion Teeth (Bevel)", 6, 200, 1, 10)
            pinion_in.tooltip = "Tooth count for the mating bevel pinion."

            # ── FDM options ───────────────────────────────────────────────
            fdm_in = inputs.addBoolValueInput(
                "fdm_opt", "3-D Print Optimisation", True, "", False)
            fdm_in.tooltip = (
                "Applies backlash, bore oversize and tip-relief adjustments\n"
                "tuned for FDM 3-D printing.")

            nozzle_in = inputs.addDropDownCommandInput(
                "nozzle_size", "Nozzle Size",
                adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            for lbl in NOZZLE_LABELS:
                nozzle_in.listItems.add(lbl, lbl == "0.4 mm", "")
            nozzle_in.tooltip = (
                "Nozzle diameter preset.\n"
                "0.2 mm → backlash +0.12 mm, bore oversize +0.10 mm, tip relief 0.06 mm\n"
                "0.4 mm → backlash +0.20 mm, bore oversize +0.15 mm, tip relief 0.10 mm\n"
                "0.6 mm → backlash +0.28 mm, bore oversize +0.20 mm, tip relief 0.12 mm\n"
                "0.8 mm → backlash +0.40 mm, bore oversize +0.30 mm, tip relief 0.16 mm")

            # Initial visibility
            _refresh_visibility(inputs)

            # Wire up handlers
            on_changed = _InputChangedHandler()
            cmd.inputChanged.add(on_changed)
            _handlers.append(on_changed)

            on_exec = _ExecuteHandler()
            cmd.execute.add(on_exec)
            _handlers.append(on_exec)

            on_validate = _ValidateHandler()
            cmd.validateInputs.add(on_validate)
            _handlers.append(on_validate)

        except Exception:
            _ui.messageBox(
                "GearGenerator dialog error:\n" + traceback.format_exc())


# ============================================================================
#  Input-changed handler  (show/hide inputs by gear type / units / FDM)
# ============================================================================

class _InputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            _refresh_visibility(args.inputs)
        except Exception:
            pass


def _refresh_visibility(inputs):
    """Show/hide inputs depending on current gear-type and unit selections."""
    gt_in     = inputs.itemById("gear_type")
    units_in  = inputs.itemById("units")
    fdm_in    = inputs.itemById("fdm_opt")
    nozzle_in = inputs.itemById("nozzle_size")
    dp_in     = inputs.itemById("diametral_pitch")
    mm_in     = inputs.itemById("module_mm")
    helix_in  = inputs.itemById("helix_angle")
    starts_in = inputs.itemById("num_starts")
    pinion_in = inputs.itemById("num_teeth_pinion")
    bore_in   = inputs.itemById("bore_dia")

    if not all([gt_in, units_in, fdm_in, nozzle_in]):
        return

    gear_type  = gt_in.selectedItem.name    if gt_in.selectedItem else ""
    is_imperial = (units_in.selectedItem.name == "Imperial"
                   if units_in.selectedItem else True)
    is_fdm     = fdm_in.value if fdm_in else False

    dp_in.isVisible     = is_imperial
    mm_in.isVisible     = not is_imperial
    nozzle_in.isVisible = is_fdm

    helix_in.isVisible  = (gear_type == "Helical (External)")
    starts_in.isVisible = (gear_type == "Worm Set")
    pinion_in.isVisible = (gear_type == "Bevel (Straight)")
    # Rack has no bore
    if bore_in:
        bore_in.isVisible = (gear_type != "Rack")


# ============================================================================
#  Validate handler
# ============================================================================

class _ValidateHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        args.areInputsValid = True


# ============================================================================
#  Execute handler  (the actual gear builder)
# ============================================================================

class _ExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            inputs    = args.command.commandInputs
            _generate(inputs)
        except Exception:
            _ui.messageBox(
                "GearGenerator – generation failed:\n" + traceback.format_exc())


def _generate(inputs):
    """Read inputs, apply FDM presets if requested, call the right builder."""
    design = adsk.fusion.Design.cast(_app.activeProduct)
    root   = design.rootComponent

    # ── read gear type & units ────────────────────────────────────────────
    gear_type  = inputs.itemById("gear_type").selectedItem.name
    is_imperial = (inputs.itemById("units").selectedItem.name == "Imperial")

    # ── resolve module ────────────────────────────────────────────────────
    if is_imperial:
        dp     = inputs.itemById("diametral_pitch").value
        m_mm   = utils.dp_to_module(max(dp, 0.1))
    else:
        m_mm   = inputs.itemById("module_mm").value * 10.0   # cm → mm

    # ── common params ─────────────────────────────────────────────────────
    params = {
        "module_mm":          m_mm,
        "num_teeth":          inputs.itemById("num_teeth").value,
        "face_width_mm":      inputs.itemById("face_width").value * 10.0,
        "pressure_angle_deg": inputs.itemById("pressure_angle").value,
        "bore_dia_mm":        inputs.itemById("bore_dia").value * 10.0,
        "backlash_mm":        inputs.itemById("backlash").value * 10.0,
        "tip_relief_mm":      0.0,
        "helix_angle_deg":    inputs.itemById("helix_angle").value,
        "num_starts":         inputs.itemById("num_starts").value,
        "num_teeth_pinion":   inputs.itemById("num_teeth_pinion").value,
    }

    # ── FDM preset ────────────────────────────────────────────────────────
    fdm = inputs.itemById("fdm_opt").value
    if fdm:
        nozzle_label = inputs.itemById("nozzle_size").selectedItem.name
        nozzle_mm    = NOZZLE_VALUES[NOZZLE_LABELS.index(nozzle_label)]
        params = utils.apply_fdm_preset(params, nozzle_mm)

    # ── create a new component ────────────────────────────────────────────
    occ  = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = gear_type.replace(" ", "_").replace("(", "").replace(")", "")

    # ── dispatch ─────────────────────────────────────────────────────────
    if gear_type == "Spur (External)":
        spur.create_spur(comp, params)

    elif gear_type == "Helical (External)":
        helical.create_helical(comp, params)

    elif gear_type == "Internal (Ring)":
        internal.create_internal(comp, params)

    elif gear_type == "Rack":
        rack.create_rack(comp, params)

    elif gear_type == "Bevel (Straight)":
        bevel.create_bevel(comp, params)

    elif gear_type == "Worm Set":
        worm.create_worm(comp, params)

    else:
        raise ValueError(f"Unknown gear type: {gear_type!r}")

    _ui.messageBox(
        f"{gear_type} generated successfully!\n"
        f"Module: {m_mm:.3f} mm  |  Teeth: {params['num_teeth']}\n"
        f"Face width: {params['face_width_mm']:.2f} mm"
        + (f"\nFDM preset active ({nozzle_label} nozzle)." if fdm else ""),
        "Gear Generator")
