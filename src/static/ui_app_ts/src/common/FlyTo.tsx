import { MapRef as ReactMapGLRef } from "react-map-gl/maplibre";

export interface FlyToProps {
  mapRef: React.RefObject<ReactMapGLRef>;
  lat: number;
  long: number;
  label: string;
  zoom?: number;
}

export const FlyTo = ({ mapRef, lat, long, label, zoom = 9 }: FlyToProps) => {
  return (
    <button
      className="fr-btn fr-btn--sm fr-btn--secondary fr-ml-1v fr-mb-1v"
      onClick={() => mapRef.current.flyTo({ center: [long, lat], zoom })}
    >
      {label}
    </button>
  );
};
