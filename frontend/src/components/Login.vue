<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-6 col-lg-4">
        <div class="card shadow">
          <div class="card-body p-4">
            <h3 class="text-center mb-4">Login to ParkEase</h3>
            
            <form @submit.prevent="login">
              <div class="mb-3">
                <label for="email" class="form-label">Email</label>
                <input 
                  type="email" 
                  class="form-control" 
                  id="email" 
                  v-model="email" 
                  required
                >
              </div>
              
              <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input 
                  type="password" 
                  class="form-control" 
                  id="password" 
                  v-model="password" 
                  required
                >
              </div>
              
              <div v-if="error" class="alert alert-danger" role="alert">
                {{ error }}
              </div>
              
              <button type="submit" class="btn btn-primary w-100" :disabled="loading">
                {{ loading ? 'Logging in...' : 'Login' }}
              </button>
            </form>
            
            <div class="text-center mt-3">
              
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { authApi } from '../api.js';

export default {
  name: 'LoginForm',
  data() {
    return {
      email: '',
      password: '',
      loading: false,
      error: ''
    };
  },
  methods: {
    async login() {
      this.loading = true;
      this.error = '';
      
      try {
        const response = await authApi.post('/login', {
          email: this.email,
          password: this.password
        });
        
        // Store user data
        localStorage.setItem('user', JSON.stringify(response.data.user));
        localStorage.setItem('access_token', response.data.access_token);
        this.$emit('login-success', response.data.user);
        // Reload the page to ensure cookies/session are set for admin requests
        window.location.reload();
        
      } catch (error) {
        this.error = error.response?.data?.error || 'Login failed';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script> 