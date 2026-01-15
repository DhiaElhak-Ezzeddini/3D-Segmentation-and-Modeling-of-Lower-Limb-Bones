# 3D Bone Viewer Application (Clean Architecture & PWA)

A full-stack medical application for 3D bone visualization and surgical planning. Built with a robust **Clean Architecture** backend and a **Progressive Web App (PWA)** frontend.

![Bone Viewer Demo](images/example.png)

## Features

- 🏗️ **Clean Architecture Backend** - Scalable, domain-centric design
- 📱 **Progressive Web App (PWA)** - Installable, offline-capable, and responsive
- 🦴 **NIfTI Processing** - Automatic bone extraction from medical segmentations. See [`Medical_Image_Segmentation.ipynb`](Medical_Image_Segmentation.ipynb) for the inference process.
- 🎨 **Medical Visualization** - High-fidelity 3D rendering with medical color schemes
- ✋ **Interactive Controls** - Move, rotate, and scale bones and implants
- 🔧 **Implant System** - Support for STL, PLY, and OBJ implants
- 🔒 **Secure Data Handling** - Organized file storage and processing

## Stack

- **Backend**: FastAPI (Python), Clean Architecture (Domain/Application/Infra/Presentation)
- **Frontend**: HTML5, CSS3 (Light Theme), JavaScript (Module), Three.js
- **Processing**: Nibabel, NumPy

## File Structure

```
bone_viewer_app/
├── backend/
│   ├── src/                 # Clean Architecture Source
│   │   ├── domain/          # Entities & Interfaces (Pure Python)
│   │   ├── application/     # Business Logic (Services)
│   │   ├── infrastructure/  # External Adapters (File System, libraries)
│   │   └── presentation/    # API Layer (FastAPI)
│   ├── main.py              # Entry Point
│   ├── requirements.txt
│   └── uploads/             # Data Storage
└── frontend/
    ├── index.html           # PWA Entry Point
    ├── manifest.json        # PWA Manifest
    ├── sw.js                # Service Worker (Offline Support)
    ├── css/
    ├── js/
    └── images/
```

## Installation

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Backend Server

```bash
# This launches the clean architecture app via src.main
python main.py
```
*API runs on `http://localhost:8001`*

### 3. Run Frontend (PWA)

```bash
cd frontend
python -m http.server 8080
```
*Open `http://localhost:8080` in Chrome/Edge*

## Usage

1.  **Install App**: Click the install icon in your browser address bar to install as a desktop/mobile app.
2.  **Upload**: Drag & drop a `.nii.gz` segmentation file.
3.  **Visualisation**: bones are extracted and displayed in 3D.
4.  **Implants**: Upload `.stl` or `.ply` implant files to plan surgeries.
5.  **Offline**: The app structure is cached; you can open the UI even without an internet connection (backend required for new processing).

## Architecture Details

The backend strictly follows the Dependency Rule:
- **Domain**: Knows nothing about outer layers.
- **Application**: Orchestrates the Domain.
- **Infrastructure**: Implements interfaces defined in Domain.
- **Presentation**: Depends on Application services.

## License
MIT
