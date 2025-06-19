import "maplibre-gl/dist/maplibre-gl.css";
import ReactMapGL, {
  NavigationControl,
  ScaleControl,
  Source,
  Layer,
  Marker,
  MapLayerMouseEvent,
  LineLayerSpecification,
  MapRef,
  Popup,
} from "react-map-gl/maplibre";

import {
  setPlotPopup,
  setStatsOpened,
  setSelectedRegion,
  setSelectedDepartment,
  fetchData,
  setSelectedCompany,
} from "../store/uiSlice.ts";
import { useCallback, useMemo, useState, useEffect } from "react";
import { StatsContainer } from "./StatsContainer.tsx";
import { MapGeoJSONFeature } from "maplibre-gl";

import {
  RootState,
  useAppDispatch,
  useAppSelector,
} from "../../map/store/root.ts";

import { LocMarker } from "../../map/components/icons/LocMarker.tsx";
import {
  markerBlue,
  markerRed,
  markerDark,
  markerYellow,
  red,
} from "../constants.ts";
import { Legend } from "./Legend.tsx";
import { scaleSequential, interpolateOranges } from "./colorsUtils.ts";

const annualRubriques = ["2760-1", "2760-2"];

const MAP_STYLE =
  "https://openmaptiles.geo.data.gouv.fr/styles/osm-bright/style.json";

export interface MapContainerProps {
  mapRef: React.RefObject<MapRef>;
  lat: number;
  lng: number;
}

const getMarkerColor = (value, selectedRubrique) => {
  if (value["quantite_autorisee"] == 0 || value["quantite_autorisee"] == null) {
    return markerRed;
  } else if (
    (!annualRubriques.includes(selectedRubrique) &&
      (value["moyenne_quantite_journaliere_traitee"] == null ||
        value["moyenne_quantite_journaliere_traitee"] == 0)) ||
    (annualRubriques.includes(selectedRubrique) &&
      (value["cumul_quantite_traitee"] == null ||
        value["cumul_quantite_traitee"] == 0))
  ) {
    return markerYellow;
  } else if (
    value["taux_consommation"] != null &&
    (value["taux_consommation"] <= 0.2 || value["taux_consommation"] >= 1)
  ) {
    return markerDark;
  } else {
    return markerBlue;
  }
};

// Department layers
const adminLayerDepartments: LineLayerSpecification = {
  id: "departements",
  type: "line",
  source: "departements",
  paint: {
    "line-color": "#198EC8",
    "line-width": 1,
  },
};

const adminLayerDepartmentsFill: LineLayerSpecification = {
  id: "departements-fill",
  type: "fill",
  source: "departements",
  paint: {
    "fill-color": "transparent",
    "fill-opacity": 0.1,
  },
};

// Department highlight layers
const adminLayerDepartmentsHighlight: LineLayerSpecification = {
  id: "departements-highlight",
  type: "line",
  source: "departements",
  paint: {
    "line-color": "#ff6b6b",
    "line-width": 1,
  },
  filter: ["==", ["get", "nom"], ""], // Initially show nothing
};

const adminLayerDepartmentsFillHighlight: LineLayerSpecification = {
  id: "departements-fill-highlight",
  type: "fill",
  source: "departements",
  paint: {
    "fill-color": "#fff",
    "fill-opacity": 0.2,
  },
  filter: ["==", ["get", "nom"], ""], // Initially show nothing
};

// Region layers
const adminLayerRegions: LineLayerSpecification = {
  id: "regions",
  type: "line",
  source: "regions",
  paint: {
    "line-color": "#198EC8",
    "line-width": 2,
  },
};

const adminLayerRegionsFill: LineLayerSpecification = {
  id: "regions-fill",
  type: "fill",
  source: "regions",
  paint: {
    "fill-color": "transparent",
    "fill-opacity": 0.1,
  },
};

// Region highlight layers
const adminLayerRegionsHighlight: LineLayerSpecification = {
  id: "regions-highlight",
  type: "line",
  source: "regions",
  paint: {
    "line-color": "#0000ff",
    "line-width": 2,
  },
  filter: ["==", ["get", "nom"], ""], // Initially show nothing
};
const colorScale = scaleSequential(interpolateOranges);

const getColorForConsumptionRate = (
  rate: number | null,
  processedQuantity: number | null,
): string => {
  if (rate > 1 || (rate === null && processedQuantity == null)) {
    return red;
  }
  if (rate === null || rate === undefined) {
    return "#2f3640"; // Gray for null values
  }
  return colorScale(rate);
};

