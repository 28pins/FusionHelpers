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
            ui.messageBox('No name, no magic. Please enter a folder name to continue.')
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
            # No pre-selected bodies – collect all visible bodies in the design.
            all_bodies = []
            for component in design.allComponents:
                for body in component.bRepBodies:
                    if body.isVisible:
                        all_bodies.append(body)

            if not all_bodies:
                ui.messageBox('I couldn’t find any visible bodies in this design to share with you.')
                return

            result = ui.messageBox(
                f'No bodies are currently selected.\n\n'
                f'Found {len(all_bodies)} visible {"body" if len(all_bodies) == 1 else "bodies"} in the design.\n\n'
                f'Click OK to export all bodies, or Cancel to abort.\n\n'
                f'Tip: to export specific bodies only, select them in the\n'
                f'canvas before running this add-in, then run it again.',
                'Export All Bodies?',
                adsk.core.MessageBoxButtonTypes.OKCancelButtonType,
                adsk.core.MessageBoxIconTypes.QuestionIconType)
            if result != adsk.core.DialogResults.DialogOK:
                return
            selected_bodies = all_bodies

        # Helper to create 3MF export options in a way that matches the
        # available Fusion API surface on macOS and Windows.
        def _create_3mf_options(body, file_path):
            bodies = adsk.core.ObjectCollection.create()
            bodies.add(body)
            component = getattr(body, 'parentComponent', None)
            factories = []

            # Preferred APIs first (C3MF on macOS, 3MF elsewhere), with fallbacks
            if hasattr(export_mgr, 'createC3MFExportOptions'):
                factories.append(export_mgr.createC3MFExportOptions)
            if hasattr(export_mgr, 'create3MFExportOptions'):
                factories.append(export_mgr.create3MFExportOptions)
            if hasattr(export_mgr, 'createMeshExportOptions'):
                # Mesh export can also target 3MF when other factories are missing
                def _mesh_factory(target, path=None):
                    try:
                        return export_mgr.createMeshExportOptions(
                            target,
                            path,
                            adsk.fusion.MeshFileFormat.MeshFileFormat3MF)
                    except Exception:
                        return export_mgr.createMeshExportOptions(target, path)
                factories.append(_mesh_factory)

            # Try each factory with (target, path) then (target) to handle
            # differing overloads between platforms.
            for factory in factories:
                for target in (bodies, component) if component else (bodies,):
                    try:
                        opts = factory(target, file_path)
                    except Exception as exc:
                        print(f'[Export3MF] Factory {getattr(factory, "__name__", factory)} with path failed: {exc}')
                        try:
                            opts = factory(target)
                        except Exception as exc2:
                            print(f'[Export3MF] Factory {getattr(factory, "__name__", factory)} without path failed: {exc2}')
                            opts = None
                    if opts:
                        try:
                            opts.filename = file_path
                        except Exception as exc:
                            print(f'[Export3MF] Unable to set filename: {exc}')
                        try:
                            opts.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
                        except Exception as exc:
                            print(f'[Export3MF] Unable to set mesh refinement: {exc}')
                        try:
                            opts.sendToPrintUtility = False
                        except Exception as exc:
                            print(f'[Export3MF] Unable to disable print utility: {exc}')
                        return opts
            return None

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
            options = _create_3mf_options(body, file_path)
            if not options:
                ui.messageBox('Hmm… I tried a few different export paths, but 3MF isn’t available here.')
                return
            export_mgr.execute(options)

        ui.messageBox(f'Exported {len(selected_bodies)} bodies to {downloads_dir}')

    except Exception:
        if ui:
            ui.messageBox(f'Failed:\n{traceback.format_exc()}')
