const rulerBtn = document.getElementById("rulerBtn");
const sideRuler = document.getElementById("sideRuler");

if (rulerBtn && sideRuler) {
    rulerBtn.addEventListener("click", () => {
        sideRuler.classList.toggle("show-ruler");
        rulerBtn.classList.toggle("shifted");
    });
}

const inventoryWoItems = [
    "bed_frame",
    "mattress",
    "wardrobe_closet",
    "dresser",
    "desk",
    "chair",
    "hutch_light",
    "bookshelf",
    "bedroom_walls_ceiling",
    "bedroom_floor",
    "bedroom_window_screen_crank",
    "bedroom_blinds",
    "bedroom_light_cover_plate",
    "bedroom_phone_internet_outlets",
    "smoke_detector",
    "thermostat",
    "room_door_lock",
    "bedroom_wall_outside_room",

    "sofa",
    "overstuffed_chair",
    "living_walls_ceiling",
    "living_floor",
    "living_window_screen_crank",
    "living_blinds",
    "living_light_cover_plate",
    "living_phone_internet_outlets",
    "front_door_lock",
    "living_wall_outside_room",

    "mirror",
    "sink",
    "cabinet_drawers",
    "shelves",
    "towel_racks",
    "tub_shower_curtain",
    "bathroom_walls_ceiling",
    "bathroom_floor",
    "light_fan",
    "bathroom_outlets",
    "bathroom_wall_outside_room"
];

// ---- Residence-hall (traditional dorm) form ----------------------------------
// One section, no Qty column, walls split into Left/Right/Front/Back plus
// separate Ceiling/Floor. Keys are prefixed rh_ so the two forms' data never
// collide. Used by the dorms in RH_DORMS below.
const rhItems = [
    ["Bed Frame", "rh_bed_frame"],
    ["Mattress", "rh_mattress"],
    ["Wardrobe/Closet", "rh_wardrobe_closet"],
    ["Dresser", "rh_dresser"],
    ["Desk", "rh_desk"],
    ["Chair", "rh_chair"],
    ["Hutch (with Light)", "rh_hutch_light"],
    ["Bookshelf", "rh_bookshelf"],
    ["Walls: Left", "rh_walls_left"],
    ["Walls: Right", "rh_walls_right"],
    ["Walls: Front", "rh_walls_front"],
    ["Walls: Back", "rh_walls_back"],
    ["Ceiling", "rh_ceiling"],
    ["Floor", "rh_floor"],
    ["Window/Screen/Crank", "rh_window_screen_crank"],
    ["Blinds", "rh_blinds"],
    ["Light/Cover Plate", "rh_light_cover_plate"],
    ["Phone/Internet/Outlets", "rh_phone_internet_outlets"],
    ["Smoke Detector", "rh_smoke_detector"],
    ["Thermostat", "rh_thermostat"],
    ["Room Door/Lock", "rh_room_door_lock"],
    ["Wall Outside Room", "rh_wall_outside_room"],
];
const rhItemKeys = rhItems.map(pair => pair[1]);

// Dorms that use the residence-hall form; everything else uses the apartment form.
const RH_DORMS = ["Arend", "Baldwin-Jenkins", "Ballard", "Village", "McMillan", "Warren"];

// Current form type ("apartment" | "residence_hall"), driven by the chosen dorm
// or by a previously saved form.
let currentFormType = "apartment";

function formTypeForDorm(dorm) {
    return RH_DORMS.includes(dorm) ? "residence_hall" : "apartment";
}

// The active item-key set for whichever form is showing.
function activeItems() {
    return currentFormType === "residence_hall" ? rhItemKeys : inventoryWoItems;
}

// Show the correct table for the given form type and remember it.
function setFormType(type) {
    currentFormType = type;
    const apt = document.getElementById("apartmentInventory");
    const rh = document.getElementById("rhInventory");
    if (apt) apt.style.display = (type === "residence_hall") ? "none" : "";
    if (rh) rh.style.display = (type === "residence_hall") ? "" : "none";
}