export default function MapContainer({ mapRef, lat, lng }: MapContainerProps) {
  const [showLoader, setShowLoader] = useState(false);

  const {
    adminDivision,
    regionData,
    departementsData,
    installationsData,
    displayPlots,
    rubrique,
    plotPopup,
    selectedRegion,
    selectedDepartement,
  } = useAppSelector((state: RootState) => state.ui);

  const markers = useMemo(() => {
    if (!installationsData.data || !displayPlots) {
      return [];
    }
    return Object.values(installationsData.data)
      .filter((plot) => plot.longitude)
      .map((plot, index) => (
        <Marker
          key={`marker-${index}`}
          longitude={plot.longitude}
          latitude={plot.latitude}
          anchor="center"
          onClick={(e) => {
            e.originalEvent.stopPropagation();

            dispatch(setSelectedCompany(plot));
            // dispatch(fetchGraph());
            dispatch(setStatsOpened(true));
          }}
        >
          <div
            onMouseEnter={() => {
              dispatch(
                setPlotPopup({
                  latitude: plot.latitude,
                  longitude: plot.longitude,
                  text: plot.raison_sociale,
                }),
              );
              // dispatch(setHoveredPlot(plot));
            }}
            onMouseLeave={() => {
              dispatch(setPlotPopup(null));
            }}
            style={{ cursor: "pointer" }}
          >
            <LocMarker color={getMarkerColor(plot, rubrique)} />
          </div>
        </Marker>
      ));
  }, [installationsData, displayPlots]);

  const departementsColors = useMemo(() => {
    const colors: Record<string, string> = {};
    if (!Object.keys(departementsData).length) {
      return {};
    }

    Object.entries(departementsData).forEach(([code, reg]) => {
      const processedQuantity = annualRubriques.includes(rubrique)
        ? reg?.cumul_quantite_traitee
        : reg?.moyenne_quantite_journaliere_traitee;
      colors[code] = getColorForConsumptionRate(
        reg.taux_consommation ?? null,
        processedQuantity,
      );
    });
    console.log(departementsData);
    return colors;
  }, [departementsData]);

  const regionColors = useMemo(() => {
    const colors: Record<string, string> = {};
    if (!Object.keys(regionData).length) {
      return {};
    }

    Object.entries(regionData).forEach(([code, reg]) => {
      colors[code] = getColorForConsumptionRate(reg.taux_consommation);
    });

    return colors;
  }, [regionData]);

  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(fetchData());
  }, [dispatch]);

  const adminLayerRegionsFillHighlight: LineLayerSpecification = useMemo(
    () => ({
      id: "regions-fill-highlight",
      type: "fill",
      source: "regions",
      paint: {
        "fill-color":
          Object.keys(regionColors).length > 0
            ? [
                "case",
                ...Object.entries(regionColors).flatMap(([code, color]) => [
                  ["==", ["get", "code"], code],
                  color,
                ]),
                "#2f3640", // Default color
              ]
            : "#ff6b6b",

        "fill-opacity": 0.8,
      },
      filter: ["!=", ["get", "code"], ""], // Show all departments when using consumption colors
    }),
    [regionColors],
  );
  const adminLayerDepartementsFillHighlight: LineLayerSpecification = useMemo(
    () => ({
      id: "departements-fill-highlight",
      type: "fill",
      source: "departements",
      paint: {
        "fill-color":
          Object.keys(departementsColors).length > 0
            ? [
                "case",
                ...Object.entries(departementsColors).flatMap(
                  ([code, color]) => [["==", ["get", "code"], code], color],
                ),
                "#2f3640", // Default color
              ]
            : "#ff6b6b",

        "fill-opacity": 0.7,
      },
      filter: ["!=", ["get", "code"], ""], // Show all departments when using consumption colors
    }),
    [departementsColors],
  );

  // Update highlight layer filters when selections change
  useEffect(() => {
    if (mapRef.current) {
      updateHighlightFilters();
    }
  }, [selectedRegion, selectedDepartement]);

  const regionLayers = [
    "regions",
    "regions-fill",
    "regions-highlight",
    "regions-fill-highlight",
  ];

  const departmentLayers = [
    "departements",
    "departements-fill",
    "departements-highlight",
    "departements-fill-highlight",
  ];

  const allInteractiveLayers = [...regionLayers, ...departmentLayers];

  const updateHighlightFilters = useCallback(() => {
    if (!mapRef.current) return;

    // Access the underlying MapLibre map instance
    const map = mapRef.current.getMap();

    // Check if the map is loaded and layers exist
    if (map && map.isStyleLoaded()) {
      return;
      try {
        // Update region highlight filters
        const regionFilter = selectedRegion?.name
          ? ["==", ["get", "name"], selectedRegion.name]
          : ["==", ["get", "name"], ""]; // Empty filter to show nothing

        if (map.getLayer("regions-highlight")) {
          map.setFilter("regions-highlight", regionFilter);
        }
        if (map.getLayer("regions-fill-highlight")) {
          map.setFilter("regions-fill-highlight", regionFilter);
        }

        // Update department highlight filters
        const departmentFilter = selectedDepartement?.name
          ? ["==", ["get", "name"], selectedDepartement.name]
          : ["==", ["get", "name"], ""]; // Empty filter to show nothing

        if (map.getLayer("departements-highlight")) {
          map.setFilter("departements-highlight", departmentFilter);
        }
        if (map.getLayer("departements-fill-highlight")) {
          map.setFilter("departements-fill-highlight", departmentFilter);
        }
      } catch (error) {
        console.error("Error updating filters:", error);
      }
    }
  }, [selectedRegion, selectedDepartement]);

  const handleMapClick = useCallback((event: MapLayerMouseEvent) => {
    const { features } = event;

    if (!features || features.length === 0) {
      setSelectedRegion(null);
      setSelectedDepartment(null);
      return;
    }

    const feature: MapGeoJSONFeature = features[0];

    // Check if the clicked feature belongs to region layers
    if (regionLayers.includes(feature.layer.id)) {
      console.log("Region clicked:", feature);

      dispatch(
        setSelectedRegion({
          code: feature.properties.code,
          name: feature.properties.name,
        }),
      );
      dispatch(setStatsOpened(true));

      setSelectedDepartment(null); // Clear department selection
    }
    // Check if the clicked feature belongs to department layers
    else if (departmentLayers.includes(feature.layer.id)) {
      console.log("Department clicked:", feature);

      dispatch(
        setSelectedDepartment({
          code: feature.properties.code,
          name: feature.properties.name,
        }),
      );
      dispatch(setStatsOpened(true));
    } else {
      // Handle other layer clicks or clear selection
      setSelectedDepartment({
        code: feature.properties.code,
        name: feature.properties.name,
      });

      setSelectedRegion(null);
    }
  }, []);

  // Optional: Handle hover effects
  const handleMapHover = useCallback((event: MapLayerMouseEvent) => {
    if (mapRef.current) {
      const { features } = event;
      if (features && features.length > 0) {
        const feature = features[0];
        if (allInteractiveLayers.includes(feature.layer.id)) {
          mapRef.current.getCanvas().style.cursor = "pointer";
        }
      } else {
        mapRef.current.getCanvas().style.cursor = "";
      }
    }
  }, []);

  const selectedItem = selectedRegion || selectedDepartement;

  const selectedType = selectedRegion
    ? "Region"
    : selectedDepartement
      ? "Department"
      : "";

  return (
    <>
      <ReactMapGL
        ref={mapRef}
        initialViewState={{
          longitude: lng,
          latitude: lat,
          zoom: 5,
        }}
        dragRotate={false}
        touchZoomRotate={false}
        mapStyle={MAP_STYLE}
        onLoad={(event) => {
          if (mapRef.current) {
            const mapBounds = event.target.getBounds();

            // handleMapLoad(event);
            const sw = mapBounds.getSouthWest();
            const ne = mapBounds.getNorthEast();

            // Ensure filters are applied after map loads
            setTimeout(() => {
              updateHighlightFilters();
            }, 100);
          }
        }}
        onMoveEnd={(event) => {
          // dispatch(setZoom(event.target.getZoom()));
        }}
        // IMPORTANT: Add the layer IDs you want to make interactive
        interactiveLayerIds={allInteractiveLayers}
        onClick={handleMapClick}
        onMouseMove={handleMapHover}
      >
        <NavigationControl showCompass={false} />
        <ScaleControl />

        {/* Administrative boundaries */}
        {adminDivision === "departements" && (
          <Source
            id="departements"
            type="geojson"
            data="/static/geo/departements-avec-outre-mer-light.geojson"
          >
            {/* Base department layers */}
            {/*<Layer {...adminLayerDepartmentsFill} />*/}
            <Layer {...adminLayerDepartments} />

            {/* Department highlight layers - render on top */}
            {/*<Layer {...adminLayerDepartmentsFillHighlight} />*/}

            <Layer {...adminLayerDepartementsFillHighlight} />
            {/*<Layer {...adminLayerDepartmentsHighlight} />*/}
          </Source>
        )}
        {markers}
        {plotPopup && (
          <Popup
            anchor={"left"}
            longitude={plotPopup.longitude}
            latitude={plotPopup.latitude}
          >
            {plotPopup.text}
          </Popup>
        )}
        {adminDivision === "regions" && (
          <Source
            id="regions"
            type="geojson"
            data="/static/geo/regions-avec-outre-mer-light.geojson"
          >
            {/* Base region layers */}
            <Layer {...adminLayerRegionsFill} />
            <Layer {...adminLayerRegions} />

            {/* Region highlight layers - render on top */}
            <Layer {...adminLayerRegionsFillHighlight} />
            <Layer {...adminLayerRegionsHighlight} />
          </Source>
        )}

        <StatsContainer />
        <Legend />
      </ReactMapGL>
    </>
  );
}
