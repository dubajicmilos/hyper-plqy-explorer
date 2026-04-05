"""
HyperPLQY Explorer -- Interactive power-dependent PLQY visualization.

Load a PLQY HDF5 cube (PLQY vs excitation intensity at every pixel),
draw rectangular ROIs on the spatial map, and instantly see PLQY vs
excitation intensity curves for each selected region.

Usage:
    python plqy_explorer.py                              # default file
    python plqy_explorer.py --file my_plqy_data.h5       # custom file

Controls:
    - Click-drag on the left panel to draw ROI rectangles
    - Each ROI plots a PLQY vs suns curve on the right panel
    - Slider changes which excitation intensity is displayed on the map
    - "Clear ROIs" button removes all selections

HDF5 file format:
    Required datasets:
        PLQY_percent    (n_intensities, H, W)   PLQY in % at each pixel
        suns            (n_intensities,)         excitation intensity values
    Optional datasets:
        saturation_valid (n_intensities, H, W)   boolean validity mask
        masks/           group with named masks   e.g. 'Crystal (all)'
"""

import argparse
import sys
import h5py
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider
from matplotlib.patches import Rectangle

# Use TkAgg if available, fall back to default
try:
    matplotlib.use('TkAgg')
except Exception:
    pass

ROI_COLORS = [
    '#e6194b', '#3cb44b', '#4363d8', '#f58231', '#911eb4',
    '#42d4f4', '#f032e6', '#bfef45', '#fabed4', '#469990',
    '#dcbeff', '#9A6324', '#800000', '#aaffc3', '#808000',
]


