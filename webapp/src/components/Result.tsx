import React from "react";
import Figure from "./Figure";
import { AnalyzeResponse } from "../lib/api";

type ResultProps = {
  data: AnalyzeResponse;
};

const badgeClass = (status: string) => {
  switch (status) {
    case "PASS":
      return "bg-emerald-500/20 text-emerald-200";
    case "FAIL":
      return "bg-red-500/20 text-red-200";
    default:
      return "bg-slate-500/20 text-slate-200";
  }
};

const Result: React.FC<ResultProps> = ({ data }) => {
  const figures = Array.isArray(data.outputs.figures) ? data.outputs.figures : [];
  return (
    <section className="rounded-lg bg-slate-800 p-6 shadow-lg">
      <h2 className="text-2xl font-semibold">Results</h2>
      <div className="mt-4 grid gap-4">
        {data.results.map((item) => (
          <div key={item.clause_id} className="rounded border border-slate-700 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-lg font-semibold">{item.clause_id} – {item.title}</h3>
              <span className={`rounded px-3 py-1 text-sm font-semibold ${badgeClass(item.status)}`}>
                {item.status}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-300">{item.notes}</p>
          </div>
        ))}
      </div>
      <div className="mt-6 flex flex-wrap gap-4">
        <a href={data.outputs.pdf} className="rounded bg-blue-500 px-4 py-2 font-semibold text-white hover:bg-blue-400" download>
          Download PDF
        </a>
        <a href={data.outputs.xlsx} className="rounded bg-blue-500 px-4 py-2 font-semibold text-white hover:bg-blue-400" download>
          Download Matrix (XLSX)
        </a>
      </div>
      {figures.length > 0 && (
        <div className="mt-6">
          <h3 className="text-xl font-semibold">Overshadowing Figures</h3>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            {figures.map((fig) => (
              <Figure key={fig} src={fig} />
            ))}
          </div>
        </div>
      )}
    </section>
  );
};

export default Result;
