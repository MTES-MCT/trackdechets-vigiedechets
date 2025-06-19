import { useEffect, useRef } from "react";

// import { useAppDispatch } from "./store/root";
import MapContainer from "./components/Map.tsx";
import { Sidebar } from "./components/Sidebar.tsx";

import { MapRef as ReactMapGLRef } from "react-map-gl/maplibre";

function App() {
  // const dispatch = useAppDispatch();
  const mapRef = useRef<ReactMapGLRef>(null) as React.RefObject<ReactMapGLRef>;

  // Use the custom hook to fetch plots when filters change

  // default coords for France
  const lng = 2.209667;
  const lat = 46.232193;

  return (
    <div className="icpe-map-app">
      {/*<Filters />*/}
      <Sidebar mapRef={mapRef} />

      {/*<Suspense fallback={<div>Loading...</div>}>*/}

      <MapContainer lat={lat} lng={lng} mapRef={mapRef} />
      {/*</Suspense>*/}
    </div>
  );
}

export default App;
