export interface AerospaceMaterial {
    id: string;
    name: string;
    density: number; // kg/m³
    yieldStrength: number; // MPa
    cost: string; // $, $$, $$$
    description: string;
}

export const MATERIALS: AerospaceMaterial[] = [
    {
        id: 'al7075',
        name: 'ALUMINUM 7075-T6',
        density: 2810,
        yieldStrength: 503,
        cost: '$$',
        description: 'High static strength, standard for airframes.'
    },
    {
        id: 'ti6al4v',
        name: 'TITANIUM Ti-6Al-4V',
        density: 4430,
        yieldStrength: 880,
        cost: '$$$$',
        description: 'Excellent strength-to-weight, high heat resistance.'
    },
    {
        id: 'cf_epoxy',
        name: 'CARBON FIBER (Epoxy)',
        density: 1600,
        yieldStrength: 600,
        cost: '$$$',
        description: 'Extremely lightweight, high stiffness.'
    },
    {
        id: 'steel4340',
        name: 'STEEL 4340',
        density: 7850,
        yieldStrength: 1620,
        cost: '$',
        description: 'Very high strength, heavy. Used for landing gear.'
    },
    {
        id: 'al2024',
        name: 'ALUMINUM 2024-T3',
        density: 2780,
        yieldStrength: 345,
        cost: '$$',
        description: 'High fatigue resistance, used for wings/fuselage.'
    }
];