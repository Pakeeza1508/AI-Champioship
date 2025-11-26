from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import math

router = APIRouter(prefix="/simulate", tags=["simulation"])

class SimRequest(BaseModel):
    material_yield: float    # MPa
    material_density: float  # kg/m3
    altitude: float          # m
    speed: float             # m/s
    span: float              # m
    root_chord: float        # m
    thickness: float         # %
@router.post("/structural")
async def run_structural_simulation(req: SimRequest):
    """
    Run a rigorous structural analysis using Beam Theory.
    Simulates a 2.5G Limit Load Maneuver (FAA Standard).
    """
    try:
        # 1. ATMOSPHERIC PHYSICS
        # Standard Atmosphere: density drops with altitude
        rho = 1.225 * math.exp(-req.altitude / 8500)
        
        # 2. AERODYNAMIC LOADS
        # Estimate Wing Area (Trapezoidal approx)
        area = req.span * req.root_chord * 0.85 
        
        # --- PHYSICS FIX: LOAD FACTOR ---
        # Previous version used 1.2 (Cruise). 
        # Real structural testing uses Limit Load Factor (2.5G for Transport/Commercial)
        # This effectively multiplies the force by ~2.1x compared to before.
        load_factor_g = 2.5 
        
        # Lift Coefficient (Cl) during high-G pull up
        cl_maneuver = 1.5 
        
        # Total Lift Force = Dynamic Pressure * Area * Cl * G-Load
        # 0.5 * rho * v^2
        dynamic_pressure = 0.5 * rho * (req.speed ** 2)
        
        # Total design load to withstand (Newtons)
        lift_force = dynamic_pressure * area * cl_maneuver * load_factor_g
        
        # 3. STRUCTURAL MECHANICS (Cantilever Beam)
        # Moment at root. We assume lift center is at 45% of semi-span.
        moment = (lift_force / 2) * (req.span / 2 * 0.45)
        
        # 4. GEOMETRY & SECTION MODULUS (Z)
        # Thickness in meters
        t_meters = req.root_chord * (req.thickness / 100.0)
        
        # Structural Efficiency Factor
        # 0.15 = Optimized Composite/Machined Ribs (Very Strong)
        # 0.10 = Standard Aluminum Construction (Realistic)
        efficiency_factor = 0.10 # Reduced to make it more realistic/breakable
        
        # Z ≈ Efficiency * Chord * Thickness^2
        section_modulus = efficiency_factor * req.root_chord * (t_meters ** 2)
        
        # 5. STRESS CALCULATION
        if section_modulus <= 0.000001:
            bending_stress_pa = 999999999
        else:
            bending_stress_pa = moment / section_modulus
            
        bending_stress_mpa = bending_stress_pa / 1_000_000
        
        # 6. SAFETY FACTOR
        if bending_stress_mpa <= 0.001:
            safety_factor = 100.0
        else:
            safety_factor = req.material_yield / bending_stress_mpa
            
        if safety_factor > 100: safety_factor = 100.0
            
        # STRICTER PASS/FAIL: 
        # Aerospace standard requires holding 1.5x the Limit Load
        status = "PASS" if safety_factor >= 1.5 else "FAIL"
        
        return {
            "success": True,
            "status": status,
            "safety_factor": round(safety_factor, 2),
            "max_stress": round(bending_stress_mpa, 2),
            "lift_force_kn": round(lift_force / 1000, 1),
            "details": {
                "air_density": round(rho, 4),
                "dynamic_pressure": round(dynamic_pressure, 0)
            }
        }

    except Exception as e:
        print(f"Simulation error: {e}")
        return {
            "success": False,
            "error": str(e)
        }