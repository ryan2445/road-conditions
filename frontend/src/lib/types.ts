export interface CameraData {
  id: string;
  name: string;
  error: boolean;
  clearness_score: number | null;
  image_url: string | null;
}

export interface RoadConditionAlert {
  roadway: string;
  description: string;
  condition: string;
  secondaryConditions: string[];
  lastUpdated: string;
}

export interface CameraGroup {
  name: string;
  cameras: CameraData[];
  alerts?: RoadConditionAlert[];
}

export interface RoadConditionsData {
  timestamp: string;
  groups: CameraGroup[];
}
