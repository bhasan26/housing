// Salwa - login ui
function selectRole(button) {
    const buttons = document.querySelectorAll(".role-btn");
    buttons.forEach((btn) => btn.classList.remove("active"));
    button.classList.add("active");
}

async function login()  {
    const user = document.getElementById("user").value.trim();
    const password = document.getElementById("password").value.trim();
    const message = document.getElementById("message");
    const activeRole = document.querySelector(".role-btn.active").dataset.role;

    if (user === "" || password === "") {
        message.textContent = "Please enter Student ID / Email and password.";
        return;
    }

    // email with a whitworth.edu address is required for both roles
    if (!user.includes("@") || !user.endsWith("whitworth.edu")) {
        message.textContent = "Please use a valid whitworth.edu email address.";
        return;
    }

    try {
        const response = await fetch("http://localhost:5001/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                sign_in_id: user,
                password: password,
                role: activeRole
            })
        });

        const data = await response.json();

        if (data.status !== "success") {
            message.textContent = "Incorrect email, password, or role.";
            return;
        }

        // Save logged user for later pages
        localStorage.setItem("sign_in_id", user);
        localStorage.setItem("role", activeRole);

        message.textContent = `Login successful as ${activeRole}. Redirecting.!.`;
        // wait a second before second page to see response
        setTimeout(() => {
            window.location.href = activeRole === "student" ? "room-inventory.html" : "admin-dashboard.html";
        }, 900);

    } catch (error) {
        console.error("Login error:", error);
        message.textContent = "Could not connect to backend.";
    }
}

//Profile account drop down for student dashboard
function toggleDropdown() {
    const menu = document.getElementById("dropdown-menu");
    menu.style.display = menu.style.display === "block" ? "none" : "block";
}

/* close when clicking outside */
window.onclick = function(event) {
    const menu = document.getElementById("dropdown-menu");

    if (!event.target.closest('.account-wrapper')) {
        if (menu) menu.style.display = "none";
    }
};