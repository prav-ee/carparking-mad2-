<template>
  <div class="user-dashboard-history">
    <!-- Export CSV Button and Alert -->
    <div style="margin-bottom: 1em;">
      <button class="user-btn" @click="startExportCsv">Export Parking History as CSV</button>
      <span v-if="exportCsvStatus" style="margin-left: 1em; color: green;">{{ exportCsvStatus }}</span>
      <span v-if="exportCsvError" style="margin-left: 1em; color: red;">{{ exportCsvError }}</span>
      <a v-if="exportCsvDownloadUrl" :href="exportCsvDownloadUrl" download style="margin-left: 1em;">
        <button class="user-btn">Download CSV</button>
      </a>
    </div>
    <!-- Header Bar -->
    <div class="header-green user-header-bar">
      <div class="header-left">
        <span class="welcome-msg">Welcome{{ currentUser && currentUser.full_name ? `, ${currentUser.full_name}` : '' }}</span>
      </div>
      <div class="header-center">
        <a href="#" class="nav-link" :class="{active: activeTab === 'home'}" @click.prevent="activeTab = 'home'">Home</a>
        <span>|</span>
        <a href="#" class="nav-link" :class="{active: activeTab === 'summary'}" @click.prevent="activeTab = 'summary'">Summary</a>
        <span>|</span>
        <a href="#" class="nav-link" @click.prevent="logout">Logout</a>
      </div>
      <div class="header-right">
        <a href="#" class="edit-profile" @click.prevent="showEditProfile = true">Edit Profile</a>
      </div>
    </div>

    <div v-if="activeTab === 'home'" class="main-content user-main-content">
      <!-- Recent Parking History -->
      <div class="user-section-title">
        Recent parking history
        <button @click="fetchHistory" class="user-btn" style="margin-left: 10px; font-size: 12px;">🔄 Refresh</button>
      </div>
      <div class="user-card user-history-card">
        <table class="table user-history-table mb-0">
          <thead>
            <tr>
              <th class="user-th">ID</th>
              <th class="user-th">location</th>
              <th class="user-th">vehicle_no</th>
              <th class="user-th">timestamp</th>
              <th class="user-th">Total Cost</th>
              <th class="user-th">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="h in history.slice(0, 5)" :key="h.id">
              <td class="user-td">{{ h.id }}</td>
              <td class="user-td">{{ h.location }}</td>
              <td class="user-td">{{ h.vehicle_no }}</td>
              <td class="user-td">
                <div v-if="h.status === 'out'">
                  <div><b>Parking time :</b> {{ formatDate(h.parking_time || h.timestamp) }}</div>
                  <div><b>Releasing time :</b> {{ formatDate(h.released_time) }}</div>
                </div>
                <div v-else>
                  {{ formatDate(h.parking_time || h.timestamp) }}
                </div>
              </td>
              <td class="user-td">
                <span v-if="h.status === 'out' && h.total_cost">₹{{ h.total_cost }}</span>
                <span v-else>---</span>
              </td>
              <td class="user-td">
                <button v-if="h.status === 'active'" class="user-btn release" @click="openReleaseModal(h)">Release</button>
                <button v-else class="user-btn parked" disabled>Parked Out</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="lastHistoryFetch" style="text-align: right; font-size: 12px; color: #666; margin-top: 10px;">
          Last updated: {{ formatDate(lastHistoryFetch) }}
        </div>
        <div v-if="history.length > 5" class="history-scroll-bar">
          <div class="history-scroll-list">
            <div class="history-scroll-card" v-for="h in history.slice(5)" :key="h.id">
              <div><b>ID:</b> {{ h.id }}</div>
              <div><b>Location:</b> {{ h.location }}</div>
              <div><b>Vehicle:</b> {{ h.vehicle_no }}</div>
              <div v-if="h.status === 'out'">
                <div><b>Parking time :</b> {{ formatDate(h.parking_time || h.timestamp) }}</div>
                <div><b>Releasing time :</b> {{ formatDate(h.released_time) }}</div>
                <div><b>Total Cost:</b> <span v-if="h.total_cost">₹{{ h.total_cost }}</span><span v-else>---</span></div>
              </div>
              <div v-else>
                <b>Time:</b> {{ formatDate(h.parking_time || h.timestamp) }}
              </div>
              <div>
                <button v-if="h.status === 'active'" class="user-btn release" @click="openReleaseModal(h)">Release</button>
                <button v-else class="user-btn parked" disabled>Parked Out</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Search Section -->
      <div class="user-search-row">
        <span class="user-search-label">Search parking</span>
        <input v-model="lotSearch" class="user-search-input" placeholder="Dadar Road" />
      </div>

      <!-- Parking Lots Table -->
      <div class="user-section-title">Parking Lots at {{ lotSearch || '...' }}</div>
      <div class="user-card user-lots-card">
        <table class="table user-lots-table mb-0">
          <thead>
            <tr>
              <th class="user-th">ID</th>
              <th class="user-th">Address</th>
              <th class="user-th">Price/Hour</th>
              <th class="user-th">Availability</th>
              <th class="user-th">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lot in filteredLots" :key="lot.id">
              <td class="user-td">{{ lot.id }}</td>
              <td class="user-td">{{ lot.location }}, {{ lot.pincode }}</td>
              <td class="user-td">₹{{ lot.price_per_hour }}</td>
              <td class="user-td">{{ lot.available_spots }}</td>
              <td class="user-td">
                <button class="user-btn book" @click="bookLot(lot)" :disabled="lot.available_spots === 0">Book</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- Booking Modal -->
      <div v-if="showBookModal" class="booking-modal-backdrop">
        <div class="booking-modal-content">
          <div class="booking-modal-header">Book the parking spot</div>
          <form @submit.prevent="reserveSpot" class="booking-modal-form">
            <div class="booking-modal-row">
              <label class="booking-modal-label">Spot_ID :</label>
              <input type="text" class="booking-modal-input" v-model="bookingData.spot_id" readonly />
            </div>
            <div class="booking-modal-row">
              <label class="booking-modal-label">Lot_ID :</label>
              <input type="text" class="booking-modal-input" v-model="bookingData.lot_id" readonly />
            </div>
            <div class="booking-modal-row">
              <label class="booking-modal-label">User ID :</label>
              <input type="text" class="booking-modal-input" v-model="bookingData.user_id" readonly />
            </div>
            <div class="booking-modal-row">
              <label class="booking-modal-label">Vehicle Number :</label>
              <input type="text" class="booking-modal-input" v-model="bookingData.vehicle_no" required placeholder="Enter vehicle number" />
            </div>
            <div class="booking-modal-actions">
              <button type="submit" class="booking-modal-btn reserve">Reserve</button>
              <button type="button" class="booking-modal-btn cancel" @click="showBookModal = false">Cancel</button>
            </div>
          </form>
        </div>
      </div>
      <!-- Release Modal -->
      <div v-if="showReleaseModal" class="booking-modal-backdrop">
        <div class="booking-modal-content">
          <div class="booking-modal-header">Release the parking spot</div>
          <form @submit.prevent="confirmRelease" class="booking-modal-form">
            <div class="booking-modal-row">
              <label class="booking-modal-label">Spot_ID :</label>
              <input type="text" class="booking-modal-input" v-model="releaseData.spot_id" readonly />
            </div>
            <div class="booking-modal-row">
              <label class="booking-modal-label">Vehicle Number :</label>
              <input type="text" class="booking-modal-input" v-model="releaseData.vehicle_no" readonly />
            </div>
            <div class="booking-modal-row">
              <label class="booking-modal-label">Parking time :</label>
              <input type="text" class="booking-modal-input" v-model="releaseData.parking_time" readonly />
            </div>
            <div class="booking-modal-row">
              <label class="booking-modal-label">Releasing time :</label>
              <input type="text" class="booking-modal-input" v-model="releaseData.releasing_time" readonly />
            </div>
            <div class="booking-modal-row">
              <label class="booking-modal-label">Total cost :</label>
              <input type="text" class="booking-modal-input" :value="formatTotalCost(releaseData.total_cost)" readonly />
            </div>
            <div class="booking-modal-actions">
              <button type="submit" class="booking-modal-btn reserve">Release</button>
              <button type="button" class="booking-modal-btn cancel" @click="showReleaseModal = false">Cancel</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'summary'" class="main-content user-main-content">
      <div class="user-section-title">Summary</div>
      <div class="summary-charts-row">
        <div class="summary-chart-block">
          <div class="summary-chart-label">Parking Duration Distribution</div>
          <BarChart v-if="pieData" :data="pieData" :options="barOptions" />
        </div>
        <div class="summary-chart-block">
          <div class="summary-chart-label">Number of Parkings per Lot</div>
          <BarChart v-if="barData" :data="barData" :options="barOptions" />
        </div>
      </div>
    </div>
    <!-- Edit Profile Modal -->
    <div v-if="showEditProfile" class="booking-modal-backdrop">
      <div class="booking-modal-content">
        <div class="booking-modal-header">Edit Profile</div>
        <form v-if="editProfileMode" @submit.prevent="saveProfile" class="booking-modal-form">
          <div class="booking-modal-row">
            <label class="booking-modal-label">Full Name :</label>
            <input type="text" class="booking-modal-input" v-model="editProfileData.full_name" required />
          </div>
          <div class="booking-modal-row">
            <label class="booking-modal-label">Phone :</label>
            <input type="text" class="booking-modal-input" v-model="editProfileData.phone" />
          </div>
          <div class="booking-modal-actions">
            <button type="submit" class="booking-modal-btn reserve">Save</button>
            <button type="button" class="booking-modal-btn cancel" @click="cancelEditProfile">Cancel</button>
          </div>
        </form>
        <div v-else class="booking-modal-form">
          <div class="booking-modal-row">
            <label class="booking-modal-label">Full Name :</label>
            <span class="booking-modal-value">{{ currentUser.full_name }}</span>
          </div>
          <div class="booking-modal-row">
            <label class="booking-modal-label">Phone :</label>
            <span class="booking-modal-value">{{ currentUser.phone || '-' }}</span>
          </div>
          <div class="booking-modal-actions">
            <button type="button" class="booking-modal-btn reserve" @click="editProfileMode = true">Edit</button>
            <button type="button" class="booking-modal-btn cancel" @click="showEditProfile = false">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { parkingApi } from '../api.js';
