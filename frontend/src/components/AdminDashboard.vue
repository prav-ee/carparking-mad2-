<template>
  <div class="admin-dashboard">
    <!-- Header Bar -->
    <div class="header-green header-bar">
      <div class="header-left">
        <span class="welcome-msg">Welcome to Admin</span>
      </div>
      <div class="header-center">
        <a href="#" :class="{active: activeTab === 'dashboard'}" @click.prevent="activeTab = 'dashboard'">Home</a>
        <span>|</span>
        <a href="#" :class="{active: activeTab === 'users'}" @click.prevent="activeTab = 'users'">Users</a>
        <span>|</span>
        <a href="#" :class="{active: activeTab === 'search'}" @click.prevent="activeTab = 'search'">Search</a>
        <span>|</span>
        <a href="#" :class="{active: activeTab === 'summary'}" @click.prevent="activeTab = 'summary'">Summary</a>
        <span>|</span>
        <a href="#" :class="{active: activeTab === 'reminder'}" @click.prevent="activeTab = 'reminder'">Reminder</a>
        <span>|</span>
        <a href="#" @click.prevent="logout">Logout</a>
      </div>
      <div class="header-right">
        <!-- Edit Profile removed -->
      </div>
    </div>

    <!-- Main Content -->
    <div v-if="activeTab === 'dashboard'" class="main-content">
      <h2 class="parking-lots-title">Parking Lots</h2>
      <div class="summary-cards-row">
        <div class="summary-card">
          <div class="summary-title">Total Lots</div>
          <div class="summary-value">{{ parkingLots.length }}</div>
        </div>
        <div class="summary-card">
          <div class="summary-title">Total Users</div>
          <div class="summary-value">{{ nonAdminUsers.length }}</div>
        </div>
        <div class="summary-card">
          <div class="summary-title">Available Spots</div>
          <div class="summary-value">{{ totalAvailableSpots }}</div>
        </div>
        <div class="summary-card">
          <div class="summary-title">Occupied Spots</div>
          <div class="summary-value">{{ totalOccupiedSpots }}</div>
        </div>
      </div>
      <div class="lots-row lots-grid-scroll">
        <div v-for="lot in parkingLots" :key="lot.id" class="lot-card lot-card-grid">
          <div class="lot-card-header">
            <span class="lot-name">{{ lot.name }}</span>
            <span class="lot-actions">
              <span class="edit-link" @click="editLot(lot)">Edit</span> |
              <span class="delete-link" @click="deleteLot(lot)">Delete</span>
            </span>
          </div>
          <div class="lot-details">
            <div class="lot-address"><i class="bi bi-geo-alt"></i> {{ lot.address || lot.location }}</div>
            <div class="lot-price"><i class="bi bi-currency-rupee"></i> {{ lot.price_per_hour }}/hr</div>
          </div>
          <div class="lot-occupancy-bar">
            <div class="lot-occupancy-fill" :style="{width: occupancyPercent(lot) + '%'}"></div>
            <span class="lot-occupancy-label occupancy-green">(Occupied : {{ lot.spots.filter(s => s.is_occupied).length }}/{{ lot.spots.length }})</span>
          </div>
          <div class="lot-grid">
            <div
              v-for="spot in lot.spots"
              :key="spot.id"
              :class="['spot-square', spot.is_occupied ? 'occupied' : 'available', 'd-flex', 'align-items-center', 'justify-content-center']"
              @click="showSpotModalFn(spot.id)" style="cursor:pointer"
            >
              <span>{{ spot.is_occupied ? 'O' : 'A' }}</span>
            </div>
          </div>
        </div>
      </div>
      <button class="add-lot-btn" @click="showAddLotModal = true">+ Add Lot</button>
    </div>

    <!-- Users Tab -->
    <div v-if="activeTab === 'users'" class="main-content">
      <div class="users-section-title">Registered Users</div>
      <input v-model="userSearch" placeholder="Search users..." class="search-input" />
      <div class="users-card">
        <table class="table users-table mb-0">
          <thead>
            <tr>
              <th class="users-th">ID</th>
              <th class="users-th">E_Mail</th>
              <th class="users-th">Full Name</th>
              <th class="users-th">Phone</th>
              <th class="users-th">Current Spot</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in filteredUsers" :key="user.id">
              <td class="users-td">{{ user.id }}</td>
              <td class="users-td">{{ user.email }}</td>
              <td class="users-td">{{ user.full_name }}</td>
              <td class="users-td">{{ user.phone || '-' }}</td>
              <td class="users-td">
                <div v-if="user.current_spots && user.current_spots.length">
                  <table style="width:100%; border-collapse:collapse; background:transparent;">
                    <thead>
                      <tr style="font-size:0.95em; color:#888;">
                        <th style="text-align:left; padding-right:8px;">location</th>
                        <th style="text-align:left; padding-right:8px;">Spot_ID</th>
                        <th style="text-align:left;">vehicle_no</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="spot in user.current_spots" :key="spot.spot_id">
                        <td style="padding-right:8px;">{{ spot.lot_name }}</td>
                        <td style="padding-right:8px;">{{ spot.spot_number }}</td>
                        <td>{{ spot.license_plate }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <span v-else>-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Reminder Time Tab -->
    <div v-if="activeTab === 'reminder'" class="main-content">
      <SetReminderTime />
    </div>

    <!-- Summary Tab (placeholder) -->
    <div v-if="activeTab === 'summary'" class="main-content">
      <div class="summary-header">
        <span class="summary-title">Summary shows statistical Charts</span>
      </div>
      <div class="summary-charts-row">
        <div class="summary-chart-block">
          <div class="summary-chart-label">Revenue from each parking lot</div>
          <PieChart v-if="revenueData" :data="revenueData" :options="pieOptions" />
          <div v-else>Loading revenue data...</div>
        </div>
        <div class="summary-chart-block">
          <div class="summary-chart-label">Summary on available and occupied parking lots</div>
          <BarChart v-if="occupancyData" :data="occupancyData" :options="barOptions" />
          <div v-else>Loading occupancy data...</div>
        </div>
      </div>
    </div>

    <!-- Search Tab (placeholder) -->
    <div v-if="activeTab === 'search'" class="main-content">
      <h2 class="search-title">Search</h2>
      <div class="search-bar-row">
        <select v-model="searchType" class="search-type-select">
          <option value="users">Users</option>
          <option value="lots">Parking Lots</option>
        </select>
        <input v-model="searchQuery" placeholder="Enter search..." class="search-bar-input" />
        <button @click="performSearch" :disabled="searchLoading" class="search-btn">Search</button>
      </div>
      <div v-if="searchLoading" class="search-loading">Searching...</div>
      <div v-if="searchError" class="search-error">{{ searchError }}</div>
      <div v-if="searchResults.length">
        <table v-if="searchType === 'users'" class="table users-table mb-0">
          <thead>
            <tr>
              <th class="users-th">ID</th>
              <th class="users-th">E_Mail</th>
              <th class="users-th">Full Name</th>
              <th class="users-th">Phone</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in searchResults.filter(u => u.role !== 'admin')" :key="u.id">
              <td class="users-td">{{ u.id }}</td>
              <td class="users-td">{{ u.email }}</td>
              <td class="users-td">{{ u.full_name }}</td>
              <td class="users-td">{{ u.phone || '-' }}</td>
            </tr>
          </tbody>
        </table>
        <table v-else-if="searchType === 'lots'" class="table users-table mb-0">
          <thead>
            <tr>
              <th class="users-th">ID</th>
              <th class="users-th">Name</th>
              <th class="users-th">Address</th>
              <th class="users-th">Pin</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="l in searchResults" :key="l.id">
              <td class="users-td">{{ l.id }}</td>
              <td class="users-td">{{ l.name }}</td>
              <td class="users-td">{{ l.address }}</td>
              <td class="users-td">{{ l.pincode }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else-if="!searchLoading && searchQuery" class="search-no-results">No results found.</div>
    </div>

    <!-- Add Parking Lot Modal -->
    <div v-if="showAddLotModal" class="edit-modal-backdrop">
      <div class="edit-modal-content">
        <div class="edit-modal-header">New Parking Lot</div>
        <form @submit.prevent="addParkingLot" class="edit-modal-form">
          <div class="edit-modal-row">
            <label class="edit-modal-label">Prime Location Name :</label>
            <input type="text" class="edit-modal-input" v-model="newLot.name" required />
          </div>
          <div class="edit-modal-row">
            <label class="edit-modal-label">Address :</label>
            <textarea class="edit-modal-textarea" v-model="newLot.address" rows="3" required></textarea>
          </div>
          <div class="edit-modal-row">
            <label class="edit-modal-label">Pin code :</label>
            <input type="text" class="edit-modal-input" v-model="newLot.pincode" required />
          </div>
          <div class="edit-modal-row">
            <label class="edit-modal-label">Price(per hour) :</label>
            <input type="number" class="edit-modal-input" v-model="newLot.price_per_hour" min="0" required />
          </div>
          <div class="edit-modal-row">
            <label class="edit-modal-label">Maximum spots :</label>
            <input type="number" class="edit-modal-input" v-model="newLot.max_spots" min="1" required />
          </div>
          <div class="edit-modal-actions">
            <button type="submit" class="edit-modal-btn update">Add</button>
            <button type="button" class="edit-modal-btn cancel" @click="showAddLotModal = false">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit Parking Lot Modal -->
    <div v-if="editLotModal" class="edit-modal-backdrop">
      <div class="edit-modal-content">
        <div class="edit-modal-header">Edit Parking Lot</div>
        <form @submit.prevent="submitEditLot" class="edit-modal-form">
          <div class="edit-modal-row">
            <label class="edit-modal-label">Prime Location Name :</label>
            <input type="text" class="edit-modal-input" v-model="editLotData.name" required />
          </div>
          <div class="edit-modal-row">
            <label class="edit-modal-label">Address :</label>
            <textarea class="edit-modal-textarea" v-model="editLotData.address" rows="3" required></textarea>
          </div>
          <div class="edit-modal-row">
            <label class="edit-modal-label">Pin code :</label>
            <input type="text" class="edit-modal-input" v-model="editLotData.pincode" required />
          </div>
          <div class="edit-modal-row">
            <label class="edit-modal-label">Price(per hour) :</label>
            <input type="number" class="edit-modal-input" v-model="editLotData.price_per_hour" min="0" required />
          </div>
          <div class="edit-modal-row">
            <label class="edit-modal-label">Maximum spots :</label>
            <input type="number" class="edit-modal-input" v-model="editLotData.max_spots" min="1" required />
          </div>
          <div class="edit-modal-actions">
            <button type="submit" class="edit-modal-btn update">Update</button>
            <button type="button" class="edit-modal-btn cancel" @click="editLotModal = false">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Spot Details Modal -->
    <div v-if="showSpotModal" class="edit-modal-backdrop">
      <div class="edit-modal-content">
        <div class="edit-modal-header" :style="{background:'#ffe082', fontWeight:'bold'}">
          {{ selectedSpot.is_occupied ? 'Occupied Parking Spot Details' : 'Parking Spot Details' }}
        </div>
        <div class="edit-modal-row">
          <label>ID :</label>
          <input type="text" :value="selectedSpot.spot_number" readonly />
        </div>
        <template v-if="selectedSpot.is_occupied && selectedSpot.vehicle && selectedSpot.user">
          <div class="edit-modal-row">
            <label>Customer ID :</label>
            <input type="text" :value="selectedSpot.user.id" readonly />
          </div>
          <div class="edit-modal-row">
            <label>Vehicle number :</label>
            <input type="text" :value="selectedSpot.vehicle.license_plate" readonly />
          </div>
          <div class="edit-modal-row">
            <label>Parking time :</label>
            <input type="text" :value="selectedSpot.start_time || 'Not available'" readonly />
          </div>
          
        </template>
        <template v-else>
          <div class="edit-modal-row" style="color:#1a7f37;font-weight:bold;">
            This spot is available.
          </div>
        </template>
        <div class="edit-modal-actions">
          <button class="edit-modal-btn cancel" @click="showSpotModal = false">Close</button>
        </div>
      </div>
    </div>
    <!-- Occupied Spot Details Modal -->
    <div v-if="showOccupiedModal" class="edit-modal-backdrop">
      <div class="edit-modal-content">
        <div class="edit-modal-header">Occupied Parking Spot Details</div>
        <div class="edit-modal-row">
          <label>ID :</label>
          <input type="text" :value="occupiedDetails.id" readonly />
        </div>
        <div class="edit-modal-row">
          <label>Customer ID :</label>
          <input type="text" :value="occupiedDetails.customer_id" readonly />
        </div>
        <div class="edit-modal-row">
          <label>Vehicle number :</label>
          <input type="text" :value="occupiedDetails.vehicle_number" readonly />
        </div>
        <div class="edit-modal-row">
          <label>Date/time of parking :</label>
          <input type="text" :value="occupiedDetails.parking_time" readonly />
        </div>
        <div class="edit-modal-row">
          <label>Est. parking cost :</label>
          <input type="text" :value="occupiedDetails.est_parking_cost" readonly />
        </div>
        <!-- etc., fields... -->
        <div class="edit-modal-actions">
          <button class="edit-modal-btn cancel" @click="showOccupiedModal = false">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api, { authApi, parkingApi } from '../api';
import PieChart from './PieChart.vue';
import BarChart from './BarChart.vue';
import SetReminderTime from './SetReminderTime.vue';

export default {
  name: 'AdminDashboard',
  components: {
    PieChart,
    BarChart,
    SetReminderTime,
  },
  data() {
    return {
      activeTab: 'dashboard',
      users: [],
      parkingLots: [],
      showAddLotModal: false,
      newLot: {
        name: '',
        address: '',
        pincode: '',
        price_per_hour: 0,
        max_spots: 0
      },
      editLotModal: false,
      editLotData: {
        id: null,
        name: '',
        address: '',
        pincode: '',
        price_per_hour: 0,
        max_spots: 0
      },
      showSpotModal: false,
      selectedSpot: null,
      showOccupiedModal: false,
      occupiedDetails: null,
      userSearch: '',
      revenueData: null,
      occupancyData: null,
      barOptions: { responsive: true, plugins: { legend: { display: false } } },
      pieOptions: { responsive: true },
      searchType: 'users',
      searchQuery: '',
      searchResults: [],
      searchLoading: false,
      searchError: '',
    };
  },
  computed: {
    nonAdminUsers() {
      return Array.isArray(this.users) ? this.users.filter(u => u.role !== 'admin') : [];
    },
    totalOccupiedSpots() {
      return this.parkingLots.reduce((sum, lot) => sum + (lot.spots ? lot.spots.filter(s => s.is_occupied).length : 0), 0);
    },
    totalAvailableSpots() {
      // Use max_spots for each lot
      const totalMaxSpots = this.parkingLots.reduce((sum, lot) => sum + (lot.max_spots || 0), 0);
      return totalMaxSpots - this.totalOccupiedSpots;
    },
    filteredUsers() {
      if (!this.userSearch) return this.nonAdminUsers;
      const q = this.userSearch.toLowerCase();
      return this.nonAdminUsers.filter(u =>
        u.full_name.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        (u.current_spot && (
          (u.current_spot.lot_name || '').toLowerCase().includes(q) ||
          (u.current_spot.license_plate || '').toLowerCase().includes(q)
        ))
      );
    }
  },
  async mounted() {
    await this.loadDashboardData();
    // Fetch summary data for charts
    try {
      const revRes = await api.get('/summary/revenue');
      this.revenueData = {
        labels: revRes.data.revenue_per_lot.map(l => l.lot_name),
        datasets: [{ label: 'Revenue', data: revRes.data.revenue_per_lot.map(l => l.revenue), backgroundColor: '#1976d2' }]
      };
      const occRes = await api.get('/summary/occupancy');
      this.occupancyData = {
        labels: occRes.data.occupancy_per_lot.map(l => l.lot_name),
        datasets: [
          { label: 'Occupied', data: occRes.data.occupancy_per_lot.map(l => l.occupied_spots), backgroundColor: '#d32f2f' },
          { label: 'Available', data: occRes.data.occupancy_per_lot.map(l => l.available_spots), backgroundColor: '#4fc3f7' }
        ]
      };
    } catch (e) { /* handle error if needed */ }
  },
  methods: {
    async loadDashboardData() {
      this.error = null;
      try {
        // Fetch users (admin only)
        const usersRes = await api.get('/users');
        this.users = Array.isArray(usersRes.data) ? usersRes.data : usersRes.data.users;
      } catch (err) {
        if (err.response && err.response.status === 403) {
          this.error = 'Access denied. You must be an admin.';
        } else if (err.response && err.response.status === 401) {
          this.error = 'Not logged in.';
        } else {
          this.error = 'An error occurred while fetching users.';
        }
        this.users = [];
      }
      // Fetch lots
      try {
        const lotsRes = await api.get('/parking-lots');
        const lots = lotsRes.data.lots;
        // For each lot, fetch its spots and attach
        const lotsWithSpots = await Promise.all(lots.map(async lot => {
          const spotsRes = await api.get(`/parking-lots/${lot.id}/spots`);
          return { ...lot, spots: spotsRes.data.spots };
        }));
        this.parkingLots = lotsWithSpots;
      } catch (e) {
        this.parkingLots = [];
      }
    },
    async addParkingLot() {
      try {
        await api.post('/parking-lots', this.newLot);
        this.showAddLotModal = false;
        this.newLot = { name: '', address: '', pincode: '', price_per_hour: 0, max_spots: 0 };
        await this.loadDashboardData();
      } catch (error) {
        console.error('Error adding parking lot:', error);
      }
    },
    editLot(lot) {
      this.editLotData = { ...lot };
      this.editLotModal = true;
    },
    async submitEditLot() {
      // Convert to numbers
      this.editLotData.max_spots = Number(this.editLotData.max_spots);
      this.editLotData.price_per_hour = Number(this.editLotData.price_per_hour);

      // Optionally, check for empty fields
      if (
        !this.editLotData.name ||
        !this.editLotData.address ||
        !this.editLotData.pincode ||
        !this.editLotData.price_per_hour ||
        !this.editLotData.max_spots
      ) {
        alert('All fields are required!');
        return;
      }

      try {
        await api.put(`/parking-lots/${this.editLotData.id}`, this.editLotData);
        alert('Lot updated successfully!');
        this.editLotModal = false;
        this.loadDashboardData();
      } catch (error) {
        alert('Failed to update lot');
      }
    },
    async deleteLot(lot) {
      if (!confirm('Are you sure you want to delete this lot? This can only be done if all spots are empty.')) return;
      try {
        await api.delete(`/parking-lots/${lot.id}`);
        await this.loadDashboardData();
      } catch (error) {
        alert('Failed to delete lot. Make sure all spots are empty.');
      }
    },
    async logout() {
      try {
        await authApi.post('/logout', {});
      } catch (error) {
        // ignore error
      }
      localStorage.removeItem('user');
      this.$emit('logout');
      window.location.reload(); // Force reload to clear all state
    },
    showSpotModalFn(spotId) {
      api.get(`/parking-spots/${spotId}/details`).then(res => {
        console.log('Spot details received:', res.data);
        this.selectedSpot = res.data;
        this.showSpotModal = true;
      }).catch(error => {
        console.error('Error fetching spot details:', error);
        alert('Failed to load spot details');
      });
    },
    openOccupiedDetails(spot) {
      if (!spot.is_occupied) {
        alert('This spot is not occupied.');
        return;
      }
      api.get(`/parking-spots/${spot.id}/occupied-details`).then(res => {
        this.occupiedDetails = res.data;
        this.showOccupiedModal = true;
      }).catch(() => {
        alert('Failed to load occupied spot details.');
      });
    },
    deleteSpot(spot) {
      if (spot.is_occupied) return;
      api.delete(`/parking-spots/${spot.id}`).then(() => {
        this.showSpotModal = false;
        this.loadDashboardData();
      });
    },
    async performSearch() {
      this.searchLoading = true;
      this.searchError = '';
      let endpoint = '';
      if (this.searchType === 'users') endpoint = `/users/search?query=${encodeURIComponent(this.searchQuery)}`;
      if (this.searchType === 'lots') endpoint = `/parking-lots/search?query=${encodeURIComponent(this.searchQuery)}`;
      if (this.searchType === 'spots') endpoint = `/parking-spots/search?query=${encodeURIComponent(this.searchQuery)}`;
      try {
        const res = await api.get(endpoint);
        this.searchResults = res.data.results;
      } catch (e) {
        this.searchError = 'Search failed';
      }
      this.searchLoading = false;
    },
    occupancyPercent(lot) {
      if (!lot.spots || lot.spots.length === 0) return 0;
      return Math.round((lot.spots.filter(s => s.is_occupied).length / lot.spots.length) * 100);
    },
    async releaseSpot(vehicle_id) {
      try {
        await parkingApi.post('/unpark', { vehicle_id });
        alert('Vehicle released successfully!');
        this.loadDashboardData(); // or whatever method reloads the user list
      } catch (error) {
        alert('Failed to release vehicle.');
      }
    },

  }
};
</script>

<style scoped>
.admin-dashboard {
  background: #f8fbff;
  min-height: 100vh;
}
.header-green.header-bar {
  background: #b6f7c1;
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
.header-center a {
  color: #1a7f37;
  text-decoration: none;
  font-weight: 500;
}
.header-center a.active, .header-center a:focus {
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
.main-content {
  max-width: 1100px;
  margin: 2rem auto 0 auto;
  background: #e6f0ff;
  border-radius: 16px;
  padding: 2rem 2.5rem 2.5rem 2.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.parking-lots-title {
  color: #2563eb;
  font-weight: bold;
  margin-bottom: 1.5rem;
  text-align: center;
  font-size: 1.5rem;
}
.lots-row {
  display: flex;
  gap: 32px;
  overflow-x: auto;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
}
.lot-card {
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  padding: 1.2rem 1.5rem 1.5rem 1.5rem;
  min-width: 220px;
  max-width: 260px;
  flex: 0 0 auto;
  border: 2px solid #b6f7c1;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.lot-card-header {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.lot-name {
  font-size: 1.1rem;
  font-weight: bold;
  color: #2563eb;
}
.lot-actions a {
  color: #ff9800;
  font-weight: 500;
  margin-left: 4px;
  margin-right: 4px;
  text-decoration: underline;
  cursor: pointer;
}
.lot-actions a:last-child {
  color: #e53935;
}
.lot-occupancy {
  color: #1a7f37;
  font-weight: 500;
  margin-bottom: 0.7rem;
}
.spot-square {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  border: 2.5px solid #4fc3f7;
  font-weight: bold;
  font-size: 1.2rem;
  margin: 3px;
  transition: background 0.2s;
}
.spot-square.available {
  background-color: #c8e6c9; /* light green */
  border: 1px solid #388e3c;
}
.spot-square.occupied {
  background-color: #ffcdd2; /* light red */
  border: 1px solid #d32f2f;
}
.lot-grid {
  display: flex;
  flex-wrap: wrap;
  max-width: 210px;
  margin: 0 auto 0.5rem auto;
}
.add-lot-btn {
  display: block;
  margin: 2rem auto 0 auto;
  background: #ff9800;
  color: #fff;
  font-weight: bold;
  font-size: 1.2rem;
  border: 2px solid #ff9800;
  border-radius: 8px;
  padding: 12px 36px;
  cursor: pointer;
  transition: background 0.2s;
}
.add-lot-btn:hover {
  background: #ffb74d;
  border-color: #ffb74d;
}
.edit-modal-backdrop {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}
.edit-modal-content {
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 4px 32px rgba(0,0,0,0.12);
  min-width: 380px;
  max-width: 95vw;
  padding: 0 2.5rem 2.5rem 2.5rem;
  position: relative;
}
.edit-modal-header {
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
.edit-modal-form {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}
.edit-modal-row {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  margin-bottom: 0.2rem;
}
.edit-modal-label {
  min-width: 160px;
  font-size: 1.08rem;
  font-weight: 500;
  color: #222;
  text-align: right;
}
.edit-modal-input {
  flex: 1;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: 1.5px solid #b6f7c1;
  font-size: 1.08rem;
  color: #ff9800;
  font-weight: bold;
  background: #f8fbff;
}
.edit-modal-textarea {
  flex: 1;
  padding: 0.5rem 1rem;
  border-radius: 12px;
  border: 1.5px solid #b6f7c1;
  font-size: 1.08rem;
  color: #ff9800;
  font-weight: bold;
  background: #f8fbff;
  min-height: 60px;
  resize: vertical;
}
.edit-modal-actions {
  display: flex;
  justify-content: center;
  gap: 2.5rem;
  margin-top: 1.2rem;
}
.edit-modal-btn {
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
.edit-modal-btn.update {
  background: #90caf9;
  color: #fff;
  border-color: #90caf9;
}
.edit-modal-btn.update:hover {
  background: #42a5f5;
  color: #fff;
}
.edit-modal-btn.cancel:hover {
  background: #ffd6d6;
  color: #e53935;
  border-color: #e53935;
}
.users-section-title {
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #1976d2;
}
.users-card {
  margin-top: 0.5rem;
  padding: 1.5rem 1rem 1rem 1rem;
  background: #f8fafc;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.users-table {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  overflow: hidden;
}
.users-th, .users-td {
  padding: 0.75rem 1.2rem;
  text-align: left;
  vertical-align: middle;
}
.users-th {
  background: #f3f6fa;
  font-weight: 700;
  color: #2563eb;
  border-bottom: 2px solid #e0e0e0;
}
.users-td {
  border-bottom: 1px solid #f0f0f0;
  color: #222;
}
.users-table tr:last-child .users-td {
  border-bottom: none;
}
.users-etc {
  color: #e53935;
  font-size: 1.05rem;
  margin-top: 0.7rem;
  text-align: left;
}
.search-input {
  margin-bottom: 1.2rem;
  border-radius: 8px;
  border: 1px solid #d0d7de;
  padding: 0.5rem 1rem;
  width: 100%;
  max-width: 350px;
}
.summary-cards-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.summary-card {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 1rem 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  text-align: center;
  min-width: 120px;
}
.summary-title {
  font-size: 1rem;
  color: #888;
}
.summary-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #1976d2;
}
.summary-header {
  text-align: center;
  margin-bottom: 1.5rem;
}
.summary-title {
  color: #ff9800;
  font-size: 1.3rem;
  font-weight: bold;
}
.summary-charts-row {
  display: flex;
  justify-content: center;
  gap: 3rem;
  margin-top: 2rem;
}
.summary-chart-block {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  padding: 1.5rem 2rem;
  min-width: 320px;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.summary-chart-label {
  font-size: 1.1rem;
  color: #2563eb;
  font-weight: 500;
  margin-bottom: 1rem;
  text-align: center;
}
.lots-row.lots-grid-scroll {
  display: flex;
  flex-wrap: nowrap;
  overflow-x: auto;
  gap: 1.5rem;
  padding-bottom: 1rem;
  margin-bottom: 1.5rem;
}
.lot-card.lot-card-grid {
  min-width: 240px;
  max-width: 240px;
  min-height: 220px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  padding: 1.1rem 1rem 1rem 1rem;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: flex-start;
  transition: box-shadow 0.2s, transform 0.2s;
}
@media (max-width: 900px) {
  .lot-card.lot-card-grid {
    min-width: 180px;
    max-width: 180px;
    padding: 0.8rem 0.6rem 0.8rem 0.6rem;
  }
}
@media (max-width: 600px) {
  .lot-card.lot-card-grid {
    min-width: 95vw;
    max-width: 95vw;
    margin-right: 0.5rem;
  }
}
.lot-card.lot-card-grid:hover {
  box-shadow: 0 6px 24px rgba(59,130,246,0.13);
  transform: translateY(-2px) scale(1.03);
}
.lot-card-header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.08rem;
  font-weight: 600;
  color: #1976d2;
  margin-bottom: 0.3rem;
}
.lot-icon {
  font-size: 1.5rem;
  color: #2563eb;
  margin-right: 0.3rem;
}
.lot-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: #222;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.lot-actions {
  display: flex;
  gap: 0.3rem;
}
.icon-btn {
  background: none;
  border: none;
  color: #1976d2;
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  transition: background 0.15s;
}
.icon-btn:hover {
  background: #e3f2fd;
}
.lot-details {
  width: 100%;
  font-size: 0.97rem;
  color: #4a5568;
  margin-bottom: 0.3rem;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}
.lot-address, .lot-price {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
.lot-price {
  color: #388e3c;
  font-weight: 600;
}
.lot-occupancy-bar {
  width: 100%;
  height: 18px;
  background: #f3f6fa;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  position: relative;
  overflow: hidden;
  margin-top: 0.2rem;
}
.lot-occupancy-fill {
  height: 100%;
  background: linear-gradient(90deg, #1976d2 60%, #4fc3f7 100%);
  border-radius: 8px 0 0 8px;
  transition: width 0.3s;
}
.lot-occupancy-label {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.93rem;
  color: #1976d2;
  font-weight: 600;
  pointer-events: none;
}
.lot-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-top: 0.3rem;
}
.spot-square {
  width: 22px;
  height: 22px;
  border-radius: 4px;
  background: #e3f2fd;
  color: #1976d2;
  font-size: 0.95rem;
  font-weight: 600;
  border: 1.5px solid #90caf9;
  display: flex;
  align-items: center;
  justify-content: center;
}
.spot-square.occupied {
  background: #ffcdd2;
  color: #d32f2f;
  border: 1.5px solid #e57373;
}
.spot-square.available {
  background: #c8e6c9;
  color: #388e3c;
  border: 1.5px solid #81c784;
}
.search-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: #1976d2;
  margin-bottom: 1.2rem;
}
.search-bar-row {
  display: flex;
  gap: 0.7rem;
  align-items: center;
  margin-bottom: 1.2rem;
}
.search-type-select, .search-bar-input {
  border-radius: 8px;
  border: 1px solid #d0d7de;
  padding: 0.5rem 1rem;
  font-size: 1rem;
}
.search-btn {
  background: #1976d2;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1.2rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.search-btn:disabled {
  background: #b6c6e0;
  cursor: not-allowed;
}
.search-loading {
  color: #1976d2;
  font-weight: 500;
  margin-bottom: 1rem;
}
.search-error {
  color: #e53935;
  font-weight: 500;
  margin-bottom: 1rem;
}
.search-results-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.search-result-card {
  display: flex;
  align-items: flex-start;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 1rem 1.2rem;
  gap: 1.1rem;
}
.result-icon {
  font-size: 2.1rem;
  color: #2563eb;
  flex-shrink: 0;
  margin-top: 0.2rem;
}
.result-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.result-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #222;
}
.result-detail {
  font-size: 0.98rem;
  color: #4a5568;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
.search-no-results {
  color: #888;
  font-size: 1.05rem;
  margin-top: 1.2rem;
}
.edit-link, .delete-link {
  color: orange;
  cursor: pointer;
  font-weight: bold;
  margin: 0 2px;
}
.edit-link:hover, .delete-link:hover {
  text-decoration: underline;
}
.occupancy-green {
  color: #1a7f37;
  font-weight: bold;
}
</style> 