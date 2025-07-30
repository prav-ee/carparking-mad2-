import { createRouter, createWebHistory } from 'vue-router';
import HomePage from '../components/HomePage.vue';
import AdminDashboard from '../components/AdminDashboard.vue';
// import OtherComponent from '../components/OtherComponent.vue';

const routes = [
  { path: '/', component: HomePage },
  { path: '/admin', component: AdminDashboard },
  // { path: '/other', component: OtherComponent },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router; 