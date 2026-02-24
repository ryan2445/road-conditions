<script lang="ts">
  interface Props {
    timestamp: string;
  }

  let { timestamp }: Props = $props();

  const formattedTime = $derived(() => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      timeZone: 'America/Los_Angeles',
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  });
</script>

<header>
  <h1>Road Conditions</h1>
  <p class="timestamp">Updated: {formattedTime()}</p>
  <!-- <p class="legend">
    Road score:
    <span class="legend-bar"></span>
    0% = wet, 100% = dry
  </p> -->
</header>

<style>
  header {
    margin-bottom: 24px;
  }

  h1 {
    margin: 0 0 8px 0;
    color: #333;
  }

  .timestamp {
    color: #666;
    margin: 0 0 10px 0;
  }

  /* .legend {
    color: #666;
    font-size: 14px;
    margin: 0;
  } */

  /* .legend-bar {
    display: inline-block;
    width: 150px;
    height: 16px;
    background: linear-gradient(to right, hsl(0, 70%, 80%), hsl(60, 70%, 80%), hsl(120, 70%, 80%));
    border-radius: 3px;
    vertical-align: middle;
    margin: 0 8px;
  } */
</style>
