import { useEffect, useState } from "react";
import Papa from "papaparse";

const FEATURES_COUNT = 30;
const API_BASE = "http://127.0.0.1:8000";
const TOKEN_STORAGE_KEY = "breast-cancer-auth-token";

type DiagnosisMode = "biochemical" | "image";

const FEATURE_NAMES = [
  "radius",
  "texture",
  "perimeter",
  "area",
  "smoothness",
  "compactness",
  "concavity",
  "concave points",
  "symmetry",
  "fractal dimension"
];

const FEATURE_GROUPS = [
  { label: "Mean", start: 0, end: 10 },
  { label: "Standard Error", start: 10, end: 20 },
  { label: "Worst", start: 20, end: 30 }
];

type ShapExplanation = {
  values?: Record<string, number>;
  text?: string[];
  error?: string;
};

type PredictionResponse = {
  prediction: "benign" | "malignant";
  probability: number;
  explanation?: ShapExplanation | null;
  history_id?: string | null;
  record_code?: string | null;
  created_at?: string | null;
};

type ImagePredictionResponse = {
  prediction: "benign" | "malignant";
  confidence: number;
  probabilities: {
    benign: number;
    malignant: number;
  };
  gradcam?: string | null;
  history_id?: string | null;
  record_code?: string | null;
  created_at?: string | null;
};

type UserResponse = {
  id: string;
  username: string;
  role: string;
  created_at: string;
};

type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  user: UserResponse;
};

type HistoryRecord = {
  id: string;
  record_code?: string | null;
  diagnosis_type: DiagnosisMode;
  prediction: "benign" | "malignant";
  confidence: number;
  created_at: string;
  file_name?: string | null;
  probabilities?: {
    benign: number;
    malignant: number;
  } | null;
  explanation?: ShapExplanation | null;
  input_data: Record<string, unknown>;
};

type AdminUser = {
  id: string;
  username: string;
  role: string;
  created_at: string;
  history_count: number;
};

function formatPrediction(prediction: "benign" | "malignant") {
  return prediction === "benign" ? "Lành tính" : "Ác tính";
}

function formatDiagnosisType(type: DiagnosisMode) {
  return type === "biochemical" ? "Sinh hóa" : "Hình ảnh";
}

function formatTimestamp(value?: string | null) {
  if (!value) return "Vừa xong";

  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(new Date(value));
}

async function readErrorMessage(response: Response, fallback: string) {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail ?? fallback;
  } catch {
    return fallback;
  }
}

