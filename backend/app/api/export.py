from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from app.models import ExportRequest, Model3D
from app.services import export_service
import app.api.generation as generation

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/stl")
async def export_stl(req: Request):
    """
    Export model as STL file.
    """
    # Read raw JSON body so we can accept either { model_id, options }
    body = await req.json()
    model_id = body.get("model_id")
    options = body.get("options")
    model_obj = body.get("model")

    # Debug: log current model vs requested id to diagnose 404s
    try:
        current_id = generation.current_model.id if generation.current_model is not None else None
    except Exception:
        current_id = None
    print(f"[EXPORT] requested model_id={model_id}, current_model_id={current_id}, model_in_body={'yes' if model_obj else 'no'}")

    # Determine which model to export:
    model_to_use = None
    if generation.current_model is not None and model_id and generation.current_model.id == model_id:
        model_to_use = generation.current_model
    elif model_obj:
        # Client provided full model in request body; validate via Pydantic
        try:
            model_to_use = Model3D.parse_obj(model_obj)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid model in request: {e}")
    else:
        # No model available server-side and client didn't send one
        raise HTTPException(status_code=404, detail="Model not found")

    try:
        # If client passed options as JSON, it will be a dict here
        inspect_flag = False
        if isinstance(options, dict):
            inspect_flag = bool(options.get('inspect', False))

        result = export_service.export_stl(model_to_use, options)

        # export_stl may return (bytes, metadata) when inspect=True
        if inspect_flag and isinstance(result, tuple):
            stl_bytes, metadata = result
            # If ASCII (options.binary == False) we can include text directly
            ascii_mode = not bool(options.get('binary', True)) if isinstance(options, dict) else False
            stl_text = None
            stl_b64 = None
            if ascii_mode:
                try:
                    stl_text = stl_bytes.decode('utf-8', errors='replace')
                except Exception:
                    stl_text = None
            else:
                import base64
                stl_b64 = base64.b64encode(stl_bytes).decode('ascii')

            return {
                'filename': f"{model_to_use.name}.stl",
                'ascii': ascii_mode,
                'stl_text': stl_text,
                'stl_b64': stl_b64,
                'metadata': metadata,
            }

        # Normal case: return bytes for download
        stl_bytes = result if not isinstance(result, tuple) else result[0]
        return Response(
            content=stl_bytes,
            media_type="application/sla",
            headers={
                "Content-Disposition": f"attachment; filename={model_to_use.name}.stl"
            }
        )

    except Exception as e:
        # Print traceback to server logs for debugging
        import traceback
        print("[EXPORT] Exception while exporting STL:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step")
async def export_step(req: Request):
    """
    Export model as STEP file.
    Note: Requires pythonOCC - currently not implemented.
    """
    body = await req.json()
    model_id = body.get("model_id")
    options = body.get("options")
    model_obj = body.get("model")

    try:
        current_id = generation.current_model.id if generation.current_model is not None else None
    except Exception:
        current_id = None
    print(f"[EXPORT STEP] requested model_id={model_id}, current_model_id={current_id}, model_in_body={'yes' if model_obj else 'no'}")

    model_to_use = None
    if generation.current_model is not None and model_id and generation.current_model.id == model_id:
        model_to_use = generation.current_model
    elif model_obj:
        try:
            model_to_use = Model3D.parse_obj(model_obj)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid model in request: {e}")
    else:
        raise HTTPException(status_code=404, detail="Model not found")

    try:
        step_data = export_service.export_step(model_to_use, options)

        return Response(
            content=step_data,
            media_type="application/step",
            headers={
                "Content-Disposition": f"attachment; filename={model_to_use.name}.step"
            }
        )

    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/iges")
async def export_iges(req: Request):
    """
    Export model as IGES file.
    Note: Requires pythonOCC - currently not implemented.
    """
    body = await req.json()
    model_id = body.get("model_id")
    options = body.get("options")
    model_obj = body.get("model")

    try:
        current_id = generation.current_model.id if generation.current_model is not None else None
    except Exception:
        current_id = None
    print(f"[EXPORT IGES] requested model_id={model_id}, current_model_id={current_id}, model_in_body={'yes' if model_obj else 'no'}")

    model_to_use = None
    if generation.current_model is not None and model_id and generation.current_model.id == model_id:
        model_to_use = generation.current_model
    elif model_obj:
        try:
            model_to_use = Model3D.parse_obj(model_obj)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid model in request: {e}")
    else:
        raise HTTPException(status_code=404, detail="Model not found")

    try:
        iges_data = export_service.export_iges(model_to_use, options)

        return Response(
            content=iges_data,
            media_type="application/iges",
            headers={
                "Content-Disposition": f"attachment; filename={model_to_use.name}.iges"
            }
        )

    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
