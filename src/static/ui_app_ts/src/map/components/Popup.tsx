import { PopupProps } from "../types";

export function Popup({
  title,
  text,
  onClose,
  registeredOnTd,
  row1 = null,
  row2 = null,
  row3 = null,
  link = null,
}: PopupProps) {
  return (
    <div className="map-popup">
      <div className="map-popup__close" onClick={onClose}>
        Fermer ×
      </div>
      <h3>{title}</h3>
      <p>{text}</p>
      {row1 && (
        <p className="fr-text">
          {row1[0]} : <strong>{row1[1]}</strong>{" "}
          {registeredOnTd ? (
            <span className="fr-badge fr-badge--success">
              Inscrit sur Trackdéchets
            </span>
          ) : (
            <span className="fr-badge fr-badge--warning fr-badge--no-icon">
              Non inscrit sur Trackdéchets
            </span>
          )}
        </p>
      )}
      {row2 && (
        <p className="fr-text">
          {row2[0]} : <strong>{row2[1]}</strong>
        </p>
      )}
      {row3 && (
        <p className="fr-text">
          {row3[0]} : <strong>{row3[1]}</strong>
        </p>
      )}
      {link && (
        <p>
          <a href={link} className="fr-btn fr-btn--secondary" target="_blank">
            Voir la fiche établissement
          </a>
        </p>
      )}
    </div>
  );
}
