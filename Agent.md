# SIM Card Provisioning Platform – Application Design Plan

## 1. Project Overview

A web-based **internal ISP tool** to manage the full lifecycle of SIM cards:

- Track SIM inventory (ICCID, PIN, PUK)
- Assign SIMs to customers
- Activate / suspend / terminate SIMs
- Maintain full event history for each SIM
- Visualize SIM status distribution, activations over time, etc. using **D3.js**

The application will be built as a **Flask web app** with:

- Server-rendered **Jinja** views backed by Flask blueprints
- Rich UI components powered by **JavaScript and D3.js**
- A **relational database** (e.g. PostgreSQL or MySQL) accessed via SQLAlchemy
- **Docker** for containerised development/runtime

---

## 2. High-Level Architecture

### 2.1 Layers

- **Presentation Layer**
    - Flask blueprints + Jinja templates
    - JS (ES6) modules
    - D3.js charts for dashboards and visualizations

- **Application Layer**
    - Python services / domain managers (`SimLifecycleManager`, `SimImportService`, etc.)
    - WTForms or custom validation for CRUD and workflows
    - Workflow/state-machine helper (custom or library) for SIM state machine

- **Domain Layer**
    - SQLAlchemy models (`SimCard`, `Customer`, `ActivationCode`, `SimEvent`, `TariffPlan`)
    - Domain logic embedded in services + models when appropriate

- **Infrastructure Layer**
    - SQLAlchemy sessions + repositories
    - Database (PostgreSQL/MySQL)
    - Docker services (Flask app, reverse proxy, DB)
    - Asset bundling with Vite/Rollup (optional)

### 2.2 Runtime Components (Dockerized)

- `web` container running the Flask app via Gunicorn
- `nginx` (or Caddy) container serving HTTP and static assets
- `db` container (PostgreSQL or MySQL)
- Optional: `node` container for building assets (if not building locally)

---

## 3. Tech Stack

- **Backend**
    - Python 3.11+
    - Flask 3.x (or latest stable)
    - SQLAlchemy / Alembic
    - Flask-Security / Flask-Login
    - State-machine helper (Transitions, custom service, etc.)

- **Frontend**
    - HTML + Twig
    - CSS (plain / Tailwind / Bootstrap – choose one)
    - JavaScript (ES6+, organized in modules)
    - **D3.js** for charts and data visualizations

- **Database**
    - PostgreSQL (recommended) or MySQL/MariaDB

- **Containerisation**
    - Docker & Docker Compose

- **Tooling**
    - Poetry/pip for Python dependencies
    - Yarn/npm for JS dependencies
    - Pytest / Flask testing utilities for tests

---

## 4. Core Domain Model

### 4.1 Entities

#### `SimCard`
Represents a physical SIM.

- `id: int`
- `iccid: string` (unique)
- `msisdn: string|null` (unique, nullable)
- `status: string`
    - Enum-like values: `AVAILABLE`, `RESERVED`, `ACTIVE`, `SUSPENDED`, `LOST_STOLEN`, `TERMINATED`
- `type: string` (e.g. `prepaid`, `postpaid`, `data-only`)
- `pin: string|null`
- `puk: string|null`
- `createdAt: \DateTimeImmutable`
- `updatedAt: \DateTimeImmutable`
- Relations:
    - `customer: ?Customer` (ManyToOne)
    - `tariffPlan: ?TariffPlan` (ManyToOne)
    - `activationCode: ?ActivationCode` (OneToOne or ManyToOne)
    - `events: Collection<SimEvent>` (OneToMany)

#### `ActivationCode`
Represents code used to activate a SIM (optional but useful).

- `id: int`
- `code: string` (unique)
- `status: string` (`UNUSED`, `USED`, `EXPIRED`)
- `expiresAt: \DateTimeImmutable|null`
- `usedAt: \DateTimeImmutable|null`
- Relation:
    - `simCard: ?SimCard` (OneToOne or ManyToOne)

#### `Customer`
Represents a customer owning one or more SIMs.

- `id: int`
- `firstName: string`
- `lastName: string`
- `email: string`
- `phone: string|null`
- `createdAt: \DateTimeImmutable`
- Relations:
    - `simCards: Collection<SimCard>`

> NOTE: You can merge `Customer` into a `User` entity if you want login for customers.

#### `TariffPlan`
Represents a pricing plan for SIMs.

- `id: int`
- `name: string`
- `monthlyPrice: float`
- `description: text`
- `type: string` (e.g. `mobile`, `data-only`)
- Relations:
    - `simCards: Collection<SimCard>`

#### `SimEvent`
Audit log for each action on a SIM.

- `id: int`
- `simCard: SimCard` (ManyToOne)
- `type: string` (`CREATED`, `ASSIGNED`, `STATUS_CHANGED`, `ACTIVATED`, `SUSPENDED`, `TERMINATED`, `IMPORTED`, `SWAPPED`, etc.)
- `oldStatus: string|null`
- `newStatus: string|null`
- `note: text|null`
- `createdAt: \DateTimeImmutable`
- `createdBy: ?User` (optional if you implement backend users)

#### `User` (for back-office login)
- `id: int`
- `email: string`
- `password: string`
- `roles: json` (e.g. `ROLE_ADMIN`, `ROLE_SUPPORT`)
- Optional relation to `Customer` if you unify them.

---

## 5. Application Modules

### 5.1 SIM Management

**Features:**

- List all SIMs with filters (status, type, customer, tariff)
- View SIM details (info + event timeline)
- CRUD operations for SIMs (admin-only)
- Status transitions: reserve, activate, suspend, report lost, terminate
- SIM swap: assign number and tariff to a new card, terminate old one

### 5.2 Customer Management

**Features:**