// Build the residence-hall table (Item | Check-In | W.O. | Check-Out | W.O.),
// no Qty column. Every item and condition column is required; the work order
// columns are optional and default to "No".
function buildResidenceHallTable() {
    const container = document.getElementById("rhInventory");
    if (!container || container.dataset.built === "1") return;

    const woOptions = `
        <option value="No" selected>No</option>
        <option value="Yes">Yes</option>`;

    let rows = "";
    rhItems.forEach(([label, key]) => {
        rows += `
            <tr>
              <td>${label} <span class="req-star">*</span></td>
              <td><input type="text" id="${key}_checkin" /></td>
              <td><select class="wo-select" id="${key}_wo_checkin">${woOptions}</select></td>
              <td><input type="text" id="${key}_checkout" /></td>
              <td><select class="wo-select" id="${key}_wo_checkout">${woOptions}</select></td>
            </tr>`;
    });

    container.innerHTML = `
        <table class="inventory-table">
          <thead>
            <tr>
              <th>Item</th>
              <th>Check-In (Move-In) <span class="req-star">*</span></th>
              <th>Work Order<span class="wo-note">Items that are unusable or unsafe will be repaired/replaced. However, items with minor damage will be addressed as time permits.</span></th>
              <th>Check-Out (Move-Out) <span class="req-star">*</span></th>
              <th>Work Order<span class="wo-note">Items that are unusable or unsafe will be repaired/replaced. However, items with minor damage will be addressed as time permits.</span></th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>`;

    container.dataset.built = "1";
}

// ---- Who this page is acting for, and in what capacity -----------------------
// Students always work on their own form and only ever perform the check-in.
// The check-out is a move-out inspection done by an RA/AC together with the
// student, so an admin opens a specific student's form via ?student=<email>.
//
// IMPORTANT: this is a UI-level control ONLY. The backend does not authenticate
// requests, so this decides what the page offers, not what the server permits.
// It is a workflow guide, not access enforcement. See the auth follow-up.
const requestedStudent = new URLSearchParams(window.location.search).get("student");
const viewerRole = localStorage.getItem("role") || "student";

// Admin check-out mode: an admin viewing someone else's form.
const adminMode = Boolean(requestedStudent) && viewerRole === "admin";

// The student whose form this page loads, saves, and generates a PDF for.
const targetStudent = adminMode ? requestedStudent : localStorage.getItem("sign_in_id");

document.addEventListener("DOMContentLoaded", async () => {
    const signInId = targetStudent;

    if (!signInId) {
        alert("No student ID found. Please log in first.");
        window.location.href = "index.html";
        return;
    }

    // A non-admin can't open someone else's form, even by editing the URL.
    if (requestedStudent && !adminMode) {
        alert("Only an RA or AC can open another student's form.");
        window.location.href = "room-inventory.html";
        return;
    }

    const studentIdField = document.getElementById("studentID");
    if (studentIdField) {
        studentIdField.value = signInId;
        studentIdField.readOnly = true;
    }

    // In check-out mode the RA/AC arrived from the dashboard queue, so give
    // them a way back and make it obvious whose form this is.
    if (adminMode) {
        const title = document.querySelector(".page-title");
        if (title) title.textContent = `Check-Out Inspection — ${signInId}`;

        const topBar = document.querySelector(".top-bar");
        if (topBar) {
            const back = document.createElement("a");
            back.href = "admin-dashboard.html";
            back.className = "admin-back-link";
            back.textContent = "← Back to dashboard";
            topBar.insertAdjacentElement("afterbegin", back);
        }
    }

    buildResidenceHallTable();
    addQtyInputIds();
    addCheckInWorkOrderDropdowns();
    setupWorkOrderPhotoInputs();

    // Switch the visible form when the student picks a dorm (fresh forms only —
    // a saved form's type is fixed and re-applied in loadBacklogForm).
    const dormSelect = document.getElementById("dorm");
    if (dormSelect) {
        dormSelect.addEventListener("change", () => {
            setFormType(formTypeForDorm(dormSelect.value));
        });
    }

    const formData = await loadBacklogForm(signInId);
    let status = formData?.form_status || "draft";

    // An admin should only ever arrive here from the check-out queue, i.e. for a
    // student who has already checked in. Anything else is a bad link.
    if (adminMode && !formData) {
        alert(`${signInId} has not submitted a check-in form yet.`);
        window.location.href = "admin-dashboard.html";
        return;
    }

    // Apply the correct form type: a saved form dictates it; otherwise follow
    // the currently selected dorm (defaults to apartment).
    if (formData && formData.form_type) {
        setFormType(formData.form_type);
    } else {
        setFormType(formTypeForDorm(dormSelect ? dormSelect.value : ""));
    }

    applyFormLocking(status);
    updateModeLabel(status);
    updateInstructions(status);
    updateButton(status);

    const form = document.querySelector(".work-order-form");

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            // Block early on missing fields so we don't ask for confirmation first.
            if (!validateBeforeSubmit(status)) return;

            let confirmMsg = "";

            if (status === "draft") {
                confirmMsg = "Submit Check-In? You won't be able to edit it.";
            } else if (status === "checked-in") {
                confirmMsg = "Submit Check-Out and finish form?";
            }

            if (!confirm(confirmMsg)) return;

            status = await handleFormSubmit(status);

            applyFormLocking(status);
            updateModeLabel(status);
            updateInstructions(status);
            updateButton(status);
        });
    }
});

