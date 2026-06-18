import { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
  CircleMarker,
  Popup,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import type { HotelOption, Poi } from "../types";

interface Props {
  center: [number, number];
  attractions?: Poi[];
  hotels?: HotelOption[];
}

function numberedIcon(n: number) {
  return L.divIcon({
    className: "voyage-num",
    html:
      `<div style="background:#2563eb;color:#fff;width:24px;height:24px;border-radius:50%;` +
      `display:flex;align-items:center;justify-content:center;font:600 12px/1 sans-serif;` +
      `border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.45)">${n}</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

function FitBounds({ points }: { points: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (points.length === 1) {
      map.setView(points[0], 13);
    } else if (points.length > 1) {
      map.fitBounds(points, { padding: [40, 40], maxZoom: 14 });
    }
  }, [points, map]);
  return null;
}

export default function TripMap({ center, attractions = [], hotels = [] }: Props) {
  const stops = attractions.filter(
    (a): a is Poi & { lat: number; lon: number } => a.lat != null && a.lon != null
  );
  const path = stops.map((s) => [s.lat, s.lon] as [number, number]);
  const fitPoints = path.length ? path : [center];

  return (
    <MapContainer
      center={center}
      zoom={12}
      scrollWheelZoom={false}
      style={{ height: 380, width: "100%" }}
      className="rounded-md"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds points={fitPoints} />

      {/* route connecting the attractions in order */}
      {path.length > 1 && (
        <Polyline positions={path} pathOptions={{ color: "#2563eb", weight: 3, dashArray: "6 8", opacity: 0.8 }} />
      )}

      {/* numbered attraction stops */}
      {stops.map((s, i) => (
        <Marker key={`a${i}`} position={[s.lat, s.lon]} icon={numberedIcon(i + 1)}>
          <Popup>
            <b>{i + 1}. {s.name}</b>
            {s.tag ? <br /> : null}
            {s.tag}
          </Popup>
        </Marker>
      ))}

      {/* hotels as subtle secondary markers */}
      {hotels
        .filter((h) => h.lat != null && h.lon != null)
        .slice(0, 6)
        .map((h, i) => (
          <CircleMarker
            key={`h${i}`}
            center={[h.lat as number, h.lon as number]}
            radius={5}
            pathOptions={{ color: "#16a34a", fillColor: "#16a34a", fillOpacity: 0.7, weight: 1 }}
          >
            <Popup>🏨 {h.name}</Popup>
          </CircleMarker>
        ))}
    </MapContainer>
  );
}
