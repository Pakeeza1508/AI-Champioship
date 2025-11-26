#!/usr/bin/env python3
"""Inspect and validate an STL (or other mesh) file using trimesh.

Usage:
  python tools\inspect_stl.py C:\path\to\file.stl
  python tools\inspect_stl.py C:\path\to\file.stl --ascii-out C:\path\to\out_ascii.stl
  python tools\inspect_stl.py C:\path\to\file.stl --show

This prints vertex/face counts, bounding box, NaNs, degenerate faces, and whether mesh
is watertight. It can also write an ASCII STL copy for viewing in Notepad.
"""
import argparse
import sys
import os
from pathlib import Path
import json

try:
    import trimesh
    import numpy as np
except Exception as e:
    print("Missing dependency: please install trimesh and numpy:\n  pip install trimesh numpy")
    raise


def human(n):
    for unit in ['','K','M','G']:
        if abs(n) < 1000.0:
            return f"{n:.2f}{unit}"
        n /= 1000.0
    return f"{n:.2f}T"


def inspect(path: Path, ascii_out: Path | None = None, show: bool = False):
    print(f"Inspecting: {path}")
    if not path.exists():
        print("File not found")
        return 2

    size = path.stat().st_size
    print(f"File size: {size} bytes ({human(size)})")

    # Peek at header for ASCII vs binary
    with open(path, 'rb') as f:
        header = f.read(80)
    try:
        prefix = header.decode('ascii', errors='ignore')[:5]
    except Exception:
        prefix = ''
    print(f"Header prefix: {repr(prefix)}")
    if prefix.lower().startswith('solid'):
        print("Likely ASCII STL (or ASCII with 'solid' header). You can open in Notepad/VSCode.")
    else:
        print("Likely binary STL. Not human-readable in plain text editors.")

    # Load mesh with trimesh
    try:
        mesh = trimesh.load(path, force='mesh')
    except Exception as e:
        print(f"Failed to load mesh: {e}")
        return 3

    if mesh is None:
        print("trimesh.load returned None (not a mesh)")
        return 4

    print(f"Mesh type: {type(mesh)}")
    try:
        v = np.asarray(mesh.vertices)
        f = np.asarray(mesh.faces)
    except Exception as e:
        print(f"Failed to access vertices/faces arrays: {e}")
        return 5

    print(f"Vertices: {v.shape}  Faces: {f.shape}")

    nan_vertices = np.isnan(v).any()
    nan_faces = np.isnan(f).any()
    print(f"Contains NaNs in vertices? {nan_vertices}")
    print(f"Contains NaNs in faces? {nan_faces}")

    # Basic geometry checks
    try:
        bbox = mesh.bounds
        bbox_extent = bbox[1] - bbox[0]
        centroid = mesh.centroid
        volume = None
        try:
            volume = mesh.volume
        except Exception:
            volume = None
        print(f"Bounds min: {bbox[0]} max: {bbox[1]} extent: {bbox_extent}")
        print(f"Centroid: {centroid}")
        print(f"Volume (may be 0 or None for non-closed meshes): {volume}")
    except Exception as e:
        print(f"Error computing bounds/volume: {e}")

    # Watertight, validate, face areas
    try:
        print(f"Is watertight? {mesh.is_watertight}")
        valid = mesh.is_winding_consistent
        print(f"Winding consistent? {valid}")
    except Exception as e:
        print(f"Error checking watertight/winding: {e}")

    try:
        areas = mesh.area_faces
        small_faces = (areas <= 1e-12).sum() if areas is not None else 'n/a'
        print(f"Faces areas: min={areas.min():.6g} max={areas.max():.6g} mean={areas.mean():.6g} tiny_count={small_faces}")
    except Exception as e:
        print(f"Failed to compute face areas: {e}")

    # Degenerate faces
    try:
        degenerate_count = trimesh.geometry.triangles_area(mesh.triangles).size - np.count_nonzero(trimesh.geometry.triangles_area(mesh.triangles))
        print(f"Degenerate faces (zero area) approx: {degenerate_count}")
    except Exception:
        # fallback: count exactly zero-area faces
        try:
            areas = trimesh.triangles.area(mesh.triangles)
            degenerate_count = (areas == 0).sum()
            print(f"Degenerate faces (zero area) exact: {degenerate_count}")
        except Exception:
            pass

    # Validation report
    try:
        report = mesh.validate()
        print(f"Validate() result: {report}")
    except Exception:
        # Some trimesh versions return None or raise; ignore
        pass

    # Export ASCII copy if requested
    if ascii_out:
        try:
            ascii_out = Path(ascii_out)
            ascii_out.parent.mkdir(parents=True, exist_ok=True)
            mesh.export(ascii_out.as_posix(), file_type='stl', ascii=True)
            print(f"Wrote ASCII STL to: {ascii_out}")
        except Exception as e:
            print(f"Failed to write ASCII STL: {e}")

    # Optionally show the mesh (needs pyglet / scene viewer). This will block.
    if show:
        try:
            mesh.show()
        except Exception as e:
            print(f"mesh.show() failed: {e}")

    # Dump a small JSON summary next to the file
    try:
        summary = {
            'path': str(path),
            'size_bytes': size,
            'vertices': int(v.shape[0]) if v.ndim == 2 else None,
            'faces': int(f.shape[0]) if f.ndim == 2 else None,
            'bounds_min': bbox[0].tolist() if 'bbox' in locals() else None,
            'bounds_max': bbox[1].tolist() if 'bbox' in locals() else None,
            'is_watertight': bool(mesh.is_watertight) if hasattr(mesh, 'is_watertight') else None,
        }
        json_path = path.with_suffix(path.suffix + '.inspect.json')
        with open(json_path, 'w', encoding='utf8') as jf:
            json.dump(summary, jf, indent=2)
        print(f"Wrote summary JSON: {json_path}")
    except Exception as e:
        print(f"Failed to write summary JSON: {e}")

    return 0


def main(argv):
    p = argparse.ArgumentParser(description='Inspect an STL/mesh file')
    p.add_argument('file', help='Path to STL/mesh file')
    p.add_argument('--ascii-out', help='Write ASCII STL copy (path)')
    p.add_argument('--show', action='store_true', help='Open a viewer (may require extra deps)')
    args = p.parse_args(argv)
    return inspect(Path(args.file), args.ascii_out, args.show)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
