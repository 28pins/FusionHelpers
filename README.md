# FusionHelpers

A collection of utilities and add-ins for Autodesk Fusion 360, designed to streamline CAD workflows and extend Fusion's capabilities.

---

## What's Included

### 1. GearGenerator – Parametric Gear Add-In

A powerful parametric gear generator supporting six different gear types with Imperial/Metric units and FDM 3D printing optimization.

**Gear Types:**
- Spur (External)
- Helical (External)
- Internal (Ring)
- Rack
- Bevel (Straight)
- Worm Set

**Features:**
- Imperial (Diametral Pitch) and Metric (Module) units
- Customizable parameters: teeth count, pressure angle, backlash, bore diameter
- Built-in FDM 3D printing presets (0.2mm to 0.8mm nozzles)
- Fully parametric design using stable Fusion 360 API

📁 [View GearGenerator Documentation](addins/GearGenerator/README.md)

---

### 2. BlueprintSplineHelper – Coordinate Spline Creator

A utility script for creating 2D and 3D splines from coordinate points. Perfect for tracing blueprints, importing data, or reverse engineering curves.

**Features:**
- Create 2D splines on construction planes or planar faces
- Create 3D freeform splines in space
- Input coordinates as comma or space-separated values
- Automatic fit point spline interpolation

📁 [View BlueprintSplineHelper Documentation](addins/BlueprintSplineHelper/README.md)

---

## Quick Start

### Installation

1. **Download this repository:**
   ```bash
   git clone https://github.com/28pins/FusionHelpers.git
   ```
   Or download as ZIP and extract.

2. **Open Fusion 360's Scripts and Add-Ins panel:**
   - Press **Shift+S** or go to **Tools → Add-Ins → Scripts and Add-Ins**

3. **Install the tools:**

   **For GearGenerator (Add-In):**
   - Click the **Add-Ins** tab
   - Click the **+** icon next to *My Add-Ins*
   - Navigate to `addins/GearGenerator/` and click **Select**
   - Check **Run on Startup** (optional), then click **Run**
   - The Gear Generator button appears in **Solid → Create** panel

   **For BlueprintSplineHelper (Script):**
   - Click the **Scripts** tab
   - Click the **+** icon next to *My Scripts*
   - Navigate to `addins/BlueprintSplineHelper/` and click **Select**
   - Select it from the list and click **Run** when needed

---

## Requirements

- **Autodesk Fusion 360** (any recent version with Python 3 support)
- **Operating System:** Windows, macOS, or Linux (via Fusion web)
- **No external dependencies** – all tools use only built-in Fusion 360 Python API

---

## Usage Examples

### Creating a Spur Gear

1. Run **GearGenerator** from the Create panel
2. Select "Spur (External)" from gear type dropdown
3. Set parameters:
   - Number of Teeth: 24
   - Module: 2.0 mm (or Diametral Pitch: 12)
   - Pressure Angle: 20°
   - Face Width: 10 mm
4. Enable "3-D Print Optimisation" if printing (select nozzle size)
5. Click **OK** – gear component is created

### Tracing a Blueprint Curve

1. Run **BlueprintSplineHelper** script
2. Choose "2D Spline (X, Y only)"
3. Select your blueprint image plane or construction plane
4. Measure and enter X coordinates: `0, 5, 10, 15, 20`
5. Enter corresponding Y coordinates: `0, 3, 8, 7, 2`
6. Click **OK** – spline is created through the points

---

## Project Structure

```
FusionHelpers/
├── LICENSE                          # MIT + NoAI license for the project
├── README.md                        # This file
└── addins/
    ├── GearGenerator/              # Parametric gear generator add-in
    │   ├── LICENSE                 # Component-specific license
    │   ├── README.md               # Detailed documentation
    │   ├── GearGenerator.py        # Main add-in entry point
    │   └── gearlib/                # Gear calculation library
    │       ├── __init__.py
    │       ├── spur.py             # Spur gear logic
    │       ├── helical.py          # Helical gear logic
    │       ├── internal.py         # Internal gear logic
    │       ├── rack.py             # Rack gear logic
    │       ├── bevel.py            # Bevel gear logic
    │       ├── worm.py             # Worm set logic
    │       └── utils.py            # Shared utilities
    │
    └── BlueprintSplineHelper/      # Coordinate spline creator script
        ├── LICENSE                 # Component-specific license
        ├── README.md               # Detailed documentation
        └── BlueprintSplineHelper.py # Main script
```

---

## Contributing

Contributions are welcome! If you have ideas for new tools, improvements, or bug fixes:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-tool`)
3. Commit your changes (`git commit -m 'Add amazing tool'`)
4. Push to the branch (`git push origin feature/amazing-tool`)
5. Open a Pull Request

Please ensure:
- Code follows existing style and conventions
- Documentation is updated for any new features
- Testing has been done in Fusion 360

---

## Support & Issues

If you encounter problems or have questions:

- **Check the documentation** in each tool's README
- **Open an issue** on GitHub with details about your problem
- **Include:** Fusion 360 version, operating system, and steps to reproduce

---

## License

This project is licensed under the **MIT License with NoAI clause**.

See [LICENSE](LICENSE) for full terms. Each component includes its own LICENSE file with identical terms.

**Key points:**
- ✅ Free to use, modify, and distribute
- ✅ Commercial use allowed
- ✅ Must include license and copyright notice
- ❌ Cannot be used for training AI/ML models or LLMs

---

## Acknowledgments

- Built using the [Autodesk Fusion 360 API](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-A92A4B10-3781-4925-94C6-47DA85A4F65A)
- Gear mathematics based on standard involute gear theory
- Inspired by the Fusion 360 community's need for parametric design tools

---

## Roadmap

Future enhancements under consideration:
- Planetary gear set generator
- Belt and pulley designer
- Spline import from CSV/JSON files
- Additional tooth profiles (cycloidal, pin gears)

Have ideas? Open an issue or submit a pull request!

---

**Made with ❤️ for the Fusion 360 community**
