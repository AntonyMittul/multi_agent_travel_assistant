import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import type { HotelOption, Poi } from "../types";

interface Props {
  center: [number, number];
  hotels?: HotelOption[];
  pois?: Poi[];
}

// CircleMarker avoids Leaflet's broken default-icon asset issue with bundlers.
export default function TripMap({ center, hotels = [], pois = [] }: Props) {
  return (
    <MapContainer
      center={center}
      zoom={12}
      scrollWheelZoom={false}
      style={{ height: 360, width: "100%" }}
      className="rounded-md"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <CircleMarker center={center} radius={8} pathOptions={{ color: "#2563eb", fillOpacity: 0.7 }}>
        <Popup>Destination</Popup>
      </CircleMarker>

      {hotels.filter((h) => h.lat && h.lon).map((h, i) => (
        <CircleMarker
          key={`h${i}`}
          center={[h.lat as number, h.lon as number]}
          radius={5}
          pathOptions={{ color: "#16a34a", fillOpacity: 0.6 }}
        >
          <Popup>
            🏨 {h.name}
            <br />~${h.nightly_rate.toFixed(0)}/night (est.)
          </Popup>
        </CircleMarker>
      ))}

      {pois.filter((p) => p.lat && p.lon).map((p, i) => (
        <CircleMarker
          key={`p${i}`}
          center={[p.lat as number, p.lon as number]}
          radius={4}
          pathOptions={{ color: "#ea580c", fillOpacity: 0.6 }}
        >
          <Popup>
            {p.name}
            <br />
            <span style={{ opacity: 0.7 }}>{p.category}</span>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