// The Qty box is the 2nd cell of each item row and ships without an id in the
// static HTML. Give it a stable id ({item}_qty) and make it a non-negative
// number input so it can be read, validated, saved, and reloaded.
function addQtyInputIds() {
    inventoryWoItems.forEach(item => {
        const checkinInput = document.getElementById(`${item}_checkin`);
        if (!checkinInput) return;

        const mainRow = checkinInput.closest("tr");
        if (!mainRow) return;

        const cells = mainRow.querySelectorAll("td");
        if (cells.length < 6) return;

        const qtyInput = cells[1].querySelector("input");
        if (!qtyInput || document.getElementById(`${item}_qty`)) return;

        qtyInput.id = `${item}_qty`;
        qtyInput.type = "number";
        qtyInput.min = "0";
        qtyInput.step = "1";
    });
}

function addCheckInWorkOrderDropdowns() {
    inventoryWoItems.forEach(item => {
        const checkinInput = document.getElementById(`${item}_checkin`);
        if (!checkinInput) return;

        const mainRow = checkinInput.closest("tr");
        if (!mainRow) return;

        const cells = mainRow.querySelectorAll("td");
        if (cells.length < 6) return;

        const checkInWoCell = cells[3];

        if (!document.getElementById(`${item}_wo_checkin`)) {
            checkInWoCell.innerHTML = `
                <select class="wo-select" id="${item}_wo_checkin">
                    <option value="No" selected>No</option>
                    <option value="Yes">Yes</option>
                </select>
            `;
        }

        if (!document.getElementById(`${item}_checkin_image_row`)) {
            const imageRow = document.createElement("tr");
            imageRow.className = "wo-image-row";
            imageRow.id = `${item}_checkin_image_row`;
            imageRow.style.display = "none";

            imageRow.innerHTML = `
                <td colspan="6">
                    <span class="wo-image-label">Attach check-in photo(s):</span>
                    <input type="file" accept="image/*" multiple id="${item}_wo_checkin_images" />
                    <div class="wo-image-preview" id="${item}_wo_checkin_preview"></div>
                </td>
            `;

            mainRow.insertAdjacentElement("afterend", imageRow);
        }
    });
}

function setupWorkOrderPhotoInputs() {
    inventoryWoItems.forEach(item => {
        setupSingleWorkOrderPhotoInput(item, "checkin");
        setupSingleWorkOrderPhotoInput(item, "checkout");
    });
}

