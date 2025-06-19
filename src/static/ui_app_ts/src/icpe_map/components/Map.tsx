import "maplibre-gl/dist/maplibre-gl.css";
import ReactMapGL, {
  NavigationControl,
  ScaleControl,
  Source,
  Layer,
  Marker,
  MapLayerMouseEvent,
  LineLayerSpecification,
} from "react-map-gl/maplibre";
import { useCallback, useMemo, useState, useRef, useEffect } from "react";

import { MapGeoJSONFeature } from "maplibre-gl";

const MAP_STYLE =
  "https://openmaptiles.geo.data.gouv.fr/styles/osm-bright/style.json";

// Component props types
export interface MapContainerProps {
  mapRef: React.RefObject<ReactMapGLRef>;
  lat: number;
  lng: number;
}
const adminLayerDepartments: LineLayerSpecification = {
  id: "departements",
  type: "line",
  source: "departements",
  paint: {
    "line-color": "#198EC8",
  },
};

const adminLayerRegions: LineLayerSpecification = {
  id: "regions",
  type: "line",
  source: "regions",
  paint: {
    "line-color": "#198EC8",
  },
};

const MARKER_BLUE = "#000091";

export default function MapContainer({ mapRef, lat, lng }: MapContainerProps) {
  // const zoom = useAppSelector(selectZoom);
  // const {
  //   plots,
  //   clusters,
  //   status: loadingStatus,
  // } = useAppSelector((state: RootState) => state.mapData);
  // const { bounds } = useAppSelector((state) => state.mapUi);
  const [showLoader, setShowLoader] = useState(false);
  const loaderTimerRef = useRef<number | null>(null);

  return (
    <>
      <ReactMapGL
        ref={mapRef}
        initialViewState={{
          longitude: lng,
          latitude: lat,
          zoom: 4,
        }}
        dragRotate={false}
        touchZoomRotate={false}
        mapStyle={MAP_STYLE}
        onLoad={(event) => {
          if (mapRef.current) {
            const mapBounds = event.target.getBounds();
            const sw = mapBounds.getSouthWest();
            const ne = mapBounds.getNorthEast();

            // dispatch(
            //   setBounds({
            //     _sw: { lng: sw.lng, lat: sw.lat },
            //     _ne: { lng: ne.lng, lat: ne.lat },
            //   }),
            // );
          }
        }}
        onMoveEnd={(event) => {
          // dispatch(setZoom(event.target.getZoom()));

          const mapBounds = event.target.getBounds();
          // const sw = mapBounds.getSouthWest();
          // const ne = mapBounds.getNorthEast();
          //
          // dispatch(
          //   setBounds({
          //     _sw: { lng: sw.lng, lat: sw.lat },
          //     _ne: { lng: ne.lng, lat: ne.lat },
          //   }),
          // );
        }}
        // interactiveLayerIds={["clusters", "unclustered-point"]}
        // onClick={handleMapClick}
      >
        <NavigationControl showCompass={false} />
        <ScaleControl />

        {/* Administrative boundaries */}
        <Source
          id="departements"
          type="geojson"
          data="/static/geo/departements.geojson"
        >
          <Layer {...adminLayerDepartments} />
        </Source>

        <Source id="regions" type="geojson" data="/static/geo/regions.geojson">
          <Layer {...adminLayerRegions} />
        </Source>
      </ReactMapGL>
    </>
  );
}
