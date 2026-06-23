<script lang="ts">
  import type { RoadConditionAlert } from '../types';

  interface Props {
    alerts: RoadConditionAlert[];
  }

  let { alerts }: Props = $props();
</script>

<div class="alerts">
  {#each alerts as alert (alert.roadway + alert.condition)}
    <div class="alert">
      <span class="alert-icon">&#9888;</span>
      <div class="alert-content">
        <strong>{alert.condition}</strong>
        <span class="alert-roadway">{alert.roadway}</span>
        {#if alert.description}
          <span class="alert-segment">{alert.description}</span>
        {/if}
        {#if alert.secondaryConditions.length > 0}
          <span class="alert-secondary">{alert.secondaryConditions.join(', ')}</span>
        {/if}
      </div>
      <span class="alert-time">{alert.lastUpdated}</span>
    </div>
  {/each}
</div>

<style>
  .alerts {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 12px;
  }

  .alert {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 0.9rem;
    color: #664d03;
  }

  .alert-icon {
    font-size: 1.2rem;
    flex-shrink: 0;
    line-height: 1.4;
  }

  .alert-content {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 8px;
    flex: 1;
    line-height: 1.4;
  }

  .alert-roadway {
    color: #856404;
  }

  .alert-segment {
    flex-basis: 100%;
    font-size: 0.85rem;
    color: #856404;
  }

  .alert-secondary {
    flex-basis: 100%;
    font-size: 0.85rem;
    font-style: italic;
    color: #856404;
  }

  .alert-time {
    font-size: 0.8rem;
    color: #997404;
    white-space: nowrap;
    flex-shrink: 0;
    line-height: 1.4;
  }
</style>
