# GearGenerator – Fusion 360 Add-In

A parametric gear generator for Autodesk Fusion 360, supporting six gear
types, Imperial/Metric units, and optional FDM 3-D-printing optimisation.

---

## Gear types

| Type | Description |
|------|-------------|
| **Spur (External)** | Standard external spur gear with involute tooth profile |
| **Helical (External)** | External helical gear – stacked cross-sections lofted with a twist |
| **Internal (Ring)** | Ring gear with inward-pointing involute teeth |
| **Rack** | Linear rack with pressure-angle flanks |
| **Bevel (Straight)** | Straight bevel gear pair (gear + pinion), 90° shaft angle |
| **Worm Set** | Worm cylinder with helical ridge + worm-wheel spur body |

---

## Installation

1. Download or clone this repository.
2. In Fusion 360, open **Tools → Add-Ins → Scripts and Add-Ins** (keyboard
   shortcut **Shift+S**).
3. Click the **Add-Ins** tab, then the **+** icon next to *My Add-Ins*.
4. Navigate to the `addins/GearGenerator/` folder and click **Select**.
5. The add-in appears in the list – tick **Run on Startup** if desired, then
   click **Run**.
6. The **Gear Generator** button appears in the **Solid → Create** panel.

### Requirements

- Autodesk Fusion 360 (any recent version with Python 3 add-in support)
- No external Python packages required

---

## Usage

1. Open a Fusion 360 design (or create a new one).
2. Click **Gear Generator** in the Create panel (or run from Add-Ins).
3. Set parameters in the dialog:
   - **Gear Type** – select from the drop-down.
   - **Units** – *Imperial* (Diametral Pitch, inches) or *Metric* (Module, mm).
   - **Number of Teeth**, **Face Width**, **Pressure Angle**, **Bore Diameter**,
     **Backlash**.
   - Gear-type-specific options (Helix Angle, Worm Starts, Pinion Teeth).
   - **3-D Print Optimisation** – tick to apply nozzle-specific tolerances.
   - **Nozzle Size** – visible when 3-D Print Optimisation is enabled.
4. Click **OK**. A new component is added to your design.

> Bevel and Worm Set generate **two bodies** (gear + pinion / worm + wheel)
> in the same component.

---

## FDM nozzle presets

When **3-D Print Optimisation** is enabled the following adjustments are
automatically added on top of any manual backlash / bore values you set:

| Nozzle | Backlash added | Bore oversize | Tip relief |
|--------|---------------|---------------|------------|
| 0.2 mm | +0.12 mm | +0.10 mm | 0.06 mm |
| 0.4 mm | +0.20 mm | +0.15 mm | 0.10 mm |
| 0.6 mm | +0.28 mm | +0.20 mm | 0.12 mm |
| 0.8 mm | +0.40 mm | +0.30 mm | 0.16 mm |

**Applied as:**

```
effective_backlash = manual_backlash + preset_backlash
effective_bore     = manual_bore + preset_bore_oversize
tip_relief         = preset_tip_relief   (overrides any manual value when FDM is on)
```

---

## Parameters reference

| Parameter | Imperial default | Metric default | Notes |
|-----------|-----------------|----------------|-------|
| Diametral Pitch | 20 teeth/in | – | Imperial only |
| Module | – | 1.27 mm | Metric only |
| Number of Teeth | 20 | 20 | Min 6 (spur/helical/bevel) |
| Face Width | 10 mm | 10 mm | Gear depth / length |
| Pressure Angle | 20° | 20° | Standard 14.5° or 20° |
| Bore Diameter | 0 | 0 | 0 = no bore hole |
| Backlash | 0 | 0 | Added tooth-space clearance |
| Helix Angle | 15° | 15° | Helical only |
| Worm Starts | 2 | 2 | Worm Set only |
| Pinion Teeth | 10 | 10 | Bevel only |

---

## Technical notes

- All geometry uses **stable Fusion 360 API features only**: sketches,
  extrude, combine, loft, and move.  No coil or sweep features are used,
  so the add-in remains forward-compatible.
- The involute profile is computed analytically; the spur/helical/internal
  tooth flanks use a fitted spline through ≥ 10 involute sample points per
  flank.
- Helical gears are approximated by lofting 8+ cross-sections, each rotated
  progressively.  This gives excellent printable geometry while avoiding
  unstable coil/sweep API paths.

---

## License

MIT + NoAI – see [LICENSE](LICENSE).
