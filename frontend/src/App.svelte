<script lang="ts">
  import { fetchRoadConditions } from './lib/api';
  import type { RoadConditionsData } from './lib/types';
  import Header from './lib/components/Header.svelte';
  import CameraCard from './lib/components/CameraCard.svelte';

  let data: RoadConditionsData | null = $state(null);
  let error: string | null = $state(null);
  let loading = $state(true);

  async function loadData() {
    try {
      loading = true;
      error = null;
      data = await fetchRoadConditions();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load data';
    } finally {
      loading = false;
    }
  }

  $effect(() => {
    loadData();
  });
</script>

<main>
  {#if loading}
    <p class="status">Loading...</p>
  {:else if error}
    <p class="status error">{error}</p>
  {:else if data}
    <Header timestamp={data.timestamp} />
    <div class="grid">
      {#each data.cameras as camera (camera.id)}
        <CameraCard {camera} />
      {/each}
    </div>
  {/if}
</main>

<style>
  :global(body) {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    margin: 0;
    padding: 20px;
    background: #f5f5f5;
  }

  main {
    max-width: 1200px;
    margin: 0 auto;
  }

  .status {
    text-align: center;
    color: #666;
    padding: 40px;
  }

  .status.error {
    color: #d32f2f;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
  }
</style>
