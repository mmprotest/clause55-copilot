import React from "react";

type FigureProps = {
  src: string;
};

const Figure: React.FC<FigureProps> = ({ src }) => {
  const filename = src.split("/").pop();
  return (
    <div className="rounded border border-slate-700 p-2 text-center">
      <img src={src} alt={filename ?? "Figure"} className="mx-auto max-h-48" />
      <p className="mt-2 text-xs text-slate-400">{filename}</p>
    </div>
  );
};

export default Figure;
