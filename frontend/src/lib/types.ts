export interface CameraData {
  id: string;
  name: string;
  error: boolean;
  clearness_score: number | null;
  image_url: string | null;
}

export interface RoadConditionsData {
  timestamp: string;
  cameras: CameraData[];
}
