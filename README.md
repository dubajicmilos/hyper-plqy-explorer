# HyperPLQY Explorer

Interactive visualization of spatially-resolved, power-dependent photoluminescence quantum yield (PLQY) from hyperspectral imaging data.

Draw rectangular regions of interest on a PLQY map and instantly see how quantum yield varies with excitation intensity for each region.

## Quick start

```bash
pip install -r requirements.txt
python plqy_explorer.py --file PLQY_absolute_vs_suns.h5
```

## Demo data

A sample dataset (`PLQY_absolute_vs_suns.h5`, 62 MB) of a CsPbBr3 single crystal measured at 20 excitation intensities (1-100 suns) is available as a GitHub Release:

**[Download from Releases](https://github.com/dubajicmilos/hyper-plqy-explorer/releases/latest)**

Download the `.h5` file, place it in this directory, and run:

```bash
python plqy_explorer.py
```

## How to use

| Action | What happens |
|--------|-------------|
| Click-drag on the map | Draws an ROI rectangle |
| Slider (bottom) | Changes which excitation intensity is displayed |
| Clear ROIs button | Removes all rectangles and curves |

Each ROI is color-coded and its mean PLQY vs excitation curve appears on the right panel. The 1-sun point is shown as an open circle (near lasing threshold, potentially unreliable).

## HDF5 file format

The explorer reads an HDF5 file with the following structure:

```
PLQY_percent        (n_intensities, H, W)    float    PLQY in % at each pixel
suns                (n_intensities,)          float    excitation intensity values
saturation_valid    (n_intensities, H, W)    bool     [optional] pixel validity mask
masks/              group                             [optional] named spatial masks
```

### Creating your own data

To use this tool with your own data, create an HDF5 file with at least `PLQY_percent` and `suns` datasets:

```python
import h5py
import numpy as np

with h5py.File('my_plqy_data.h5', 'w') as f:
    f.create_dataset('PLQY_percent', data=plqy_cube)  # shape: (n_powers, H, W)
    f.create_dataset('suns', data=suns_array)          # shape: (n_powers,)
```

## How the PLQY data was generated

1. **Photometric hyperspectral cube** (Photon etc. IMA, 100x objective, 480-570 nm) measured at 27 suns CW 405 nm excitation, calibrated to absolute units: photons/(eV s cm^2 sr).
2. **Spectral integration** per pixel over energy, multiplied by 2*pi (hemisphere, isotropic assumption) to get total photon flux.
3. **Calibration constant** k established by registering the spectrally-integrated map to a broadband image at the same excitation, giving k = photons/(cm^2 per detector count).
4. **Applied to 20 broadband images** at 1-100 suns (background-subtracted, sub-pixel registered).
5. **PLQY = emitted photon flux / (absorbed photon flux) x 100%**, assuming 80% absorption.

Full method documentation: see `PLQY_calculation_method.md` in the data repository.

## Dependencies

- Python 3.9+
- numpy
- matplotlib (with TkAgg or another interactive backend)
- h5py

## License

MIT
