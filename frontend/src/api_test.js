import fetch from "node-fetch";
import jwt from "jsonwebtoken";

const API_BASE_URL = "http://localhost:8000/api/v1";
const email = "abc@gmail.com";
const password = "abc12345";

const testAuth = async () => {
  try {
    // 1. Login để lấy token
    const loginRes = await fetch(`${API_BASE_URL}/auth/login/json`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const loginData = await loginRes.json();
    if (!loginRes.ok) {
      console.error("Login failed:", loginData);
      return;
    }

    const token = loginData.access_token;
    console.log("Access token:", token);

    // 2. Decode token thử (check payload và exp)
    try {
      const decoded = jwt.decode(token, { complete: true });
      console.log("Decoded token:", decoded);
    } catch (err) {
      console.log("Token decode failed:", err.message);
    }

    // 3. Fetch profile
    const profileRes = await fetch(`${API_BASE_URL}/auth/me`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      }
    });

    const profileData = await profileRes.json();
    console.log("Status:", profileRes.status);
    console.log("Profile response:", profileData);

  } catch (err) {
    console.error("Unexpected error:", err);
  }
};

testAuth();
