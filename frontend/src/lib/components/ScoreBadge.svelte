<script lang="ts">
  interface Props {
    score: number;
  }

  let { score }: Props = $props();

  const hue = $derived(Math.round(score * 120));
  const percentage = $derived(Math.round(score * 100));
</script>

<span class="badge" style="background-color: hsl({hue}, 70%, 80%);">
  {percentage}%
</span>

<style>
  .badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 14px;
  }
</style>