import BarChart from './BarChart.vue';

export default {
  name: 'UserDashboard',
  components: { BarChart },
  data() {
    return {
      activeTab: 'home',
      currentUser: JSON.parse(localStorage.getItem('user')),
      history: [],
      lots: [],
      lotSearch: '',
      showBookModal: false,
      bookingData: {
        spot_id: '',
        lot_id: '',
        user_id: '',
        vehicle_no: ''
      },
      userVehicles: [],
      showReleaseModal: false,
      releaseData: {
        spot_id: '',
        vehicle_no: '',
        parking_time: '',
        releasing_time: '',
        total_cost: ''
      },
      pieData: null,
      barData: null,
      pieOptions: { responsive: true, plugins: { legend: { position: 'bottom' } } },
      barOptions: { responsive: true, plugins: { legend: { display: false } } },
      releaseEntry: null,
      showEditProfile: false,
      editProfileData: {
        full_name: '',
        phone: ''
      },
      editProfileMode: false,
      exportCsvTaskId: null,
      exportCsvStatus: null,
      exportCsvDownloadUrl: null,
      exportCsvError: null,
      exportCsvPollingInterval: null,
      lastHistoryFetch: null,
    };
  },
  computed: {
    filteredLots() {
      const q = this.lotSearch.toLowerCase();
      return this.lots.filter(lot =>
        (lot.location && lot.location.toLowerCase().includes(q)) ||
        (lot.pincode && lot.pincode.toLowerCase().includes(q))
      );
    }
  },
  async mounted() {
    await this.fetchHistory();
    await this.fetchLots();
    // Pre-fill edit profile data
    if (this.currentUser) {
      this.editProfileData.full_name = this.currentUser.full_name;
      this.editProfileData.phone = this.currentUser.phone || '';
    }
    this.prepareSummaryCharts();
  },
  methods: {
    async fetchHistory() {
      try {
        // Force refresh cache before fetching
        await parkingApi.post('/history/refresh');
        
        const res = await parkingApi.get('/history');
        this.history = res.data.history;
        
        // Add a timestamp to track when data was last fetched
        this.lastHistoryFetch = new Date().toISOString();
      } catch (error) {
        console.error('Error fetching history:', error);
      }
    },
    async fetchLots() {
      try {
        const res = await parkingApi.get('/lots');
        this.lots = res.data.lots;
      } catch (error) {
        console.error('Error fetching lots:', error);
      }
    },
    async bookLot(lot) {
      try {
        // 1. Fetch available spots for this lot
        const spotsRes = await parkingApi.get(`/lots/${lot.id}/spots`);
        const availableSpots = spotsRes.data.spots.filter(s => !s.is_occupied);
        if (availableSpots.length === 0) {
          alert('No available spots in this lot!');
          return;
        }
        const spot = availableSpots[0];

        // 3. Show modal with pre-filled data
        this.bookingData = {
          spot_id: spot.id,
          lot_id: lot.id,
          user_id: this.currentUser.id,
          vehicle_no: '' // Always reset to empty string
        };
        this.showBookModal = true;
      } catch (error) {
        alert('Booking failed. Please try again.');
        console.error('Booking error:', error);
      }
    },
    async reserveSpot() {
      if (!this.bookingData.vehicle_no || !this.bookingData.vehicle_no.trim()) {
        alert('Please enter a vehicle number.');
        return;
      }
      try {
        await parkingApi.post('/park', {
          vehicle_no: this.bookingData.vehicle_no,
          spot_id: this.bookingData.spot_id
        }, { withCredentials: true });
        alert('Booking successful!');
        this.showBookModal = false;
        await this.fetchLots();
        await this.fetchHistory();
      } catch (error) {
        alert('Booking failed. Please try again.');
        console.error('Booking error:', error);
      }
    },
    formatDate(date) {
      // If the date is already in Indian format (from backend), return as is
      if (typeof date === 'string' && (date.includes('AM') || date.includes('PM'))) {
        return date;
      }
      // If no date provided
      if (!date) return 'Not available';
      
      // If it's a Date object or ISO string, format it to Indian timezone
      const d = new Date(date);
      if (isNaN(d.getTime())) return 'Invalid date';
      
      // Format to Indian timezone using a more reliable method
      const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
        timeZone: 'Asia/Kolkata'
      };
      
      return d.toLocaleString('en-US', options).replace(',', '');
    },
    getCurrentIndianTime() {
      const now = new Date();
      const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
        timeZone: 'Asia/Kolkata'
      };
      return now.toLocaleString('en-US', options).replace(',', '');
    },
    openReleaseModal(entry) {
      const calculatedCost = this.calculateCost(entry);
      this.releaseData = {
        spot_id: entry.spot_id || entry.id,
        vehicle_no: entry.vehicle_no,
        parking_time: this.formatDate(entry.parking_time || entry.timestamp),
        releasing_time: this.getCurrentIndianTime(),
        total_cost: calculatedCost
      };
      this.releaseEntry = entry;
      this.showReleaseModal = true;
    },
    async confirmRelease() {
      try {
        // Find vehicle_id if not present
        let vehicleId = this.releaseEntry.vehicle_id;
        if (!vehicleId) {
                  // Try to get from backend by vehicle_no
        const vehicleRes = await parkingApi.get('/vehicles');
          const vehicle = vehicleRes.data.vehicles.find(v => v.license_plate === this.releaseEntry.vehicle_no);
          if (!vehicle) {
            alert('Vehicle not found');
            return;
          }
          vehicleId = vehicle.id;
        }
        await parkingApi.post('/unpark', { vehicle_id: vehicleId });
        this.showReleaseModal = false;
        await this.fetchHistory();
      } catch (error) {
        alert('Failed to release vehicle.');
      }
    },
    calculateCost(entry) {
      const inTime = new Date(entry.parking_time || entry.timestamp);
      const outTime = new Date();
      const hours = Math.ceil((outTime - inTime) / (1000 * 60 * 60));
      
      // Get price_per_hour from the entry (now available from backend)
      const pricePerHour = entry.price_per_hour || 100; // Default to 100 if not available
      
      const totalCost = Math.round(hours * pricePerHour);
      return totalCost;
    },
    formatTotalCost(cost) {
      if (cost && cost > 0) {
        return `₹${cost}`;
      }
      return '---';
    },
    prepareSummaryCharts() {
      // Pie chart: parking duration distribution
      const short = this.history.filter(h => this.getDurationHours(h) < 1).length;
      const medium = this.history.filter(h => this.getDurationHours(h) >= 1 && this.getDurationHours(h) <= 3).length;
      const long = this.history.filter(h => this.getDurationHours(h) > 3).length;
      this.pieData = {
        labels: ['< 1 hour', '1-3 hours', '> 3 hours'],
        datasets: [{
          data: [short, medium, long],
          backgroundColor: ['#1976d2', '#90caf9', '#388e3c']
        }]
      };
      // Bar chart: number of parkings per lot
      const lotCounts = {};
      this.history.forEach(h => {
        const lot = h.location || 'Unknown';
        lotCounts[lot] = (lotCounts[lot] || 0) + 1;
      });
      this.barData = {
        labels: Object.keys(lotCounts),
        datasets: [{
          label: 'Number of Parkings',
          data: Object.values(lotCounts),
          backgroundColor: '#1976d2'
        }]
      };
    },
    getDurationHours(h) {
      // Use released_time for completed sessions, otherwise use now
      const start = new Date(h.parking_time || h.timestamp);
      const end = h.released_time ? new Date(h.released_time) : new Date();
      return (end - start) / (1000 * 60 * 60);
    },
    logout() {
      localStorage.removeItem('user');
      this.$emit('logout');
    },
    async saveProfile() {
      try {
        await parkingApi.put('/me', {
          full_name: this.editProfileData.full_name,
          phone: this.editProfileData.phone
        });
        // Update localStorage and UI
        this.currentUser.full_name = this.editProfileData.full_name;
        this.currentUser.phone = this.editProfileData.phone;
        localStorage.setItem('user', JSON.stringify(this.currentUser));
        this.showEditProfile = false;
        this.editProfileMode = false;
        alert('Profile updated successfully!');
      } catch (error) {
        alert('Failed to update profile.');
      }
    },
    cancelEditProfile() {
      this.editProfileMode = false;
      this.editProfileData.full_name = this.currentUser.full_name;
      this.editProfileData.phone = this.currentUser.phone || '';
      this.showEditProfile = false;
    },
    async startExportCsv() {
      this.exportCsvStatus = 'Exporting...';
      this.exportCsvError = null;
      this.exportCsvDownloadUrl = null;
      try {
        const res = await parkingApi.post('/export-csv', {});
        this.exportCsvTaskId = res.data.task_id;
        this.pollExportCsvStatus();
      } catch (e) {
        this.exportCsvStatus = null;
        this.exportCsvError = 'Failed to start export.';
      }
    },
    pollExportCsvStatus() {
      if (this.exportCsvPollingInterval) clearInterval(this.exportCsvPollingInterval);
      this.exportCsvPollingInterval = setInterval(async () => {
        try {
          const res = await parkingApi.get(`/export-csv-status/${this.exportCsvTaskId}`);
          if (res.data.ready) {
            clearInterval(this.exportCsvPollingInterval);
            this.exportCsvStatus = 'Your CSV is ready!';
            this.exportCsvDownloadUrl = 'http://localhost:5000' + res.data.download_url;
          } else if (res.data.error) {
            clearInterval(this.exportCsvPollingInterval);
            this.exportCsvStatus = null;
            this.exportCsvError = res.data.error;
          }
        } catch (e) {
          clearInterval(this.exportCsvPollingInterval);
          this.exportCsvStatus = null;
          this.exportCsvError = 'Error checking export status.';
        }
      }, 3000);
    },
  },
  beforeUnmount() {
    if (this.exportCsvPollingInterval) clearInterval(this.exportCsvPollingInterval);
  }
};
</script>

