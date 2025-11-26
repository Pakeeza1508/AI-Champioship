export function calculateAtmosphere(altitudeMeters: number) {
    // Standard Atmosphere Model (Troposphere < 11km, Stratosphere > 11km)
    // Simplified model for UI context
    
    let tempK = 288.15; // Sea level standard temp
    let pressure = 101325; // Sea level pressure (Pa)
    
    if (altitudeMeters <= 11000) {
        // Troposphere
        tempK = 288.15 - (0.0065 * altitudeMeters);
    } else {
        // Lower Stratosphere (isothermal approx for simple display)
        tempK = 216.65;
    }

    // Speed of sound (a) = sqrt(gamma * R * T)
    // gamma = 1.4, R = 287.05
    const speedOfSound = Math.sqrt(1.4 * 287.05 * tempK);

    let zone = 'LOW ALTITUDE';
    if (altitudeMeters > 5000) zone = 'MEDIUM ALTITUDE';
    if (altitudeMeters > 10000) zone = 'HIGH ALTITUDE';
    if (altitudeMeters > 18000) zone = 'STRATOSPHERE';

    return {
        tempK,
        speedOfSound, // m/s
        zone
    };
}

export function mpsToKmph(mps: number): number {
    return mps * 3.6;
}