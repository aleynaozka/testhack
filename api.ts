// Lovable projesinde src/lib/api.ts olarak kullanabilirsiniz.
const API_URL = import.meta.env.VITE_API_URL;

if (!API_URL) {
  throw new Error("VITE_API_URL tanımlı değil.");
}

async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "API isteği başarısız oldu.");
  }
  return response.json() as Promise<T>;
}

export const isovApi = {
  health: () => apiRequest("/health"),

  validateRegistration: (email: string, role: "student" | "academic" | "industry") =>
    apiRequest("/api/auth/validate-registration", {
      method: "POST",
      body: JSON.stringify({ email, role }),
    }),

  getVerifiedUser: (accessToken: string) =>
    apiRequest("/api/auth/me", {
      headers: { Authorization: `Bearer ${accessToken}` },
    }),

  validateIndustry: (payload: {
    industry_type: "entrepreneur" | "company_without_rd" | "rd_center";
    method: "google_oauth" | "work_email" | "manual_review" | "rd_center_document";
    email: string;
    company_name?: string;
  }) =>
    apiRequest("/api/auth/industry-verification", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  analyzeProblem: (problemText: string, industryType: string, aiMode = "auto") =>
    apiRequest("/api/ai/analyze-problem", {
      method: "POST",
      body: JSON.stringify({
        problem_text: problemText,
        industry_type: industryType,
        ai_mode: aiMode,
      }),
    }),

  matchAcademics: (problemText: string, industryType: string) =>
    apiRequest("/api/match", {
      method: "POST",
      body: JSON.stringify({
        problem_text: problemText,
        target_role: "academic",
        industry_type: industryType,
        ai_mode: "auto",
        top_k: 5,
      }),
    }),

  matchTeam: (problemText: string, industryType: string, studentCount = 3) =>
    apiRequest("/api/match/team", {
      method: "POST",
      body: JSON.stringify({
        problem_text: problemText,
        industry_type: industryType,
        student_count: studentCount,
        ai_mode: "auto",
        confidentiality: "masked",
      }),
    }),

  searchStudents: (query: string) =>
    apiRequest("/api/ai/talent-search", {
      method: "POST",
      body: JSON.stringify({ query, ai_mode: "auto", top_k: 5 }),
    }),

  assistant: (message: string, industryType: string) =>
    apiRequest("/api/assistant/message", {
      method: "POST",
      body: JSON.stringify({
        message,
        industry_type: industryType,
        ai_mode: "auto",
      }),
    }),
};
