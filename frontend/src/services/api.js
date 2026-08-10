import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  register: (payload) => api.post("/api/auth/register", payload),
  login: (payload) => api.post("/api/auth/login", payload),
  logout: () => api.post("/api/auth/logout"),
  me: () => api.get("/api/auth/me"),
};

export const imagesApi = {
  upload: (formData, onUploadProgress) =>
    api.post("/api/images/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress,
    }),
  status: (processingId) => api.get(`/api/images/${processingId}/status`),
  result: (processingId) => api.get(`/api/images/${processingId}/result`),
  vehicle: (processingId) => api.get(`/api/images/${processingId}/vehicle`),
  failure: (processingId) => api.get(`/api/images/${processingId}/failure`),
  retry: (processingId) => api.post(`/api/images/${processingId}/retry`),
  list: (params) => api.get("/api/images", { params }),
  remove: (processingId) => api.delete(`/api/images/${processingId}`),
};

export const analyticsApi = {
  summary: () => api.get("/api/analytics/summary"),
  stateWise: (params) => api.get("/api/analytics/state-wise", { params }),
  exportStateWiseCsv: async (params) => {
    const response = await api.get("/api/analytics/state-wise/export", {
      params, responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "state_analysis.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

export default api;
