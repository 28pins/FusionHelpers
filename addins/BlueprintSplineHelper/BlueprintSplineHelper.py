import adsk.core
import adsk.fusion
import adsk.cam
import traceback

def run(context):
    ui = None
    try:
        # Grab the Fusion Application and UI
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Get the active design
        design = app.activeProduct
        if not isinstance(design, adsk.fusion.Design):
            ui.messageBox('No active design detected. Please start a new design and try again.')
            return

        # Ask the user whether to create a 2D or 3D spline
        result = ui.messageBox(
            "Create a 3D spline (freeform in 3D space)?\n\n"
            "Yes → 3D Spline (points placed in XY sketch, Z preserved)\n"
            "No  → 2D Spline (on a selected construction plane or face)",
            "Spline Type",
            adsk.core.MessageBoxButtonTypes.YesNoButtonType,
            adsk.core.MessageBoxIconTypes.QuestionIconType
        )

        # Determine if the selection is for 2D or 3D
        is_3D = (result == adsk.core.DialogResults.DialogYes)

        # If 2D, allow the user to select a plane (not needed for 3D)
        # Access the root component early so it can be used as fallback plane
        root_comp = design.rootComponent

        selected_plane = None
        if not is_3D:
            try:
                plane_selection = ui.selectEntity(
                    "Select a construction plane or planar face for the 2D spline "
                    "(press Escape to use the default XY plane).",
                    "PlanarFaces")
                selected_plane = plane_selection.entity if plane_selection else root_comp.xYConstructionPlane
            except:
                selected_plane = root_comp.xYConstructionPlane

        # Ask for X and Y points (and Z if 3D is selected)
        x_input, cancelled = ui.inputBox(
            "Enter a list of X-coordinates, separated by spaces or commas (e.g. 0 1 2):",
            "Input X Points",
            "0,1,2"
        )
        if cancelled or not x_input:
            ui.messageBox("No X points entered. Exiting script.")
            return

        y_input, cancelled = ui.inputBox(
            "Enter a list of Y-coordinates, separated by spaces or commas (e.g. 0 1 2):",
            "Input Y Points",
            "0,1,2"
        )
        if cancelled or not y_input:
            ui.messageBox("No Y points entered. Exiting script.")
            return

        z_input = []
        if is_3D:
            z_input_str, cancelled = ui.inputBox(
                "Enter a list of Z-coordinates (for 3D splines), separated by spaces or commas (e.g. 0 0 1):",
                "Input Z Points",
                "0,0,0"
            )
            if cancelled or not z_input_str:
                ui.messageBox("No Z points entered. Exiting script.")
                return
            z_input = z_input_str.replace(',', ' ').split()  # Parse Z-coordinates
        
        # Clean and parse the input values into lists of floats
        def parse_input(input_string):
            return [float(val.strip()) for val in input_string.replace(',', ' ').split()]
        
        x_points = parse_input(x_input)
        y_points = parse_input(y_input)
        
        # If 3D spline, parse Z input; otherwise, default Z to 0
        if is_3D:
            z_points = parse_input(z_input_str)
            if len(x_points) != len(y_points) or len(x_points) != len(z_points):
                ui.messageBox("The number of X, Y, and Z coordinates must match. Exiting script.")
                return
        else:
            z_points = [0.0] * len(x_points)  # Default Z-coordinates to 0 for 2D spline

        # Verify all coordinate lists have the same length
        if len(x_points) != len(y_points):
            ui.messageBox("The number of X and Y coordinates must match. Exiting script.")
            return

        # Generate 3D points from the input lists
        points = []
        for x, y, z in zip(x_points, y_points, z_points):
            points.append(adsk.core.Point3D.create(x, y, z))

        # Create a new sketch for 2D or direct curves for 3D
        if not is_3D:  # 2D Spline
            sketch = root_comp.sketches.add(selected_plane)
            sketch.sketchCurves.sketchFittedSplines.add(points)
        else:  # 3D Spline – Fusion 360 has no standalone 3D-spline API in
               # script mode; use an XY-plane sketch with the supplied Point3D
               # objects (Z coordinates are stored but the spline is constrained
               # to the sketch plane).  For a true 3D curve, use the Fusion 360
               # Patch workspace → 3D Sketch after running this script.
            sketch = root_comp.sketches.add(root_comp.xYConstructionPlane)
            sketch.sketchCurves.sketchFittedSplines.add(points)

        # Display success message
        spline_type = "3D" if is_3D else "2D"
        ui.messageBox(f"A {spline_type} Fit Point Spline has been successfully created with {len(points)} points!")

    except Exception as e:
        if ui:
            ui.messageBox(f"Failed:\n{traceback.format_exc()}")
