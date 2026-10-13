# Counterfeit Hologram Detector

A portable-camera research prototype for distinguishing original security holograms from duplicates. The project combines a controlled-light enclosure, snapshot visible hyperspectral image (VIS-HSI) reconstruction from an RGB camera frame, automatic region-of-interest (ROI) selection, and a wavelength-dependent brightness decision. This repository contains the supplied application, calibration files, sample images, enclosure designs, screenshots, and two related research papers.

> **Research prototype:** The papers report small pilot studies under controlled conditions. This repository does not establish performance on other holograms, banknotes, cameras, or lighting setups. The software's thresholds are specific to its original configuration.

## Research context and novelty

Conventional spectral imaging hardware can be bulky and expensive. Security holograms also change appearance with illumination and viewing angle, which makes comparisons unreliable unless image capture is controlled. The hologram study addresses those problems by combining a Raspberry Pi camera with an enclosed LED-lit fixture and reconstructing spectral information from one RGB exposure. The companion currency study applies the same snapshot VIS-HSI idea to 100 New Taiwan dollar (NTD) notes. The papers describe a Raspberry Pi 4, Raspberry Pi Camera Module v2, 2.8-inch TFT display, 3000 K chip-on-board LED strip, opal diffuser, and LED dimmer; the `Design/` folder contains housing drawings and printable parts. [Hologram paper](Documentation/Hologram.pdf) · [Currency paper](Documentation/Currency.pdf)

The distinguishing idea is **software-based spectral estimation from a common camera**, followed by inspection of a specific security feature under controlled illumination. This is a calibrated regression/PCA and image-analysis pipeline, rather than a deep-learning counterfeit classifier. A spectrometer and 24-patch color chart were used to establish the camera-to-spectrum relationship in the research work; the released application loads the resulting conversion parameters from `SRC/weight.npz`. [Hologram paper](Documentation/Hologram.pdf) · [Application source](SRC/Final_app.py)

## How the method works

```text
Controlled LED illumination + camera frame
    → RGB-to-visible-spectrum reconstruction
    → user-selected narrow wavelength band and gain
    → spectral-band image
    → template-matched hologram ROI
    → mean ROI intensity
    → original / counterfeit label
```

1. **Acquire a frame.** The Windows PyQt5 application reads a Raspberry Pi camera stream using OpenCV. The enclosure, dimmer, and diffuser aim to keep illumination consistent between samples.
2. **Estimate spectral data.** `SpectrumTransfer` loads a PCA basis and regression parameters from `weight.npz` and transforms RGB pixels into a reconstructed visible-spectrum cube. `ColorReproducer` uses the tables in `SRC/cr_weights/` to render the selected spectral band. The code indexes wavelengths from 380 to 780 nm at 1 nm intervals.
3. **Select an ROI.** OpenCV template matching locates `SRC/Template.png` in the rendered image and crops that region. In the hologram paper, the studied ROI is the central **“UR”** letters in “SECURITY.” The currency paper studies two different banknote ROIs, including a security-feature region.
4. **Classify.** The papers compare mean gray value (MGV) with class-specific confidence intervals. The current `Final_app.py` implementation instead computes the mean pixel value of the cropped rendered image and compares it with fixed thresholds for selected starting wavelengths: 400, 450, 500, 550, 600, 650, and 700 nm. Other values fall through to the “Counterfeit” label. These implementation thresholds are not a general-purpose authenticity standard. [Hologram paper](Documentation/Hologram.pdf) · [Currency paper](Documentation/Currency.pdf) · [Application source](SRC/Final_app.py)

## Evidence reported in the papers

