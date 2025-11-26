import trimesh
import numpy as np
from io import BytesIO
from app.models import Model3D, ExportOptions
import traceback


class ExportService:
    def export_stl(self, model: Model3D, options: ExportOptions | dict = None):
        """
        Export model to STL format (binary or ASCII).
        """
        # options may be a Pydantic ExportOptions or a plain dict from request JSON
        opts = None
        if options is None:
            opts = {}
        elif isinstance(options, dict):
            opts = options
        else:
            # Pydantic model -> convert to dict
            try:
                opts = options.dict()
            except Exception:
                opts = {}

        # Reconstruct trimesh from model geometry
        try:
            # Accept either a flat list [x,y,z,...] or nested [[x,y,z], ...]
            verts = np.array(model.geometry.vertices, dtype=np.float64)
            if verts.ndim == 1:
                if verts.size % 3 != 0:
                    raise ValueError(f"Vertices length {verts.size} is not divisible by 3")
                vertices = verts.reshape(-1, 3)
            elif verts.ndim == 2 and verts.shape[1] == 3:
                vertices = verts
            else:
                raise ValueError(f"Unsupported vertices shape: {verts.shape}")

            idx = np.array(model.geometry.indices, dtype=np.int64)
            if idx.ndim == 1:
                if idx.size % 3 != 0:
                    raise ValueError(f"Indices length {idx.size} is not divisible by 3")
                faces = idx.reshape(-1, 3)
            elif idx.ndim == 2 and idx.shape[1] == 3:
                faces = idx
            else:
                raise ValueError(f"Unsupported indices shape: {idx.shape}")

            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        except Exception as e:
            # Log full traceback for diagnosis and re-raise
            print(f"[EXPORT SERVICE] Failed to reconstruct mesh: {e}")
            traceback.print_exc()
            raise

        # Export to BytesIO
        output = BytesIO()
        # Determine ASCII vs binary based on options. ExportOptions.binary==True => binary.
        ascii_flag = False
        if isinstance(opts, dict):
            # If client explicitly requests non-binary (binary=false) we export ASCII
            ascii_flag = not bool(opts.get('binary', True))

        # Call export with the file_obj kw only. If ascii_flag is True, request ASCII export
        if ascii_flag:
            mesh.export(file_obj=output, file_type='stl', ascii=True)
        else:
            mesh.export(file_obj=output, file_type='stl')
        output.seek(0)

        stl_bytes = output.getvalue()

        # Prepare lightweight metadata useful for debugging/inspection
        metadata = {
            'vertices': int(vertices.shape[0]),
            'faces': int(faces.shape[0]),
            'bounds_min': mesh.bounds[0].tolist() if hasattr(mesh, 'bounds') else None,
            'bounds_max': mesh.bounds[1].tolist() if hasattr(mesh, 'bounds') else None,
            'is_watertight': bool(mesh.is_watertight) if hasattr(mesh, 'is_watertight') else None,
        }

        # If inspect flag set in options, return both bytes and metadata for the caller to format
        if isinstance(opts, dict) and bool(opts.get('inspect', False)):
            return stl_bytes, metadata

        return stl_bytes

    def export_step(self, model: Model3D, options: ExportOptions = None) -> bytes:
        """
        Export model to STEP format.
        Note: This requires pythonOCC which is complex to install.
        For MVP, we'll return a placeholder or convert via intermediate format.
        """
        # TODO: Implement STEP export with pythonOCC
        # For now, we'll raise an error or return STL as fallback
        raise NotImplementedError(
            "STEP export requires pythonOCC installation. "
            "Please use STL export for now."
        )

    def export_iges(self, model: Model3D, options: ExportOptions = None) -> bytes:
        """
        Export model to IGES format.
        Note: This also requires pythonOCC.
        """
        # TODO: Implement IGES export with pythonOCC
        raise NotImplementedError(
            "IGES export requires pythonOCC installation. "
            "Please use STL export for now."
        )

    def export_obj(self, model: Model3D) -> bytes:
        """
        Export model to OBJ format (additional format).
        """
        vertices = np.array(model.geometry.vertices).reshape(-1, 3)
        faces = np.array(model.geometry.indices).reshape(-1, 3)

        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

        output = BytesIO()
        mesh.export(file_obj=output, file_type='obj')
        output.seek(0)

        return output.getvalue()


export_service = ExportService()
