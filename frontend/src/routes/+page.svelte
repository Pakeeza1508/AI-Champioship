<script lang="ts">
	import Viewer3D from '$lib/components/3d/Viewer3D.svelte';
	import ComponentEditor from '$lib/components/editor/ComponentEditor.svelte';
	import ExportPanel from '$lib/components/ui/ExportPanel.svelte';
	import AircraftChat from '$lib/components/chat/AircraftChat.svelte';
	import {
		aircraft,
		activeComponent,
		completionStatus,
		isAssemblyReady,
		allComponents,
		allComponentsComplete,
		compiledAircraft,
		isCompiling,
		type ComponentType
	} from '$lib/stores/aircraftStore';
	import { apiService } from '$lib/services/apiService';
	import { missionProfile } from '$lib/stores/aircraftStore';
	import { calculateAtmosphere, mpsToKmph } from '$lib/utils/physics';

	import { MATERIALS } from '$lib/data/materials';
	import { componentMaterials } from '$lib/stores/aircraftStore';
	// Local UI state for transient toasts
	let showContextToast = false;
	let contextToastText = '';

	type ViewMode = 'edit' | 'assembly';
	let viewMode: ViewMode = 'edit';

	const componentLabels: Record<ComponentType, string> = {
		wings: 'Wings',
		fuselage: 'Fuselage',
		engines: 'Engines'
	};

	// Technical component codes
	const componentCodes: Record<ComponentType, string> = {
		wings: 'WNG-01',
		fuselage: 'FSL-02',
		engines: 'ENG-03'
	};

	function selectComponent(type: ComponentType) {
		activeComponent.set(type);
		viewMode = 'edit';
	}

	function goToAssembly() {
		viewMode = 'assembly';
	}

	$: canAssemble = $isAssemblyReady;
	$: assemblyComponentCount = $allComponents.length;
	$: canCompile = $allComponentsComplete && !$compiledAircraft;
	$: assemblyProgress = (assemblyComponentCount / 3) * 100;

	async function handleCompileAircraft() {
		isCompiling.set(true);

		try {
			const response = await apiService.compileAircraft($aircraft);

			if (response.success && response.model) {
				compiledAircraft.set(response.model);
				console.log('Aircraft compiled successfully:', response.model.name);
			} else {
				console.error('Compilation failed:', response.error);
				alert('Failed to compile aircraft: ' + (response.error || 'Unknown error'));
			}

		} catch (error) {
			console.error('Error compiling aircraft:', error);
			alert('Error compiling aircraft');
		} finally {
			isCompiling.set(false);
		}
	}

	// Simulation State
	let isSimulating = false;
	let simResult: any = null;

	async function handleSimulation() {
		// We need wings to run a wing stress test
		if (!$aircraft.wings.model) {
			alert("Please generate wings first.");
			return;
		}

		isSimulating = true;
		simResult = null;

		try {
			// Get Wing Parameters
			const wingParams = $aircraft.wings.model.parameters;
			
			// Get Current Wing Material
			const matId = $componentMaterials.wings;
			const material = MATERIALS.find(m => m.id === matId) || MATERIALS[0];

			// Call API
			const result = await apiService.runSimulation({
				materialYield: material.yieldStrength,
				materialDensity: material.density,
				altitude: $missionProfile.altitude,
				speed: $missionProfile.speed,
				span: wingParams.span,
				rootChord: wingParams.rootChord,
				thickness: wingParams.thickness
			});

			if (result.success) {
				simResult = result;
			} else {
				alert("Simulation failed: " + result.error);
			}
		} catch (e) {
			console.error(e);
			alert("Simulation error");
		} finally {
			isSimulating = false;
		}
	}

	// Physics Calculations
	$: atmosphere = calculateAtmosphere($missionProfile.altitude);
	$: machNumber = $missionProfile.speed / atmosphere.speedOfSound;
	$: speedKmph = mpsToKmph($missionProfile.speed);
    
	function applyContext() {
		$missionProfile.isContextApplied = true;
		// Show a short in-app success toast
		contextToastText = `Mission Profile Applied — ${atmosphere.zone}, Mach ${machNumber.toFixed(2)}`;
		showContextToast = true;
		// Hide after 2.5s
		setTimeout(() => {
			showContextToast = false;
		}, 2500);
	}

	// ... existing imports and variables ...

	// NEW: Optimization Logic
	async function optimizeDesign() {
		if (!simResult || simResult.status === 'PASS' || !$aircraft.wings.model) return;

		// 1. Calculate target Safety Factor (1.5)
		const currentSF = simResult.safety_factor;
		const targetSF = 1.55; // Aim slightly higher for safety
		
		// 2. Calculate required strength increase
		// Stress is inversely proportional to Thickness^2 (roughly) for Section Modulus
		// We need to increase thickness.
		// Ratio = Target / Current
		const ratio = targetSF / currentSF;
		
		// 3. Get current parameters
		const currentParams = $aircraft.wings.model.parameters;
		const currentThickness = currentParams.thickness;
		
		// 4. Calculate new thickness (Simple approximation: Thickness * sqrt(ratio))
		// Since Z ~ Thickness^2, then Thickness ~ sqrt(Z)
		let newThickness = currentThickness * Math.sqrt(ratio);
		
		// Cap it reasonably (max 25%)
		if (newThickness > 25) newThickness = 25;
		if (newThickness < currentThickness) newThickness = currentThickness + 2; // Minimum bump

		// 5. Round to integer
		newThickness = Math.floor(newThickness);

		// 6. Apply the change
		// We use the apiService to update just like the slider would
		const newParams = { ...currentParams, thickness: newThickness };
		
		// Notify User
		alert(`AI OPTIMIZATION:\nIncreasing Wing Thickness from ${currentThickness}% to ${newThickness}%\nto handle ${simResult.lift_force_kn} kN load.`);
		
		// 7. Trigger Update
		// We need to find the ComponentEditor logic to update. 
		// Since we are in +page.svelte, we can manually trigger the API update via the service.
		isCompiling = true; // Show spinner
		
		try {
			const response = await apiService.updateParameters(newParams);
			if (response.success && response.model) {
				// Update the store
				// We need to import setComponentModel from stores if not already imported
				// (Make sure setComponentModel is imported at the top!)
				
				// Force refresh the specific component in the store
				// Note: In +page.svelte we need to access the store writer.
				// The cleanest way is to just re-run the simulation after a short delay
				// But first, we update the backend model.
				
				// A trick to update the UI:
				// We will rely on the user re-running the sim, but the model IS updated.
				// To update the UI visual, we need to update the 'aircraft' store.
				
				// IMPORTANT: Add this import at the top if missing:
				// import { setComponentModel } from '$lib/stores/aircraftStore';
				
				setComponentModel('wings', response.model);
				
				// Reset sim result so they have to run it again to see the green PASS
				simResult = null;
				
				// Show toast/alert
				contextToastText = "Optimization Applied. Re-run simulation.";
				showContextToast = true;
				setTimeout(() => showContextToast = false, 3000);
			}
		} catch (e) {
			console.error(e);
		} finally {
			isCompiling = false;
		}
	}
