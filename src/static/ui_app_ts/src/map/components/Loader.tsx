import React from "react";

export const Loader: React.FC = () => {
  return (
    <div className="map-loader">
      <div className="map-spinner">
        <div className="fr-spinner" aria-label="Chargement en cours..."></div>
        <div className="spinner">
          <div className="rect1"></div>
          <div className="rect2"></div>
          <div className="rect3"></div>
          <div className="rect4"></div>
          <div className="rect5"></div>
          <p style={{ fontSize: "12px" }}>Chargement en cours…</p>
        </div>
      </div>
    </div>
  );
};
