// ======================= 🌍 COUNTRY DROPDOWN =======================
const countrySelect = document.getElementById("cuisine");
const countries = [
  "Afghanistan","Albania","Algeria","Andorra","Angola","Antigua and Barbuda",
  "Argentina","Armenia","Australia","Austria","Azerbaijan","Bahamas","Bahrain",
  "Bangladesh","Barbados","Belarus","Belgium","Belize","Benin","Bhutan","Bolivia",
  "Bosnia and Herzegovina","Botswana","Brazil","Brunei","Bulgaria","Burkina Faso",
  "Burundi","Cambodia","Cameroon","Canada","Cape Verde","Central African Republic",
  "Chad","Chile","China","Colombia","Comoros","Congo","Costa Rica","Croatia",
  "Cuba","Cyprus","Czech Republic","Denmark","Djibouti","Dominica","Dominican Republic",
  "Ecuador","Egypt","El Salvador","Equatorial Guinea","Eritrea","Estonia","Eswatini",
  "Ethiopia","Fiji","Finland","France","Gabon","Gambia","Georgia","Germany","Ghana",
  "Greece","Grenada","Guatemala","Guinea","Guinea-Bissau","Guyana","Haiti","Honduras",
  "Hungary","Iceland","India","Indonesia","Iran","Iraq","Ireland","Israel","Italy",
  "Ivory Coast","Jamaica","Japan","Jordan","Kazakhstan","Kenya","Kiribati","Kuwait",
  "Kyrgyzstan","Laos","Latvia","Lebanon","Lesotho","Liberia","Libya","Liechtenstein",
  "Lithuania","Luxembourg","Madagascar","Malawi","Malaysia","Maldives","Mali","Malta",
  "Marshall Islands","Mauritania","Mauritius","Mexico","Micronesia","Moldova","Monaco",
  "Mongolia","Montenegro","Morocco","Mozambique","Myanmar","Namibia","Nauru","Nepal",
  "Netherlands","New Zealand","Nicaragua","Niger","Nigeria","North Korea",
  "North Macedonia","Norway","Oman","Pakistan","Palau","Palestine","Panama",
  "Papua New Guinea","Paraguay","Peru","Philippines","Poland","Portugal","Qatar",
  "Romania","Russia","Rwanda","Saint Kitts and Nevis","Saint Lucia",
  "Saint Vincent and the Grenadines","Samoa","San Marino","Sao Tome and Principe",
  "Saudi Arabia","Senegal","Serbia","Seychelles","Sierra Leone","Singapore","Slovakia",
  "Slovenia","Solomon Islands","Somalia","South Africa","South Korea","South Sudan",
  "Spain","Sri Lanka","Sudan","Suriname","Sweden","Switzerland","Syria","Taiwan",
  "Tajikistan","Tanzania","Thailand","Timor-Leste","Togo","Tonga","Trinidad and Tobago",
  "Tunisia","Turkey","Turkmenistan","Tuvalu","Uganda","Ukraine","United Arab Emirates",
  "United Kingdom","United States","Uruguay","Uzbekistan","Vanuatu","Vatican City",
  "Venezuela","Vietnam","Western Sahara","Yemen","Zambia","Zimbabwe","Kosovo",
  "Taiwan","Northern Cyprus","Western Sahara","South Ossetia","Abkhazia","Transnistria",
  "Somaliland","Nagorno-Karabakh"
];
countrySelect.innerHTML = '<option value="">Select...</option>';
countries.forEach(c => {
  const option = document.createElement("option");
  option.value = c;
  option.textContent = c;
  countrySelect.appendChild(option);
});

// ======================= 🥗 DIET DROPDOWN =======================
const dietSelect = document.getElementById("diet");
dietSelect.innerHTML = '<option value="">Select...</option>';
const diets = ["Vegetarian","Vegan","High Protein","Gluten Free"];
diets.forEach(d => dietSelect.appendChild(new Option(d,d)));

// ======================= 🍽️ MEAL TYPE DROPDOWN =======================
const mealTypeSelect = document.getElementById("meal_type");
mealTypeSelect.innerHTML = '<option value="">Select...</option>';
const mealTypes = ["Breakfast","Lunch","Snack","Dinner"];
mealTypes.forEach(m => mealTypeSelect.appendChild(new Option(m,m)));
const resultEl = document.getElementById("result");
const RESULT_LIMIT = 15;
let activeController = null;
let stopRequested = false;

