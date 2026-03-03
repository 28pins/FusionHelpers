# Export3MF – Fusion 360 Script

A utility script for Autodesk Fusion 360 that exports selected bodies as `.3mf` files into a subfolder of the user's `Downloads` directory.

---

## Features

- **Multiple Body Selection** – Export one or more bodies in a single run
- **Export to Downloads Subfolder** – Files are saved to `~/Downloads/<folder_name>/`
- **Automatic Folder Creation** – Creates the target folder if it does not already exist

---

## Installation

1. Download or clone this repository.
2. In Fusion 360, open **Tools → Add-Ins → Scripts and Add-Ins** (keyboard shortcut **Shift+S**).
3. Click the **Scripts** tab, then the **+** icon next to *My Scripts*.
4. Navigate to the `addins/Export3MF/` folder and click **Select**.
5. The script appears in the list – select it and click **Run**.

### Requirements

- Autodesk Fusion 360 (any recent version with Python 3 script support)
- No external Python packages required

---

## Usage

1. Open a Fusion 360 design containing the bodies you want to export.
2. Select the bodies you want to export in the viewport or browser.
3. Run the **Export3MF** script from the Scripts and Add-Ins panel.
4. When prompted, enter a folder name (e.g. `my_parts`).
5. The script creates `~/Downloads/my_parts/` and exports each selected body as `<body_name>.3mf`.
6. A confirmation message reports how many bodies were exported and the destination path.

---

## Example

Select three bodies named `Base`, `Lid`, and `Clip`, then run the script and enter `enclosure_v1` as the folder name.

The following files are created:

```
~/Downloads/enclosure_v1/
├── Base.3mf
├── Lid.3mf
└── Clip.3mf
```

---

## Technical Notes

- Uses Fusion 360's native `exportManager.create3MFExportOptions` API for reliable 3MF output
- Each body is exported individually so files can be imported into slicers one at a time
- The destination folder path is printed in the confirmation dialog for easy reference

---

## License

MIT + NoAI – see [LICENSE](LICENSE).
