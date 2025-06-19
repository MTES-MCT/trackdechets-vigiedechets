// import { FlyToProps, SidebarProps } from "../types";
// import { setModalState } from "../store/modalSlice";
// import { useAppDispatch, useAppSelector, RootState } from "../store/root";
// import { ProfileFilterState, removeFilter } from "../store/searchFiltersSlice";
// import { FRENCH_DEPARTMENTS } from "../constants/departments.ts";
// import { useFileDownload } from "../hooks/downloadHook";

import { MapRef as ReactMapGLRef } from "react-map-gl/maplibre";

export interface SidebarProps {
  mapRef: React.RefObject<ReactMapGLRef>;
}
export function Sidebar({ mapRef }: SidebarProps) {
  return (
    <div className="icpe-map__sidebar">
      <p className="fr-text--lg fr-text--bold">Informations</p>

      <div>
        <select name="" id=""></select>

        <div className="fr-select-group fr-mb-1w">
          <label className="fr-label" htmlFor="year-select">
            Année
          </label>
          <select className="fr-select" id="year-select" name="select-annee">
            <option value="2024">2024</option>
            <option selected value="2023">
              2023
            </option>
            <option value="2022">2022</option>
          </select>
        </div>

        <div className="fr-select-group">
          <label className="fr-label" htmlFor="rubrique-select">
            Rubrique
          </label>
          <select
            className="fr-select"
            id="rubrique-select"
            name="select-rubrique"
          >
            <option value="2760-1">2760-1 (Enfouissement DD)</option>
            <option selected value="2770">
              2770 (Incinération DD)
            </option>
            <option selected value="2790">
              2790 (Traitement DD)
            </option>
            <option value="2760-2">2760-2 (Enfouissement DND/TEXS)</option>
            <option selected value="2771">
              2771 (Incinération DND/TEXS)
            </option>
            <option selected value="2791">
              2791 (Traitement DND/TEXS)
            </option>
          </select>
        </div>

        <button
          id="back-to-france"
          className="fr-btn fr-btn--secondary fr-mb-2w"
        >
          Afficher les données pour la France
        </button>

        <h6 className="fr-mb-1w">Affichage</h6>
        <div>
          <div className="fr-toggle fr-toggle--border-bottom fr-mb-1w">
            <input
              type="checkbox"
              className="fr-toggle__input"
              aria-describedby="toggle-installations-hint-text"
              id="toggle-installations"
            />
            <label className="fr-toggle__label" htmlFor="toggle-installations">
              Afficher les installations
            </label>
            <p className="fr-hint-text" id="toggle-installations-hint-text">
              Cliquez pour afficher les ICPE sur la carte.
            </p>
          </div>
          <div className="fr-select-group fr-mb-1w">
            <label className="fr-label" htmlFor="layer-select">
              Découpage
            </label>
            <select
              className="fr-select"
              id="layer-select"
              name="select-vue-carte"
            >
              <option selected value="regions">
                Régional
              </option>
              <option value="departements">Départemental</option>
            </select>
          </div>
          <div className="fr-select-group">
            <label className="fr-label" htmlFor="zoom-select">
              Zoom
            </label>
            <select
              className="fr-select"
              id="zoom-select"
              name="select-zoom-carte"
            >
              <option selected value="metropole">
                Métropole
              </option>
              <option value="mgg">Guadeloupe, Guyane et Martinique</option>
              <option value="mr">Mayotte et La Réunion</option>
            </select>
          </div>

          <div id="icon-legend">
            <h6 className="fr-mb-1w">Légende</h6>
            <div>
              <img
                src="/static/img/blue_icon.png"
                alt="Icone bleue"
                className="legend-img"
              />
              <span>Installation non problématique</span>
            </div>
            <div>
              <img
                src="/static/img/yellow_icon.png"
                alt="Icone Jaune"
                className="legend-img"
              />
              <span>
                Installation avec une quantité traitée nulle ou manquante
              </span>
            </div>
            <div>
              <img
                src="/static/img/red_icon.png"
                alt="Icone bleue"
                className="legend-img"
              />
              <span>
                Installation avec une quantité autorisée nulle ou manquante
              </span>
            </div>
            <div>
              <img
                src="/static/img/dark_icon.png"
                alt="Icone Jaune"
                className="legend-img"
              />
              <span>
                Installation avec un taux de consommation inférieur à 20% ou
                supérieur à 100%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