class PLQYExplorer:
    """Interactive matplotlib GUI for exploring power-dependent PLQY cubes."""

    def __init__(self, h5_path):
        print(f"Loading {h5_path} ...")
        with h5py.File(h5_path, 'r') as f:
            self.plqy = f['PLQY_percent'][:]
            self.suns = f['suns'][:]
            self.sat_valid = None
            if 'saturation_valid' in f:
                self.sat_valid = f['saturation_valid'][:]

        self.n_suns, self.H, self.W = self.plqy.shape
        print(f"  Cube: {self.plqy.shape}, suns: {self.suns[0]:.1f} to {self.suns[-1]:.1f}")

        self.rois = []
        self.roi_patches = []
        self.roi_lines = []
        self.roi_labels = []
        self._dragging = False
        self._drag_start = None
        self._rubber_rect = None
        self._sun_idx = np.argmin(np.abs(self.suns - 27.0))

        self._build_gui()

    def _build_gui(self):
        self.fig = plt.figure(figsize=(15, 7))
        self.fig.canvas.manager.set_window_title('HyperPLQY Explorer')

        gs = self.fig.add_gridspec(2, 2, height_ratios=[12, 1],
                                   width_ratios=[1, 1], hspace=0.25, wspace=0.3)
        self.ax_map = self.fig.add_subplot(gs[0, 0])
        self.ax_plot = self.fig.add_subplot(gs[0, 1])
        ax_slider = self.fig.add_subplot(gs[1, 0])
        ax_btn = self.fig.add_subplot(gs[1, 1])

        self._draw_map()

        self.ax_plot.set_xlabel('Excitation intensity (suns)')
        self.ax_plot.set_ylabel('PLQY (%)')
        self.ax_plot.set_title('Mean PLQY vs suns (draw rectangles on map)')
        self.ax_plot.grid(True, alpha=0.3)

        self.slider = Slider(ax_slider, 'Display suns',
                             0, self.n_suns - 1,
                             valinit=self._sun_idx, valstep=1,
                             valfmt='%.0f')
        self.slider.on_changed(self._on_slider)
        ax_slider.set_title(f'Showing: {self.suns[self._sun_idx]:.1f} suns',
                            fontsize=9, loc='left')

        ax_btn.set_visible(False)
        ax_clear = self.fig.add_axes([0.75, 0.02, 0.1, 0.04])
        self.btn_clear = Button(ax_clear, 'Clear ROIs', color='lightsalmon',
                                hovercolor='salmon')
        self.btn_clear.on_clicked(self._on_clear)

        self.fig.canvas.mpl_connect('button_press_event', self._on_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.fig.canvas.mpl_connect('button_release_event', self._on_release)

    def _get_display_image(self):
        return self.plqy[self._sun_idx].copy()

    def _draw_map(self):
        self.ax_map.clear()
        img = self._get_display_image()
        vmin, vmax = np.percentile(img, [3, 97])
        self._map_im = self.ax_map.imshow(img, origin='lower', cmap='inferno',
                                           vmin=vmin, vmax=vmax, aspect='equal')
        self.ax_map.set_title(f'PLQY at {self.suns[self._sun_idx]:.1f} suns  '
                              f'[click-drag to select ROI]')
        self.ax_map.axis('off')
        self.roi_patches.clear()
        self.roi_labels.clear()
        for i, (y0, y1, x0, x1) in enumerate(self.rois):
            color = ROI_COLORS[i % len(ROI_COLORS)]
            rect = Rectangle((x0, y0), x1 - x0, y1 - y0,
                              linewidth=2, edgecolor=color,
                              facecolor=color, alpha=0.15)
            self.ax_map.add_patch(rect)
            self.roi_patches.append(rect)
            lbl = self.ax_map.text(x0 + 2, y1 - 5, f'R{i+1}',
                                   color=color, fontsize=9, fontweight='bold')
            self.roi_labels.append(lbl)

    def _on_slider(self, val):
        self._sun_idx = int(val)
        self._draw_map()
        self.slider.ax.set_title(f'Showing: {self.suns[self._sun_idx]:.1f} suns',
                                 fontsize=9, loc='left')
        self.fig.canvas.draw_idle()

    def _on_clear(self, event):
        self.rois.clear()
        self.roi_patches.clear()
        self.roi_labels.clear()
        self.roi_lines.clear()
        self._draw_map()
        self.ax_plot.clear()
        self.ax_plot.set_xlabel('Excitation intensity (suns)')
        self.ax_plot.set_ylabel('PLQY (%)')
        self.ax_plot.set_title('Mean PLQY vs suns (draw rectangles on map)')
        self.ax_plot.grid(True, alpha=0.3)
        self.fig.canvas.draw_idle()

    def _on_press(self, event):
        if event.inaxes != self.ax_map or event.button != 1:
            return
        self._dragging = True
        self._drag_start = (event.xdata, event.ydata)
        self._rubber_rect = Rectangle((event.xdata, event.ydata), 0, 0,
                                       linewidth=1.5, edgecolor='white',
                                       facecolor='white', alpha=0.2,
                                       linestyle='--')
        self.ax_map.add_patch(self._rubber_rect)

    def _on_motion(self, event):
        if not self._dragging or event.inaxes != self.ax_map:
            return
        x0, y0 = self._drag_start
        self._rubber_rect.set_xy((min(x0, event.xdata), min(y0, event.ydata)))
        self._rubber_rect.set_width(abs(event.xdata - x0))
        self._rubber_rect.set_height(abs(event.ydata - y0))
        self.fig.canvas.draw_idle()

    def _on_release(self, event):
        if not self._dragging:
            return
        self._dragging = False

        if self._rubber_rect is not None:
            self._rubber_rect.remove()
            self._rubber_rect = None

        if event.inaxes != self.ax_map:
            self.fig.canvas.draw_idle()
            return

        x0, y0 = self._drag_start
        x1, y1 = event.xdata, event.ydata

        px0, px1 = sorted([int(round(x0)), int(round(x1))])
        py0, py1 = sorted([int(round(y0)), int(round(y1))])
        px0 = max(0, px0)
        py0 = max(0, py0)
        px1 = min(self.W - 1, px1)
        py1 = min(self.H - 1, py1)

        if (px1 - px0) < 3 or (py1 - py0) < 3:
            self.fig.canvas.draw_idle()
            return

        self.rois.append((py0, py1, px0, px1))
        roi_idx = len(self.rois) - 1
        color = ROI_COLORS[roi_idx % len(ROI_COLORS)]

        rect = Rectangle((px0, py0), px1 - px0, py1 - py0,
                          linewidth=2, edgecolor=color,
                          facecolor=color, alpha=0.15)
        self.ax_map.add_patch(rect)
        self.roi_patches.append(rect)
        lbl = self.ax_map.text(px0 + 2, py1 - 5, f'R{roi_idx+1}',
                               color=color, fontsize=9, fontweight='bold')
        self.roi_labels.append(lbl)

        plqy_vs_suns = np.zeros(self.n_suns)
        n_pixels = (py1 - py0) * (px1 - px0)
        for i in range(self.n_suns):
            region = self.plqy[i, py0:py1, px0:px1]
            plqy_vs_suns[i] = np.mean(region)

        line, = self.ax_plot.plot(self.suns[1:], plqy_vs_suns[1:], 'o-',
                                  color=color, markersize=5, linewidth=1.5,
                                  label=f'R{roi_idx+1} ({n_pixels} px)')
        self.ax_plot.plot(self.suns[0], plqy_vs_suns[0], 'o',
                          color=color, markersize=7,
                          markerfacecolor='none', markeredgewidth=1.5)
        self.roi_lines.append(line)
        self.ax_plot.legend(fontsize=8, loc='upper left')
        self.ax_plot.set_title('Mean PLQY vs suns per ROI')

        self.fig.canvas.draw_idle()

    def show(self):
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description='HyperPLQY Explorer - Interactive power-dependent PLQY visualization')
    parser.add_argument('--file', default='PLQY_absolute_vs_suns.h5',
                        help='Path to PLQY HDF5 file (default: PLQY_absolute_vs_suns.h5)')
    args = parser.parse_args()

    explorer = PLQYExplorer(args.file)
    explorer.show()


if __name__ == '__main__':
    main()
