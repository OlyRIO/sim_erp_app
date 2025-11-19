# Data Seeding Tasks (Revised Plan)

1. ~Create seed tasks doc~
2. ~Add seeding module (`app/seed.py`) with `ensure_seed_data()`~
   - Detect empty DB (no `Customer` rows)
   - Generate customers, SIMs, and assignments
   - Idempotent: skip if data already present
3. ~Wire seeding on startup~
   - ~Call `ensure_seed_data()` in `create_app()` after app init~
   - ~Guard with try/except so it no-ops if tables aren’t ready~
   - ~Add env flag `SEED_ON_START=true|false` (default true) to enable/disable~
4. Add Faker-based Croatian data
   - ~Install `Faker` and use `Faker("hr_HR")` for names/emails~
   - ~Generate Croatian-like ICCIDs: `89` + `385` + MNC (`01/10/02`) + random + Luhn~
   - ~Generate MSISDNs in E.164 form `+3859XYYYYYYY` with prefixes `[91,92,95,97,98,99]`~
5. Evolve model/schema for seeding
   - ~Add `msisdn` to `Sim` (unique, indexed, nullable)~
   - Generate Alembic migration for initial schema (includes `msisdn`) and apply
6. CLI: manual seeding
   - Add `flask seed` command to force seeding on demand
7. Configuration & docs
   - Document seeding behavior, env flags, and how to reset volume to reseed
   - Make counts configurable via env: `SEED_CUSTOMERS`, `SEED_SIMS`
8. Run & verify
   - Start stack; confirm first run seeds data; subsequent runs skip
   - Validate unique constraints (ICCID/MSISDN) honored

Optional enhancements
- Deterministic mode: accept `SEED_RANDOM_SEED` for reproducible data
- Add basic factories/fixtures for tests using same generators
