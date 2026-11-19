import type { RoadConditionsData } from './types';

function makePlaceholderImage(label: string, accent: string): string {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#1e293b"/>
        <stop offset="100%" stop-color="#334155"/>
      </linearGradient>
    </defs>
    <rect width="640" height="360" fill="url(#bg)"/>
    <rect x="0" y="290" width="640" height="70" fill="${accent}" opacity="0.25"/>
    <text x="320" y="175" text-anchor="middle" fill="#e2e8f0" font-family="sans-serif" font-size="22" font-weight="600">${label}</text>
    <text x="320" y="210" text-anchor="middle" fill="#94a3b8" font-family="sans-serif" font-size="14">Mock Camera Feed</text>
  </svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

export const mockRoadConditionsData: RoadConditionsData = {
  timestamp: new Date().toISOString(),
  groups: [
    {
      name: 'Mt Rose',
      alerts: [
        {
          roadway: 'SR-431 (Mt. Rose Hwy)',
          description: 'From Incline Village to Mt. Rose Summit (MP 0.0 - 8.5)',
          condition: 'Chains or Snow Tires Required',
          secondaryConditions: ['Blowing Snow', 'Reduced Visibility'],
          lastUpdated: '10 mins ago',
        },
        {
          roadway: 'SR-431 (Mt. Rose Hwy)',
          description: 'From Mt. Rose Summit to Thomas Creek (MP 8.5 - 16.2)',
          condition: 'Chains or Snow Tires Required',
          secondaryConditions: ['Icy Patches'],
          lastUpdated: '15 mins ago',
        },
      ],
      cameras: [
        {
          id: '5008',
          name: 'SR431 @ Thomas Creek',
          error: false,
          image_url: makePlaceholderImage('SR431 @ Thomas Creek', '#38bdf8'),
        },
        {
          id: '5265',
          name: 'SR431 Mt Rose Summit',
          error: false,
          image_url: makePlaceholderImage('SR431 Mt Rose Summit', '#38bdf8'),
        },
        {
          id: '5093',
          name: 'SR-431 @ Mt Rose Ski Area',
          error: true,
          image_url: null,
        },
      ],
    },
    {
      name: 'Washoe Lake',
      alerts: [
        {
          roadway: 'I-580',
          description: 'Between Washoe Valley and Galena Creek Bridge',
          condition: 'High Wind Advisory',
          secondaryConditions: ['High-Profile Vehicles Prohibited'],
          lastUpdated: '5 mins ago',
        },
      ],
      cameras: [
        {
          id: '9286',
          name: 'I580@Galena Creek Bridge',
          error: false,
          image_url: makePlaceholderImage('I580 @ Galena Creek Bridge', '#f59e0b'),
        },
        {
          id: '9295',
          name: 'I580 @ N. Washoe Valley',
          error: false,
          image_url: makePlaceholderImage('I580 @ N. Washoe Valley', '#f59e0b'),
        },
      ],
    },
    {
      name: 'I80',
      alerts: [
        {
          roadway: 'I-80',
          description: 'Eastbound from State Line to Verdi (MP 0.0 - 4.0)',
          condition: 'Wet Pavement',
          secondaryConditions: [],
          lastUpdated: '22 mins ago',
        },
        {
          roadway: 'I-80',
          description: 'Westbound from Mogul to State Line (MP 0.0 - 7.0)',
          condition: 'Wet Pavement',
          secondaryConditions: ['Fog'],
          lastUpdated: '22 mins ago',
        },
      ],
      cameras: [
        {
          id: '5010',
          name: 'I-80 @ Verdi',
          error: false,
          image_url: makePlaceholderImage('I-80 @ Verdi', '#10b981'),
        },
      ],
    },
  ],
};
