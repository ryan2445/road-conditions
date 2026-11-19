import { mockRoadConditionsData } from './mockData';
import type { RoadConditionsData } from './types';

function shouldUseMockData(): boolean {
  if (import.meta.env.MODE === 'mock' || import.meta.env.VITE_USE_MOCK === 'true') {
    return true;
  }
  return (
    import.meta.env.DEV &&
    typeof window !== 'undefined' &&
    new URLSearchParams(window.location.search).has('mock')
  );
}

export async function fetchRoadConditions(): Promise<RoadConditionsData> {
  if (shouldUseMockData()) {
    return mockRoadConditionsData;
  }

  const response = await fetch('/data.json');
  if (!response.ok) {
    throw new Error(`Failed to fetch road conditions: ${response.statusText}`);
  }
  return response.json();
}
