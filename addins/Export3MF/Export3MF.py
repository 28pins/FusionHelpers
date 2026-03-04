import os
import adsk.core
import adsk.fusion
import adsk.cam
import traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Get the active design.
        design = app.activeProduct
        if not isinstance(design, adsk.fusion.Design):
            ui.messageBox('No active Fusion 360 design')
            return

        # Prompt the user for a folder name.
        folder_name, cancelled = ui.inputBox('Enter a folder name for 3MF exports:', 'Export Folder Name', '')
        if cancelled or not folder_name:
            ui.messageBox('No folder name provided')
            return

        # Determine the Downloads directory.
        downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads', folder_name)
        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir)

        # Get all selected bodies.
        export_mgr = design.exportManager
        active_selections = ui.activeSelections
        selected_bodies = [sel.entity for sel in active_selections if isinstance(sel.entity, adsk.fusion.BRepBody)]

        if not selected_bodies:
            ui.messageBox('No bodies selected for export')
            return

        # Export each body.
        used_names = {}
        for body in selected_bodies:
            # Sanitize the body name to remove characters invalid on common file systems.
            safe_name = ''.join(c if c not in r'\/:*?"<>|' else '_' for c in body.name)
            # Handle duplicate names by appending a numeric suffix.
            if safe_name in used_names:
                used_names[safe_name] += 1
                safe_name = f'{safe_name}_{used_names[safe_name]}'
            else:
                used_names[safe_name] = 0
            file_path = os.path.join(downloads_dir, f'{safe_name}.3mf')
            options = export_mgr.createC3MFExportOptions(body, file_path)
            export_mgr.execute(options)

        ui.messageBox(f'Exported {len(selected_bodies)} bodies to {downloads_dir}')

    except Exception:
        if ui:
            ui.messageBox(f'Failed:\n{traceback.format_exc()}')
