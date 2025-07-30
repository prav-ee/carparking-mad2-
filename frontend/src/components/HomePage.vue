<template>
  <div class="home-dashboard">
    <!-- Header Bar (Dashboard Style) -->
    <div class="header-green header-bar">
      <div class="header-left">
        <span class="welcome-msg">Welcome to ParkEase</span>
      </div>
      <div class="header-center">
        <a href="#" class="nav-link active">Home</a>
        <span>|</span>
        <a href="#" class="nav-link" @click.prevent="showLogin = true">Sign In</a>
        <span>|</span>
        <a href="#" class="nav-link" @click.prevent="showSignup = true">Get Started</a>
      </div>
      <div class="header-right">
        <span class="brand-text">ParkEase</span>
      </div>
    </div>

    <!-- Modal Overlay: Hide main content when modal is open -->
    <div v-if="showLogin || showSignup" class="modal-backdrop">
      <div class="modal-content">
        <LoginForm v-if="showLogin" @close="showLogin = false" @login-success="handleLoginSuccess" />
        <SignupForm v-if="showSignup" @close="showSignup = false" />
      </div>
    </div>

    <!-- Main Content (hidden when modal is open) -->
    <div v-else>
      <div class="main-content home-main-content">
        <!-- Hero Section -->
        <section class="hero-section-dashboard text-center">
          <h1 class="hero-title mb-3">
            Smart Parking <span class="text-primary">Made Simple</span>
          </h1>
          <p class="hero-subtitle mb-4">
            Find, reserve, and manage parking spots effortlessly. Real-time availability, automated billing, and seamless check-in.
          </p>
          <div>
            <button class="btn btn-primary btn-lg me-2" @click="showLogin = true">Start Parking</button>
            <button class="btn btn-outline-primary btn-lg" @click="showSignup = true">Get Started</button>
          </div>
        </section>

        <!-- Features Section -->
        <section class="features-section py-5">
          <h2 class="section-title text-center mb-5">Why Choose ParkEase?</h2>
          <div class="row g-4 justify-content-center">
            <div class="col-lg-4 col-md-6">
              <div class="feature-card p-4 text-center h-100">
                <div class="feature-icon mb-3"><i class="bi bi-geo-alt-fill"></i></div>
                <h5 class="feature-title mb-2">Real-Time Availability</h5>
                <p class="feature-description mb-0">See available spots instantly and reserve your space before you arrive.</p>
              </div>
            </div>
            <div class="col-lg-4 col-md-6">
              <div class="feature-card p-4 text-center h-100">
                <div class="feature-icon mb-3"><i class="bi bi-shield-check"></i></div>
                <h5 class="feature-title mb-2">Secure & Reliable</h5>
                <p class="feature-description mb-0">Safe, monitored parking areas with 24/7 security and automated access.</p>
              </div>
            </div>
            <div class="col-lg-4 col-md-6">
              <div class="feature-card p-4 text-center h-100">
                <div class="feature-icon mb-3"><i class="bi bi-clock-history"></i></div>
                <h5 class="feature-title mb-2">Flexible Booking</h5>
                <p class="feature-description mb-0">Book hourly, daily, or monthly. Automatic billing and usage reports.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
      <!-- Footer -->
      <footer class="footer mt-5">
        <div class="container d-flex align-items-center justify-content-between">
          <div class="d-flex align-items-center">
            <i class="bi bi-car-front-fill logo-icon me-2"></i>
            <span class="brand-text">ParkEase</span>
          </div>
          <span class="footer-text">&copy; 2024 ParkEase. Smart parking made simple.</span>
        </div>
      </footer>
    </div>
  </div>
</template>

<script>
import LoginForm from './Login.vue';
import SignupForm from './SignupForm.vue';

export default {
  name: 'HomePage',
  components: { LoginForm, SignupForm },
  data() {
    return {
      showLogin: false,
      showSignup: false,
    };
  },
  methods: {
    handleLoginSuccess(user) {
      // Emit the login success event to parent App.vue
      this.$emit('login-success', user);
      this.showLogin = false;
    },
  },
};
</script>

<style scoped>
.home-dashboard {
  background: #f8fbff;
  min-height: 100vh;
}
.header-green.header-bar {
  background: #d6fbe3;
  padding: 14px 0 8px 0;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-radius: 16px 16px 0 0;
}
.header-left {
  flex: 1;
  text-align: left;
  margin-left: 2.5rem;
}
.header-center {
  flex: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 1.1rem;
}
.header-center .nav-link {
  color: #1a7f37;
  text-decoration: none;
  font-weight: 500;
}
.header-center .nav-link.active, .header-center .nav-link:focus {
  text-decoration: underline;
  color: #0d6efd;
}
.header-center span {
  color: #888;
}
.header-right {
  flex: 1;
  text-align: right;
  margin-right: 2.5rem;
}
.brand-text {
  font-size: 1.5rem;
  font-weight: bold;
  color: #222;
}
.welcome-msg {
  font-size: 1.2rem;
  color: #e53935;
  font-weight: bold;
}
.main-content.home-main-content {
  max-width: 1100px;
  margin: 2rem auto 0 auto;
  background: #fff;
  border-radius: 16px;
  padding: 2rem 2.5rem 2.5rem 2.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.hero-section-dashboard {
  min-height: 40vh;
  padding-top: 30px;
  background: linear-gradient(90deg, #f8fafc 60%, #e9f1ff 100%);
}
.hero-title {
  font-size: 2.8rem;
  font-weight: 800;
  color: #222;
}
.text-primary {
  color: #3b82f6 !important;
}
.hero-subtitle {
  font-size: 1.15rem;
  color: #4a5568;
  max-width: 600px;
  margin: 0 auto 1.5rem auto;
}
.features-section {
  background: #fff;
}
.section-title {
  font-size: 2rem;
  font-weight: 700;
  color: #222;
}
.feature-card {
  background: #f8fafc;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  border: 1px solid #e5e7eb;
  transition: box-shadow 0.2s;
}
.feature-card:hover {
  box-shadow: 0 6px 24px rgba(59,130,246,0.08);
}
.feature-icon {
  font-size: 2.2rem;
  color: #3b82f6;
}
.feature-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: #222;
}
.feature-description {
  color: #4a5568;
  font-size: 1rem;
}
.stats-section {
  background: #2563eb;
  color: #fff;
  border-radius: 12px;
  margin-top: 2rem;
}
.stat-item {
  padding: 1.5rem 0;
}
.stat-number {
  font-size: 2.2rem;
  font-weight: 800;
  margin-bottom: 0.3rem;
  color: #fff;
}
.stat-label {
  font-size: 1.05rem;
  color: #dbeafe;
  margin: 0;
  font-weight: 500;
}
.footer {
  background: #1a202c;
  color: white;
  padding: 1.2rem 0 1rem 0;
  border-radius: 0 0 16px 16px;
}
.footer-text {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.95rem;
}
/* Modal Styles */
.modal-backdrop {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}
.modal-content {
  background: #fff;
  padding: 2.5rem 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 32px rgba(0,0,0,0.12);
  min-width: 350px;
  max-width: 90vw;
}
</style> 