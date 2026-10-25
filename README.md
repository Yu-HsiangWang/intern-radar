# Intern Radar

Daily scan of Summer 2027 internship postings for hardware design, design verification,
computer architecture and AI-accelerator roles.

Every morning a GitHub Actions job (`.github/workflows/scan.yml`):

1. reads the [SimplifyJobs Summer 2027 list](https://github.com/SimplifyJobs/Summer2027-Internships);
2. queries company careers sites directly (Workday sites such as NVIDIA, Intel, Marvell, Micron;
   Qualcomm, AMD, Amazon, Google, Apple, Meta, Arm, TI and others; Greenhouse/Ashby boards of
   AI-chip startups; 104 for Taiwan);
3. keeps internships that an undergraduate can apply to, in the US or Taiwan, and tags each one
   `core` (ASIC/RTL/verification/architecture/accelerator), `related` (hardware, embedded, firmware,
   validation, compilers, ML systems) or `stretch`;
4. writes `data/board.json` (the board), `data/status.json` (per-source results) and
   `data/state.json` (first-seen dates, used to flag new postings).

Add a company: one line in `radar/sources.py`. Relevance rules live in `radar/rules.py`.

Run locally: `pip install -r requirements.txt && python radar/build.py`.

Job data belongs to the respective employers; always confirm details on the original posting.
