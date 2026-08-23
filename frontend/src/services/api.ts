import axios from 'axios';

let rawUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
rawUrl = rawUrl.replace(/\/+$/, '');
if (!rawUrl.endsWith('/api')) {
  rawUrl = `${rawUrl}/api`;
}

const API_URL = rawUrl;

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 60000, // 60s timeout for cold starts on Render free tier
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

  const response = await apiClient.post('/assessment/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getStatus = async (assessmentId: string) => {
  const response = await apiClient.get(`/assessment/${assessmentId}/status`);
  return response.data;
};

export const generateAnswers = async (assessmentId: string) => {
  const response = await apiClient.post(`/assessment/${assessmentId}/generate`);
  return response.data;
};

export const getPreview = async (assessmentId: string) => {
  const response = await apiClient.get(`/assessment/${assessmentId}/preview`);
  return response.data;
};

export const getDownloadUrl = (assessmentId: string) => {
  return `${API_URL}/assessment/${assessmentId}/download`;
};
