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
import { MapContainerProps } from "../types.ts";
import { selectZoom, setZoom, setBounds } from "../store/mapUiSlice.ts";
import { closePopup, setPopupData } from "../store/mapPopupSlice";
import { RootState, useAppDispatch, useAppSelector } from "../store/root.ts";
import { Popup } from "./Popup";
import { Loader } from "./Loader.tsx";
import { LocMarker } from "./icons/LocMarker";
import { ZOOM_ETABS, ZOOM_CLUSTERS } from "../constants/constants.ts";
import { Plot, PopupData } from "../types";
import { Cluster } from "./icons/Cluster.tsx";
import { MapGeoJSONFeature } from "maplibre-gl";
import type { Geometry, BBox, GeoJsonProperties } from "geojson";
import Supercluster from "supercluster";

type PlotProperties = GeoJsonProperties & {
  id: string;
  cluster?: boolean;
  count?: number;
  nom_etablissement?: string;
  adresse_td?: string;
  siret?: string;
  profiles?: string;
  wastes?: string;
  lat: number;
  long: number;
};

type PlotFeature = {
  type: "Feature";
  properties: PlotProperties;
  geometry: {
    type: "Point";
    coordinates: [number, number];
  };
};

type ClusterProperties = {
  cluster: true;
  cluster_id: number;
  point_count: number;
  point_count_abbreviated: number;
};

const MAP_STYLE =
  "https://openmaptiles.geo.data.gouv.fr/styles/osm-bright/style.json";

const PREPARE_SLUG = "/sheets/sheet-prepare/";

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

const mapPlotToPopup = (plot: Plot, zoom: number): PopupData | null => {
  if (zoom >= ZOOM_ETABS) {
    return {
      popupTitle: plot.nom_etablissement || "Nom non renseigné",
      popupText: plot.adresse_td || "",
      registeredOnTd: plot.registered_on_td,
      popupRow1: ["Siret", plot.siret || ""],
      popupRow2: ["Profil", plot.profiles || ""],
      popupRow3: ["Déchet", plot.wastes || ""],
      popupLink: `${PREPARE_SLUG}?siret=${plot.siret || ""}`,
    };
  }
  return null;
};

function hasCoordinates(
  geometry: Geometry,
): geometry is
  | GeoJSON.Point
  | GeoJSON.LineString
  | GeoJSON.Polygon
  | GeoJSON.MultiPoint
  | GeoJSON.MultiLineString
  | GeoJSON.MultiPolygon {
  return geometry.type !== "GeometryCollection" && "coordinates" in geometry;
}

