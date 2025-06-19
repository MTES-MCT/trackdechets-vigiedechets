import React, { ReactNode } from "react";

import { RootState, useAppDispatch } from "../store/root";
import { useSelector } from "react-redux";
import { setModalState } from "../store/modalSlice";
import { resetFilters } from "../store/searchFiltersSlice";
import { fetchPlots } from "../store/mapDataSlice.ts";

interface ModalProps {
  children: ReactNode;
}

export const Modal: React.FC<ModalProps> = ({ children }) => {
  const opened = useSelector((state: RootState) => state.modal.opened);
  const dispatch = useAppDispatch();

  if (!opened) {
    return null;
  }
  return (
    <dialog
      aria-labelledby="fr-modal-title-modal"
      role="dialog"
      className="fr-modal fr-modal--opened"
      data-fr-js-modal={false}
    >
      <div className="fr-container fr-container--fluid fr-container-md">
        <div className="fr-grid-row fr-grid-row--center">
          <div className="fr-col-10">
            <div className="fr-modal__body">
              <div className="fr-modal__header">
                <button
                  className="fr-btn--close fr-btn"
                  title="Fermer la fenêtre modale"
                  aria-controls="fr-modal"
                  onClick={() => dispatch(setModalState(false))}
                >
                  Fermer
                </button>
              </div>
              <div className="fr-modal__content">{children}</div>
              <div className="fr-modal__footer">
                <div className="fr-btns-group fr-btns-group--right fr-btns-group--inline-reverse fr-btns-group--inline-lg fr-btns-group--icon-left">
                  <button
                    className="fr-btn"
                    onClick={() => {
                      dispatch(fetchPlots());
                      dispatch(setModalState(false));
                    }}
                  >
                    Appliquer
                  </button>
                  <button
                    className="fr-btn fr-btn--secondary"
                    onClick={() => dispatch(resetFilters())}
                  >
                    Supprimer les filtres
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </dialog>
  );
};
