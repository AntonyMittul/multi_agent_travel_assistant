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

// Loose itinerary shape — the backend assembles every agent's slice here.
export interface Itinerary {
  summary?: string;
  preferences?: Record<string, unknown>;
  destination?: {
    name?: string;
    blurb?: string;
    best_time?: string;
    highlights?: string[];
    why_chosen?: string;
  };
  weather?: {
    summary?: string;
    avg_high_c?: number;
    avg_rain_pct?: number;
    days?: { date: string; high_c: number; low_c: number; rain_pct: number; condition: string }[];
  };
  flights?: {
    summary?: string;
    cheapest?: FlightOption;
    options?: FlightOption[];
  };
  hotels?: {
    summary?: string;
    best_value?: HotelOption;
    options?: HotelOption[];
  };
  activities?: {
    estimated_cost?: number;
    plan?: { day: number; morning: string; afternoon: string; evening: string }[];
  };
  logistics?: {
    summary?: string;
    currency?: string;
    languages?: string[];
    capital?: string;
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

export interface FlightOption {
  airline: string;
  tier: string;
  stops: number;
  depart_time: string;
  duration_h: number;
  total_price: number;
}

export interface HotelOption {
  name: string;
  tier: string;
  rating: number;
  nightly_rate: number;
  nights: number;
  total_price: number;
}