export default function MapContainer({ mapRef, lat, lng }: MapContainerProps) {
  const zoom = useAppSelector(selectZoom);
  const {
    plots,
    clusters,
    status: loadingStatus,
  } = useAppSelector((state: RootState) => state.mapData);
  const { bounds } = useAppSelector((state) => state.mapUi);
  const [showLoader, setShowLoader] = useState(false);
  const loaderTimerRef = useRef<number | null>(null);

  const dispatch = useAppDispatch();

  const {
    popupTitle,
    popupText,
    popupRow1,
    popupRow2,
    popupRow3,
    popupLink,
    registeredOnTd,
  } = useAppSelector((state: RootState) => state.mapPopup);

  const points = useMemo(() => {
    return plots.map((plot) => ({
      type: "Feature" as const,
      properties: {
        id: `${plot.siret || plot.lat + plot.long}`,
        cluster: false,
        ...plot,
      },
      geometry: {
        type: "Point" as const,
        coordinates: [plot.long, plot.lat] as [number, number],
      },
    })) as PlotFeature[];
  }, [plots]);

  const supercluster = useMemo(() => {
    const instance = new Supercluster<PlotProperties, ClusterProperties>({
      radius: 40, // Clustering radius in pixels
      maxZoom: 10, // Maximum zoom level to cluster points
    });

    if (points.length > 0) {
      instance.load(points);
    }

    return instance;
  }, [points]);

  const clusteredCompanies = useMemo(() => {
    if (!supercluster || zoom < 8 || plots.length === 0) {
      return [];
    }

    if (!bounds || !bounds._sw || !bounds._ne) return [];
    const { _sw, _ne } = bounds;
    const bbox: BBox = [_sw.lng, _sw.lat, _ne.lng, _ne.lat];
    return supercluster.getClusters(bbox, Math.floor(zoom));
  }, [bounds, supercluster, plots, zoom]);

  useEffect(() => {
    if (loadingStatus === "loading") {
      if (loaderTimerRef.current !== null) {
        window.clearTimeout(loaderTimerRef.current);
      }

      loaderTimerRef.current = window.setTimeout(() => {
        setShowLoader(true);
      }, 100);
    } else {
      if (loaderTimerRef.current !== null) {
        window.clearTimeout(loaderTimerRef.current);
        loaderTimerRef.current = null;
      }

      setShowLoader(false);
    }

    return () => {
      if (loaderTimerRef.current !== null) {
        window.clearTimeout(loaderTimerRef.current);
      }
    };
  }, [loadingStatus]);

  const handleMapClick = useCallback(
    (event: MapLayerMouseEvent) => {
      const { features } = event;
      if (!features || features.length === 0) return;

      const feature: MapGeoJSONFeature = features[0];
      if (hasCoordinates(feature.geometry)) {
        const coordinates = feature.geometry.coordinates;

        if (feature.layer.id === "clusters") {
          const clusterId = feature.properties.cluster_id;
          const source = mapRef.current.getSource("plots");
          if (!source) {
            return;
          } // @ts-expect-error library type def error
          source.getClusterExpansionZoom(
            clusterId,
            (err: Error, newZoom: number) => {
              if (err) return;

              mapRef.current.flyTo({
                // @ts-expect-error library type def error
                center: coordinates,
                zoom: newZoom,
              });
            },
          );
        } else if (feature.layer.id === "unclustered-point") {
          const properties = feature.properties;

          const plot: Plot = {
            long: coordinates[0] as number,
            lat: coordinates[1] as number,
            nom_etablissement: properties.nom_etablissement,
            adresse_td: properties.adresse_td,
            siret: properties.siret,
            profiles: properties.profiles,
            wastes: properties.wastes,
            registered_on_td: properties.registered_on_td,
            count: 1,
          };

          dispatch(setPopupData(mapPlotToPopup(plot, zoom)));
        }
      } else {
        return;
      }
    },
    [dispatch, mapRef, zoom],
  );

  const color = "#000091";

  // regions and departments markers
  const clustersMarkers = useMemo(() => {
    return clusters.map((plot, index) => (
      <Marker
        key={`marker-${index}`}
        longitude={plot.long}
        latitude={plot.lat}
        anchor="center"
        onClick={(e) => {
          e.originalEvent.stopPropagation();
          mapRef.current?.getMap().flyTo({
            center: [plot.long, plot.lat],
            zoom: zoom + 2,
            duration: 500,
          });
        }}
      >
        {zoom < ZOOM_ETABS ? (
          <Cluster txt={`${plot.count}`} fill={color} />
        ) : (
          <LocMarker />
        )}
      </Marker>
    ));
  }, [zoom, clusters, mapRef]);

  const handleClusterClick = useCallback(
    (clusterId: number, longitude: number, latitude: number) => {
      const expansionZoom = Math.min(
        supercluster.getClusterExpansionZoom(clusterId),
        20,
      );

      mapRef.current?.getMap().flyTo({
        center: [longitude, latitude],
        zoom: expansionZoom,
        duration: 500,
      });
    },
    [supercluster, mapRef],
  );
  return (
    <>
      {showLoader && <Loader />}
      <ReactMapGL
        ref={mapRef}
        initialViewState={{
          longitude: lng,
          latitude: lat,
          zoom: zoom,
        }}
        dragRotate={false}
        touchZoomRotate={false}
        mapStyle={MAP_STYLE}
        onLoad={(event) => {
          if (mapRef.current) {
            const mapBounds = event.target.getBounds();
            const sw = mapBounds.getSouthWest();
            const ne = mapBounds.getNorthEast();

            dispatch(
              setBounds({
                _sw: { lng: sw.lng, lat: sw.lat },
                _ne: { lng: ne.lng, lat: ne.lat },
              }),
            );
          }
        }}
        onMoveEnd={(event) => {
          dispatch(setZoom(event.target.getZoom()));

          const mapBounds = event.target.getBounds();
          const sw = mapBounds.getSouthWest();
          const ne = mapBounds.getNorthEast();

          dispatch(
            setBounds({
              _sw: { lng: sw.lng, lat: sw.lat },
              _ne: { lng: ne.lng, lat: ne.lat },
            }),
          );
        }}
        interactiveLayerIds={["clusters", "unclustered-point"]}
        onClick={handleMapClick}
      >
        <NavigationControl showCompass={false} />
        <ScaleControl />

        {clusteredCompanies.map((cluster) => {
          const [longitude, latitude] = cluster.geometry.coordinates;
          const {
            cluster: isCluster,
            point_count: pointCount,
            cluster_id: clusterId,
          } = cluster.properties;

          if (isCluster) {
            return (
              <Marker
                key={`cluster-${clusterId}`}
                longitude={longitude}
                latitude={latitude}
                anchor="center"
                onClick={(e) => {
                  e.originalEvent.stopPropagation();
                  handleClusterClick(clusterId, longitude, latitude);
                }}
              >
                <Cluster txt={pointCount} fill={MARKER_BLUE} />
              </Marker>
            );
          } else {
            const plot = cluster.properties as unknown as Plot;
            return (
              <Marker
                key={`marker-${plot.siret || `${longitude}-${latitude}`}`}
                longitude={longitude}
                latitude={latitude}
                anchor="center"
                onClick={(e) => {
                  e.originalEvent.stopPropagation();
                  if (zoom >= ZOOM_CLUSTERS) {
                    dispatch(setPopupData(mapPlotToPopup(plot, zoom)));
                  }
                }}
              >
                <LocMarker color={plot.registered_on_td ? "#000091" : "#777"} />
              </Marker>
            );
          }
        })}

        {clustersMarkers}

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

        {/* Popup component */}
        {popupTitle && (
          <Popup
            title={popupTitle}
            text={popupText}
            row1={[popupRow1[0], popupRow1[1]]}
            row2={[popupRow2[0], popupRow2[1]]}
            row3={[popupRow3[0], popupRow3[1]]}
            registeredOnTd={registeredOnTd}
            link={popupLink}
            onClose={() => dispatch(closePopup())}
          />
        )}
      </ReactMapGL>
    </>
  );
}
