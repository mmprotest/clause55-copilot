import React, { useState } from "react";
import Upload from "./components/Upload";
import Result from "./components/Result";
import { AnalyzeResponse, analyze } from "./lib/api";

const App: React.FC = () => {
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (formData: FormData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await analyze(formData);
      setResult(response);
    } catch (err) {
      console.error(err);
      setError("Analysis failed. Check the server logs.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <header className="px-6 py-8 text-center">
        <h1 className="text-3xl font-semibold">Clause55 Copilot</h1>
        <p className="text-slate-300">Upload your site and massing to run Clause 55 checks.</p>
      </header>
      <main className="mx-auto flex max-w-5xl flex-col gap-8 px-6 pb-16">
        <Upload onAnalyze={handleAnalyze} loading={loading} />
        {error && <div className="rounded bg-red-500/20 p-4 text-red-200">{error}</div>}
        {result && <Result data={result} />}
      </main>
    </div>
  );
};

export default App;
