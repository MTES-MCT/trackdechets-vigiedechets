import React from "react";
import { useSelector } from "react-redux";
import {
  addFilter,
  setFilter,
  removeFilter,
  clearFilter,
} from "../../store/searchFiltersSlice";
import { RootState, useAppDispatch } from "../../store/root";
import {
  BSDD,
  BSDA,
  BSDASRI,
  BSFF,
  BSVHU,
  BSDND,
  TEXS,
  ROLE_EMITTER,
  ROLE_TRANSPORTER,
  ROLE_WORKER,
  ROLE_DESTINATION,
  SSD,
  TEXS_DD,
} from "../../constants/constants";

const BSD_TYPE_FILTER_KEY = "bsdTypeFilters";
const ROLE_FILTER_KEY = "roleFilters";

type WasteTypesProps = object;

const WasteTypesAndRoles: React.FC<WasteTypesProps> = () => {
  const {
    bsdTypeFilters: selectBsdTypeFilter,
    roleFilters: selectRoleFilters,
  } = useSelector((state: RootState) => state.searchFilters);

  const dispatch = useAppDispatch();

  return (
    <div>
      <p>Types de déchets</p>
      <div className="fr-grid-row">
        <div className="fr-col">
          <div className="fr-fieldset__element">
            <div className="fr-radio-group">
              <input
                id="id_waste_type_all"
                type="radio"
                checked={selectBsdTypeFilter.root.length === 0}
                name="waste_type"
                onChange={() =>
                  dispatch(clearFilter({ filterKey: BSD_TYPE_FILTER_KEY }))
                }
              />
              <label htmlFor="id_waste_type_all">
                Tous les types de déchets
              </label>
            </div>
          </div>

          <div className="fr-fieldset__element">
            <div className="fr-radio-group">
              <input
                id="id_waste_type_bsda"
                type="radio"
                name="waste_type"
                checked={selectBsdTypeFilter.root.includes(BSDA)}
                onChange={() =>
                  dispatch(
                    setFilter({ filterKey: BSD_TYPE_FILTER_KEY, value: BSDA }),
                  )
                }
              />
              <label htmlFor="id_waste_type_bsda">Amiante</label>
            </div>
          </div>

          <div className="fr-fieldset__element">
            <div className="fr-radio-group">
              <input
                id="id_waste_type_bsdasri"
                type="radio"
                name="waste_type"
                checked={selectBsdTypeFilter.root.includes(BSDASRI)}
                onChange={() =>
                  dispatch(
                    setFilter({
                      filterKey: BSD_TYPE_FILTER_KEY,
                      value: BSDASRI,
                    }),
                  )
                }
              />
              <label htmlFor="id_waste_type_bsdasri">DASRI</label>
            </div>
          </div>

          <div className="fr-fieldset__element">
            <div className="fr-radio-group">
              <input
                id="id_waste_type_bsdd"
                type="radio"
                name="waste_type"
                checked={selectBsdTypeFilter.root.includes(BSDD)}
                onChange={() =>
                  dispatch(
                    setFilter({ filterKey: BSD_TYPE_FILTER_KEY, value: BSDD }),
                  )
                }
              />
              <label htmlFor="id_waste_type_bsdd">Déchets dangereux</label>
            </div>
          </div>

          <div className="fr-fieldset__element">
            <div className="fr-radio-group">
              <input
                id="id_waste_type_bsdnd"
                type="radio"
                name="waste_type"
                checked={selectBsdTypeFilter.root.includes(BSDND)}
                onChange={() =>
                  dispatch(
                    setFilter({ filterKey: BSD_TYPE_FILTER_KEY, value: BSDND }),
                  )
                }
              />
              <label htmlFor="id_waste_type_bsdnd">Déchets non dangereux</label>
            </div>
          </div>

          <div className="fr-fieldset__element">
            <div className="fr-radio-group">
              <input
                id="id_waste_type_6"
                type="radio"
                name="waste_type"
                checked={selectBsdTypeFilter.root.includes(BSFF)}
                onChange={() =>
                  dispatch(
                    setFilter({ filterKey: BSD_TYPE_FILTER_KEY, value: BSFF }),
                  )
                }
              />
              <label htmlFor="id_waste_type_6">Fluide frigorigène</label>
            </div>
          </div>
          <div className="fr-fieldset__element">
            <div className="fr-radio-group">
              <input
                id="id_waste_type_ssd"
                type="radio"
                name="waste_type"
                checked={selectBsdTypeFilter.root.includes(SSD)}
                onChange={() =>
                  dispatch(
                    setFilter({ filterKey: BSD_TYPE_FILTER_KEY, value: SSD }),
                  )
                }
              />
              <label htmlFor="id_waste_type_ssd">
                Sortie de statut de déchet
              </label>
            </div>
          </div>
          <div className="fr-fieldset__element">
            <div className="fr-radio-group">
              <input
                id="id_waste_type_texs"
                type="radio"
                name="waste_type"
                checked={selectBsdTypeFilter.root.includes(TEXS)}
                onChange={() =>
                  dispatch(
                    setFilter({ filterKey: BSD_TYPE_FILTER_KEY, value: TEXS }),
                  )
                }
              />
              <label htmlFor="id_waste_type_texs">
                Terres et Sédiments - Déchets Non Dangereux
              </label>
            </div>
          </div>
          <div className="fr-fieldset__element">
            <div className="fr-radio-group">
              <input
                id="id_waste_type_texs_dd"
                type="radio"
                name="waste_type"
                checked={selectBsdTypeFilter.root.includes(TEXS_DD)}
                onChange={() =>
                  dispatch(
                    setFilter({
                      filterKey: BSD_TYPE_FILTER_KEY,
                      value: TEXS_DD,
                    }),
                  )
                }
              />
              <label htmlFor="id_waste_type_texs_dd">
                Terres et Sédiments - Déchets Dangereux
              </label>
            </div>
          </div>
          <div className="fr-fieldset__element">
            <div className="fr-radio-group">
              <input
                id="id_waste_type_vhu"
                type="radio"
                name="waste_type"
                checked={selectBsdTypeFilter.root.includes(BSVHU)}
                onChange={() =>
                  dispatch(
                    setFilter({ filterKey: BSD_TYPE_FILTER_KEY, value: BSVHU }),
                  )
                }
              />
              <label htmlFor="id_waste_type_vhu">Véhicules hors d'usage</label>
            </div>
          </div>
        </div>

        <div className="fr-col">
          <fieldset
            className="fr-fieldset"
            id="checkboxes"
            aria-labelledby="checkboxes-legend checkboxes-messages"
          >
            <legend
              className="fr-fieldset__legend--regular fr-fieldset__legend"
              id="checkboxes-legend"
            >
              Rôle sur le bordereau
            </legend>
            <div className="fr-fieldset__element">
              <div className="fr-checkbox-group">
                <input
                  name="checkboxes-1"
                  id="checkboxes-1"
                  type="checkbox"
                  aria-describedby="checkboxes-1-messages"
                  disabled={selectBsdTypeFilter.root.includes(SSD)}
                  checked={selectRoleFilters.root.includes(ROLE_EMITTER)}
                  onChange={(e) =>
                    e.target.checked
                      ? dispatch(
                          addFilter({
                            filterKey: ROLE_FILTER_KEY,
                            value: ROLE_EMITTER,
                          }),
                        )
                      : dispatch(
                          removeFilter({
                            filterKey: ROLE_FILTER_KEY,
                            value: ROLE_EMITTER,
                          }),
                        )
                  }
                />
                <label className="fr-label" htmlFor="checkboxes-1">
                  Producteur - émetteur
                </label>
                <div
                  className="fr-messages-group"
                  id="checkboxes-1-messages"
                  aria-live="assertive"
                ></div>
              </div>
            </div>
            <div className="fr-fieldset__element">
              <div className="fr-checkbox-group">
                <input
                  name="checkboxes-2"
                  id="checkboxes-2"
                  type="checkbox"
                  aria-describedby="checkboxes-2-messages"
                  checked={selectRoleFilters.root.includes(ROLE_TRANSPORTER)}
                  disabled={
                    selectBsdTypeFilter.root.includes(SSD) ||
                    selectBsdTypeFilter.root.includes(TEXS)
                  }
                  onChange={(e) =>
                    e.target.checked
                      ? dispatch(
                          addFilter({
                            filterKey: ROLE_FILTER_KEY,
                            value: ROLE_TRANSPORTER,
                          }),
                        )
                      : dispatch(
                          removeFilter({
                            filterKey: ROLE_FILTER_KEY,
                            value: ROLE_TRANSPORTER,
                          }),
                        )
                  }
                />
                <label className="fr-label" htmlFor="checkboxes-2">
                  Transporteur
                </label>
                <div
                  className="fr-messages-group"
                  id="checkboxes-2-messages"
                ></div>
              </div>
            </div>
            <div className="fr-fieldset__element">
              <div className="fr-checkbox-group">
                <input
                  name="checkboxes-3"
                  id="checkboxes-3"
                  type="checkbox"
                  aria-describedby="checkboxes-3-messages"
                  disabled={!selectBsdTypeFilter.root.includes(BSDA)}
                  checked={selectRoleFilters.root.includes(ROLE_WORKER)}
                  onChange={(e) =>
                    e.target.checked
                      ? dispatch(
                          addFilter({
                            filterKey: ROLE_FILTER_KEY,
                            value: ROLE_WORKER,
                          }),
                        )
                      : dispatch(
                          removeFilter({
                            filterKey: ROLE_FILTER_KEY,
                            value: ROLE_WORKER,
                          }),
                        )
                  }
                />
                <label className="fr-label" htmlFor="checkboxes-3">
                  Entreprise de travaux amiante
                </label>
                <div
                  className="fr-messages-group"
                  id="checkboxes-3-messages"
                ></div>
              </div>
            </div>{" "}
            <div className="fr-fieldset__element">
              <div className="fr-checkbox-group">
                <input
                  name="checkboxes-4"
                  id="checkboxes-4"
                  type="checkbox"
                  aria-describedby="checkboxes-4-messages"
                  disabled={selectBsdTypeFilter.root.includes(SSD)}
                  checked={selectRoleFilters.root.includes(ROLE_DESTINATION)}
                  onChange={(e) =>
                    e.target.checked
                      ? dispatch(
                          addFilter({
                            filterKey: ROLE_FILTER_KEY,
                            value: ROLE_DESTINATION,
                          }),
                        )
                      : dispatch(
                          removeFilter({
                            filterKey: ROLE_FILTER_KEY,
                            value: ROLE_DESTINATION,
                          }),
                        )
                  }
                />
                <label className="fr-label" htmlFor="checkboxes-4">
                  Destinataire (lié au traitement réalisé)
                </label>
                <div
                  className="fr-messages-group"
                  id="checkboxes-4-messages"
                ></div>
              </div>
            </div>
            <div className="fr-messages-group" id="checkboxes-messages"></div>
          </fieldset>
        </div>
      </div>
    </div>
  );
};

export default WasteTypesAndRoles;