function setupSingleWorkOrderPhotoInput(item, mode) {
    const select = document.getElementById(`${item}_wo_${mode}`);
    const imageRow =
        document.getElementById(`${item}_${mode}_image_row`) ||
        document.getElementById(`${item}_image_row`);

    const fileInput =
        document.getElementById(`${item}_wo_${mode}_images`) ||
        document.getElementById(`${item}_wo_images`);

    const preview =
        document.getElementById(`${item}_wo_${mode}_preview`) ||
        document.getElementById(`${item}_wo_preview`);

    if (!select || !imageRow || !fileInput || !preview) return;

    select.addEventListener("change", () => {
        if (select.value === "Yes") {
            imageRow.style.display = "";
        } else {
            imageRow.style.display = "none";
            fileInput.value = "";
            preview.innerHTML = "";
        }
    });

    fileInput.addEventListener("change", () => {
        preview.innerHTML = "";

        Array.from(fileInput.files).forEach(file => {
            if (!file.type.startsWith("image/")) return;

            const photoBox = document.createElement("div");
            photoBox.className = "photo-upload-box";

            const img = document.createElement("img");
            img.src = URL.createObjectURL(file);
            img.className = "photo-preview-img";

            const measurementLabel = document.createElement("label");
            measurementLabel.className = "form-label";
            measurementLabel.textContent = "Add measurements for this photo?";

            const measurementSelect = document.createElement("select");
            measurementSelect.className = "form-input measurement-choice";
            measurementSelect.innerHTML = `
                <option value="">Select an option</option>
                <option value="yes">Yes</option>
                <option value="no">No</option>
            `;

            const measurementFields = document.createElement("div");
            measurementFields.className = "measurement-fields";
            measurementFields.style.display = "none";

            measurementFields.innerHTML = `
                <label class="form-label">Length (inches)</label>
                <input type="number" class="form-input photo-length" step="0.01" placeholder="Example: 3.5">

                <label class="form-label">Width (inches)</label>
                <input type="number" class="form-input photo-width" step="0.01" placeholder="Example: 2">
            `;

            measurementSelect.addEventListener("change", () => {
                measurementFields.style.display = measurementSelect.value === "yes" ? "block" : "none";
            });

            photoBox.appendChild(img);
            photoBox.appendChild(measurementLabel);
            photoBox.appendChild(measurementSelect);
            photoBox.appendChild(measurementFields);

            preview.appendChild(photoBox);
        });
    });
}

async function uploadWorkOrderPhotos(signInId) {
    const formData = new FormData();
    let hasPhotos = false;

    inventoryWoItems.forEach(item => {
        addPhotosToFormData(formData, item, "checkin");
        addPhotosToFormData(formData, item, "checkout");
    });

    for (const pair of formData.entries()) {
        if (pair[0] === "photos") {
            hasPhotos = true;
        }
    }

    if (!hasPhotos) return;

    try {
        const res = await fetch(`http://localhost:5001/upload_photos/${encodeURIComponent(signInId)}`, {
            method: "POST",
            body: formData
        });

        const data = await res.json();

        if (data.status !== "success") {
            alert("Form saved, but photos did not upload: " + data.message);
        }
    } catch (err) {
        console.error(err);
        alert("Form saved, but photo upload failed.");
    }
}

function addPhotosToFormData(formData, item, mode) {
    const fileInput =
        document.getElementById(`${item}_wo_${mode}_images`) ||
        document.getElementById(`${item}_wo_images`);

    const preview =
        document.getElementById(`${item}_wo_${mode}_preview`) ||
        document.getElementById(`${item}_wo_preview`);

    if (!fileInput || !preview || !fileInput.files) return;

    Array.from(fileInput.files).forEach((file, index) => {
        if (!file.type.startsWith("image/")) return;

        const renamedFile = new File([file], `${item}_${mode}_${file.name}`, { type: file.type });
        formData.append("photos", renamedFile);

        const photoBoxes = preview.querySelectorAll(".photo-upload-box");
        const box = photoBoxes[index];

        let length = "";
        let width = "";

        if (box) {
            const lengthInput = box.querySelector(".photo-length");
            const widthInput = box.querySelector(".photo-width");

            if (lengthInput) length = lengthInput.value;
            if (widthInput) width = widthInput.value;
        }

        formData.append("lengths", length);
        formData.append("widths", width);
    });
}

