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
    Run a simplified structural analysis using Beam Theory.
    Calculates Lift, Bending Moment, and Stress to determine Safety Factor.
    """
    try:
        # 1. ATMOSPHERIC PHYSICS
        # Standard Atmosphere Model: density drops with altitude
        # rho0 = 1.225 kg/m3 at sea level
        # Scale height approx 8500m
        rho = 1.225 * math.exp(-req.altitude / 8500)
        
        # 2. AERODYNAMIC LOADS
        # Lift Equation: L = 0.5 * rho * v^2 * Area * Cl
        # Estimate Wing Area (Trapezoidal approx)
        area = req.span * req.root_chord * 0.85 
        
        # Cl (Lift Coefficient) - estimated max load (e.g., 2.5G maneuver)
        cl_max = 1.2 
        
        # Total Lift Force (Newtons)
        lift_force = 0.5 * rho * (req.speed ** 2) * area * cl_max
        
        # 3. STRUCTURAL MECHANICS (Cantilever Beam Approximation)
        # We model the wing as a cantilever beam fixed at the fuselage.
        # Bending Moment at Root: M ~ (Lift/2) * (Span/4) 
        # (assuming elliptical lift distribution center of pressure is at ~centroid of semi-span)
        moment = (lift_force / 2) * (req.span / 4)
        
        # Section Modulus (Z) for the Wing Root
        # Model root cross-section roughly as a hollow structural box/airfoil
        # Thickness in meters
        t_meters = req.root_chord * (req.thickness / 100.0)
        
        # Approximation of Section Modulus for a structural airfoil shape
        # Z ≈ k * c * t^2
        # Using a simplified factor for a hollow spar box
        section_modulus = (req.root_chord * (t_meters ** 2)) * 0.15
        
        # 4. STRESS CALCULATION
        # Bending Stress = Moment / Section Modulus
        if section_modulus <= 0.000001:
            bending_stress_pa = 999999999 # Prevent divide by zero
        else:
            bending_stress_pa = moment / section_modulus
            
        bending_stress_mpa = bending_stress_pa / 1_000_000
        
        # 5. SAFETY FACTOR
        # SF = Yield Strength / Actual Stress
        if bending_stress_mpa <= 0.001:
            safety_factor = 100.0
        else:
            safety_factor = req.material_yield / bending_stress_mpa
            
        # Cap SF for display
        if safety_factor > 100: safety_factor = 100.0
            
        # Determine Status
        # Aerospace standard safety factor is typically 1.5
        status = "PASS" if safety_factor >= 1.5 else "FAIL"
        
        return {
            "success": True,
            "status": status,
            "safety_factor": round(safety_factor, 2),
            "max_stress": round(bending_stress_mpa, 2),
            "lift_force_kn": round(lift_force / 1000, 1),
            "details": {
                "air_density": round(rho, 4),
                "dynamic_pressure": round(0.5 * rho * (req.speed ** 2), 0)
            }
        }

    except Exception as e:
        print(f"Simulation error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }