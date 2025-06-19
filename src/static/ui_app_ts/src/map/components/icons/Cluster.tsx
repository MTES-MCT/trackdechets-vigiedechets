import React from "react";

interface ClusterProps {
  txt?: string | number;
  fill?: string;
}

export const Cluster: React.FC<ClusterProps> = ({
  txt = 11,
  fill = "#777",
}) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    height="80"
    width="80"
    className="pointable"
  >
    <circle cx="40px" cy="40px" r="18px" fill={fill} />
    <circle cx="40px" cy="40px" r="24px" fillOpacity="0.8" fill={fill} />
    <circle cx="40px" cy="40px" r="30px" fillOpacity="0.5" fill={fill} />
    <circle cx="40px" cy="40px" r="36px" fillOpacity="0.20" fill={fill} />
    <circle cx="40px" cy="40px" r="40px" fillOpacity="0.10" fill={fill} />
    <text
      x="40"
      y="28"
      fill="white"
      fontSize="12"
      fontWeight="bold"
      textAnchor="middle"
      dominantBaseline="middle"
      fontFamily="Verdana"
      dy="12px"
    >
      {txt}
    </text>
  </svg>
);
