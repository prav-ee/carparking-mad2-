<template>
  <div class="modal-outer">
    <div class="signup-modal">
      <button class="close-btn" @click="$emit('close')">&times;</button>
      <h2 class="modal-title">Join ParkEase</h2>
      <p class="modal-subtitle">Create your account to start parking smarter</p>
      <form @submit.prevent="onSubmit">
        <div class="form-group">
          <label for="fullname">Full Name *</label>
          <input type="text" id="fullname" v-model="fullname" placeholder="John Doe" required />
        </div>
        <div class="form-group">
          <label for="email">Email *</label>
          <input type="email" id="email" v-model="email" placeholder="your@email.com" required />
        </div>
        <div class="form-group">
          <label for="phone">Phone Number *</label>
          <input type="tel" id="phone" v-model="phone" placeholder="+1 (555) 123-4567" required />
        </div>
        <div class="form-group password-group">
          <label for="password">Password *</label>
          <div class="password-wrapper">
            <input :type="showPassword ? 'text' : 'password'" id="password" v-model="password" placeholder="Create a password" required />
            <span class="toggle-password" @click="showPassword = !showPassword">
              <i :class="showPassword ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
            </span>
          </div>
        </div>
        <div class="form-group password-group">
          <label for="confirmPassword">Confirm Password *</label>
          <div class="password-wrapper">
            <input :type="showConfirm ? 'text' : 'password'" id="confirmPassword" v-model="confirmPassword" placeholder="Confirm your password" required />
            <span class="toggle-password" @click="showConfirm = !showConfirm">
              <i :class="showConfirm ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
            </span>
          </div>
        </div>
        <div v-if="error" class="error-msg">{{ error }}</div>
        <button class="btn btn-primary w-100 mt-3" type="submit" :disabled="loading">
          <span v-if="loading">Creating Account...</span>
          <span v-else>Create Account</span>
        </button>
      </form>
      <p class="terms-text mt-3">By creating an account, you agree to our Terms of Service and Privacy Policy.</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SignupForm',
  data() {
    return {
      fullname: '',
      email: '',
      phone: '',
      password: '',
      confirmPassword: '',
      showPassword: false,
      showConfirm: false,
      loading: false,
      error: ''
    };
  },
  methods: {
    async onSubmit() {
      if (!this.fullname || !this.email || !this.phone || !this.password || !this.confirmPassword) return;
      if (this.password !== this.confirmPassword) {
        this.error = 'Passwords do not match!';
        return;
      }
      this.loading = true;
      this.error = '';
      try {
        const response = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ full_name: this.fullname, email: this.email, phone: this.phone, password: this.password })
        });
        const data = await response.json();
        if (!response.ok) {
          this.error = data.msg || 'Registration failed';
          this.loading = false;
          return;
        }
        // Store JWT and redirect
        localStorage.setItem('token', data.access_token);
        this.$router.push('/user-dashboard');
        this.$emit('close');
      } catch (err) {
        this.error = 'Network error';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.modal-outer {
  position: fixed;
  top: 0; left: 0; width: 100vw; height: 100vh;
  background: rgba(40, 60, 90, 0.18);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.signup-modal {
  background: #fff;
  border-radius: 1.2rem;
  box-shadow: 0 8px 40px rgba(40, 60, 90, 0.18);
  padding: 1.7rem 1.2rem 1.2rem 1.2rem;
  min-width: 300px;
  max-width: 350px;
  width: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  animation: popin 0.25s cubic-bezier(.4,2,.6,1) 1;
}
@keyframes popin {
  0% { transform: scale(0.95); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
.close-btn {
  position: absolute;
  top: 1.1rem;
  right: 1.1rem;
  background: none;
  border: none;
  font-size: 1.7rem;
  cursor: pointer;
  color: #a0aec0;
  transition: color 0.2s;
  z-index: 10;
}
.close-btn:hover {
  color: #2563eb;
}
.modal-title {
  font-size: 1.6rem;
  font-weight: 800;
  text-align: center;
  margin-bottom: 0.3rem;
  color: #22223b;
  letter-spacing: -1px;
}
.modal-subtitle {
  text-align: center;
  color: #6b7280;
  margin-bottom: 1.1rem;
  font-size: 1.01rem;
}
.form-group {
  margin-bottom: 1rem;
}
label {
  font-weight: 600;
  margin-bottom: 0.3rem;
  display: block;
  color: #22223b;
  font-size: 1.01rem;
}
input {
  width: 100%;
  padding: 0.65rem 0.9rem;
  border: 1.5px solid #d1d5db;
  border-radius: 10px;
  font-size: 1.01rem;
  outline: none;
  margin-top: 0.2rem;
  background: #f9fafb;
  transition: border 0.2s, box-shadow 0.2s;
  box-shadow: 0 1px 2px rgba(40,60,90,0.03);
}
input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 2px #2563eb22;
}
.password-group {
  position: relative;
}
.password-wrapper {
  display: flex;
  align-items: center;
  position: relative;
}
.toggle-password {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  color: #6b7280;
  font-size: 1.2rem;
  transition: color 0.2s;
}
.toggle-password:hover {
  color: #2563eb;
}
.btn-primary {
  background: linear-gradient(90deg, #2563eb 60%, #764ba2 100%);
  border: none;
  color: #fff;
  font-weight: 700;
  border-radius: 10px;
  padding: 0.85rem 0;
  font-size: 1.08rem;
  transition: background 0.2s, box-shadow 0.2s;
  box-shadow: 0 2px 8px rgba(40,60,90,0.08);
  margin-top: 0.3rem;
}
.btn-primary:hover {
  background: linear-gradient(90deg, #1d4ed8 60%, #764ba2 100%);
  box-shadow: 0 4px 16px rgba(40,60,90,0.13);
}
.terms-text {
  color: #6b7280;
  font-size: 0.93rem;
  text-align: center;
  margin-top: 1.1rem;
}
.error-msg {
  color: #e53e3e;
  background: #fff0f0;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  margin-bottom: 1rem;
  text-align: center;
  font-size: 1rem;
}
@media (max-width: 400px) {
  .signup-modal {
    min-width: 95vw;
    max-width: 98vw;
    padding: 1rem 0.3rem 1rem 0.3rem;
  }
  .modal-title {
    font-size: 1.2rem;
  }
}
</style> 