<template>
  <div class="admin-reminder-time">
    <h3>Set Daily Reminder Time</h3>
    <form @submit.prevent="saveReminderTime">
      <label>
        Hour (0-23):
        <input type="number" v-model.number="hour" min="0" max="23" required />
      </label>
      <label>
        Minute (0-59):
        <input type="number" v-model.number="minute" min="0" max="59" required />
      </label>
      <button type="submit" class="admin-btn">Save</button>
    </form>
    <div v-if="status" style="color: green; margin-top: 1em;">{{ status }}</div>
    <div v-if="error" style="color: red; margin-top: 1em;">{{ error }}</div>
    <div style="margin-top: 1em;">
      <b>Current Reminder Time:</b>
      <span v-if="currentTime">{{ currentTime }}</span>
      <span v-else>Loading...</span>
    </div>
  </div>
</template>

<script>
import { api } from '../api.js';

export default {
  name: 'SetReminderTime',
  data() {
    return {
      hour: 18,
      minute: 0,
      status: '',
      error: '',
      currentTime: ''
    };
  },
  async mounted() {
    await this.fetchCurrentTime();
  },
  methods: {
    async fetchCurrentTime() {
      try {
        const res = await api.get('/reminder-time');
        this.hour = res.data.hour;
        this.minute = res.data.minute;
        this.currentTime = `${this.hour.toString().padStart(2, '0')}:${this.minute.toString().padStart(2, '0')}`;
      } catch (e) {
        this.currentTime = '';
        this.error = 'Failed to fetch current reminder time.';
      }
    },
    async saveReminderTime() {
      this.status = '';
      this.error = '';
      try {
        await api.post('/reminder-time', { hour: this.hour, minute: this.minute });
        this.status = 'Reminder time updated!';
        this.currentTime = `${this.hour.toString().padStart(2, '0')}:${this.minute.toString().padStart(2, '0')}`;
      } catch (e) {
        this.error = 'Failed to update reminder time.';
      }
    }
  }
};
</script>

<style scoped>
.admin-reminder-time {
  border: 1px solid #ccc;
  padding: 1.5em;
  border-radius: 8px;
  max-width: 350px;
  margin: 2em auto;
  background: #f9f9f9;
}
.admin-btn {
  margin-left: 1em;
  padding: 0.5em 1.2em;
  background: #1976d2;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.admin-btn:hover {
  background: #1565c0;
}
label {
  display: block;
  margin-bottom: 0.5em;
}
input[type='number'] {
  width: 60px;
  margin-left: 0.5em;
}
</style> 