async function loadBacklogForm(signInId) {
    try {
        const response = await fetch(`http://localhost:5001/get_backlog_form/${encodeURIComponent(signInId)}`);
        const data = await response.json();

        if (data.status !== "success" || !data.form) return null;

        const form = data.form;

        setValue("studentID", form.student_id || signInId);
        setValue("studentName", form.student_name);
        setValue("dorm", form.dorm);
        setValue("roomNumber", form.room_number);

        if (form.present === true) setValue("present", "Yes");
        else if (form.present === false) setValue("present", "No");
        else setValue("present", "");

        setValue("formCompletionDate", form.completion_date);
        setValue("checkoutDate", form.checkout_date);

        // Populate whichever item set this saved form used.
        const isRH = form.form_type === "residence_hall";
        const items = isRH ? rhItemKeys : inventoryWoItems;

        items.forEach(item => {
            if (!isRH) setValue(`${item}_qty`, form[`${item}_qty`]);
            setValue(`${item}_checkin`, form[`${item}_checkin`]);
            setValue(`${item}_checkout`, form[`${item}_checkout`]);
            // Work orders default to "No", so a blank/missing saved value falls
            // back to "No" rather than leaving the dropdown showing nothing.
            setValue(`${item}_wo_checkin`, form[`${item}_wo_checkin`] || "No");
            setValue(`${item}_wo_checkout`, form[`${item}_wo_checkout`] || "No");

            // The apartment form has work-order photo rows; the residence-hall form does not.
            if (!isRH) {
                if (form[`${item}_wo_checkin`] === "Yes") {
                    const row = document.getElementById(`${item}_checkin_image_row`);
                    if (row) row.style.display = "";
                }
                if (form[`${item}_wo_checkout`] === "Yes") {
                    const row = document.getElementById(`${item}_image_row`);
                    if (row) row.style.display = "";
                }
            }
        });

        return form;
    } catch (err) {
        console.error(err);
        return null;
    }
}

function applyFormLocking(status) {
    const checkIn = document.querySelectorAll("[id$='_checkin']");
    const checkOut = document.querySelectorAll("[id$='_checkout']");
    const qtyInputs = document.querySelectorAll("[id$='_qty']");
    const woDropdowns = document.querySelectorAll(".wo-select");
    const woFileInputs = document.querySelectorAll(".wo-image-row input[type='file']");

    // Check-in belongs to the student; check-out is the RA/AC move-out
    // inspection, so those columns only open in admin mode.
    const canEditCheckIn  = (status === "draft")      && !adminMode;
    const canEditCheckOut = (status === "checked-in") && adminMode;

    // Qty is a check-in field: editable during check-in, locked after.
    qtyInputs.forEach(i => i.disabled = !canEditCheckIn);

    const topFields = ["studentName", "present", "dorm", "subDorm", "houseName", "roomNumber", "formCompletionDate"];

    topFields.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = !canEditCheckIn;
    });

    // The Check-Out date is part of the inspection, so it follows the check-out
    // columns: editable only by an RA/AC, and only while the form is checked in.
    const checkoutDateEl = document.getElementById("checkoutDate");
    if (checkoutDateEl) checkoutDateEl.disabled = !canEditCheckOut;

    if (canEditCheckIn) {
        checkIn.forEach(i => i.disabled = false);
        checkOut.forEach(i => i.disabled = true);

        woDropdowns.forEach(s => {
            s.disabled = !s.id.endsWith("_wo_checkin");
        });

        woFileInputs.forEach(f => {
            f.disabled = !f.id.includes("_wo_checkin_images");
        });
    } else if (canEditCheckOut) {
        checkIn.forEach(i => i.disabled = true);
        checkOut.forEach(i => i.disabled = false);

        woDropdowns.forEach(s => {
            s.disabled = !s.id.endsWith("_wo_checkout");
        });

        woFileInputs.forEach(f => {
            f.disabled = f.id.includes("_wo_checkin_images");
        });

        inventoryWoItems.forEach(item => {
            const checkinRow = document.getElementById(`${item}_checkin_image_row`);

            if (checkinRow) {
                checkinRow.style.display = "none";
            }
        });

        inventoryWoItems.forEach(item => {
            const checkoutSelect = document.getElementById(`${item}_wo_checkout`);
            const checkoutRow = document.getElementById(`${item}_image_row`);

            if (!checkoutSelect || !checkoutRow) return;

            if (checkoutSelect.value === "Yes") {
                checkoutRow.style.display = "";
            } else {
                checkoutRow.style.display = "none";
            }
        });
    } else {
        [...checkIn, ...checkOut].forEach(i => i.disabled = true);
        woDropdowns.forEach(s => s.disabled = true);
        woFileInputs.forEach(f => f.disabled = true);
    }
}

