# API Documentation

## Authentication

### POST `/api/auth/login`
- **Description:** User login.
- **Request:**  
  `{ "email": "user@example.com", "password": "yourpassword" }`
- **Response:**  
  `{ "message": "Login successful", "access_token": "...", "user": { ... } }`

### POST `/api/auth/logout`
- **Description:** User logout (client should delete JWT).
- **Authentication:** Required (JWT)

### POST `/api/auth/register`
- **Description:** Register a new user.
- **Request:**  
  `{ "email": "...", "password": "...", "full_name": "...", "phone": "..." }`
- **Response:**  
  `{ "message": "User registered successfully" }`

### GET `/api/auth/me`
- **Description:** Get current user profile.
- **Authentication:** Required (JWT)

---

## Parking

### GET `/api/parking/lots`
- **Description:** List all parking lots.
- **Authentication:** Required (JWT)

### GET `/api/parking/lots/<lot_id>/spots`
- **Description:** List all spots in a parking lot.
- **Authentication:** Required (JWT)

### GET `/api/parking/vehicles`
- **Description:** List user’s vehicles.
- **Authentication:** Required (JWT)

### POST `/api/parking/vehicles`
- **Description:** Add a new vehicle.
- **Request:**  
  `{ "license_plate": "ABC123" }`
- **Authentication:** Required (JWT)

### GET `/api/parking/history`
- **Description:** Get user’s parking history.
- **Authentication:** Required (JWT)

### POST `/api/parking/park`
- **Description:** Park a vehicle.
- **Request:**  
  `{ "vehicle_no": "...", "spot_id": ... }`
- **Authentication:** Required (JWT)

### POST `/api/parking/unpark`
- **Description:** Unpark a vehicle.
- **Authentication:** Required (JWT)

---

## Admin

> All admin endpoints require admin privileges and JWT authentication.

### GET `/api/admin/dashboard`
- **Description:** Get system statistics.

### GET `/api/admin/users`
- **Description:** List all users.

### PUT `/api/admin/users/<user_id>`
- **Description:** Update user details.

### DELETE `/api/admin/users/<user_id>`
- **Description:** Delete a user.

### GET `/api/admin/users/search`
- **Description:** Search users.

### GET `/api/admin/parking-lots`
- **Description:** List all parking lots.

### POST `/api/admin/parking-lots`
- **Description:** Create a new parking lot.

### GET `/api/admin/parking-lots/<lot_id>/spots`
- **Description:** List all spots in a parking lot.

### PUT `/api/admin/parking-lots/<lot_id>`
- **Description:** Edit a parking lot.

### DELETE `/api/admin/parking-lots/<lot_id>`
- **Description:** Delete a parking lot.

### GET `/api/admin/parking-spots/<spot_id>/details`
- **Description:** Get details of a parking spot.

### GET `/api/admin/summary/revenue`
- **Description:** Get revenue summary.

### GET `/api/admin/summary/occupancy`
- **Description:** Get occupancy summary.

### POST `/api/admin/monthly-report/<user_id>`
- **Description:** Trigger monthly report for a user.

### POST `/api/admin/monthly-reports/all`
- **Description:** Trigger monthly reports for all users.

---

**Note:**  
- All endpoints requiring authentication expect a JWT token in the request headers or cookies.
- For full request/response examples and error codes, refer to the backend code or extend this document as needed. 