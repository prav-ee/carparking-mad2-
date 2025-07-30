<template>
  <div id="app">
    <!-- Show HomePage if not logged in -->
    <HomePage v-if="!currentUser" @login-click="showLogin = true" @admin-click="showLogin = true" @login-success="handleLoginSuccess" />
    
    <!-- Show Login Modal -->
    <div v-if="showLogin && !currentUser" class="modal fade show" style="display: block;">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Login to ParkEase</h5>
            <button type="button" class="btn-close" @click="showLogin = false"></button>
          </div>
          <div class="modal-body">
            <LoginForm @login-success="handleLoginSuccess" @show-register="showRegister = true" />
          </div>
        </div>
      </div>
    </div>
    
    <!-- Show Register Modal -->
    <div v-if="showRegister && !currentUser" class="modal fade show" style="display: block;">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Register for ParkEase</h5>
            <button type="button" class="btn-close" @click="showRegister = false"></button>
          </div>
          <div class="modal-body">
            <RegisterForm @register-success="handleRegisterSuccess" @show-login="showLogin = true" />
          </div>
        </div>
      </div>
    </div>
    
    <!-- Show Admin Dashboard if admin user -->
    <AdminDashboard v-if="currentUser && currentUser.role === 'admin'" @logout="handleLogout" />
    
    <!-- Show User Dashboard if regular user -->
    <UserDashboard v-if="currentUser && currentUser.role === 'user'" @logout="handleLogout" />
  </div>
</template>

<script>
import HomePage from './components/HomePage.vue';
import LoginForm from './components/Login.vue';
import RegisterForm from './components/Register.vue';
import AdminDashboard from './components/AdminDashboard.vue';
import UserDashboard from './components/UserDashboard.vue';

export default {
  name: 'App',
  components: {
    HomePage,
    LoginForm,
    RegisterForm,
    AdminDashboard,
    UserDashboard
  },
  data() {
    return {
      currentUser: null,
      showLogin: false,
      showRegister: false
    };
  },
  created() {
    const user = localStorage.getItem('user');
    if (user) {
      this.currentUser = JSON.parse(user);
    }
  },
  methods: {
    handleLoginSuccess(user) {
      this.currentUser = user;
      this.showLogin = false;
      this.showRegister = false;
    },
    
    handleRegisterSuccess(user) {
      this.currentUser = user;
      this.showLogin = false;
      this.showRegister = false;
    },
    
    handleLogout() {
      this.currentUser = null;
      this.showLogin = false;
      this.showRegister = false;
    }
  }
};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}

.modal {
  background-color: rgba(0, 0, 0, 0.5);
}
</style>
