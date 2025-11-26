<script lang="ts">
	import { apiService } from '$lib/services/apiService';
	import { currentModel } from '$lib/stores/modelStore';
	import { compiledAircraft, isCompiling } from '$lib/stores/aircraftStore';
	
	// Determine which model to export:
	// If we have a Compiled Aircraft (Assembly view), use that.
	// Otherwise, use the Current Model (Editor view).
	$: modelToExport = $compiledAircraft || $currentModel;
	
	let isExporting = false;

	async function handleExport(format: 'stl' | 'step' | 'iges') {
		if (!modelToExport) return;

		isExporting = true;
		try {
			const blob = await apiService.exportModel(modelToExport.id, {
				format,
				options: { binary: true, units: 'm' }
			}, modelToExport);

			// Create download link
			const url = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			// Name the file based on the model name
			a.download = `${modelToExport.name.replace(/\s+/g, '_')}.${format}`;
			document.body.appendChild(a);
			a.click();
			window.URL.revokeObjectURL(url);
			document.body.removeChild(a);
		} catch (error) {
			console.error('Export failed:', error);
			alert('Export failed. See console for details.');
		} finally {
			isExporting = false;
		}
	}
</script>

<div class="export-panel">
	{#if modelToExport}
		<div class="export-grid">
			<button class="export-btn" disabled={isExporting} on:click={() => handleExport('stl')}>
				<span class="ext">STL</span>
				<span class="desc">3D PRINTING</span>
			</button>
			<button class="export-btn" disabled={isExporting} on:click={() => handleExport('step')}>
				<span class="ext">STEP</span>
				<span class="desc">CAD SOLID</span>
			</button>
			<button class="export-btn" disabled={isExporting} on:click={() => handleExport('iges')}>
				<span class="ext">IGES</span>
				<span class="desc">SURFACE</span>
			</button>
		</div>
		<div class="file-info">
			Ready to export: <span class="filename">{modelToExport.name}</span>
		</div>
	{:else}
		<div class="empty-state">
			<div class="icon-box">
				<svg viewBox="0 0 24 24" fill="none">
					<path d="M12 15V3m0 12l-4-4m4 4l4-4M2 17l.621 2.485A2 2 0 0 0 4.561 21h14.878a2 2 0 0 0 1.94-1.515L22 17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
				</svg>
			</div>
			<p class="empty-text">
				{#if $isCompiling}
					Compiling aircraft geometry...
				{:else}
					Generate a model or Compile Aircraft to enable export
				{/if}
			</p>
		</div>
	{/if}
</div>

<style>
	.export-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--space-3);
		margin-bottom: var(--space-3);
	}

	.export-btn {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--space-3);
		background: var(--blueprint-bg);
		border: 1px solid var(--cyan-500);
		cursor: pointer;
		transition: all 0.2s;
	}

	.export-btn:hover:not(:disabled) {
		background: rgba(3, 169, 244, 0.1);
		box-shadow: 0 0 15px var(--cyan-glow);
		transform: translateY(-2px);
	}

	.export-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		border-color: var(--gray-600);
	}

	.ext {
		font-weight: 800;
		font-size: 1rem;
		color: var(--cyan-400);
		margin-bottom: 4px;
	}

	.desc {
		font-size: 0.5rem;
		color: var(--gray-400);
		letter-spacing: 0.05em;
	}

	.file-info {
		font-size: 0.6875rem;
		color: var(--gray-400);
		text-align: center;
	}

	.filename {
		color: var(--gray-100);
		font-family: var(--font-technical);
	}

	/* Empty State */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--space-4);
		border: 1px dashed var(--border-technical);
		background: rgba(10, 22, 40, 0.5);
	}

	.icon-box {
		color: var(--gray-600);
		width: 24px;
		height: 24px;
		margin-bottom: var(--space-2);
	}
	
	.icon-box svg {
		width: 100%;
		height: 100%;
	}

	.empty-text {
		font-size: 0.75rem;
		color: var(--gray-500);
		text-align: center;
		line-height: 1.4;
	}
</style>