export default function App() {
  const [mode, setMode] = useState<DiagnosisMode>("biochemical");
  const [features, setFeatures] = useState<string[]>(Array(FEATURES_COUNT).fill(""));
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [historySearchCode, setHistorySearchCode] = useState("");
  const [historySearchResult, setHistorySearchResult] = useState<HistoryRecord | null>(null);
  const [historySearchMessage, setHistorySearchMessage] = useState<string | null>(null);
  const [historyFilterActive, setHistoryFilterActive] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [imageResult, setImageResult] = useState<ImagePredictionResponse | null>(null);
  const [historyRecords, setHistoryRecords] = useState<HistoryRecord[]>([]);
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([]);
  const [adminLoading, setAdminLoading] = useState(false);
  const [adminError, setAdminError] = useState<string | null>(null);
  const [adminSuccess, setAdminSuccess] = useState<string | null>(null);
  const [createDoctorLoading, setCreateDoctorLoading] = useState(false);
  const [doctorCredentials, setDoctorCredentials] = useState({ username: "", password: "" });
  const [editingUser, setEditingUser] = useState<{ id: string; newPassword: string } | null>(null);
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [currentUser, setCurrentUser] = useState<UserResponse | null>(null);

  const isAuthenticated = Boolean(token && currentUser);
  const isAdmin = currentUser?.role === "admin";
  const canDiagnose = !isAdmin;

  const resetSession = () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setCurrentUser(null);
    setHistoryRecords([]);
    setHistorySearchResult(null);
    setHistorySearchCode("");
    setHistorySearchMessage(null);
    setHistoryFilterActive(false);
    setAdminUsers([]);
    setAdminSuccess(null);
  };

  const loadAdminUsers = async (activeToken: string) => {
    try {
      setAdminLoading(true);
      setAdminError(null);
      const response = await fetch(`${API_BASE}/admin/users`, {
        headers: { Authorization: `Bearer ${activeToken}` }
      });
      if (!response.ok) throw new Error(await readErrorMessage(response, "Kh\u00f4ng th\u1ec3 t\u1ea3i danh s\u00e1ch ng\u01b0\u1eddi d\u00f9ng."));
      setAdminUsers((await response.json()) as AdminUser[]);
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "L\u1ed7i kh\u00f4ng x\u00e1c đ\u1ecbnh.");
    } finally {
      setAdminLoading(false);
    }
  };

  const handleDeleteUser = async (userId: string, username: string) => {
    if (!token) return;
    if (!window.confirm(`X\u00f3a t\u00e0i kho\u1ea3n "${username}"? H\u00e0nh đ\u1ed9ng n\u00e0y kh\u00f4ng th\u1ec3 ho\u00e0n t\u00e1c.`)) return;
    try {
      const res = await fetch(`${API_BASE}/admin/users/${userId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(await readErrorMessage(res, "Kh\u00f4ng th\u1ec3 x\u00f3a."));
      setAdminUsers((prev) => prev.filter((u) => u.id !== userId));
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "L\u1ed7i khi x\u00f3a.");
    }
  };

  const handleChangeRole = async (userId: string, newRole: "admin" | "doctor") => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/admin/users/${userId}`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ role: newRole })
      });
      if (!res.ok) throw new Error(await readErrorMessage(res, "Kh\u00f4ng th\u1ec3 c\u1eadp nh\u1eadt role."));
      const updated = (await res.json()) as AdminUser;
      setAdminUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "L\u1ed7i khi c\u1eadp nh\u1eadt.");
    }
  };

  const handleResetPassword = async (userId: string) => {
    if (!token || !editingUser || editingUser.id !== userId) return;
    if (!editingUser.newPassword || editingUser.newPassword.length < 6) {
      setAdminError("M\u1eadt kh\u1ea9u ph\u1ea3i t\u1ed1i thi\u1ec3u 6 k\u00fd t\u1ef1.");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/admin/users/${userId}`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ password: editingUser.newPassword })
      });
      if (!res.ok) throw new Error(await readErrorMessage(res, "Kh\u00f4ng th\u1ec3 đ\u1ed5i m\u1eadt kh\u1ea9u."));
      setEditingUser(null);
      setAdminError(null);
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "L\u1ed7i khi đ\u1ed5i m\u1eadt kh\u1ea9u.");
    }
  };

  const handleCreateDoctorAccount = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!token) return;

    const username = doctorCredentials.username.trim();
    const password = doctorCredentials.password;
    if (username.length < 3) {
      setAdminError("Tên đăng nhập bác sĩ phải từ 3 ký tự.");
      return;
    }
    if (password.length < 6) {
      setAdminError("Mật khẩu bác sĩ phải từ 6 ký tự.");
      return;
    }

    try {
      setCreateDoctorLoading(true);
      setAdminError(null);
      setAdminSuccess(null);
      const response = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response, "Không thể tạo tài khoản bác sĩ."));
      }

      setDoctorCredentials({ username: "", password: "" });
      setAdminSuccess(`Đã tạo tài khoản bác sĩ: ${username}`);
      await loadAdminUsers(token);
    } catch (err) {
      setAdminError(err instanceof Error ? err.message : "Không thể tạo tài khoản bác sĩ.");
    } finally {
      setCreateDoctorLoading(false);
    }
  };

  const loadHistory = async (activeToken: string) => {
    try {
      setHistoryLoading(true);
      setHistoryError(null);
      const response = await fetch(`${API_BASE}/history`, {
        headers: {
          Authorization: `Bearer ${activeToken}`
        }
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response, "Không thể tải lịch sử chẩn đoán."));
      }

      const data = (await response.json()) as HistoryRecord[];
      setHistoryRecords(data);
      setHistorySearchResult(null);
      setHistorySearchMessage(null);
      setHistoryFilterActive(false);
    } catch (err) {
      setHistoryError(err instanceof Error ? err.message : "Không thể tải lịch sử chẩn đoán.");
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleSearchHistoryByCode = async () => {
    if (!token) {
      setHistoryError("Bạn cần đăng nhập để tìm kiếm hồ sơ.");
      return;
    }

    const code = historySearchCode.trim().toUpperCase();
    if (!code) {
      setHistorySearchMessage("Vui lòng nhập mã hồ sơ.");
      setHistorySearchResult(null);
      setHistoryFilterActive(false);
      return;
    }

    try {
      setHistoryLoading(true);
      setHistoryError(null);
      setHistorySearchMessage(null);

      const response = await fetch(`${API_BASE}/history/search?record_code=${encodeURIComponent(code)}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response, "Không thể tìm hồ sơ."));
      }

      const data = (await response.json()) as HistoryRecord;
      setHistorySearchResult(data);
      setHistorySearchMessage(`Đã tìm thấy hồ sơ ${code}.`);
      setHistoryFilterActive(true);
    } catch (err) {
      setHistorySearchResult(null);
      setHistorySearchMessage(err instanceof Error ? err.message : "Không thể tìm hồ sơ.");
      setHistoryFilterActive(true);
    } finally {
      setHistoryLoading(false);
    }
  };

  const displayedHistoryRecords = historyFilterActive
    ? (historySearchResult ? [historySearchResult] : [])
    : historyRecords;

  useEffect(() => {
    if (!token) {
      setCurrentUser(null);
      setHistoryRecords([]);
      return;
    }

    let cancelled = false;

    const loadSession = async () => {
      try {
        const response = await fetch(`${API_BASE}/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error(await readErrorMessage(response, "Phiên đăng nhập không còn hợp lệ."));
        }

        const user = (await response.json()) as UserResponse;
        if (cancelled) return;
        setCurrentUser(user);
        setAuthError(null);
        if (user.role === "admin") {
          setHistoryRecords([]);
          setHistorySearchResult(null);
          setHistoryFilterActive(false);
          await loadAdminUsers(token);
        } else {
          await loadHistory(token);
        }
      } catch (err) {
        if (cancelled) return;
        resetSession();
        setAuthError(err instanceof Error ? err.message : "Phiên đăng nhập không còn hợp lệ.");
      }
    };

    void loadSession();

    return () => {
      cancelled = true;
    };
  }, [token]);

  const handleFeatureChange = (index: number, value: string) => {
    const newFeatures = [...features];
    newFeatures[index] = value;
    setFeatures(newFeatures);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    Papa.parse(file, {
      header: false,
      skipEmptyLines: true,
      complete: (results: Papa.ParseResult<string[]>) => {
        if (results.data.length === 0) {
          setError("File không có dữ liệu.");
          return;
        }

        const rows = results.data as string[][];

        const parseRow = (row: string[]) => {
          const candidates: number[] = [];
          if (row.length >= FEATURES_COUNT) {
            candidates.push(0);
          }
          if (row.length >= FEATURES_COUNT + 2) {
            candidates.push(2);
          }

          for (const start of candidates) {
            const values = row.slice(start, start + FEATURES_COUNT);
            if (values.length < FEATURES_COUNT) continue;
            const isValid = values.every((v) => {
              const trimmed = v.trim();
              return trimmed !== "" && !Number.isNaN(Number(trimmed));
            });
            if (isValid) {
              return values;
            }
          }

          return null;
        };

        let found: string[] | null = null;
        for (const row of rows) {
          const values = parseRow(row);
          if (values) {
            found = values;
            break;
          }
        }

        if (!found) {
          setError(`Không tìm thấy ${FEATURES_COUNT} giá trị hợp lệ trong file CSV.`);
          return;
        }

        setFeatures(found);
        setError(null);
        setResult(null);
        event.target.value = "";
      }
    });
  };

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Vui lòng chọn file ảnh hợp lệ (JPEG, PNG, etc.)");
      return;
    }

    setImageFile(file);
    setError(null);
    setImageResult(null);

    const reader = new FileReader();
    reader.onload = (e) => {
      setImagePreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    event.target.value = "";
  };

  const handleCredentialsChange = (field: "username" | "password", value: string) => {
    setCredentials((current) => ({
      ...current,
      [field]: value
    }));
  };

  const handleAuthSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setAuthError(null);

    try {
      setAuthLoading(true);
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          username: credentials.username.trim(),
          password: credentials.password
        })
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response, "Không thể đăng nhập."));
      }

      const data = (await response.json()) as AuthResponse;
      localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token);
      setToken(data.access_token);
      setCurrentUser(data.user);
      setCredentials({ username: "", password: "" });
      if (data.user.role === "admin") {
        await loadAdminUsers(data.access_token);
      }
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "Không thể xác thực.");
    } finally {
      setAuthLoading(false);
    }
  };

  const downloadPdf = async (historyId: string) => {
    if (!token) {
      setHistoryError("Bạn cần đăng nhập để tải PDF.");
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/history/${historyId}/pdf`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response, "Không thể tạo PDF."));
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `diagnosis-${historyId}.pdf`;
      document.body.append(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setHistoryError(err instanceof Error ? err.message : "Không thể tạo PDF.");
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setResult(null);

    if (!isAuthenticated) {
      setError("Vui lòng đăng nhập tài khoản bác sĩ trước khi chẩn đoán.");
      return;
    }

    const values = features.map((value) => (value.trim() === "" ? Number.NaN : Number(value)));

    if (values.some((value) => Number.isNaN(value))) {
      setError(`Vui lòng nhập đầy đủ ${FEATURES_COUNT} giá trị hợp lệ.`);
      return;
    }

    try {
      setLoading(true);
      const headers: Record<string, string> = {
        "Content-Type": "application/json"
      };

      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        headers,
        body: JSON.stringify({ features: values })
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response, "Không thể dự đoán. Vui lòng thử lại."));
      }

      const data = (await response.json()) as PredictionResponse;
      setResult(data);
      if (data.history_id && token) {
        await loadHistory(token);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi không xác định.");
    } finally {
      setLoading(false);
    }
  };

  const handleImageSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setImageResult(null);

    if (!isAuthenticated) {
      setError("Vui lòng đăng nhập tài khoản bác sĩ trước khi chẩn đoán.");
      return;
    }

    if (!imageFile) {
      setError("Vui lòng chọn ảnh trước khi phân tích.");
      return;
    }

    try {
      setLoading(true);
      const formData = new FormData();
      formData.append("file", imageFile);

      const headers: Record<string, string> = {};
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}/predict/image`, {
        method: "POST",
        headers,
        body: formData
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response, "Không thể dự đoán. Vui lòng thử lại."));
      }

      const data = (await response.json()) as ImagePredictionResponse;
      setImageResult(data);
      if (data.history_id && token) {
        await loadHistory(token);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi không xác định.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <main className="app-shell">
        <section className="card main-card">
          <header className="hero">
            <div>
              <p className="eyebrow">Clinical Decision Support</p>
              <h1>Hệ thống chẩn đoán ung thư vú</h1>
              <p className="subtitle">
                Bổ sung đăng nhập, lưu lịch sử cá nhân và xuất kết quả dưới dạng PDF ngay sau khi dự đoán.
              </p>
            </div>
            <div className="status-pill">
              {isAuthenticated ? `Đang lưu cho ${currentUser?.username}` : "Chưa đăng nhập"}
            </div>
          </header>

          {canDiagnose && (
            <>
              <div className="mode-tabs">
                <button
                  className={`tab ${mode === "biochemical" ? "active" : ""}`}
                  onClick={() => {
                    setMode("biochemical");
                    setError(null);
                    setResult(null);
                    setImageResult(null);
                  }}
                  type="button"
                >
                  Chỉ số sinh hóa
                </button>
                <button
                  className={`tab ${mode === "image" ? "active" : ""}`}
                  onClick={() => {
                    setMode("image");
                    setError(null);
                    setResult(null);
                    setImageResult(null);
                  }}
                  type="button"
                >
                  Hình ảnh y khoa
                </button>
              </div>

              {!isAuthenticated && (
                <div className="alert info">
                  Bác sĩ cần đăng nhập trước khi chẩn đoán để đảm bảo minh bạch và truy vết hồ sơ.
                </div>
              )}

              {mode === "biochemical" && (
                <form onSubmit={handleSubmit} className="form">
                  <div className="toolbar">
                    <label className="toolbar-btn upload">
                      Upload CSV
                      <input
                        type="file"
                        accept=".csv"
                        onChange={handleFileUpload}
                        style={{ display: "none" }}
                      />
                    </label>
                  </div>

                  {FEATURE_GROUPS.map((group) => (
                    <div key={group.label} className="feature-group">
                      <h3 className="group-title">{group.label}</h3>
                      <div className="feature-grid">
                        {Array.from({ length: group.end - group.start }).map((_, i) => {
                          const index = group.start + i;
                          const featureName = FEATURE_NAMES[i % FEATURE_NAMES.length];
                          return (
                            <div key={index} className="input-wrapper">
                              <label htmlFor={`feature-${index}`} className="input-label">
                                {featureName}
                              </label>
                              <input
                                id={`feature-${index}`}
                                type="number"
                                step="any"
                                value={features[index]}
                                onChange={(e) => handleFeatureChange(index, e.target.value)}
                                placeholder="0.0"
                                className="feature-input"
                              />
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}

                  {error && <div className="alert error">{error}</div>}

                  {result && (
                    <div className={`result ${result.prediction}`}>
                      <div className="result-header">
                        <span className="result-icon">{result.prediction === "benign" ? "OK" : "!"}</span>
                        <div>
                          <div className="result-title">Kết quả chẩn đoán</div>
                          <div className={`result-value ${result.prediction}`}>
                            {formatPrediction(result.prediction)}
                          </div>
                          <div className="result-timestamp">{formatTimestamp(result.created_at)}</div>
                          {result.record_code && <div className="result-record-code">Mã hồ sơ: {result.record_code}</div>}
                        </div>
                      </div>
                      <div className="result-detail">
                        <span className="detail-label">Độ tin cậy</span>
                        <div className="progress-bar">
                          <div className="progress-fill" style={{ width: `${result.probability * 100}%` }} />
                        </div>
                        <span className="detail-value">{(result.probability * 100).toFixed(1)}%</span>
                      </div>
                      {result.explanation?.values && (
                        <div className="probabilities shap-explanation">
                          <div className="shap-title">Đặc trưng ảnh hưởng mạnh nhất</div>
                          <div className="shap-values-list">
                            {Object.entries(result.explanation.values).map(([feature, value]) => (
                              <div className="prob-item shap-item" key={feature}>
                                <span className="shap-feature">{feature}</span>
                                <span className={value > 0 ? "shap-pos" : "shap-neg"}>
                                  {value > 0 ? "+" : ""}
                                  {value.toFixed(4)}
                                </span>
                              </div>
                            ))}
                          </div>
                          {result.explanation.text && (
                            <div className="shap-desc-list">
                              {result.explanation.text.map((description, index) => (
                                <div className="shap-desc" key={`${description}-${index}`}>
                                  {description}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                      <div className="result-actions">
                        {result.history_id ? (
                          <button
                            type="button"
                            className="secondary-btn"
                            onClick={() => void downloadPdf(result.history_id as string)}
                          >
                            Tải PDF
                          </button>
                        ) : (
                          <span className="helper-text">Kết quả này chưa được lưu vào lịch sử.</span>
                        )}
                      </div>
                    </div>
                  )}

                  <button type="submit" disabled={loading || !isAuthenticated} className="submit-btn">
                    {loading ? "Đang phân tích..." : "Phân tích"}
                  </button>
                </form>
              )}

              {mode === "image" && (
                <form onSubmit={handleImageSubmit} className="form">
              <div className="image-upload-section">
                <div className="upload-area">
                  <label className="upload-label">
                    {!imagePreview ? (
                      <div className="upload-placeholder">
                        <span className="upload-icon">Scan</span>
                        <p className="upload-text">
                          Chọn ảnh y khoa để phân tích
                          <br />
                          <small>Mammography, ultrasound hoặc histopathology</small>
                        </p>
                      </div>
                    ) : (
                      <div className="image-preview-container">
                        <img src={imagePreview} alt="Preview" className="image-preview" />
                        <button
                          type="button"
                          className="remove-image-btn"
                          onClick={() => {
                            setImageFile(null);
                            setImagePreview(null);
                            setImageResult(null);
                          }}
                        >
                          Xóa ảnh
                        </button>
                      </div>
                    )}
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      style={{ display: "none" }}
                    />
                  </label>
                </div>

                {imageFile && (
                  <div className="image-info">
                    <p>{imageFile.name}</p>
                    <p>{(imageFile.size / 1024).toFixed(2)} KB</p>
                  </div>
                )}
              </div>

              {error && <div className="alert error">{error}</div>}

              {imageResult && (
                <div className={`result ${imageResult.prediction}`}>
                  <div className="result-header">
                    <span className="result-icon">{imageResult.prediction === "benign" ? "OK" : "!"}</span>
                    <div>
                      <div className="result-title">Kết quả chẩn đoán hình ảnh</div>
                      <div className={`result-value ${imageResult.prediction}`}>
                        {formatPrediction(imageResult.prediction)}
                      </div>
                      <div className="result-timestamp">{formatTimestamp(imageResult.created_at)}</div>
                      {imageResult.record_code && <div className="result-record-code">Mã hồ sơ: {imageResult.record_code}</div>}
                    </div>
                  </div>
                  <div className="result-detail">
                    <span className="detail-label">Độ tin cậy</span>
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: `${imageResult.confidence * 100}%` }} />
                    </div>
                    <span className="detail-value">{(imageResult.confidence * 100).toFixed(1)}%</span>
                  </div>
                  <div className="probabilities">
                    <div className="prob-item">
                      <span>Benign</span>
                      <span>{(imageResult.probabilities.benign * 100).toFixed(1)}%</span>
                    </div>
                    <div className="prob-item">
                      <span>Malignant</span>
                      <span>{(imageResult.probabilities.malignant * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                  <div className="result-actions">
                    {imageResult.history_id ? (
                      <button
                        type="button"
                        className="secondary-btn"
                        onClick={() => void downloadPdf(imageResult.history_id as string)}
                      >
                        Tải PDF
                      </button>
                    ) : (
                      <span className="helper-text">Kết quả này chưa được lưu vào lịch sử.</span>
                    )}
                  </div>
                </div>
              )}

              <button type="submit" disabled={loading || !imageFile || !isAuthenticated} className="submit-btn">
                {loading ? "Đang phân tích..." : "Phân tích ảnh"}
              </button>

                  <div className="footer">Model hình ảnh: EfficientNet-B0 cho chẩn đoán tổn thương vú.</div>
                </form>
              )}

              {mode === "biochemical" && (
                <footer className="footer">
                  Dữ liệu sinh hóa được chuẩn hóa trước khi đưa qua mô hình XGBoost.
                </footer>
              )}
            </>
          )}

          {isAdmin && (
            <div className="alert info">
              Chế độ admin chỉ dùng để quản lý tài khoản bác sĩ. Chức năng chẩn đoán và lịch sử chẩn đoán đã được tắt.
            </div>
          )}
        </section>

        <aside className="side-panel">
          <section className="card side-card auth-card">
            <div className="side-card-header">
              <h2>Tài khoản</h2>
            </div>

            {currentUser ? (
              <div className="account-summary">
                <div className="account-name">{currentUser.username}</div>
                <div className="account-meta">Tạo lúc {formatTimestamp(currentUser.created_at)}</div>
                <button type="button" className="secondary-btn" onClick={resetSession}>
                  Đăng xuất
                </button>
              </div>
            ) : (
              <form onSubmit={handleAuthSubmit} className="auth-form">
                <div className="input-wrapper">
                  <label className="input-label" htmlFor="username">
                    Tên đăng nhập
                  </label>
                  <input
                    id="username"
                    className="feature-input"
                    value={credentials.username}
                    onChange={(event) => handleCredentialsChange("username", event.target.value)}
                    placeholder="doctor01"
                  />
                </div>
                <div className="input-wrapper">
                  <label className="input-label" htmlFor="password">
                    Mật khẩu
                  </label>
                  <input
                    id="password"
                    type="password"
                    className="feature-input"
                    value={credentials.password}
                    onChange={(event) => handleCredentialsChange("password", event.target.value)}
                    placeholder="••••••••"
                  />
                </div>
                {authError && <div className="alert error compact">{authError}</div>}
                <button type="submit" className="submit-btn auth-submit" disabled={authLoading}>
                  {authLoading ? "Đang xử lý..." : "Đăng nhập"}
                </button>
              </form>
            )}
          </section>

          {isAdmin && (
            <section className="card side-card admin-create-card">
              <div className="side-card-header">
                <h2>Tạo tài khoản bác sĩ</h2>
              </div>

              <form className="admin-create-form" onSubmit={handleCreateDoctorAccount}>
                <div className="input-wrapper">
                  <label className="input-label" htmlFor="doctor-username">
                    Tên đăng nhập bác sĩ
                  </label>
                  <input
                    id="doctor-username"
                    className="feature-input"
                    value={doctorCredentials.username}
                    onChange={(event) => setDoctorCredentials((prev) => ({ ...prev, username: event.target.value }))}
                    placeholder="doctor01"
                  />
                </div>
                <div className="input-wrapper">
                  <label className="input-label" htmlFor="doctor-password">
                    Mật khẩu tạm thời
                  </label>
                  <input
                    id="doctor-password"
                    type="password"
                    className="feature-input"
                    value={doctorCredentials.password}
                    onChange={(event) => setDoctorCredentials((prev) => ({ ...prev, password: event.target.value }))}
                    placeholder="Tối thiểu 6 ký tự"
                  />
                </div>
                <button type="submit" className="secondary-btn" disabled={createDoctorLoading}>
                  {createDoctorLoading ? "Đang tạo..." : "Tạo tài khoản bác sĩ"}
                </button>
              </form>

              {adminError && <div className="alert error compact">{adminError}</div>}
              {adminSuccess && <div className="alert info compact">{adminSuccess}</div>}
            </section>
          )}

          {!isAdmin && (
          <section className="card side-card history-card">
            <div className="side-card-header">
              <h2>Lịch sử chẩn đoán</h2>
              {isAuthenticated && (
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={() => token && void loadHistory(token)}
                >
                  Làm mới
                </button>
              )}
            </div>

            {!isAuthenticated && <p className="empty-state">Đăng nhập để xem lịch sử và tải lại PDF.</p>}

            {isAuthenticated && historyLoading && <p className="empty-state">Đang tải lịch sử...</p>}
            {historyError && <div className="alert error compact">{historyError}</div>}

            {isAuthenticated && (
              <div className="history-search-row">
                <input
                  className="feature-input"
                  placeholder="Nhập mã hồ sơ, ví dụ: HS-20260316-101530-A1B2"
                  value={historySearchCode}
                  onChange={(event) => setHistorySearchCode(event.target.value.toUpperCase())}
                />
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={() => void handleSearchHistoryByCode()}
                  disabled={historyLoading}
                >
                  Tìm mã
                </button>
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={() => {
                    setHistorySearchCode("");
                    setHistorySearchResult(null);
                    setHistorySearchMessage(null);
                    setHistoryFilterActive(false);
                  }}
                >
                  Xóa lọc
                </button>
              </div>
            )}

            {historySearchMessage && <p className="history-meta">{historySearchMessage}</p>}

            {isAuthenticated && !historyLoading && historyRecords.length === 0 && (
              <p className="empty-state">Chưa có bản ghi nào được lưu.</p>
            )}

            <div className="history-list">
              {displayedHistoryRecords.map((record) => (
                <article className="history-item" key={record.id}>
                  <div className="history-row">
                    <span className={`history-badge ${record.prediction}`}>{formatPrediction(record.prediction)}</span>
                    <span className="history-type">{formatDiagnosisType(record.diagnosis_type)}</span>
                  </div>
                  {record.record_code && <div className="history-code">Mã hồ sơ: {record.record_code}</div>}
                  <div className="history-meta">{formatTimestamp(record.created_at)}</div>
                  <div className="history-meta">Độ tin cậy {(record.confidence * 100).toFixed(1)}%</div>
                  {record.file_name && <div className="history-meta">Tệp {record.file_name}</div>}
                  <button
                    type="button"
                    className="secondary-btn small"
                    onClick={() => void downloadPdf(record.id)}
                  >
                    Tải PDF
                  </button>
                </article>
              ))}
            </div>
          </section>
          )}
        </aside>
      </main>

      {isAdmin && (
        <div className="admin-panel-wrap">
          <section className="card admin-panel">
            <div className="admin-header">
              <h2>Quản lý tài khoản bác sĩ</h2>
              <button
                type="button"
                className="ghost-btn"
                onClick={() => token && void loadAdminUsers(token)}
              >
                Làm mới
              </button>
            </div>

            {adminError && <div className="alert error compact">{adminError}</div>}
            {adminSuccess && <div className="alert info compact">{adminSuccess}</div>}
            {adminLoading && <p className="empty-state">Đang tải danh sách...</p>}

            {!adminLoading && (
              <div className="admin-table-wrap">
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>Tên đăng nhập</th>
                      <th>Role</th>
                      <th>Ngày tạo</th>
                      <th>Số chẩn đoán</th>
                      <th>Đổi mật khẩu</th>
                      <th>Hành động</th>
                    </tr>
                  </thead>
                  <tbody>
                    {adminUsers.map((user) => (
                      <tr key={user.id} className={user.role === "admin" ? "admin-row" : ""}>
                        <td className="admin-username">{user.username}</td>
                        <td>
                          {user.role === "admin" ? (
                            <span className="role-badge admin">Admin</span>
                          ) : (
                            <div className="role-select-wrap">
                              <span className="role-badge doctor">Bác sĩ</span>
                              <button
                                type="button"
                                className="ghost-btn tiny"
                                onClick={() => void handleChangeRole(user.id, "admin")}
                                title="Nâng lên Admin"
                              >
                                ↑ Admin
                              </button>
                            </div>
                          )}
                        </td>
                        <td className="admin-meta">{formatTimestamp(user.created_at)}</td>
                        <td className="admin-meta center">{user.history_count}</td>
                        <td>
                          {user.role !== "admin" && (
                            editingUser?.id === user.id ? (
                              <div className="pw-reset-row">
                                <input
                                  className="feature-input pw-input"
                                  type="password"
                                  placeholder="Mật khẩu mới"
                                  value={editingUser.newPassword}
                                  onChange={(e) => setEditingUser({ id: user.id, newPassword: e.target.value })}
                                />
                                <button
                                  type="button"
                                  className="secondary-btn small"
                                  onClick={() => void handleResetPassword(user.id)}
                                >
                                  Lưu
                                </button>
                                <button
                                  type="button"
                                  className="ghost-btn small"
                                  onClick={() => setEditingUser(null)}
                                >
                                  Hủy
                                </button>
                              </div>
                            ) : (
                              <button
                                type="button"
                                className="ghost-btn tiny"
                                onClick={() => setEditingUser({ id: user.id, newPassword: "" })}
                              >
                                Đổi mật khẩu
                              </button>
                            )
                          )}
                        </td>
                        <td>
                          {user.role !== "admin" && (
                            <button
                              type="button"
                              className="delete-btn"
                              onClick={() => void handleDeleteUser(user.id, user.username)}
                            >
                              Xóa
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
