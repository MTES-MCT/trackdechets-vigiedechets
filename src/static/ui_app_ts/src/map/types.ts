import { MapRef as ReactMapGLRef } from "react-map-gl/maplibre";

export interface Bounds {
  _sw?: {
    lng: number;
    lat: number;
  };
  _ne?: {
    lng: number;
    lat: number;
  };
}

export interface Plot {
  lat: number;
  long: number;
  count?: number;
  nom_etablissement?: string;
  registered_on_td: boolean;
  adresse_td?: string;
  siret?: string;
  profiles?: string;
  wastes?: string;
}

// Filter types
export interface FilterAction {
  filterKey: string;
  subFilterKey?: string;
  value: string;
}

export interface FilterValue {
  root: string[];
  [key: string]: string[];
}

export type FilterValues = {
  root: string[];
  [key: string]: string[];
};

export interface PopupData {
  popupTitle?: string;
  popupText?: string;
  popupRow1?: [string, string];
  popupRow2?: [string, string];
  popupRow3?: [string, string];
  popupLink?: string;
  registeredOnTd?: boolean;
}

// Options types
export interface Option {
  value: string;
  label: string;
  shortLabel: string;
  options?: Option[];
  subTypesName?: string;
}

// Store types
export interface MapStoreState {
  // Filter states
  bsdFilters: FilterValue;
  profileFilters: {
    root: string[];
    collectorTypes: string[];
    wasteProcessorTypes: string[];
    wasteVehiclesTypes: string[];
    [key: string]: string[];
  };
  operationCodeFilters: FilterValue;
  departmentFilters: FilterValue;

  // Map data
  regions: unknown[];
  departments: unknown[];
  plots: Plot[];

  // Map UI state
  zoom: number;
  bounds: Bounds;

  // Popup state
  popupTitle: string;
  popupText: string;
  popupRow1: [string, string] | null;
  popupRow2: [string, string] | null;
  popupRow3: [string, string] | null;
  popupLink: string;

  // Actions
  addFilter: (filter: FilterAction) => void;
  removeFilter: (filter: FilterAction) => void;
  clearFilter: (
    filter: Pick<FilterAction, "filterKey" | "subFilterKey">,
  ) => void;
  fetchPlots: () => Promise<void>;
  setZoom: (zoom: number) => void;
  setBounds: (bounds: Bounds) => void;
  setPopupData: (data: PopupData) => void;
  closePopup: () => void;
}

// Component props types
export interface MapContainerProps {
  mapRef: React.RefObject<ReactMapGLRef>;
  lat: number;
  lng: number;
}

export interface PopupProps {
  title: string;
  text: string;
  registeredOnTd: boolean;
  onClose: () => void;
  row1?: [string, string] | null;
  row2?: [string, string] | null;
  row3?: [string, string] | null;
  link?: string | null;
}

export interface SelectWithSubOptionsProps {
  options: Option[];
  filterKey: string;
  subFilterKey?: string;
  selected: FilterValue;
  onAdd: (filter: FilterAction) => void;
  onRemove: (filter: FilterAction) => void;
  onClear?: (filter: Pick<FilterAction, "filterKey" | "subFilterKey">) => void;
}

export interface MapOptionsProps {
  options: Option[];
  filterKey: string;
  subFilterKey?: string;
  parentPaths?: string[];
  ml?: number;
  onAdd: (filter: FilterAction) => void;
  onRemove: (filter: FilterAction) => void;
  selected: FilterValue;
}

export interface MapRefX {
  flyTo: (options: { center: [number, number]; zoom?: number }) => void;
  getMap: () => {
    flyTo: (options: {
      center: [number, number];
      zoom?: number;
      duration?: number;
    }) => void;
    getBounds: () => {
      getSouthWest: () => { lng: number; lat: number };
      getNorthEast: () => { lng: number; lat: number };
    };
    getZoom: () => number;
    getSource: (sourceId: string) => {
      getClusterExpansionZoom: (
        clusterId: number,
        callback: (err: Error, zoom: number) => void,
      ) => void;
    };
  };
}
export interface SidebarProps {
  mapRef: React.RefObject<ReactMapGLRef>;
}

export interface FlyToProps {
  mapRef: React.RefObject<ReactMapGLRef>;
  lat: number;
  long: number;
  label: string;
  zoom?: number;
}

// Constants types
export interface CollectorType {
  DangerousWastes: string;
  DeeeWastes: string;
  NonDangerousWastes: string;
  OtherDangerousWastes: string;
  OtherNonDangerousWastes: string;
}

export interface WasteProcessorType {
  Cremation: string;
  DangerousWastesIncineration: string;
  DangerousWastesStorage: string;
  InertWastesStorage: string;
  NonDangerousWastesIncineration: string;
  NonDangerousWastesStorage: string;
  OtherDangerousWastes: string;
  OtherNonDangerousWastes: string;
}
export interface MapBounds {
  _sw?: {
    lng: number;
    lat: number;
  };
  _ne?: {
    lng: number;
    lat: number;
  };
}
export interface MapUiState {
  zoom: number;
  bounds: MapBounds;
}
export type SubProfile = {
  value: string;
  label: string;
  shortLabel: string;
};

export type Profile = {
  value: string;
  label: string;
  shortLabel: string;
  subTypesName?: string;
  options?: SubProfile[];
};
