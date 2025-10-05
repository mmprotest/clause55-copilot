import React, { useState } from "react";

type UploadProps = {
  onAnalyze: (form: FormData) => Promise<void>;
  loading: boolean;
};

const Upload: React.FC<UploadProps> = ({ onAnalyze, loading }) => {
  const [useMockProperty, setUseMockProperty] = useState(true);
  const [analysisDate, setAnalysisDate] = useState("2024-09-22");
  const [startHour, setStartHour] = useState("09:00");
  const [endHour, setEndHour] = useState("15:00");
  const [propertyFile, setPropertyFile] = useState<File | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const spec = {
      analysis_date: analysisDate,
      start_time: startHour,
      end_time: endHour,
      time_step_minutes: 60,
      raster_resolution: 0.5
    };
    form.append("report_spec", JSON.stringify(spec));
    form.set("use_mock_property", useMockProperty ? "true" : "false");
    if (propertyFile) {
      form.append("property_report", propertyFile);
    }
    await onAnalyze(form);
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-lg bg-slate-800 p-6 shadow-lg">
      <div className="grid gap-4 md:grid-cols-2">
        <label className="flex flex-col gap-2">
          <span className="text-sm text-slate-300">Site JSON</span>
          <input name="site" type="file" accept="application/json" required disabled={loading} className="rounded border border-slate-600 bg-slate-900 p-2" />
        </label>
        <label className="flex flex-col gap-2">
          <span className="text-sm text-slate-300">Massing JSON</span>
          <input name="massing" type="file" accept="application/json" required disabled={loading} className="rounded border border-slate-600 bg-slate-900 p-2" />
        </label>
        <label className="flex flex-col gap-2">
          <span className="text-sm text-slate-300">Analysis date</span>
          <input type="date" value={analysisDate} onChange={(e) => setAnalysisDate(e.target.value)} disabled={loading} className="rounded border border-slate-600 bg-slate-900 p-2" />
        </label>
        <div className="grid grid-cols-2 gap-2">
          <label className="flex flex-col gap-2">
            <span className="text-sm text-slate-300">Start time</span>
            <input type="time" value={startHour} onChange={(e) => setStartHour(e.target.value)} disabled={loading} className="rounded border border-slate-600 bg-slate-900 p-2" />
          </label>
          <label className="flex flex-col gap-2">
            <span className="text-sm text-slate-300">End time</span>
            <input type="time" value={endHour} onChange={(e) => setEndHour(e.target.value)} disabled={loading} className="rounded border border-slate-600 bg-slate-900 p-2" />
          </label>
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-300">
          <input
            type="checkbox"
            checked={useMockProperty}
            onChange={(e) => setUseMockProperty(e.target.checked)}
            disabled={loading}
          />
          Use mock property report
        </label>
        <label className="flex flex-col gap-2">
          <span className="text-sm text-slate-300">Property report (optional)</span>
          <input
            type="file"
            accept="application/json"
            onChange={(event) => setPropertyFile(event.target.files?.[0] ?? null)}
            disabled={loading}
            className="rounded border border-slate-600 bg-slate-900 p-2"
          />
        </label>
      </div>
      <div className="mt-6">
        <button
          type="submit"
          disabled={loading}
          className="rounded bg-blue-500 px-4 py-2 font-semibold text-white hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Analyzing…" : "Run Clause 55"}
        </button>
      </div>
    </form>
  );
};

export default Upload;
