import uiReducer from "./uiSlice.ts";

// import mapDataReducer from "./mapDataSlice.ts";

import { configureStore } from "@reduxjs/toolkit";
import { useDispatch, TypedUseSelectorHook, useSelector } from "react-redux";

export const store = configureStore({
  devTools: true,
  reducer: {
    ui: uiReducer,
    // mapData: mapDataReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false, // To allow non-serializable data like bounds objects
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch = useDispatch.withTypes<AppDispatch>(); // Export a hook that can be reused to resolve types
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
