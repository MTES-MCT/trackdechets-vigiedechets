// Orange color interpolation function to mimic D 3scaleSequential
function interpolateOranges(t: number): string {
  // Clamp t to [0, 1]
  t = Math.max(0, Math.min(1, t));

  // Define orange color stops (RGB values)
  const colors = [
    [255, 245, 235], // Very light orange
    [254, 230, 206], // Light orange
    [253, 208, 162], // Light-medium orange
    [253, 174, 107], // Medium orange
    [253, 141, 60], // Medium-dark orange
    [241, 105, 19], // Dark orange
    [217, 72, 1], // Very dark orange
    [140, 45, 4], // Darkest orange
  ];

  // Scale t to color array indices
  const scaledT = t * (colors.length - 1);
  const lowerIndex = Math.floor(scaledT);
  const upperIndex = Math.ceil(scaledT);
  const fraction = scaledT - lowerIndex;

  // Handle edge case
  if (lowerIndex === upperIndex) {
    const [r, g, b] = colors[lowerIndex];
    return `rgb(${r}, ${g}, ${b})`;
  }

  // Interpolate between the two colors
  const [r1, g1, b1] = colors[lowerIndex];
  const [r2, g2, b2] = colors[upperIndex];

  const r = Math.round(r1 + (r2 - r1) * fraction);
  const g = Math.round(g1 + (g2 - g1) * fraction);
  const b = Math.round(b1 + (b2 - b1) * fraction);

  return `rgb(${r}, ${g}, ${b})`;
}

// Create a color scale function that takes domain and returns a function
function scaleSequential(
  interpolator: (t: number) => string,
  domain: [number, number] = [0, 1],
): (value: number) => string {
  const [min, max] = domain;

  return (value: number): string => {
    const normalized = (value - min) / (max - min);
    return interpolator(normalized);
  };
}

export { scaleSequential, interpolateOranges };
