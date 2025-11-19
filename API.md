# API Documentation

Base URL: `http://localhost:8000/api/v1`

## Endpoints

### 1. Get Customer's SIMs by ID

Get all SIM cards assigned to a specific customer.

**Endpoint:** `GET /customers/<customer_id>/sims`

**Parameters:**
- `customer_id` (path, required): Customer ID (integer)
- `status` (query, optional): Filter by SIM status (e.g., `active`, `inactive`, `provisioning`)
- `carrier` (query, optional): Filter by carrier name (partial match)

**Example Request:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/customers/7/sims" -Method GET
```

**Example with filters:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/customers/7/sims?status=active&carrier=A1" -Method GET
```

**Response (200 OK):**
```json
{
  "customer": {
    "id": 7,
    "name": "Branka Jaković",
    "email": "ivan98@globalnet.hr"
  },
  "sims": [
    {
      "id": 89,
      "iccid": "8938502595821186813",
      "msisdn": "+385917419708",
      "carrier": "A1 Hrvatska",
      "status": "provisioning",
      "created_at": "2025-11-17T20:06:51.939716",
      "assignment": {
        "id": 149,
        "assigned_at": "2025-11-17T20:06:52.089090",
        "note": "CLI-seeded"
      }
    }
  ],
  "total": 1
}
```

**Error Response (404):**
```json
{
  "error": "Customer not found"
}
```

---

### 2. Get Customer's SIMs by Email/Name

Get SIM cards for a customer using their email or name (chatbot-friendly).

**Endpoint:** `GET /customers/<identifier>/sims`

**Parameters:**
- `identifier` (path, required): Customer email or name (string)
- Supports same query params as endpoint #1

**Example Request:**
```powershell
# By email
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/customers/ivan98@globalnet.hr/sims" -Method GET

# By name (partial match)
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/customers/Branka/sims" -Method GET
```

**Note:** Tries exact email match first, then falls back to case-insensitive name search.

---

### 3. List All SIMs

List all SIMs with optional filtering and pagination.

**Endpoint:** `GET /sims`

**Parameters:**
- `status` (query, optional): Filter by status
- `carrier` (query, optional): Filter by carrier (partial match)
- `unassigned` (query, optional): If `true`, only show unassigned SIMs
- `limit` (query, optional): Max results (default 100, max 1000)
- `offset` (query, optional): Pagination offset (default 0)

**Example Request:**
```powershell
# Get all active SIMs
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/sims?status=active&limit=50" -Method GET

# Get unassigned SIMs
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/sims?unassigned=true" -Method GET
```

**Response (200 OK):**
```json
{
  "sims": [
    {
      "id": 89,
      "iccid": "8938502595821186813",
      "msisdn": "+385917419708",
      "carrier": "A1 Hrvatska",
      "status": "active",
      "created_at": "2025-11-17T20:06:51.939716"
    }
  ],
  "total": 1000,
  "limit": 50,
  "offset": 0
}
```

---

### 4. List All Customers

List all customers with optional search and pagination.

**Endpoint:** `GET /customers`

**Parameters:**
- `search` (query, optional): Search by name or email (partial match)
- `limit` (query, optional): Max results (default 100, max 1000)
- `offset` (query, optional): Pagination offset (default 0)

**Example Request:**
```powershell
# Search for customer
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/customers?search=Branka" -Method GET

# Paginate
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/customers?limit=50&offset=100" -Method GET
```

**Response (200 OK):**
```json
{
  "customers": [
    {
      "id": 7,
      "name": "Branka Jaković",
      "email": "ivan98@globalnet.hr",
      "created_at": "2025-11-17T20:06:51.889503"
    }
  ],
  "total": 1000,
  "limit": 50,
  "offset": 0
}
```

---

## Error Handling

All endpoints return consistent error responses:

**400 Bad Request:**
```json
{
  "error": "Bad request",
  "message": "Invalid parameter value"
}
```

**404 Not Found:**
```json
{
  "error": "Not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error"
}
```

---

## Usage in Chatbot

For a chatbot where users query their own SIMs, you can:

1. **By customer ID** (if you have their ID in session):
   ```
   GET /api/v1/customers/{customer_id}/sims
   ```

2. **By email** (if user is authenticated):
   ```
   GET /api/v1/customers/{user_email}/sims
   ```

3. **By name** (for customer service):
   ```
   GET /api/v1/customers/{customer_name}/sims
   ```

### Example Chatbot Flow:

**User:** "Show me my SIM cards"
→ Bot calls: `GET /api/v1/customers/user@example.com/sims`

**User:** "Show me only active SIMs"
→ Bot calls: `GET /api/v1/customers/user@example.com/sims?status=active`

**User:** "Show me SIMs from A1 carrier"
→ Bot calls: `GET /api/v1/customers/user@example.com/sims?carrier=A1`

---

## Testing

Test the API using PowerShell:

```powershell
# Basic test
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/customers/7/sims" -Method GET
$data = $response.Content | ConvertFrom-Json
$data | ConvertTo-Json -Depth 5

# With filters
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/customers/7/sims?status=active" -Method GET
$data = $response.Content | ConvertFrom-Json
Write-Output "Found $($data.total) SIMs"
```

Or use curl:

```bash
curl http://localhost:8000/api/v1/customers/7/sims | jq .
```