function updateModeLabel(status) {
    const el = document.getElementById("formModeLabel");
    if (!el) return;

    el.className = "mode-banner";

    if (status === "draft") {
        el.textContent = "CHECK-IN MODE";
        el.classList.add("mode-checkin");
    } else if (status === "checked-in" && adminMode) {
        el.textContent = "CHECK-OUT INSPECTION";
        el.classList.add("mode-checkout");
    } else if (status === "checked-in") {
        el.textContent = "AWAITING CHECK-OUT INSPECTION";
        el.classList.add("mode-checkout");
    } else {
        el.textContent = "FORM COMPLETED";
        el.classList.add("mode-complete");
    }
}

function updateInstructions(status) {
    const el = document.getElementById("formInstructions");
    if (!el) return;

    if (status === "draft") {
        el.textContent = "Fill the Check-In column. Add check-in work order photos if needed.";
    } else if (status === "checked-in" && adminMode) {
        el.textContent =
            `Check-out inspection for ${targetStudent}. Walk the room with the student, ` +
            `fill the Check-Out column, and add check-out work order photos if needed.`;
    } else if (status === "checked-in") {
        el.textContent =
            "Check-In submitted and locked. Your check-out is completed in person with " +
            "your RA or AC — they will fill in the Check-Out column with you.";
    } else {
        el.textContent = "Form is complete.";
    }
}

function updateButton(status) {
    const btn = document.querySelector(".submit-btn");
    if (!btn) return;

    // Students submit the check-in; only an RA/AC can complete the check-out.
    if (status === "draft" && !adminMode) {
        btn.textContent = "Submit Check-In";
        btn.style.display = "";
    } else if (status === "checked-in" && adminMode) {
        btn.textContent = "Complete Check-Out";
        btn.style.display = "";
    } else {
        btn.style.display = "none";
    }
}

// Clear any previous "missing field" highlights.
function clearFieldErrors() {
    document.querySelectorAll(".field-error").forEach(el => el.classList.remove("field-error"));
}

// Mark a field as missing, scroll to the first one, and focus it.
function flagMissing(fields) {
    fields.forEach(el => el && el.classList.add("field-error"));
    const first = fields.find(el => el);
    if (first) {
        first.scrollIntoView({ behavior: "smooth", block: "center" });
        try { first.focus({ preventScroll: true }); } catch (e) {}
    }
}

