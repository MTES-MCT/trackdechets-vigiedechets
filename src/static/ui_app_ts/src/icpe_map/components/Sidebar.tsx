import {
  setAdminDivision,
  toggleDisplayPlots,
  setRubrique,
  setYear,
  fetchData,
  fetchInstallations,
} from "../store/uiSlice.ts";
import { MapRef as ReactMapGLRef } from "react-map-gl/maplibre";
import { useAppDispatch, useAppSelector, RootState } from "../store/root";
import { useEffect } from "react";
import { FlyTo } from "../../common/FlyTo.tsx";
export interface SidebarProps {
  mapRef: React.RefObject<ReactMapGLRef>;
}
import { LocMarker } from "../../map/components/icons/LocMarker.tsx";
import {
  markerBlue,
  markerRed,
  markerDark,
  markerYellow,
} from "../constants.ts";

export function Sidebar({ mapRef }: SidebarProps) {
  const { year, rubrique, adminDivision, displayPlots } = useAppSelector(
    (state: RootState) => state.ui,
  );

  const dispatch = useAppDispatch();
  useEffect(() => {
    dispatch(fetchData());
  }, [rubrique, year, adminDivision, dispatch]);

  useEffect(() => {
    if (displayPlots) {
      dispatch(fetchInstallations());
    }
  }, [rubrique, year, displayPlots, dispatch]);

  return (
    <div className="icpe-map__sidebar">
      <p className="fr-text--lg fr-text--bold fr-mb-0">Informations</p>

      <div>
        <div className="fr-select-group fr-mb-1w">
          <label className="fr-label" htmlFor="year-select">
            Année
          </label>
          <select
            className="fr-select"
            id="year-select"
            name="select-annee"
            value={year}
            onChange={(e) => dispatch(setYear(e.target.value))}
          >
            <option value="2025">2025</option>
            <option value="2024">2024</option>
            <option value="2023">2023</option>
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
            value={rubrique}
            onChange={(e) => dispatch(setRubrique(e.target.value))}
          >
            <option value="2760-1">2760-1 (Enfouissement DD)</option>
            <option value="2760-2">2760-2 (Enfouissement DND/TEXS)</option>
            <option value="2770">2770 (Incinération DD)</option>

            <option value="2771">2771 (Incinération DND/TEXS)</option>
            <option value="2790">2790 (Traitement DD)</option>
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
              onChange={(e) => dispatch(toggleDisplayPlots(e.target.checked))}
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
              value={adminDivision}
              onChange={(e) => dispatch(setAdminDivision(e.target.value))}
            >
              <option value="regions">Régional</option>
              <option value="departements">Départemental</option>
            </select>
          </div>
          <div>
            <FlyTo
              mapRef={mapRef}
              lat={46.2321}
              long={2.209667}
              zoom={5}
              label="Métropole"
            />
            <FlyTo
              mapRef={mapRef}
              lat={14.63554}
              long={-61.02281}
              label="Martinique"
            />
            <FlyTo
              mapRef={mapRef}
              lat={16.1922}
              long={-61.272382}
              label="Guadeloupe"
            />
            <FlyTo
              mapRef={mapRef}
              lat={-21.114}
              long={55.532}
              label="La Réunion"
            />
            <FlyTo
              mapRef={mapRef}
              lat={3.9517949}
              long={-53.07822}
              label="Guyane"
              zoom={7}
            />
            <FlyTo
              mapRef={mapRef}
              lat={-12.82451}
              long={45.165455}
              label="Mayotte"
              zoom={7}
            />
          </div>

          <div id="icon-legend">
            <h6 className="fr-mb-1w">Légende</h6>
            <div className="flex">
              <span>
                <LocMarker color={markerBlue} />
              </span>
              <span className="fr-ml-1w">Installation non problématique</span>
            </div>
            <div className="flex">
              <span>
                {" "}
                <LocMarker color={markerYellow} />
              </span>
              <span className="fr-ml-1w">
                Installation avec une quantité traitée nulle ou manquante
              </span>
            </div>
            <div className="flex">
              <span>
                {" "}
                <LocMarker color={markerRed} />
              </span>
              <span className="fr-ml-1w">
                Installation avec une quantité autorisée nulle ou manquante
              </span>
            </div>
            <div className="flex">
              <span>
                {" "}
                <LocMarker color={markerDark} />
              </span>
              <span className="fr-ml-1w">
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
