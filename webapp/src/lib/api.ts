export type CheckResult = {
  clause_id: string;
  title: string;
  status: "PASS" | "FAIL" | "N/A";
  notes: string;
  metrics: Record<string, number>;
};

export type AnalyzeResponse = {
  results: CheckResult[];
  outputs: {
    pdf: string;
    xlsx: string;
    figures: string[];
  };
};

const API_BASE = (import.meta as any).env.VITE_API_BASE ?? "http://localhost:8000";

export async function analyze(form: FormData): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: form
  });
  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }
  return response.json();
}
