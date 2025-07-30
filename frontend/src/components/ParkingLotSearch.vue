<template>
  <div class="parking-lot-search">
    <div class="card search-card mt-3">
      <div class="card-header search-header">
        Search Available Parking Lots by Location or Pin Code
      </div>
      <div class="card-body p-2">
        <input v-model="lotSearch" class="form-control search-input" placeholder="Type location or pin code..." />
      </div>
    </div>
    <div class="card lots-card mt-3">
      <div class="card-body p-0">
        <table class="table table-borderless align-middle mb-0">
          <thead>
            <tr>
              <th>Name</th>
              <th>Location</th>
              <th>Pin Code</th>
              <th>Available Spots</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lot in filteredLots" :key="lot.id">
              <td>{{ lot.name }}</td>
              <td>{{ lot.location }}</td>
              <td>{{ lot.pincode }}</td>
              <td>
                <span class="badge bg-success" v-if="lot.available_spots > 0">{{ lot.available_spots }}</span>
                <span class="badge bg-danger" v-else>0</span>
              </td>
              <td>
                <button class="btn btn-primary" @click="bookLot(lot)" :disabled="lot.available_spots === 0">Book</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { parkingApi } from '../api.js';
export default {
  name: 'ParkingLotSearch',
  data() {
    return {
      lots: [],
      lotSearch: ''
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
  methods: {
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

        // 2. Get user's vehicles
        const vehiclesRes = await parkingApi.get('/vehicles');
        if (!vehiclesRes.data.vehicles.length) {
          alert('You have no registered vehicles!');
          return;
        }
        const vehicle = vehiclesRes.data.vehicles[0];

        // 3. Book the spot
        await parkingApi.post('/park', {
          vehicle_id: vehicle.id,
          spot_id: spot.id
        });

        alert('Booking successful!');
        await this.fetchLots(); // Refresh the lots list
      } catch (error) {
        alert('Booking failed. Please try again.');
        console.error('Booking error:', error);
      }
    },
    async fetchLots() {
      try {
        const res = await parkingApi.get('/lots');
        this.lots = res.data.lots;
      } catch (error) {
        console.error('Error fetching lots:', error);
      }
    }
  },
  async mounted() {
    await this.fetchLots();
  }
};
</script>

<style scoped>
.parking-lot-search {
  max-width: 900px;
  margin: 2rem auto 0 auto;
}
.lots-card {
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  overflow: hidden;
}
.search-card {
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  margin-top: 1.5rem;
  overflow: hidden;
}
.search-header {
  background: #e6f0ff;
  font-weight: 500;
  font-size: 1rem;
  border-radius: 14px 14px 0 0;
}
.search-input {
  background: #e6f0ff;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  padding: 0.7rem 1.2rem;
  margin-top: 0.5rem;
}
</style> 