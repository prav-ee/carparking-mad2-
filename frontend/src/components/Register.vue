<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-6 col-lg-4">
        <div class="card shadow">
          <div class="card-body p-4">
            <h3 class="text-center mb-4">Register for ParkEase</h3>
            <form @submit.prevent="register">
              <div class="mb-3">
                <label for="fullName" class="form-label">Full Name</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="fullName" 
                  v-model="fullName" 
                  required
                >
              </div>
              <div class="mb-3">
                <label for="regEmail" class="form-label">Email</label>
                <input 
                  type="email" 
                  class="form-control" 
                  id="regEmail" 
                  v-model="email" 
                  required
                >
              </div>
              <div class="mb-3">
                <label for="phone" class="form-label">Phone (Optional)</label>
                <input 
                  type="tel" 
                  class="form-control" 
                  id="phone" 
                  v-model="phone"
                >
              </div>
              <div class="mb-3">
                <label for="regPassword" class="form-label">Password</label>
                <input 
                  type="password" 
                  class="form-control" 
                  id="regPassword" 
                  v-model="password" 
                  required
                >
              </div>
              <div v-if="error" class="alert alert-danger" role="alert">
                {{ error }}
              </div>
              <button type="submit" class="btn btn-primary w-100" :disabled="loading">
                {{ loading ? 'Registering...' : 'Register' }}
              </button>
            </form>
            <div class="text-center mt-3">
              <p>Already have an account? <a href="#" @click="$emit('show-login')">Login here</a></p>
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
  name: 'RegisterForm',
  data() {
    return {
      fullName: '',
      email: '',
      phone: '',
      password: '',
      loading: false,
      error: ''
    };
  },
  methods: {
    async register() {
      this.loading = true;
      this.error = '';
      try {
        await authApi.post('/register', {
          full_name: this.fullName,
          email: this.email,
          phone: this.phone,
          password: this.password
        });
        // Auto-login after successful registration
        const loginResponse = await authApi.post('/login', {
          email: this.email,
          password: this.password
        });
        localStorage.setItem('user', JSON.stringify(loginResponse.data.user));
        localStorage.setItem('access_token', loginResponse.data.access_token);
        this.$emit('register-success', loginResponse.data.user);
      } catch (error) {
        this.error = error.response?.data?.error || 'Registration failed';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script> 