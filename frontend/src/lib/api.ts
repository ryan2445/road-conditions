import type { RoadConditionsData } from './types';

export async function fetchRoadConditions(): Promise<RoadConditionsData> {
  const response = await fetch('/data.json');
  if (!response.ok) {
    throw new Error(`Failed to fetch road conditions: ${response.statusText}`);
  }
  return response.json();
}
