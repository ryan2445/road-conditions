<script lang="ts">
  import type { CameraData } from '../types';

  interface Props {
    camera: CameraData;
  }

  let { camera }: Props = $props();
</script>

<div class="card">
  <div class="image-container">
    {#if camera.error}
      <div class="error-placeholder">Error loading camera</div>
    {:else if camera.image_url}
      <img src={camera.image_url} alt={camera.name} />
    {:else}
      <div class="error-placeholder">No image</div>
    {/if}
  </div>
  <div class="info">
    <span class="name">{camera.name}</span>
    {#if camera.error}
      <span class="error-badge">Error</span>
    {/if}
  </div>
</div>

<style>
  .card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    overflow: hidden;
  }

  .image-container {
    aspect-ratio: 16 / 9;
    background: #f0f0f0;
  }

  .image-container img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .error-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #d32f2f;
    font-size: 14px;
  }

  .info {
    padding: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
  }

  .name {
    font-weight: 500;
    color: #333;
    font-size: 14px;
  }

  .error-badge {
    color: #d32f2f;
    font-weight: bold;
    font-size: 14px;
  }
</style>
