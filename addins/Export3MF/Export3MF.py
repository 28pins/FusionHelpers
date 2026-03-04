import os
import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import re

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
        # Build default folder name: acronym from design name + version number
        doc = app.activeDocument
        # get design/document name
        name = ''
        if hasattr(design, 'name') and design.name:
            name = design.name
        elif doc and hasattr(doc, 'name') and doc.name:
            name = doc.name
        else:
            name = 'Export'

        # acronym = concatenation of uppercase letters; fallback to first two letters
        acronym = ''.join([c for c in name if c.isupper()])
        if len(acronym) < 2:
            acronym = ''.join([c for c in name if c.isalnum()])[:2].upper() or 'AA'

        # try to get version number from document/data file or design
        def _get_version(obj):
            if not obj:
                return None
            for attr in ('versionNumber', 'version', 'getVersion', 'versionId', 'version_id'):
                val = getattr(obj, attr, None)
                if callable(val):
                    try:
                        val = val()
                    except:
                        val = None
                if val:
                    return str(val)
            return None

        version = _get_version(getattr(doc, 'dataFile', None)) or _get_version(doc) or _get_version(design) or '1'
        m = re.search(r'\d+', version)
        version_num = m.group(0) if m else version

        default_folder = f'{acronym}_v{version_num}'
        folder_name, cancelled = ui.inputBox('Enter a folder name for 3MF exports:', 'Export Folder Name', default_folder)
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
            # Let the user select some:
            # Prompt the user to select one or more bodies
            try:
                sel_result = ui.selectEntities('Select bodies to export (Ctrl+Click to select multiple):', 'Bodies')
            except:
                sel_result = None

            # Handle different possible return shapes: some API versions return a tuple (collection, cancelled)
            sel_collection = None
            cancelled = False
            if isinstance(sel_result, tuple) or isinstance(sel_result, list):
                if len(sel_result) >= 1:
                    sel_collection = sel_result[0]
                if len(sel_result) >= 2:
                    cancelled = bool(sel_result[1])
            else:
                sel_collection = sel_result

            if cancelled or not sel_collection or getattr(sel_collection, 'count', 0) == 0:
                ui.messageBox('No bodies selected')
                return

            selected_bodies = []
            for i in range(sel_collection.count):
                sel = sel_collection.item(i)
                ent = getattr(sel, 'entity', None)
                if isinstance(ent, adsk.fusion.BRepBody):
                    selected_bodies.append(ent)

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
