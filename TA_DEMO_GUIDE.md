# Lab 8: TA Demo Guide & Walkthrough

This guide covers the live demo and code walkthrough for **CSE 108 — Lab 8 (ACME University Student Enrollment Web App)**.

---

## 1. How to Launch the App

1. Open a terminal in `lab_08`:
   ```bash
   cd "f:\[03] EDUCATION\[01] CLASSES\CSE 108\Labs AntiG\lab_08"
   python app.py
   ```
2. Open your browser to `http://localhost:5000`.
3. On first startup, `db.create_all()` creates `instance/enrollment.db` and `seed_database()` populates all users, courses, and enrollments from `Enrollment example data for Lab8.xlsx`.

---

## 2. Demo Login Accounts

- **Student (`Mindy Norris`):** username `mnorris` (or `cnorris` from Slide 4 mockup), password `password123`
- **Student (`Jose Santos`):** username `jsantos`, password `password123`
- **Teacher (`Ammon Hepworth`):** username `ahepworth`, password `password123`
- **Teacher (`Ralph Jenkins`):** username `rjenkins`, password `password123`
- **Teacher (`Susan Walker`):** username `swalker`, password `password123`
- **Admin:** username `admin`, password `admin123`

*(All 8 students and 3 teachers from the Excel sheet use `password123`, hashed with `Flask-Bcrypt`.)*

---

## 3. Live Demo Walkthrough

### Part A — Student Flow (`mnorris` / `password123`)
1. Log in as `mnorris` -> header greets `Welcome Mindy!`.
2. **Your Courses tab:** Shows `Physics 121` (`5/10`) and `CS 106` (`4/10`).
3. **Add Courses tab:** Shows all 4 courses:
   - `Math 101` (`4/8`) has a blue `+` button (not enrolled, under capacity).
   - `Physics 121` (`5/10`) and `CS 106` (`4/10`) have a red `-` button (already enrolled).
   - `CS 162` (`4/4`) has no action button because it is full.
4. Click `+` on `Math 101` -> count updates to `5/8` and `Math 101` appears under **Your Courses**.
5. Click `-` on `Math 101` -> drops the course and returns count to `4/8`.
6. Click **Sign out**.

### Part B — Teacher Flow (`ahepworth` / `password123`)
1. Log in as `ahepworth` -> header greets `Welcome Dr Hepworth!`.
2. Shows only Dr. Hepworth's courses (`CS 106` and `CS 162`).
3. Click `CS 162` -> opens the roster view with the back arrow (`←`) and all 4 enrolled students with their grades.
4. Edit a student's grade and click **Save** (or press Enter) -> refreshes/persists in SQLite.
5. Click `←` to return to the courses table, then click **Sign out**.

### Part C — Admin Flow (`admin` / `admin123`)
1. Log in as `admin` -> automatically redirects to `/admin` (powered by **Flask-Admin**).
2. Show the **User**, **Course**, and **Enrollment** tabs for full CRUD management.
3. Point out that `/admin` is protected via `Flask-Login` (`is_accessible` checks `current_user.is_authenticated and current_user.role == "admin"`), so students/teachers cannot access it.
4. Click **Sign Out** in the top navigation bar to return to `/`.
