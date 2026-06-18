// Events streamed from the backend over SSE.
export interface AgentEvent {
  agent: string;
  kind: string; // plan | route | result | revise | approve | final | start | done | error
  text: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any;
}

export interface HealthInfo {
  status: string;
  mode: string;
  model: string | null;
}

export interface Geo {
  lat?: number;
  lon?: number;
  formatted?: string;
  country?: string;
}

export interface FlightOption {
  airline: string;
  flight_number?: string;
  depart_time?: string;
  arrive_time?: string;
  tier: string;
  total_price: number;
  price_estimated?: boolean;
}

export interface HotelOption {
  name: string;
  lat?: number;
  lon?: number;
  stars?: number | null;
  website?: string;
  nightly_rate: number;
  nights: number;
  total_price: number;
  price_estimated?: boolean;
}

export interface Poi {
  name: string;
  category: string;
  lat?: number;
  lon?: number;
}

// Loose itinerary shape — the backend assembles every agent's slice here.
export interface Itinerary {
  summary?: string;
  currency?: { code: string; symbol: string };
  preferences?: Record<string, unknown>;
  destination?: {
    name?: string;
    blurb?: string;
    best_time?: string;
    highlights?: string[];
    why_chosen?: string;
    geo?: Geo;
    population?: number;
    region?: string;
  };
  weather?: {
    available?: boolean;
    summary?: string;
    avg_high_c?: number;
    avg_rain_pct?: number;
    days?: { date: string; high_c: number; low_c: number; rain_pct: number; condition: string }[];
  };
  flights?: {
    available?: boolean;
    summary?: string;
    route?: string;
    distance_km?: number;
    source?: string;
    cheapest?: FlightOption;
    options?: FlightOption[];
  };
  hotels?: {
    available?: boolean;
    summary?: string;
    source?: string;
    best_value?: HotelOption;
    options?: HotelOption[];
  };
  activities?: {
    estimated_cost?: number;
    plan?: { day: number; morning: string; afternoon: string; evening: string }[];
    pois?: Poi[];
  };
  logistics?: {
    available?: boolean;
    summary?: string;
    currency?: string;
    languages?: string[];
    timezone?: string;
    flag?: string;
  };
  budget?: {
    total?: number;
    target?: number | null;
    over_budget?: boolean;
    remaining?: number | null;
    breakdown?: Record<string, number>;
  };
  critic?: { verdict?: string; issues?: string[]; action?: string };
}
