import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import galaxyReducer from "./store/galaxySlice";
import GalaxyApp from "./components/galaxy/GalaxyApp";

const store = configureStore({
  reducer: {
    galaxy: galaxyReducer,
  },
});

const rootElement = document.getElementById("galaxy-root");

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <Provider store={store}>
        <GalaxyApp />
      </Provider>
    </StrictMode>
  );
} else {
  console.error("Galaxy root element not found");
}