| Study | Pilot samples and ROI | Reported observation |
| --- | --- | --- |
| [Hologram verification, *Scientific Reports* (2022)](https://doi.org/10.1038/s41598-022-22424-5) | Four original and four duplicate holograms; central “UR” ROI | The authors measured MGV from 400–700 nm and used a 98% confidence interval for class separation. They report strong MGV separation around 500–600 nm and a reflectance difference above about 580 nm. |
| [Counterfeit currency, *Sensors* (2023)](https://doi.org/10.3390/s23042026) | Three original and three counterfeit 100 NTD notes; two ROIs | The authors report useful MGV separation at 400–500 nm, with stronger separation for the ROI containing a security feature than for the cherry-blossom ROI. |

These are findings from the publications, **not benchmark results newly reproduced by this repository**. The papers do not establish a validated field accuracy for the current code and hardware across broad real-world conditions. The currency study also addresses whole-banknote authentication, while the application shipped here is labeled and thresholded for hologram analysis.

## Repository layout

| Path | Purpose |
| --- | --- |
| [`SRC/Final_app.py`](SRC/Final_app.py) | PyQt5 live-view, spectral reconstruction, ROI matching, and decision logic |
| [`SRC/FormMain.ui`](SRC/FormMain.ui) | Qt Designer form supplied with the project |
| [`SRC/weight.npz`](SRC/weight.npz), [`SRC/cr_weights/`](SRC/cr_weights/) | Spectral conversion parameters, light spectrum, color-matching functions, and matrix data |
| [`SRC/Template.png`](SRC/Template.png) | Image template used to locate the analysis ROI |
| [`Dataset/Hologram/`](Dataset/Hologram/) | Original/duplicate whole images and automatically selected ROIs |
| [`Dataset/Currency/`](Dataset/Currency/) | Original/duplicate currency images and ROI templates |
| [`Design/`](Design/) | Enclosure images and STL parts for the physical module |
| [`Documentation/`](Documentation/) | Hologram and currency papers plus project presentation |
| [`Screenshots/`](Screenshots/) | Supplied application screenshots |

The original `SRC/venv/` was uploaded to preserve the supplied folder. It records paths from its creator's Windows machine and should **not** be treated as a portable installation.

## Running the desktop prototype

Create a fresh Python environment. The supplied environment metadata records Python 3.10; the application imports PyQt5, OpenCV, NumPy, pandas, Matplotlib, Pillow, and scikit-image. No dependency lockfile or automated hardware test is supplied.

```powershell
git clone https://github.com/ArviZuko/Counterfeit-Hologram-Detector.git
cd Counterfeit-Hologram-Detector
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install PyQt5 opencv-python numpy pandas matplotlib Pillow scikit-image
cd SRC
python Final_app.py
```

Before launch, edit `m_cam_id` near the bottom of `SRC/Final_app.py` to point to a reachable camera stream. The supplied value is a private-network URL from the original setup. Run from `SRC/`: the code opens `weight.npz`, `cr_weights/`, and `Template.png` by relative path. The original Raspberry Pi camera, light source, enclosure, and camera calibration are needed to reproduce the published acquisition conditions.

In the UI, select a wavelength range and gain and press **Ok**, start the stream, then press **Analyse** on a frame. **Capture** saves the current frame to `Capture.png`; analysis writes `nbi.bmp` and `cropped.png` in the current working directory. The code does not provide an offline command-line inference mode. Wavelength input must stay within the 380–780 nm array represented by the conversion data, and the fixed classification thresholds only cover the seven starting wavelengths listed above.

## Interpretation and limitations

- An “Original” or “Counterfeit” label is an experimental result for the captured image and this calibration, **not proof of legal authenticity**.
- The papers' confidence-interval analyses and the application's fixed thresholds are different decision procedures. The repository does not include a script that recalculates the published intervals from the dataset.
- Camera calibration, exposure, angle, illumination, ROI placement, wavelength selection, and gain can change measured intensities. Recalibration and new validation data are needed for a different capture setup.
- The sample sizes in the two papers are small (eight holograms and six banknotes). No broader deployment or independent performance evaluation is included here.
- The paper PDFs carry their publishers' terms; no separate project-level software or dataset license was supplied with this folder.

## Publications

1. Arvind Mukundan, Yu-Ming Tsao, Fen-Chi Lin, and Hsiang-Chen Wang. “[Portable and low-cost hologram verification module using a snapshot-based hyperspectral imaging algorithm](https://doi.org/10.1038/s41598-022-22424-5).” *Scientific Reports* **12**, 18475 (2022). Local copy: [`Documentation/Hologram.pdf`](Documentation/Hologram.pdf).
2. Arvind Mukundan, Yu-Ming Tsao, Wen-Min Cheng, Fen-Chi Lin, and Hsiang-Chen Wang. “[Automatic Counterfeit Currency Detection Using a Novel Snapshot Hyperspectral Imaging Algorithm](https://doi.org/10.3390/s23042026).” *Sensors* **23**, 2026 (2023). Local copy: [`Documentation/Currency.pdf`](Documentation/Currency.pdf).
