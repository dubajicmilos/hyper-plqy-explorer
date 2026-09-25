# HyperPLQY Explorer

Interactive visualization of spatially resolved, power-dependent photoluminescence quantum yield (PLQY) from hyperspectral imaging data.

Draw rectangular regions of interest (ROIs) on a PLQY map to see how the PLQY of each region varies with excitation intensity.

## Quick start

```bash
pip install -r requirements.txt
python plqy_explorer.py --file PLQY_absolute_vs_suns.h5
```

Alternatively, open `explore_plqy.ipynb` in Jupyter. The notebook lets you define ROIs by pixel coordinates and plots PLQY maps and histograms, as well as the PLQY of single pixels as a function of excitation intensity.

## Demo data

A sample dataset (`PLQY_absolute_vs_suns.h5`, 62 MB) from a CsPbBr3 single crystal measured at 20 excitation intensities (1-100 suns) is available from the [latest GitHub release](https://github.com/dubajicmilos/hyper-plqy-explorer/releases/latest). Download the `.h5` file, place it in this directory, and run:

```bash
python plqy_explorer.py
```

## How to use

| Action | What happens |
|--------|-------------|
| Click-drag on the map | Draws an ROI rectangle |
| Slider (bottom) | Changes which excitation intensity is displayed |
| Clear ROIs button | Removes all rectangles and curves |

Each ROI is color-coded; its mean PLQY vs excitation intensity curve is plotted in the same color in the right panel. The 1-sun point is shown as an open circle because it is near the lasing threshold and may be unreliable.

## HDF5 file format

The explorer reads an HDF5 file with the following structure:

```
PLQY_percent        (n_intensities, H, W)    float    PLQY in % at each pixel
suns                (n_intensities,)          float    excitation intensity values
saturation_valid    (n_intensities, H, W)    bool     [optional] pixel validity mask
masks/              group                             [optional] named spatial masks
```

## How the PLQY data was generated

1. A photometric hyperspectral cube (Photon etc. IMA, 100x objective, 480-570 nm) was measured at 27 suns under CW 405 nm excitation and calibrated to absolute units of photons/(eV s cm^2 sr).
2. For each pixel, the spectrum was integrated over energy and multiplied by 2*pi (the solid angle of a hemisphere, assuming isotropic emission) to give the total emitted photon flux.
3. Registering the spectrally integrated map to a broadband image recorded under the same excitation gave the calibration constant k = photons/(cm^2 per detector count).
4. The constant k was then applied to 20 broadband images recorded at 1-100 suns, after background subtraction and sub-pixel registration.
5. The PLQY was calculated as PLQY = emitted photon flux / (absorbed photon flux) x 100%, assuming 80% absorption.

### Absorption estimate

The 80% absorption assumption was checked using the optical constants of single-crystal MAPbBr3 (Leguy et al.) as a proxy for CsPbBr3. At 405 nm, the refractive index is n = 2.47 and the extinction coefficient is k = 0.321, which gives an absorption coefficient of ~10^5 cm^-1. For a 220 nm thick crystal with 10% surface reflectance, the Beer-Lambert law gives 80.0% total absorption of the incident light. The 1/e penetration depth at 405 nm is ~100 nm, so most of the light that enters the crystal is absorbed within it.

The PLQY values use the isotropic hemisphere assumption (2*pi solid angle factor). If the emission is Lambertian (pi), all PLQY values would be a factor of 2 lower.


## Dependencies

- Python 3.9+
- numpy
- matplotlib (with TkAgg or another interactive backend)
- h5py

## License

MIT
