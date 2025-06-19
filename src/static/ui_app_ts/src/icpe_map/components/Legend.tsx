import { interpolateOranges, scaleSequential } from "./colorsUtils.ts";
import { dark, red } from "../constants.ts";

export const Legend = () => {
  const colorScale = scaleSequential(interpolateOranges);
  const grades = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90];
  return (
    <div className="icpe-legend">
      <h4 className="icpe-legend-title">% de la quantité autorisée</h4>

      <div className="icpe-legend-label">
        <i style={{ backgroundColor: dark }} className="icpe-legend-bar" />
        Pas de données
      </div>
      {grades.map((g) => (
        <div className="icpe-legend-label" key={`label-${g}`}>
          <i
            style={{ backgroundColor: colorScale(g / 100) }}
            className="icpe-legend-bar"
          />
          {g} - {g + 10}
        </div>
      ))}

      <div className="icpe-legend-label">
        <i style={{ backgroundColor: red }} className="icpe-legend-bar" />
        100+
      </div>
    </div>
  );
};