// Mode-aware required-field check. Returns true if OK to submit; otherwise
// highlights the offending fields, scrolls to the first, alerts, and returns false.
function validateBeforeSubmit(currentStatus) {
    clearFieldErrors();
    const missing = [];

    // Only the visible form's items are validated (apartment has Qty, the
    // residence-hall form does not).
    const items = activeItems();
    const hasQty = (currentFormType !== "residence_hall");

    if (currentStatus === "draft") {
        // Top-of-form fields.
        ["studentName", "present", "dorm", "roomNumber", "formCompletionDate"].forEach(id => {
            const el = document.getElementById(id);
            if (el && el.value.trim() === "") missing.push(el);
        });

        // Every item needs (qty >= 0 for apartment), a check-in condition, and a work order choice.
        items.forEach(item => {
            if (hasQty) {
                const qty = document.getElementById(`${item}_qty`);
                if (qty && (qty.value.trim() === "" || Number(qty.value) < 0 || !Number.isInteger(Number(qty.value)))) {
                    missing.push(qty);
                }
            }
            const cond = document.getElementById(`${item}_checkin`);
            if (cond && cond.value.trim() === "") missing.push(cond);
            // Work order is optional and defaults to "No".
        });
    } else if (currentStatus === "checked-in") {
        // Check-out phase: the Check-Out date is required...
        const checkoutDateEl = document.getElementById("checkoutDate");
        if (checkoutDateEl && checkoutDateEl.value.trim() === "") missing.push(checkoutDateEl);

        // ...and every item needs a check-out condition. The work order is
        // optional and defaults to "No".
        items.forEach(item => {
            const cond = document.getElementById(`${item}_checkout`);
            if (cond && cond.value.trim() === "") missing.push(cond);
        });
    }

    if (missing.length > 0) {
        flagMissing(missing);
        alert(`Please complete all required fields before submitting. ${missing.length} field(s) still need attention (highlighted in red).`);
        return false;
    }
    return true;
}

async function handleFormSubmit(currentStatus) {
    const signInId = targetStudent;

    if (!validateBeforeSubmit(currentStatus)) {
        return currentStatus;
    }

    // Normalize a yyyy-mm-dd date field to an ISO date string, or "" if empty.
    function formatDate(id) {
        const raw = getValue(id);
        if (!raw) return "";
        const d = new Date(raw);
        if (isNaN(d)) return null;   // signals invalid
        return d.toISOString().split("T")[0];
    }

    const formattedDate = formatDate("formCompletionDate");
    const formattedCheckoutDate = formatDate("checkoutDate");
    if (formattedDate === null || formattedCheckoutDate === null) {
        alert("Enter a valid date (YYYY-MM-DD)");
        return currentStatus;
    }

    let nextStatus = currentStatus;
    if (currentStatus === "draft") nextStatus = "checked-in";
    else if (currentStatus === "checked-in") nextStatus = "checked-out";

    const payload = {
        sign_in_id: signInId,
        student_name: getValue("studentName"),
        present: getValue("present"),
        dorm: getValue("dorm"),
        room_number: getValue("roomNumber"),
        completion_date: formattedDate,
        checkout_date: formattedCheckoutDate,
        form_type: currentFormType,
        form_status: nextStatus
    };

    activeItems().forEach(item => {
        if (currentFormType !== "residence_hall") {
            payload[`${item}_qty`] = getValue(`${item}_qty`);
        }
        payload[`${item}_checkin`] = getValue(`${item}_checkin`);
        payload[`${item}_wo_checkin`] = getValue(`${item}_wo_checkin`);
        payload[`${item}_checkout`] = getValue(`${item}_checkout`);
        payload[`${item}_wo_checkout`] = getValue(`${item}_wo_checkout`);
    });

    try {
        const res = await fetch("http://localhost:5001/save_backlog_form", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (data.status === "success") {
            await uploadWorkOrderPhotos(signInId);
            await fetch(`http://localhost:5001/generate_pdf/${encodeURIComponent(signInId)}`);

            alert("Saved!");
            return nextStatus;
        } else {
            alert("Error: " + data.message);
        }
    } catch (err) {
        console.error(err);
        alert("Network error — check the console.");
    }

    return currentStatus;
}

function getValue(id) {
    const el = document.getElementById(id);
    return el ? el.value.trim() : "";
}

function setValue(id, val) {
    const el = document.getElementById(id);
    // Use == null so a numeric 0 (e.g. a qty of zero) is preserved, not blanked.
    if (el) el.value = (val == null) ? "" : val;
}