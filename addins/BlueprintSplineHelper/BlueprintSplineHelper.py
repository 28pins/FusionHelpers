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
        dropdown_items = ["2D Spline (X, Y only)", "3D Spline (X, Y, Z)"]
        selected_option = ui.inputBox(
            "Choose the type of spline you want to create:\n1. 2D Spline (On a selected plane)\n2. 3D Spline (Freeform in 3D space)", 
            "Spline Type Selection", 
            dropdown_items[0], 
            dropdown_items
        )
        if not selected_option:
            ui.messageBox("No selection made. Exiting script.")
            return
        
        # Determine if the selection is for 2D or 3D
        is_3D = selected_option == dropdown_items[1]  # True if 3D Spline is selected

        # If 2D, allow the user to select a plane (not needed for 3D)
        selected_plane = None
        if not is_3D:
            plane_selection = ui.selectEntity("Select a construction plane or existing planar face for the 2D spline.", ["PlanarFaces", "ConstructionPlanes"])
            if not plane_selection:
                ui.messageBox("No plane selected. Exiting script.")
                return
            selected_plane = plane_selection.entity

        # Ask for X and Y points (and Z if 3D is selected)
        x_input = ui.inputBox(
            "Enter a list of X-coordinates, separated by spaces or commas (e.g. 0 1 2):",
            "Input X Points",
            "0,1,2"
        )
        if not x_input:
            ui.messageBox("No X points entered. Exiting script.")
            return

        y_input = ui.inputBox(
            "Enter a list of Y-coordinates, separated by spaces or commas (e.g. 0 1 2):",
            "Input Y Points",
            "0,1,2"
        )
        if not y_input:
            ui.messageBox("No Y points entered. Exiting script.")
            return

        z_input = []
        if is_3D:
            z_input_str = ui.inputBox(
                "Enter a list of Z-coordinates (for 3D splines), separated by spaces or commas (e.g. 0 0 1):",
                "Input Z Points",
                "0,0,0"
            )
            if not z_input_str:
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
            z_points = parse_input(z_input)
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
        
        # Access the root component
        root_comp = design.rootComponent

        # Create a new sketch for 2D or direct curves for 3D
        if not is_3D:  # 2D Spline
            sketch = root_comp.sketches.add(selected_plane)
            sketch.sketchCurves.sketchFittedSplines.add(points)
        else:  # 3D Spline
            # Add the 3D Spline directly using the root component's 3D curves API
            splines = root_comp.splineCurves
            splines.add(points)
        
        # Display success message
        spline_type = "3D" if is_3D else "2D"
        ui.messageBox(f"A {spline_type} Fit Point Spline has been successfully created with {len(points)} points!")

    except Exception as e:
        if ui:
            ui.messageBox(f"Failed:\n{traceback.format_exc()}")
