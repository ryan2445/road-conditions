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
  <h1>Road Cameras</h1>
  <p class="timestamp">Updated: {formattedTime()}</p>
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
</style>
