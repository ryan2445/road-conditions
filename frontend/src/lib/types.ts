export interface CameraData {
  id: string;
  name: string;
  error: boolean;
  clearness_score: number | null;
  image_url: string | null;
}

export interface CameraGroup {
  name: string;
  cameras: CameraData[];
}

export interface RoadConditionsData {
  timestamp: string;
  groups: CameraGroup[];
}
