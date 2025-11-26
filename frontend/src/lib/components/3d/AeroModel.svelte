<script lang="ts">
	import { T } from '@threlte/core';
	import type { Model3D } from '$lib/types/model';
	import { BufferGeometry, BufferAttribute, DoubleSide } from 'three';

	export let model: Model3D;

	let geometry: BufferGeometry;

	$: {
		// Create new geometry whenever model changes
		geometry = new BufferGeometry();

		if (model?.geometry?.vertices && model?.geometry?.indices) {
			console.log('Creating geometry with', model.geometry.vertices.length, 'vertices');
			
			// Convert arrays to Typed Arrays for Three.js
			const vertices = new Float32Array(model.geometry.vertices);
			const indices = new Uint32Array(model.geometry.indices);

			geometry.setAttribute(
				'position',
				new BufferAttribute(vertices, 3)
			);

			geometry.setIndex(new BufferAttribute(indices, 1));

			if (model.geometry.normals) {
				const normals = new Float32Array(model.geometry.normals);
				geometry.setAttribute(
					'normal',
					new BufferAttribute(normals, 3)
				);
			} else {
				geometry.computeVertexNormals();
			}
			
			console.log('Geometry created successfully', geometry);
		}
	}
</script>

{#if geometry && geometry.attributes.position}
	<T.Group position={[0, 0.5, 0]}>
		<T.Mesh
			{geometry}
			receiveShadow
			castShadow
		>
			<T.MeshStandardMaterial
				color="#3b82f6"
				metalness={0.4}
				roughness={0.3}
				side={DoubleSide}
			/>
		</T.Mesh>

		<!-- Wireframe overlay -->
		<T.Mesh
			{geometry}
		>
			<T.MeshBasicMaterial
				color="#60a5fa"
				wireframe
				transparent
				opacity={0.3}
			/>
		</T.Mesh>
	</T.Group>
{/if}
