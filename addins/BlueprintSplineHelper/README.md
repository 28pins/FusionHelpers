# BlueprintSplineHelper – Fusion 360 Script

A utility script for Autodesk Fusion 360 that creates splines from coordinate points. Useful for tracing blueprints, technical drawings, or importing point data into Fusion 360 designs.

---

## Features

- **2D Splines** – Create splines on selected construction planes or planar faces
- **3D Splines** – Create freeform splines in 3D space
- **Coordinate Input** – Enter X, Y, and optionally Z coordinates as comma or space-separated values
- **Fit Point Splines** – Automatically generates smooth fitted splines through your points

---

## Installation

1. Download or clone this repository.
2. In Fusion 360, open **Tools → Add-Ins → Scripts and Add-Ins** (keyboard shortcut **Shift+S**).
3. Click the **Scripts** tab, then the **+** icon next to *My Scripts*.
4. Navigate to the `addins/BlueprintSplineHelper/` folder and click **Select**.
5. The script appears in the list – select it and click **Run**.

### Requirements

- Autodesk Fusion 360 (any recent version with Python 3 script support)
- No external Python packages required

---

## Usage

1. Open a Fusion 360 design (or create a new one).
2. Run the **BlueprintSplineHelper** script from the Scripts and Add-Ins panel.
3. Choose spline type:
   - **2D Spline (X, Y only)** – Creates a sketch spline on a selected plane
   - **3D Spline (X, Y, Z)** – Creates a 3D curve in space
4. For 2D splines, select a construction plane or planar face when prompted.
5. Enter coordinates:
   - **X coordinates** – Space or comma-separated values (e.g., `0, 1, 2.5, 4`)
   - **Y coordinates** – Must match the number of X values
   - **Z coordinates** – Required for 3D splines only
6. Click **OK** – the spline is created with the specified points.

---

## Example

### 2D Spline on XY Plane

```
X: 0, 10, 20, 30, 40
Y: 0, 5, 8, 5, 0
```

Creates a smooth curve through these 5 points on your selected plane.

### 3D Spline

```
X: 0, 10, 20, 30
Y: 0, 5, 10, 15
Z: 0, 2, 4, 6
```

Creates a 3D curve through these 4 points in space.

---

## Use Cases

- **Blueprint Tracing** – Digitize curves from technical drawings by measuring key points
- **Data Import** – Import coordinate data from spreadsheets or calculations
- **Custom Profiles** – Create complex profiles for extrusions, lofts, or sweeps
- **Reverse Engineering** – Recreate curves from measured physical parts

---

## Technical Notes

- Uses Fusion 360's native **Fit Point Spline** functionality for smooth interpolation
- 2D splines are created as sketch entities for easy editing
- 3D splines are created as 3D curves in the root component
- All coordinates are in the current document units (cm by default)
- Minimum 2 points required for spline creation

---

## License

MIT + NoAI – see [LICENSE](LICENSE).
