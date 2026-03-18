const express = require("express");
const multer = require("multer");
const path = require("path");
const cors = require("cors");
const axios = require("axios");
const session = require("express-session"); // Moved to the top!

const app = express();
const PORT = 3000;

// --- 1. Middleware Setup (Must be before routes) ---
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.set("view engine", "ejs");

// Allow access to the public folder for your logos
app.use(express.static(path.join(__dirname, "public")));

// Session Configuration
app.use(
  session({
    secret: "dataforge-super-secret-key",
    resave: false,
    saveUninitialized: false,
    cookie: { secure: false }, // Set to true if using HTTPS
  }),
);

// --- 2. Database & Authentication Setup ---
// Stores registered users & the default demo user
const users = [{ email: "user@mail.com", password: "password" }];

// The "Bouncer" Middleware
const requireLogin = (req, res, next) => {
  if (req.session.loggedIn) {
    next(); // They are logged in, let them through
  } else {
    res.redirect("/login"); // Not logged in, kick to login page
  }
};

// --- 3. Authentication Routes ---
// Render Login Page
app.get("/login", (req, res) => {
  if (req.session.loggedIn) return res.redirect("/");
  res.render("login", { error: null });
});

// Handle Login Form Submission
app.post("/login", (req, res) => {
  const { email, password } = req.body;
  const user = users.find((u) => u.email === email && u.password === password);

  if (user) {
    console.log(`User logged in: ${email}`);
    req.session.loggedIn = true;
    req.session.user = email;
    res.redirect("/?alert=login"); // <-- Added alert query
  } else {
    res.render("login", { error: "Invalid email or password." });
  }
});

// Handle Register Form Submission
app.post("/register", (req, res) => {
  const { email, password } = req.body;

  if (users.find((u) => u.email === email)) {
    return res.render("login", {
      error: "Email already registered. Please login.",
    });
  }

  console.log(`New user registered: ${email}`);
  users.push({ email, password });
  req.session.loggedIn = true;
  req.session.user = email;
  res.redirect("/?alert=register"); // <-- Added alert query
});

// Handle Logout
app.get("/logout", (req, res) => {
  req.session.destroy();
  res.redirect("/login?alert=logout"); // <-- Added alert query
});

// --- 4. SECURE PAGE ROUTES (Protected by requireLogin) ---
app.get("/", requireLogin, (req, res) => {
  res.render("index");
});

// Catch anyone trying to type /dashboard manually and redirect them safely
app.get("/dashboard", requireLogin, (req, res) => {
  res.redirect("/");
});

// --- 5. API & Upload Routes ---
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, "uploads/");
  },
  filename: (req, file, cb) => {
    cb(null, "dataset.csv");
  },
});
const upload = multer({ storage: storage });

app.post("/upload", requireLogin, upload.single("dataset"), (req, res) => {
  if (!req.file) {
    return res
      .status(400)
      .json({ status: "error", message: "No file uploaded" });
  }
  console.log("Dataset uploaded successfully to /uploads/dataset.csv");
  res.json({ status: "success", message: "Dataset loaded into memory." });
});

app.post("/api/chat", requireLogin, async (req, res) => {
  try {
    const pythonResponse = await axios.post(
      "http://127.0.0.1:8000/analyze",
      req.body,
    );
    res.json(pythonResponse.data);
  } catch (error) {
    console.error("Python backend error:", error.message);
    res.status(500).json({ error: "Backend unreachable" });
  }
});

// --- 6. Start the Server ---
app.listen(PORT, () => {
  console.log(`=========================================`);
  console.log(`DataForge Pioneers Server Started`);
  console.log(`Dashboard available at: http://localhost:${PORT}`);
  console.log(`=========================================`);
});
