# Counterfeit Hologram Detector

This project is a desktop prototype for inspecting currency holograms from a camera image. The PyQt5 application reconstructs a selected spectral band from the camera frame using the supplied `weight.npz` and color-response tables, locates a hologram region with template matching, then applies wavelength-specific brightness thresholds to label the hologram as original or counterfeit.

## Project structure

| Folder | Contents |
| --- | --- |
| `SRC/` | `Final_app.py`, Qt UI file, matching template, spectral weights, and color-response data |
| `Dataset/Currency/` | Original and duplicate currency images and templates |
| `Dataset/Hologram/` | Whole-image and automatically selected region samples |
| `Design/` | Device drawings, photos, and 3D-printable parts |
| `Documentation/` | Project documents and presentation |
| `Screenshots/` | Application screenshots |

The supplied `SRC/venv/` is included to preserve the original folder, but its configuration points to a different Windows Python installation. Create a fresh virtual environment for use on another machine.

## Run the prototype

Use Python with PyQt5, OpenCV, NumPy, pandas, Matplotlib, Pillow, and scikit-image installed. The application expects `weight.npz`, `Template.png`, and `cr_weights/` beside `Final_app.py`, so start it from the `SRC` directory:

```powershell
cd SRC
python Final_app.py
```

The camera address is currently hard-coded in `Final_app.py` (`m_cam_id`). Set it to an accessible camera stream before launching the UI. The application captures a frame, accepts wavelength and gain settings, and writes `Capture.png`, `nbi.bmp`, and `cropped.png` in the current working directory during use.

The final decision uses fixed thresholds for selected wavelengths; it is not a separately trained counterfeit classifier. Results depend on the camera, lighting, template, and configured thresholds. The hardware workflow was not independently run during repository publication.

No project license was supplied with the folder.
