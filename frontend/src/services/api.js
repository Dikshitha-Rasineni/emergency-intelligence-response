import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

export const getHealth = async () => {
  const response = await api.get("/api/health");
  return response.data;
};

export const checkBackendHealth = getHealth;

export const createIncident = async (payload) => {
  const response = await api.post("/api/incidents", payload);
  return response.data;
};

export const getIncidents = async () => {
  const response = await api.get("/api/incidents");
  return response.data;
};

export const listIncidents = getIncidents;

export const getIncident = async (incidentId) => {
  const response = await api.get(`/api/incidents/${incidentId}`);
  return response.data;
};

export const getNearbyResources = async (incidentId, radiusKm = 25) => {
  const response = await api.get("/api/resources/nearby", {
    params: {
      incident_id: incidentId,
      radius_km: radiusKm,
    },
  });

  return response.data;
};

/* =========================================================
   GENAI — 3.1 Emergency Understanding
   ========================================================= */

export const extractEmergencyInformation = async (incidentId) => {
  const response = await api.post("/api/ai/extract", {
    incident_id: incidentId,
  });

  return response.data;
};

/* =========================================================
   GENAI — 3.3 Missing Information
   ========================================================= */

export const detectMissingInformation = async (incidentId) => {
  const response = await api.post("/api/ai/missing-info", {
    incident_id: incidentId,
  });

  return response.data;
};

/* =========================================================
   GENAI — 3.4 Safety Precautions
   ========================================================= */

export const getSafetyPrecautions = async (incidentId) => {
  const response = await api.post("/api/ai/safety", {
    incident_id: incidentId,
  });

  return response.data;
};

/* =========================================================
   GENAI — 3.5 Reporter Guidance
   ========================================================= */

export const getReporterGuidance = async (incidentId) => {
  const response = await api.post("/api/ai/reporter-guidance", {
    incident_id: incidentId,
  });

  return response.data;
};

/* =========================================================
   GENAI — 3.6 Response Generation
   ========================================================= */

export const generateResponseRecommendation = async (incidentId) => {
  const response = await api.post("/api/ai/response", {
    incident_id: incidentId,
  });

  return response.data;
};

/* =========================================================
   GENAI — 3.7 Incident Report Generation
   ========================================================= */

export const generateIncidentReport = async (incidentId) => {
  const response = await api.post("/api/ai/incident-report", {
    incident_id: incidentId,
  });

  return response.data;
};

export default api;