</script>

<main class="app-container">
	<!-- Technical Header with Status -->
	<header class="app-header">
		<div class="header-grid">
			<!-- Left: Branding -->
			<div class="header-brand">
				<div class="brand-icon">
					<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M12 2L2 12L12 16L22 12L12 2Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="bevel"/>
						<path d="M2 12L12 22L22 12" stroke="currentColor" stroke-width="1.5" stroke-linejoin="bevel"/>
					</svg>
				</div>
				<div class="brand-text">
					<h1>FUTURECRAFT</h1>
					<span class="brand-subtitle">AI BASED CAD SYSTEM</span>
				</div>
			</div>

			<!-- Center: Assembly Progress -->
			<div class="header-status">
				<div class="status-row">
					<span class="status-label">ASSEMBLY STATUS</span>
					<span class="status-value">{assemblyComponentCount}/3 MODULES</span>
				</div>
				<div class="progress-track">
					<div class="progress-bar" style="width: {assemblyProgress}%"></div>
					<div class="progress-markers">
						<div class="marker"></div>
						<div class="marker"></div>
						<div class="marker"></div>
						<div class="marker"></div>
					</div>
				</div>
			</div>

			<!-- Right: System Controls -->
			<div class="header-controls">
				<button
					class="control-btn assembly-btn"
					class:active={viewMode === 'assembly'}
					class:disabled={!canAssemble}
					disabled={!canAssemble}
					on:click={goToAssembly}
				>
					<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
						<rect x="3" y="3" width="8" height="8" stroke="currentColor" stroke-width="1.5"/>
						<rect x="13" y="3" width="8" height="8" stroke="currentColor" stroke-width="1.5"/>
						<rect x="3" y="13" width="8" height="8" stroke="currentColor" stroke-width="1.5"/>
						<rect x="13" y="13" width="8" height="8" stroke="currentColor" stroke-width="1.5"/>
					</svg>
					<span>ASSEMBLY</span>
				</button>
			</div>
		</div>
	</header>

	<div class="workspace">
		<!-- Left Panel: Component Editor -->
		<section class="editor-panel">
			{#if viewMode === 'edit'}
				<!-- Component Header with Technical Details -->
				<div class="panel-header">
					<div class="header-row">
						<div class="header-left">
							<span class="component-code">{componentCodes[$activeComponent]}</span>
							<h2 class="component-title">{componentLabels[$activeComponent]}</h2>
						</div>
						<div class="status-indicator" class:complete={$completionStatus[$activeComponent]}>
							<div class="indicator-dot"></div>
							<span>{$completionStatus[$activeComponent] ? 'READY' : 'CONFIG'}</span>
						</div>
					</div>
				</div>

				<!-- Parameter Controls -->
				<div class="panel-content">
					<ComponentEditor componentType={$activeComponent} />
				</div>
			{:else}
				<!-- Assembly View -->
				<div class="panel-header">
					<div class="header-row">
						<div class="header-left">
							<span class="component-code">ASM-MAIN</span>
							<h2 class="component-title">Final Assembly</h2>
						</div>
						<div class="status-indicator complete">
							<div class="indicator-dot"></div>
							<span>ASSEMBLY</span>
						</div>
					</div>
				</div>

				<div class="panel-content">
					<!-- MISSION PROFILE SECTION (Improved UI) -->
					<div class="compile-section" style="margin-bottom: var(--space-6);">
						<div class="compile-header">
							<svg viewBox="0 0 24 24" fill="none">
								<path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="1.5"/>
								<path d="M2 12H22" stroke="currentColor" stroke-width="1.5" stroke-dasharray="2 2"/>
								<path d="M12 2V22" stroke="currentColor" stroke-width="1.5" stroke-dasharray="2 2"/>
							</svg>
							<span>MISSION PROFILE</span>
						</div>

						<div class="mission-controls">
							<!-- Altitude Control -->
							<div class="mission-group">
								<div class="control-header">
									<label>ALTITUDE</label>
									<div class="live-value">
										{$missionProfile.altitude.toLocaleString()} <span class="unit">m</span>
									</div>
								</div>
								
								<div class="slider-container">
									<input 
										type="range" 
										min="500" 
										max="25000" 
										step="500"
										bind:value={$missionProfile.altitude}
										class="tech-slider"
									/>
									<div class="slider-scale">
										<span>SL</span>
										<span>12km</span>
										<span>25km</span>
									</div>
								</div>
								
								<div class="info-badge">
									<span class="badge-label">ZONE</span>
									<span class="badge-value">{atmosphere.zone}</span>
								</div>
							</div>

							<div class="divider-line"></div>

							<!-- Speed Control -->
							<div class="mission-group">
								<div class="control-header">
									<label>DESIGN SPEED</label>
									<div class="live-value">
										MACH {machNumber.toFixed(2)}
									</div>
								</div>

								<div class="slider-container">
									<input 
										type="range" 
										min="50" 
										max="1000" 
										step="10"
										bind:value={$missionProfile.speed}
										class="tech-slider"
									/>
									<div class="slider-scale">
										<span>50 m/s</span>
										<span>1000 m/s</span>
									</div>
								</div>

								<div class="telemetry-row">
									<div class="telemetry-item">
										<span class="t-label">VELOCITY</span>
										<span class="t-val">{$missionProfile.speed} m/s</span>
									</div>
									<div class="telemetry-item right">
										<span class="t-label">CONVERTED</span>
										<span class="t-val">{speedKmph.toFixed(0)} km/h</span>
									</div>
								</div>
							</div>

							<!-- The Context Button -->
							<button class="context-btn" on:click={applyContext} class:applied={$missionProfile.isContextApplied}>
								{#if $missionProfile.isContextApplied}
									<svg viewBox="0 0 24 24" fill="none" class="btn-icon">
										<path d="M5 13l4 4L19 7" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
									</svg>
									<span>CONTEXT LOCKED</span>
								{:else}
									<svg viewBox="0 0 24 24" fill="none" class="btn-icon">
										<path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" stroke="currentColor" stroke-width="1.5"/>
										<path d="M12 8v8m-4-4h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
									</svg>
									<span>APPLY CONTEXT</span>
								{/if}
							</button>
						</div>
					</div>
                    
					<!-- Component Tree -->
					<div class="assembly-tree">
						<div class="tree-title">MODULE STATUS</div>
						{#each Object.entries(componentLabels) as [type, label]}
							<div class="tree-node" class:complete={$completionStatus[type]}>
								<div class="node-connector"></div>
								<div class="node-content">
									<div class="node-header">
										<span class="node-code">{componentCodes[type]}</span>
										<span class="node-label">{label}</span>
									</div>
									<div class="node-status">
										{#if $completionStatus[type]}
											<svg class="check-icon" viewBox="0 0 24 24" fill="none">
												<path d="M5 12L10 17L20 7" stroke="currentColor" stroke-width="2" stroke-linecap="square"/>
											</svg>
											<span>CONFIGURED</span>
										{:else}
											<span class="pending">PENDING</span>
										{/if}
									</div>
								</div>
							</div>
						{/each}
					</div>

					<!-- Compilation Controls -->
					<div class="compile-section">
						<div class="compile-header">
							<svg viewBox="0 0 24 24" fill="none">
								<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5"/>
								<path d="M12 6V12L16 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="square"/>
							</svg>
							<span>COMPILATION</span>
						</div>
						<button
							class="compile-btn"
							class:disabled={!canCompile}
							class:compiling={$isCompiling}
							disabled={!canCompile || $isCompiling}
							on:click={handleCompileAircraft}
						>
							{#if $isCompiling}
								<div class="spinner"></div>
								<span>COMPILING...</span>
							{:else if $compiledAircraft}
								<svg viewBox="0 0 24 24" fill="none">
									<path d="M5 12L10 17L20 7" stroke="currentColor" stroke-width="2"/>
								</svg>
								<span>COMPILED</span>
							{:else}
								<svg viewBox="0 0 24 24" fill="none">
									<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5"/>
									<path d="M10 8L16 12L10 16V8Z" fill="currentColor"/>
								</svg>
								<span>COMPILE AIRCRAFT</span>
							{/if}
						</button>
						{#if !$allComponentsComplete}
							<p class="compile-hint">Complete all modules to enable compilation</p>
						{:else if $compiledAircraft}
							<p class="compile-success">Aircraft compiled successfully</p>
						{/if}
					</div>

					<!-- STRUCTURAL SIMULATION SECTION -->
					<div class="compile-section" style="margin-bottom: var(--space-6); border-color: var(--cyan-600);">
						<div class="compile-header">
							<svg viewBox="0 0 24 24" fill="none">
								<path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
							</svg>
							<span>STRUCTURAL VALIDATION</span>
						</div>

						{#if !simResult}
							<div class="sim-intro">
								Validate structural integrity based on selected materials and mission profile.
							</div>
							<button 
								class="compile-btn"
								class:compiling={isSimulating}
								on:click={handleSimulation}
								disabled={isSimulating || !$allComponentsComplete}
							>
								{#if isSimulating}
									<div class="spinner"></div>
									<span>RUNNING SOLVER...</span>
								{:else}
									<span>RUN STRESS ANALYSIS</span>
								{/if}
							</button>
						{:else}
							<!-- RESULTS DISPLAY -->
							<div class="sim-results">
								<div class="sim-status {simResult.status === 'PASS' ? 'pass' : 'fail'}">
									<span class="status-icon">{simResult.status === 'PASS' ? '✓' : '⚠'}</span>
									<span class="status-text">DESIGN {simResult.status}ED</span>
								</div>
								
								<div class="sim-grid">
									<div class="sim-item">
										<span class="label">SAFETY FACTOR</span>
										<span class="value {simResult.safety_factor < 1.5 ? 'danger' : 'good'}">
											{simResult.safety_factor}x
										</span>
									</div>
									<div class="sim-item">
										<span class="label">MAX STRESS</span>
										<span class="value">{simResult.max_stress} <span class="unit">MPa</span></span>
									</div>
									<div class="sim-item">
										<span class="label">LIFT LOAD</span>
										<span class="value">{simResult.lift_force_kn} <span class="unit">kN</span></span>
									</div>
									<div class="sim-item">
										<span class="label">DYNAMIC PRES.</span>
										<span class="value">{simResult.details.dynamic_pressure} <span class="unit">Pa</span></span>
									</div>
								</div>
								{#if simResult.status === 'FAIL'}
									<button class="optimize-btn" on:click={optimizeDesign}>
										<svg viewBox="0 0 24 24" fill="none" class="opt-icon">
											<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
										</svg>
										<span>AI AUTO-OPTIMIZE DESIGN</span>
									</button>
								{/if}
								<button class="reset-btn" on:click={() => simResult = null}>
									RUN NEW SIMULATION
								</button>
							</div>
						{/if}
					</div>

					<!-- Export Section -->
					<div class="export-section">
						<div class="section-header">
							<svg viewBox="0 0 24 24" fill="none">
								<path d="M12 2L12 16M12 2L8 6M12 2L16 6" stroke="currentColor" stroke-width="1.5"/>
								<path d="M3 16L3 20L21 20L21 16" stroke="currentColor" stroke-width="1.5"/>
							</svg>
							<span>EXPORT</span>
						</div>
						<ExportPanel />
					</div>
				</div>
			{/if}
		</section>

		<!-- Center: 3D Viewport -->
		<section class="viewer-section">
			<div class="viewport-header">
				<div class="viewport-info">
					<span class="viewport-label">3D VIEWPORT</span>
					<div class="viewport-mode">
						<div class="mode-indicator"></div>
						<span>{viewMode === 'assembly' ? 'ASSEMBLY VIEW' : componentLabels[$activeComponent]}</span>
					</div>
				</div>
				<div class="viewport-coords">
					<div class="coord-item">
						<span class="coord-label">X</span>
						<span class="coord-value">0.00</span>
					</div>
					<div class="coord-item">
						<span class="coord-label">Y</span>
						<span class="coord-value">0.00</span>
					</div>
					<div class="coord-item">
						<span class="coord-label">Z</span>
						<span class="coord-value">0.00</span>
					</div>
				</div>
			</div>

			<div class="viewport-canvas">
				<Viewer3D {viewMode} />

				<!-- Corner Brackets (CAD aesthetic) -->
				<div class="viewport-brackets">
					<div class="bracket top-left"></div>
					<div class="bracket top-right"></div>
					<div class="bracket bottom-left"></div>
					<div class="bracket bottom-right"></div>
				</div>
			</div>
		</section>

		<!-- Right Panel: AI Co-Pilot -->
		<section class="copilot-panel">
			<AircraftChat />
		</section>
	</div>

	<!-- Transient toast for context actions -->
	{#if showContextToast}
		<div class="toast toast-success" role="status" aria-live="polite">
			<div class="toast-content">{contextToastText}</div>
		</div>
	{/if}

	<!-- Bottom: Component Module Selector -->
	<nav class="module-selector">
		{#each Object.entries(componentLabels) as [type, label]}
			<button
				class="module-tab"
				class:active={$activeComponent === type && viewMode === 'edit'}
				class:complete={$completionStatus[type]}
				class:generating={$aircraft[type]?.isGenerating}
				on:click={() => selectComponent(type)}
			>
				<div class="tab-header">
					<span class="tab-code">{componentCodes[type]}</span>
					{#if $completionStatus[type]}
						<div class="tab-status complete">
							<svg viewBox="0 0 16 16" fill="none">
								<circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
								<path d="M5 8L7 10L11 6" stroke="currentColor" stroke-width="1.5"/>
							</svg>
						</div>
					{:else if $aircraft[type]?.isGenerating}
						<div class="tab-status generating">
							<div class="spinner-small"></div>
						</div>
					{:else}
						<div class="tab-status pending">
							<svg viewBox="0 0 16 16" fill="none">
								<circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5" stroke-dasharray="2 2"/>
							</svg>
						</div>
					{/if}
				</div>
				<span class="tab-label">{label}</span>
				<div class="tab-indicator"></div>
			</button>
		{/each}
	</nav>
</main>

<style>
	.app-container {
		width: 100vw;
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: var(--blueprint-bg);
		position: relative;
		z-index: 1;
	}

	/* HEADER STYLES */
	.app-header {
		background: var(--blueprint-surface);
		border-bottom: 2px solid var(--border-technical);
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
		position: relative;
		z-index: 10;
	}

	.header-grid {
		display: grid;
		grid-template-columns: 1fr 2fr 1fr;
		gap: var(--space-6);
		padding: var(--space-4) var(--space-6);
		align-items: center;
	}

	/* Brand */
	.header-brand {
		display: flex;
		align-items: center;
		gap: var(--space-4);
	}

	.brand-icon {
		width: 40px;
		height: 40px;
		color: var(--cyan-400);
	}

	.brand-icon svg {
		width: 100%;
		height: 100%;
	}

	.brand-text h1 {
		font-size: 1.25rem;
		font-weight: 700;
		letter-spacing: 0.15em;
		color: var(--gray-100);
		margin: 0;
		line-height: 1;
	}

	.brand-subtitle {
		display: block;
		font-size: 0.625rem;
		font-family: var(--font-technical);
		letter-spacing: 0.1em;
		color: var(--cyan-400);
		margin-top: var(--space-1);
	}

	/* Status */
	.header-status {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	.status-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.status-label {
		font-size: 0.625rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		color: var(--gray-400);
	}

	.status-value {
		font-family: var(--font-technical);
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--cyan-400);
	}

	.progress-track {
		position: relative;
		height: 6px;
		background: var(--blueprint-bg-secondary);
		border: 1px solid var(--border-technical);
		border-radius: 3px;
		overflow: hidden;
	}

	.progress-bar {
		position: absolute;
		left: 0;
		top: 0;
		height: 100%;
		background: linear-gradient(90deg, var(--cyan-600), var(--cyan-400));
		transition: width 0.4s ease;
		box-shadow: 0 0 10px var(--cyan-glow);
	}

	.progress-markers {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		display: flex;
		justify-content: space-between;
		padding: 0 0.5%;
	}

	.marker {
		width: 2px;
		height: 100%;
		background: var(--blueprint-surface);
	}

	/* Controls */
	.header-controls {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-3);
	}

	.control-btn {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-3) var(--space-5);
		background: var(--blueprint-bg-secondary);
		border: 1px solid var(--border-technical);
		color: var(--cyan-400);
		font-size: 0.75rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		cursor: pointer;
		transition: all 0.2s;
		position: relative;
		overflow: hidden;
	}

	.control-btn svg {
		width: 18px;
		height: 18px;
	}

	.control-btn:hover:not(:disabled) {
		background: var(--blueprint-surface);
		border-color: var(--cyan-500);
		box-shadow: 0 0 15px var(--cyan-glow);
	}

	.control-btn.active {
		background: var(--cyan-600);
		border-color: var(--cyan-500);
		color: white;
		box-shadow: 0 0 20px var(--cyan-glow);
	}

	.control-btn.disabled {
		opacity: 0.4;
		cursor: not-allowed;
		border-color: var(--border-subtle);
		color: var(--gray-500);
	}

	/* WORKSPACE */
	.workspace {
		flex: 1;
		display: grid;
		grid-template-columns: 340px 1fr 280px;
		overflow: hidden;
		position: relative;
	}

	/* PANEL STYLES */
	.editor-panel,
	.copilot-panel {
		background: var(--blueprint-bg-secondary);
		border-right: 1px solid var(--border-technical);
		display: flex;
		flex-direction: column;
		overflow: hidden;
		position: relative;
	}

	.copilot-panel {
		border-right: none;
		border-left: 1px solid var(--border-technical);
	}

	.panel-header {
		padding: var(--space-3) var(--space-4);
		border-bottom: 1px solid var(--border-technical);
		background: var(--blueprint-surface);
		flex-shrink: 0;
	}

	.header-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: var(--space-3);
	}

	.component-code {
		font-family: var(--font-technical);
		font-size: 0.5625rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		color: var(--cyan-400);
		padding: var(--space-1) var(--space-2);
		background: var(--blueprint-bg);
		border: 1px solid var(--border-technical);
		flex-shrink: 0;
	}

	.component-title {
		font-size: 0.875rem;
		font-weight: 700;
		color: var(--gray-100);
		margin: 0;
		letter-spacing: 0.05em;
		text-transform: uppercase;
	}

	.status-indicator {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		font-size: 0.5625rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		color: var(--gray-400);
		flex-shrink: 0;
	}

	.indicator-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--gray-500);
		border: 1px solid var(--gray-400);
		animation: pulse-subtle 2s infinite;
	}

	.status-indicator.complete .indicator-dot {
		background: var(--green-success);
		border-color: var(--green-success);
		box-shadow: 0 0 8px var(--green-glow);
	}

	.status-indicator.complete {
		color: var(--green-success);
	}

	@keyframes pulse-subtle {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.6; }
	}

	.panel-content {
		flex: 1;
		overflow-y: auto;
		padding: var(--space-5);
	}

	/* ASSEMBLY TREE */
	.assembly-tree {
		margin-bottom: var(--space-6);
	}

	.tree-title {
		font-size: 0.625rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		color: var(--gray-400);
		margin-bottom: var(--space-4);
		padding-bottom: var(--space-2);
		border-bottom: 1px solid var(--border-subtle);
	}

	.tree-node {
		display: flex;
		gap: var(--space-3);
		margin-bottom: var(--space-4);
		position: relative;
	}

	.node-connector {
		width: 2px;
		background: var(--border-subtle);
		position: relative;
	}

	.tree-node.complete .node-connector {
		background: var(--green-success);
		box-shadow: 0 0 5px var(--green-glow);
	}

	.node-connector::before {
		content: '';
		position: absolute;
		left: 0;
		top: 50%;
		width: 12px;
		height: 2px;
		background: inherit;
	}

	.node-content {
		flex: 1;
		padding: var(--space-3);
		background: var(--blueprint-surface);
		border: 1px solid var(--border-subtle);
		transition: all 0.2s;
	}

	.tree-node.complete .node-content {
		border-color: var(--green-success);
		background: rgba(102, 187, 106, 0.05);
	}

	.node-header {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		margin-bottom: var(--space-2);
	}

	.node-code {
		font-family: var(--font-technical);
		font-size: 0.625rem;
		font-weight: 700;
		color: var(--cyan-400);
	}

	.node-label {
		font-size: 0.8125rem;
		font-weight: 600;
		color: var(--gray-200);
	}

	.node-status {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		font-size: 0.625rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		color: var(--green-success);
	}

	.check-icon {
		width: 14px;
		height: 14px;
	}

	.pending {
		color: var(--gray-500);
	}

	/* COMPILATION SECTION */
	.compile-section {
		margin-bottom: var(--space-6);
		padding: var(--space-5);
		background: var(--blueprint-surface);
		border: 1px solid var(--border-technical);
		position: relative;
	}

	.compile-header {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		margin-bottom: var(--space-4);
		font-size: 0.625rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		color: var(--cyan-400);
	}

	.compile-header svg {
		width: 16px;
		height: 16px;
	}

	.compile-btn {
		width: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-3);
		padding: var(--space-4);
		background: linear-gradient(135deg, var(--cyan-700), var(--cyan-600));
		border: 1px solid var(--cyan-500);
		color: white;
		font-size: 0.8125rem;
		font-weight: 700;
		letter-spacing: 0.05em;
		cursor: pointer;
		transition: all 0.3s;
		text-transform: uppercase;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
	}

	.compile-btn svg {
		width: 20px;
		height: 20px;
	}

	.compile-btn:hover:not(:disabled) {
		background: linear-gradient(135deg, var(--cyan-600), var(--cyan-500));
		box-shadow: 0 6px 20px var(--cyan-glow);
		transform: translateY(-1px);
	}

	.compile-btn.disabled {
		background: var(--blueprint-bg);
		border-color: var(--border-subtle);
		color: var(--gray-500);
		cursor: not-allowed;
		box-shadow: none;
	}

	.compile-btn.compiling {
		background: var(--amber-warning);
		border-color: var(--amber-warning);
		animation: pulse-glow 1.5s infinite;
	}

	@keyframes pulse-glow {
		0%, 100% {
			box-shadow: 0 4px 12px rgba(255, 167, 38, 0.3);
		}
		50% {
			box-shadow: 0 6px 24px rgba(255, 167, 38, 0.6);
		}
	}

	.spinner {
		width: 18px;
		height: 18px;
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-top-color: white;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.compile-hint,
	.compile-success {
		margin-top: var(--space-3);
		font-size: 0.6875rem;
		text-align: center;
		color: var(--gray-400);
	}

	.compile-success {
		color: var(--green-success);
	}

	/* EXPORT SECTION */
	.export-section {
		padding: var(--space-5);
		background: var(--blueprint-surface);
		border: 1px solid var(--border-technical);
	}

	.section-header {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		margin-bottom: var(--space-4);
		font-size: 0.625rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		color: var(--cyan-400);
	}

	.section-header svg {
		width: 16px;
		height: 16px;
	}

	/* 3D VIEWPORT */
	.viewer-section {
		background: var(--blueprint-bg);
		display: flex;
		flex-direction: column;
		position: relative;
		overflow: hidden;
	}

	.viewport-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--space-4) var(--space-5);
		background: rgba(15, 31, 54, 0.8);
		border-bottom: 1px solid var(--border-technical);
		backdrop-filter: blur(10px);
		z-index: 5;
	}

	.viewport-info {
		display: flex;
		align-items: center;
		gap: var(--space-5);
	}

	.viewport-label {
		font-size: 0.625rem;
		font-weight: 700;
		letter-spacing: 0.15em;
		color: var(--gray-400);
	}

	.viewport-mode {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-2) var(--space-3);
		background: var(--blueprint-surface);
		border: 1px solid var(--border-technical);
		font-size: 0.6875rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		color: var(--cyan-400);
	}

	.mode-indicator {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--cyan-500);
		box-shadow: 0 0 8px var(--cyan-glow);
		animation: pulse-bright 2s infinite;
	}

	@keyframes pulse-bright {
		0%, 100% {
			opacity: 1;
			transform: scale(1);
		}
		50% {
			opacity: 0.7;
			transform: scale(0.9);
		}
	}

	.viewport-coords {
		display: flex;
		gap: var(--space-4);
	}

	.coord-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-1);
	}

	.coord-label {
		font-size: 0.5625rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		color: var(--gray-500);
	}

	.coord-value {
		font-family: var(--font-technical);
		font-size: 0.6875rem;
		font-weight: 600;
		color: var(--cyan-400);
	}

	.viewport-canvas {
		flex: 1;
		position: relative;
		overflow: hidden;
	}

	/* Corner Brackets */
	.viewport-brackets {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		pointer-events: none;
		z-index: 2;
	}

	.bracket {
		position: absolute;
		width: 40px;
		height: 40px;
		border: 2px solid var(--cyan-600);
		opacity: 0.6;
	}

	.bracket.top-left {
		top: 20px;
		left: 20px;
		border-right: none;
		border-bottom: none;
	}

	.bracket.top-right {
		top: 20px;
		right: 20px;
		border-left: none;
		border-bottom: none;
	}

	.bracket.bottom-left {
		bottom: 20px;
		left: 20px;
		border-right: none;
		border-top: none;
	}

	.bracket.bottom-right {
		bottom: 20px;
		right: 20px;
		border-left: none;
		border-top: none;
	}

	/* MODULE SELECTOR */
	.module-selector {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		background: var(--blueprint-surface);
		border-top: 2px solid var(--border-technical);
		position: relative;
		z-index: 10;
	}

	.module-tab {
		display: flex;
		flex-direction: column;
		padding: var(--space-4) var(--space-5);
		background: transparent;
		border: none;
		border-right: 1px solid var(--border-subtle);
		cursor: pointer;
		transition: all 0.2s;
		position: relative;
		color: var(--gray-400);
	}

	.module-tab:last-child {
		border-right: none;
	}

	.tab-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--space-2);
	}

	.tab-code {
		font-family: var(--font-technical);
		font-size: 0.625rem;
		font-weight: 700;
		letter-spacing: 0.05em;
	}

	.tab-status {
		width: 16px;
		height: 16px;
	}

	.tab-status svg {
		width: 100%;
		height: 100%;
	}

	.tab-status.complete {
		color: var(--green-success);
	}

	.tab-status.generating .spinner-small {
		width: 14px;
		height: 14px;
		border: 2px solid var(--cyan-700);
		border-top-color: var(--cyan-400);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	.tab-status.pending {
		color: var(--gray-600);
	}

	.tab-label {
		font-size: 0.8125rem;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-transform: uppercase;
		margin-bottom: var(--space-2);
	}

	.tab-indicator {
		height: 3px;
		background: transparent;
		transition: all 0.3s;
	}

	.module-tab:hover {
		background: var(--blueprint-bg-secondary);
		color: var(--gray-200);
	}

	.module-tab.active {
		background: var(--blueprint-bg);
		color: var(--cyan-400);
	}

	.module-tab.active .tab-indicator {
		background: linear-gradient(90deg, var(--cyan-600), var(--cyan-400));
		box-shadow: 0 0 10px var(--cyan-glow);
	}

	.module-tab.complete:not(.active) {
		color: var(--green-success);
	}

	.module-tab.generating {
		color: var(--amber-warning);
	}

	/* Mission Profile Styling (Improved) */
	.mission-controls {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	.mission-group {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	/* Labels & Values */
	.control-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
	}

	.control-header label {
		font-size: 0.625rem;
		font-weight: 700;
		color: var(--gray-400);
		letter-spacing: 0.1em;
	}

	.live-value {
		font-family: var(--font-technical);
		font-size: 0.875rem;
		color: var(--cyan-400);
		font-weight: 600;
	}

	.live-value .unit {
		font-size: 0.625rem;
		color: var(--gray-500);
	}

	/* Technical Slider */
	.slider-container {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.tech-slider {
		-webkit-appearance: none;
		width: 100%;
		height: 4px;
		background: var(--blueprint-bg-secondary);
		border: 1px solid var(--gray-700);
		border-radius: 0;
		outline: none;
	}

	.tech-slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		width: 12px;
		height: 12px;
		background: var(--cyan-500);
		border: 1px solid white;
		cursor: pointer;
		box-shadow: 0 0 10px var(--cyan-glow);
	}

	.tech-slider::-moz-range-thumb {
		width: 12px;
		height: 12px;
		background: var(--cyan-500);
		border: 1px solid white;
		cursor: pointer;
	}

	.slider-scale {
		display: flex;
		justify-content: space-between;
		font-family: var(--font-technical);
		font-size: 0.5rem;
		color: var(--gray-600);
	}

	/* Badges & Info */
	.info-badge {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		background: rgba(3, 169, 244, 0.05);
		border: 1px solid var(--border-technical);
		padding: 4px 8px;
		margin-top: 4px;
	}

	.badge-label {
		font-size: 0.5rem;
		color: var(--gray-500);
		font-weight: 700;
	}

	.badge-value {
		font-family: var(--font-technical);
		font-size: 0.6875rem;
		color: var(--cyan-300);
	}

	/* Divider */
	.divider-line {
		height: 1px;
		background: var(--border-subtle);
		width: 100%;
	}

	/* Telemetry Row */
	.telemetry-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--space-2);
		margin-top: 4px;
	}

	.telemetry-item {
		display: flex;
		flex-direction: column;
	}
	
	.telemetry-item.right {
		text-align: right;
	}

	.t-label {
		font-size: 0.5rem;
		color: var(--gray-500);
	}

	.t-val {
		font-family: var(--font-technical);
		font-size: 0.75rem;
		color: var(--gray-300);
	}

	/* The Context Button - Completely Redesigned */
	.context-btn {
		margin-top: var(--space-2);
		width: 100%;
		padding: 10px;
		background: transparent;
		border: 1px solid var(--cyan-500);
		color: var(--cyan-400);
		font-size: 0.75rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-2);
		transition: all 0.2s ease;
		cursor: pointer;
		text-transform: uppercase;
	}

	.context-btn:hover {
		background: rgba(3, 169, 244, 0.1);
		box-shadow: 0 0 15px var(--cyan-glow);
		transform: translateY(-1px);
	}

	.context-btn.applied {
		background: rgba(16, 185, 129, 0.1); /* Green tint */
		border-color: var(--green-success);
		color: var(--green-success);
	}

	.context-btn.applied:hover {
		box-shadow: 0 0 15px var(--green-glow);
	}

	.btn-icon {
		width: 16px;
		height: 16px;
	}

	/* Toast */
	.toast {
		position: fixed;
		top: 20px;
		right: 20px;
		z-index: 9999;
		padding: 0.6rem 1rem;
		border-radius: 8px;
		box-shadow: 0 6px 18px rgba(2,6,23,0.4);
		font-weight: 600;
		color: white;
		display: flex;
		align-items: center;
		gap: 0.6rem;
	}

	.toast-success {
		background: linear-gradient(180deg, #10b981, #059669);
	}

	.toast-content {
		font-size: 0.95rem;
	}

	/* Simulation Styles */
	.sim-intro {
		font-size: 0.75rem;
		color: var(--gray-400);
		margin-bottom: var(--space-3);
		font-style: italic;
	}

	.sim-results {
		background: var(--blueprint-bg);
		padding: var(--space-3);
		border: 1px solid var(--border-technical);
		margin-top: var(--space-2);
	}

	.sim-status {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		font-weight: 800;
		font-size: 1rem;
		padding-bottom: var(--space-3);
		border-bottom: 1px solid var(--border-subtle);
		margin-bottom: var(--space-3);
		letter-spacing: 0.05em;
	}

	.sim-status.pass { 
		color: var(--green-success); 
		text-shadow: 0 0 15px rgba(102, 187, 106, 0.4);
	}
	.sim-status.fail { 
		color: var(--red-error); 
		text-shadow: 0 0 15px rgba(239, 83, 80, 0.4);
	}

	.sim-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--space-4);
		margin-bottom: var(--space-4);
	}

	.sim-item {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.sim-item .label {
		font-size: 0.55rem;
		color: var(--gray-500);
		font-weight: 700;
		letter-spacing: 0.05em;
	}

	.sim-item .value {
		font-family: var(--font-technical);
		font-size: 1rem;
		color: var(--cyan-300);
	}

	.sim-item .value.danger { color: var(--red-error); }
	.sim-item .value.good { color: var(--green-success); }

	.sim-item .unit {
		font-size: 0.6rem;
		color: var(--gray-500);
	}

	.reset-btn {
		width: 100%;
		padding: var(--space-2);
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid var(--border-subtle);
		color: var(--gray-400);
		font-size: 0.65rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.reset-btn:hover { 
		background: var(--blueprint-surface); 
		color: var(--gray-100);
		border-color: var(--gray-500);
	}
	.optimize-btn {
		width: 100%;
		padding: var(--space-3);
		background: rgba(16, 185, 129, 0.1);
		border: 1px solid var(--green-success);
		color: var(--green-success);
		font-size: 0.75rem;
		font-weight: 800;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-2);
		margin-bottom: var(--space-3);
		transition: all 0.2s;
		box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
		animation: pulse-bright 2s infinite;
	}

	.optimize-btn:hover {
		background: rgba(16, 185, 129, 0.2);
		transform: translateY(-2px);
	}

	.opt-icon {
		width: 16px;
		height: 16px;
	}
</style>