# 3D Synthetic Data Engine — Mitsubishi 3D Tech Hackathon 2024

**Category:** Computer Vision / Synthetic Data  
**Result:** Cash Prize Winner  
**Stack:** Blender API, Python, LiDAR point clouds, Docker

## What it does
A Synthetic Data Generation engine that procedurally creates pre-labelled 3D LiDAR datasets inside Blender. Solves the data-scarcity problem for training semantic segmentation models — no manual annotation needed.

## Key technical decisions
- **Blender Geometry Nodes** used for procedural scene generation — randomised object placement, lighting, surface materials
- **Python-Blender bridge** automated batch rendering and label export in KITTI format
- Reduced manual labelling time by **11x** compared to real-world data collection
- **Docker** containerised the pipeline for reproducible generation on any machine

## Why it matters
Real-world LiDAR data for autonomous driving is expensive and rare. Synthetic data at scale lets teams train and benchmark models without waiting months for data collection campaigns.
