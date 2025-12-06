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
const diets = ["No Preference","Balanced","High Protein","Low Fat","Low Carb","Keto","Vegan","Vegetarian","Pescatarian","Paleo","Gluten Free","Dairy Free","Halal","Kosher"];
dietSelect.innerHTML = '<option value="">Select...</option>';
diets.forEach(d => dietSelect.appendChild(new Option(d,d)));

// ======================= 🍽️ MEAL TYPE DROPDOWN =======================
const mealTypeSelect = document.getElementById("meal_type");
const mealTypes = ["No Preference","Breakfast","Brunch","Lunch","Snack","Dinner","Dessert","Drink","Appetizer","Side Dish","Soup","Salad","Main Course","Street Food","Traditional Dish","Fast Food"];
mealTypeSelect.innerHTML = '<option value="">Select...</option>';
mealTypes.forEach(m => mealTypeSelect.appendChild(new Option(m,m)));

// ======================= 💾 SAVE USER SELECTIONS =======================
function saveSelections() {
  localStorage.setItem("cuisine", countrySelect.value);
  localStorage.setItem("diet", dietSelect.value);
  localStorage.setItem("mealType", mealTypeSelect.value);
}

window.addEventListener("load", () => {
  if(localStorage.getItem("cuisine")) countrySelect.value = localStorage.getItem("cuisine");
  if(localStorage.getItem("diet")) dietSelect.value = localStorage.getItem("diet");
  if(localStorage.getItem("mealType")) mealTypeSelect.value = localStorage.getItem("mealType");
});

// ======================= 🍳 GET RECOMMENDATION & SURPRISE ME =======================
async function fetchRecipe(query) {
  try {
    const response = await fetch(`/recommend?query=${encodeURIComponent(query)}`);
    const data = await response.json();

    if (!data || data.error) {
      document.getElementById("result").innerHTML = `<p>${data.error || "No results found."}</p>`;
      return;
    }

    // Clear previous results
    document.getElementById("result").innerHTML = "";

    data.forEach(recipe => {
      const card = document.createElement("div");
      card.className = "recipe-card";
      card.innerHTML = `
        <h2>${recipe.title}</h2>
        ${recipe.image ? `<img src="${recipe.image}" alt="Food image">` : ""}
        <p><strong>Country:</strong> ${recipe.country || "Unknown"}</p>
        <p><strong>Ingredients:</strong><br>${recipe.ingredients}</p>
        <p><strong>Steps:</strong><br>${recipe.instructions}</p>
        <a href="${recipe.sourceUrl}" target="_blank">View Full Recipe</a>
      `;
      document.getElementById("result").appendChild(card);
    });
  } catch (err) {
    document.getElementById("result").innerHTML = `<p>Something went wrong: ${err}</p>`;
  }
}

document.getElementById("getRecommendation").addEventListener("click", () => {
  saveSelections();
  const query = `${document.getElementById("craving").value} ${countrySelect.value} ${dietSelect.value} ${mealTypeSelect.value} recipe`;
  fetchRecipe(query);
});

document.getElementById("surpriseMe").addEventListener("click", () => {
  saveSelections();
  const randomQuery = `popular ${countries[Math.floor(Math.random()*countries.length)]} ${mealTypes[Math.floor(Math.random()*mealTypes.length)]} ${diets[Math.floor(Math.random()*diets.length)]} recipe`;
  fetchRecipe(randomQuery);
});