<style scoped>
.user-dashboard-history {
  background: #f8fbff;
  min-height: 100vh;
}
.header-green.user-header-bar {
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
.edit-profile {
  color: #2563eb;
  font-weight: 500;
  text-decoration: underline;
  cursor: pointer;
}
.welcome-msg {
  font-size: 1.2rem;
  color: #e53935;
  font-weight: bold;
}
.user-main-content {
  max-width: 1100px;
  margin: 2rem auto 0 auto;
  background: #fff;
  border-radius: 16px;
  padding: 2rem 2.5rem 2.5rem 2.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.user-section-title {
  color: #2563eb;
  font-weight: bold;
  margin-bottom: 1.2rem;
  text-align: center;
  font-size: 1.3rem;
  background: #f8fbff;
  border: 2px solid #90caf9;
  border-radius: 12px;
  max-width: 420px;
  margin-left: auto;
  margin-right: auto;
  padding: 0.6rem 0;
}
.user-card {
  background: #fff;
  border: 2.5px solid #90caf9;
  border-radius: 18px;
  padding: 1.2rem 2.2rem 1.5rem 2.2rem;
  max-width: 900px;
  margin: 0 auto 2.2rem auto;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.user-history-table, .user-lots-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: transparent;
}
.user-th {
  font-size: 1.08rem;
  font-weight: 600;
  color: #222;
  border-bottom: 2px solid #90caf9 !important;
  background: #e6f0ff !important;
  text-align: left;
  padding: 0.6rem 1.2rem;
}
.user-td {
  font-size: 1.05rem;
  color: #222;
  padding: 0.5rem 1.2rem;
  border-top: none !important;
  border-bottom: 1.5px solid #e3f0ff !important;
}
.user-btn {
  min-width: 80px;
  padding: 0.3rem 0;
  border-radius: 8px;
  font-size: 1.02rem;
  font-weight: 600;
  border: 2px solid #90caf9;
  background: #e3f0ff;
  color: #2563eb;
  cursor: pointer;
  transition: background 0.18s, color 0.18s;
}
.user-btn.release {
  background: #ffd6d6;
  color: #e53935;
  border-color: #e57373;
}
.user-btn.release:hover {
  background: #ffb74d;
  color: #fff;
}
.user-btn.parked {
  background: #b6f7c1;
  color: #1a7f37;
  border-color: #26a69a;
}
.user-btn.book {
  background: #90caf9;
  color: #fff;
  border-color: #90caf9;
}
.user-btn.book:hover {
  background: #42a5f5;
  color: #fff;
}
.user-search-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.2rem;
  margin: 2.2rem 0 1.2rem 0;
  font-size: 1.08rem;
}
.user-search-label {
  color: #e53935;
  font-weight: 500;
}
.user-search-input {
  min-width: 220px;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: 1.5px solid #b6f7c1;
  font-size: 1.08rem;
  color: #222;
  background: #f8fbff;
}
.booking-modal-backdrop {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}
.booking-modal-content {
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 4px 32px rgba(0,0,0,0.12);
  min-width: 380px;
  max-width: 95vw;
  padding: 0 2.5rem 2.5rem 2.5rem;
  position: relative;
}
.booking-modal-header {
  background: #ffe89c;
  border-radius: 18px 18px 0 0;
  padding: 1.1rem 0;
  font-size: 1.35rem;
  font-weight: bold;
  text-align: center;
  margin: 0 -2.5rem 2rem -2.5rem;
  color: #222;
  border-bottom: 2px solid #f5d76e;
}
.booking-modal-form {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}
.booking-modal-row {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  margin-bottom: 0.2rem;
}
.booking-modal-label {
  min-width: 120px;
  font-size: 1.08rem;
  font-weight: 500;
  color: #222;
  text-align: right;
}
.booking-modal-input {
  flex: 1;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: 1.5px solid #b6f7c1;
  font-size: 1.08rem;
  color: #ff9800;
  font-weight: bold;
  background: #f8fbff;
}
.booking-modal-actions {
  display: flex;
  justify-content: center;
  gap: 2.5rem;
  margin-top: 1.2rem;
}
.booking-modal-btn {
  min-width: 110px;
  padding: 0.6rem 0;
  border-radius: 8px;
  font-size: 1.08rem;
  font-weight: 600;
  border: 2px solid #90caf9;
  background: #e3f0ff;
  color: #2563eb;
  cursor: pointer;
  transition: background 0.18s, color 0.18s;
}
.booking-modal-btn.reserve {
  background: #90caf9;
  color: #fff;
  border-color: #90caf9;
}
.booking-modal-btn.reserve:hover {
  background: #42a5f5;
  color: #fff;
}
.booking-modal-btn.cancel:hover {
  background: #ffd6d6;
  color: #e53935;
  border-color: #e53935;
}
.history-scroll-bar {
  margin-top: 1.2rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
}
.history-scroll-list {
  display: flex;
  gap: 1rem;
}
.history-scroll-card {
  min-width: 220px;
  background: #f8fafc;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 1rem 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.98rem;
}
.summary-charts-row {
  display: flex;
  flex-wrap: wrap;
  gap: 2rem;
  margin-top: 2rem;
  justify-content: center;
}
.summary-chart-block {
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 1.5rem 2rem 2rem 2rem;
  min-width: 320px;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.summary-chart-label {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1976d2;
  margin-bottom: 1.2rem;
  text-align: center;
}
</style> 