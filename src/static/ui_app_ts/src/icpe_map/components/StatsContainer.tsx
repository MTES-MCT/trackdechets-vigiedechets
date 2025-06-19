import React, { ReactNode } from "react";

import { RootState, useAppDispatch, useAppSelector } from "../store/root";
import { setStatsOpened } from "../store/uiSlice";
import { formatInt, formatFloat, formatPercentage } from "./formatUtils.ts";

const Address = ({ selectedCompany }) => {
  if (!selectedCompany) {
    return null;
  }
  return (
    <>
      <div className="grouped-info">
        <p> {selectedCompany?.adresse1}</p>
        <p> {selectedCompany?.adresse2}</p>
        <p>
          {selectedCompany?.code_postal} {selectedCompany?.commune}
        </p>
      </div>
    </>
  );
};
const Info = ({ selectedDepartement, selectedRegion, selectedCompany }) => {
  let nombre_installations = null;
  let quantite_autorisee = null;
  let cumul_quantite_traitee = null;
  let taux_consommation = null;
  if (selectedDepartement) {
    nombre_installations = selectedDepartement?.nombre_installations;
    quantite_autorisee = selectedDepartement?.quantite_autorisee;
    cumul_quantite_traitee = selectedDepartement?.cumul_quantite_traitee;
    taux_consommation = selectedDepartement?.taux_consommation;
  }
  if (selectedRegion) {
    nombre_installations = selectedRegion?.nombre_installations;
    quantite_autorisee = selectedRegion?.quantite_autorisee;
    cumul_quantite_traitee = selectedRegion?.cumul_quantite_traitee;
    taux_consommation = selectedRegion?.taux_consommation;
  }
  if (selectedCompany) {
    quantite_autorisee = selectedCompany?.quantite_autorisee;
    cumul_quantite_traitee = selectedCompany?.cumul_quantite_traitee;
    taux_consommation = selectedCompany?.taux_consommation;
  }

  return (
    <>
      <Address selectedCompany={selectedCompany} />

      <div className="grouped-info">
        {nombre_installations && (
          <p>Nombre d'installations : {nombre_installations}</p>
        )}
      </div>

      <div className="grouped-info">
        <p>
          Quantité autorisée :{" "}
          <span>
            {quantite_autorisee ? formatInt(quantite_autorisee) : "N/A"} t/an
          </span>
        </p>
        <p>
          Quantité traitée en cumulé :{" "}
          <span>
            {cumul_quantite_traitee
              ? formatFloat(cumul_quantite_traitee)
              : "N/A"}{" "}
            t/an
          </span>
        </p>{" "}
        <p>
          Quantité consommée sur l'année :{" "}
          <span>
            {taux_consommation ? formatPercentage(taux_consommation) : " N/A"}
          </span>
        </p>
      </div>
    </>
  );
};

export const StatsContainer: React.FC = () => {
  const {
    statsOpened,

    selectedCompany,
    selectedRegion,
    selectedDepartement,
    graphUrl,
  } = useAppSelector((state: RootState) => state.ui);
  const dispatch = useAppDispatch();

  if (!statsOpened) {
    return null;
  }

  return (
    <div className="icpe-stats-container">
      <div className="icpe-stats-container-header">
        <button
          className="fr-btn fr-btn--tertiary-no-outline fr-btn--icon-right fr-icon-close-line"
          title="Fermer"
          id="close-stats"
          onClick={() => dispatch(setStatsOpened(false))}
        >
          Fermer
        </button>
      </div>

      {/*<div id="region-title">*/}
      {/*  <h5>*/}
      {/*    {selectedCompany?.raison_sociale}*/}
      {/*    {selectedRegion?.nom_region}*/}
      {/*    {selectedDepartement?.nom_departement}*/}
      {/*  </h5>*/}
      {/*</div>*/}

      {/*<Info*/}
      {/*  selectedDepartement={selectedDepartement}*/}
      {/*  selectedRegion={selectedRegion}*/}
      {/*  selectedCompany={selectedCompany}*/}
      {/*/>*/}

      {graphUrl && (
        <iframe
          src={graphUrl}
          style={{ height: "700px", width: "700px" }}
        ></iframe>
      )}
    </div>
  );
};

66735008600035;
66735008600035;
