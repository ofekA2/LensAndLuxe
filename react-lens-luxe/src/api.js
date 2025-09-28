import axios from "axios";

export const api = axios.create({
  baseURL: "http://localhost:5001",
  withCredentials: true, 
});

export const signup = (payload) => api.post("/api/signup", payload);
export const login  = (payload) => api.post("/api/login", payload);
export const logout = () => api.post("/api/logout");
export const checkAuth = () => api.get("/api/check-auth");