function setResultMessage(message) {
  resultEl.innerHTML = `<div class="empty-state"><p>${message}</p></div>`;
}

// ======================= 💾 SAVE USER SELECTIONS =======================
function saveSelections() {
  localStorage.setItem("cuisine", countrySelect.value);
  localStorage.setItem("diet", dietSelect.value);
  localStorage.setItem("mealType", mealTypeSelect.value);
}

function restoreSelection(selectEl, storedValue) {
  if (!storedValue) {
    selectEl.value = "";
    return;
  }
  const hasOption = Array.from(selectEl.options).some(option => option.value === storedValue);
  selectEl.value = hasOption ? storedValue : "";
}

window.addEventListener("load", () => {
  restoreSelection(countrySelect, localStorage.getItem("cuisine"));
  restoreSelection(dietSelect, localStorage.getItem("diet"));
  restoreSelection(mealTypeSelect, localStorage.getItem("mealType"));
});

// ======================= 🍳 GET RECOMMENDATION & SURPRISE ME =======================
async function fetchRecipe(query) {
  try {
    stopRequested = false;
    if (activeController) {
      activeController.abort();
    }
    activeController = new AbortController();
    setResultMessage("Finding the tastiest options...");
    const params = new URLSearchParams(query);
    params.set("limit", RESULT_LIMIT);
    const response = await fetch(`/recommend?${params.toString()}`, {
      signal: activeController.signal,
    });
    const data = await response.json();

    if (!data || data.error) {
      setResultMessage(data.error || "No results found.");
      return;
    }

    if (stopRequested) {
      return;
    }

    // Clear previous results
    resultEl.innerHTML = "";

    data.forEach((recipe, index) => {
      const card = document.createElement("div");
      card.className = "recipe-card reveal";
      card.style.animationDelay = `${index * 0.08}s`;
      const cuisine = recipe.country || "Unknown";
      const imageMarkup = recipe.image
        ? `<img src="${recipe.image}" alt="${recipe.title} photo" loading="lazy">`
        : `<div class="image-fallback">No image available</div>`;
      card.innerHTML = `
        <div class="card-media">${imageMarkup}</div>
        <div class="card-header">
          <h3>${recipe.title}</h3>
          <span class="pill">${cuisine}</span>
        </div>
        <div class="card-section">
          <p class="card-label">Ingredients</p>
          <div class="card-text">${recipe.ingredients}</div>
        </div>
        <div class="card-section">
          <p class="card-label">Steps</p>
          <div class="card-text">${recipe.instructions}</div>
        </div>
        <a class="card-link" href="${recipe.sourceUrl}" target="_blank" rel="noopener">View Full Recipe</a>
      `;
      resultEl.appendChild(card);
    });
  } catch (err) {
    if (err && err.name === "AbortError") {
      return;
    }
    const message = err && err.message ? err.message : String(err);
    setResultMessage(`Something went wrong: ${message}`);
  }
}

document.getElementById("getRecommendation").addEventListener("click", () => {
  saveSelections();
  const craving = document.getElementById("craving").value;
  const country = countrySelect.value.trim();
  const diet = dietSelect.value.trim();
  const mealType = mealTypeSelect.value.trim();
  const parts = [craving, country, diet, mealType, "recipes"].filter(Boolean);
  const query = parts.join(" ");
  fetchRecipe({
    query,
    country,
    craving,
    diet,
    meal_type: mealType,
  });
});

document.getElementById("surpriseMe").addEventListener("click", () => {
  saveSelections();
  const randomCountry = countries[Math.floor(Math.random() * countries.length)];
  const randomMeal = mealTypes[Math.floor(Math.random() * mealTypes.length)];
  const randomDiet = diets[Math.floor(Math.random() * diets.length)];
  const randomCravingOptions = ["sweet", "salty", "spicy", "sweet-spicy"];
  const randomCraving = randomCravingOptions[Math.floor(Math.random() * randomCravingOptions.length)];
  const diet = randomDiet;
  const mealType = randomMeal;
  const parts = [randomCraving, randomCountry, diet, mealType, "recipes"].filter(Boolean);
  const query = parts.join(" ");
  fetchRecipe({
    query,
    country: randomCountry,
    craving: randomCraving,
    diet,
    meal_type: mealType,
  });
});

document.getElementById("stopResults").addEventListener("click", () => {
  stopRequested = true;
  if (activeController) {
    activeController.abort();
  }
  setResultMessage("Stopped. Adjust your filters and try again.");
});