- Customer listing and search
- Customer details page:
    - Basic info
    - Assigned SIMs and their statuses
- Assign SIM to customer (from customer view)

### 5.3 Activation Code Management

**Features:**

- List / search activation codes
- View code details (status, related SIM)
- Mark code as used / expired

### 5.4 Import / Inventory Management

**Features:**

- Import CSV with new SIMs (`iccid`, `pin`, `puk`, `type`, `msisdn` optional)
- Validate and preview import results
- Bulk creation of `SimCard` entities
- Event log: `IMPORTED` for each new SIM

### 5.5 Dashboard & Analytics (D3.js)

**Features:**

- Dashboard page with interactive charts:
    - **SIMs by Status** (Pie/Donut chart in D3)
    - **Activations Over Time** (Line/Area chart in D3)
    - **SIMs by TariffPlan** (Bar chart)
- Data endpoint(s) returning JSON for D3 consumption

---

## 6. Frontend Design

### 6.1 Layout & Navigation

- **Top navigation bar**:
    - Logo / app name
    - Links: `Dashboard`, `SIMs`, `Customers`, `Tariff Plans`, `Imports`
    - User menu (Profile, Logout)

- **Left sidebar (optional)**:
    - Filters / quick actions

Use a simple CSS framework (e.g. Bootstrap) for quick layout, or Tailwind if you prefer utility classes.

### 6.2 Key Pages

#### Dashboard (`/dashboard`)
- Panels with key metrics:
    - Total SIMs, Active SIMs, Suspended SIMs, Available SIMs
- D3.js charts:
    - Pie chart: distribution of SIMs by status
    - Line chart: activations per day/week/month
    - Bar chart: SIM count per tariff plan
- Data loaded via AJAX from `/api/stats/*` endpoints

#### SIM List (`/sim-cards`)
- Table view with columns:
    - ICCID, MSISDN, Status, Type, Customer, Tariff, Actions
- Filters:
    - Status dropdown
    - Type dropdown
    - Text search (ICCID/MSISDN)
- Pagination
- Button: “Import SIMs”, “Create SIM”

#### SIM Detail (`/sim-cards/{id}`)
- Header with key info:
    - ICCID, MSISDN, Status badge, Customer, Tariff
- Action buttons:
    - Assign Customer (if none)
    - Activate / Suspend / Terminate / Mark Lost / Swap
- Tabs:
    - **Details** – technical info (PIN, PUK, activation code)
    - **History** – table of `SimEvent`s
- Small D3 mini-chart: timeline of state changes (optional but cool)

#### Customer List & Detail
- Standard CRUD pages
- Customer detail showing:
    - Info
    - Table of assigned SIMs with status

#### Import Page (`/sim-cards/import`)
- Form for file upload (CSV)
- After upload:
    - Preview of parsed rows
    - Validation errors display
    - Confirm & import button

---

## 7. API Design (for JS & D3.js)

Use Flask blueprints / views to expose JSON endpoints (no need for full REST, just what’s needed).

### 7.1 Stats Endpoints

- `GET /api/stats/sim-by-status`
    - Returns:
      ```json
      [
        {"status": "AVAILABLE", "count": 120},
        {"status": "ACTIVE", "count": 350},
        ...
      ]
      ```

- `GET /api/stats/activations-over-time?from=YYYY-MM-DD&to=YYYY-MM-DD`
    - Returns array of date + activation count.

- `GET /api/stats/sim-by-tariff`
    - Returns tariff name + count.

These endpoints will be consumed via `fetch()` in JS and visualised by D3.js.

### 7.2 SIM Actions (AJAX or full-page)

Option 1: Form submissions (traditional)
- Actions like activate/suspend handled via POST forms.

Option 2: AJAX endpoints
- `POST /api/sim-cards/{id}/activate`
- `POST /api/sim-cards/{id}/suspend`
- Return JSON with new status and maybe updated SIM data.

You can mix both approaches (full page for basic CRUD, AJAX for status buttons).

---

## 8. Services & Business Logic

### 8.1 `SimLifecycleManager`

Encapsulate status changes and rules.

Responsibilities:

- Validate allowed transitions (use a lightweight workflow/state-machine helper)
- Change SIM status (and persist)
- Create `SimEvent` entries for each change
- Handle SIM swap logic
- (Optional) Call external APIs to notify “network”

Example methods:

- `reserve(SimCard $sim, Customer $customer)`
- `activate(SimCard $sim, ?ActivationCode $code = null)`
- `suspend(SimCard $sim, string $reason)`
- `terminate(SimCard $sim, string $reason)`
- `swap(SimCard $oldSim, SimCard $newSim)`

### 8.2 `SimImportService`

Responsibilities:

- Parse uploaded CSV file
- Validate structure and individual records
- Create `SimCard` entities
- Handle duplicates (skip or mark as errors)
- Return summary report (created, skipped, errors)

---

## 9. Security & Roles

### 9.1 Roles

- `ROLE_ADMIN`
    - All permissions
    - Manage users, tariff plans, imports, deletes
- `ROLE_SUPPORT`
    - View & edit SIMs/customers
    - Perform status changes
    - No destructive system-level operations (e.g. delete import logs)
- `ROLE_VIEWER` (optional)
    - Read-only access to lists and dashboard

### 9.2 Access Control

Use annotations/attributes or security config:

- SIM management routes restricted to `ROLE_SUPPORT` and `ROLE_ADMIN`
- Import actions restricted to `ROLE_ADMIN`
- Dashboard accessible to all logged-in roles

---

## 10. Docker Setup

### 10.1 Directory Structure (simplified)

```text
project-root/
  docker/
    nginx/
      default.conf
    php/
      Dockerfile
    db/
      init.sql (optional)
  src/
  config/
  public/
  assets/
  docker-compose.yml
a
