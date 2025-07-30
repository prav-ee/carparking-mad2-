import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api/admin', // Change this if your backend runs elsewhere
  withCredentials: true // Needed if your backend uses cookies/session auth
});

const authApi = axios.create({
  baseURL: 'http://localhost:5000/api/auth', // For authentication endpoints
  withCredentials: true // Needed if your backend uses cookies/session auth
});

const parkingApi = axios.create({
  baseURL: 'http://localhost:5000/api/parking', // For parking endpoints
  withCredentials: true // Needed if your backend uses cookies/session auth
});

// Add Axios interceptor to attach JWT token from localStorage
function setAuthInterceptor(instance) {
  instance.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  }, (error) => Promise.reject(error));
}

setAuthInterceptor(api);
setAuthInterceptor(authApi);
setAuthInterceptor(parkingApi);

export { api, authApi, parkingApi };
export default api; 