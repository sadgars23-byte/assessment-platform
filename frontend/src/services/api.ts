import axios from 'axios';

let rawUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').trim();

// Strip trailing slashes
rawUrl = rawUrl.replace(/\/+$/, '');

// If the user provided /api at the end of VITE_API_URL, strip it to prevent path conflicts
if (rawUrl.endsWith('/api')) {
  rawUrl = rawUrl.slice(0, -4);
}

const BASE_URL = rawUrl;

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 120s timeout for cold starts and heavy PDF processing
});

export const analyzeAssessment = async (
  studentName: string, 
  registrationNumber: string, 
  file: File
) => {
  const formData = new FormData();
  formData.append('student_name', studentName);
  formData.append('registration_number', registrationNumber);
  formData.append('assessment_pdf', file);

  const response = await apiClient.post('/api/assessment/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getStatus = async (assessmentId: string) => {
  const response = await apiClient.get(`/api/assessment/${assessmentId}/status`);
  return response.data;
};

export const generateAnswers = async (assessmentId: string) => {
  const response = await apiClient.post(`/api/assessment/${assessmentId}/generate`);
  return response.data;
};

export const getPreview = async (assessmentId: string) => {
  const response = await apiClient.get(`/api/assessment/${assessmentId}/preview`);
  return response.data;
};

export const getDownloadUrl = (assessmentId: string) => {
  return `${BASE_URL}/api/assessment/${assessmentId}/download`;
};
