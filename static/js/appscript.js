// 🌍 Comprehensive list of countries and territories (recognized + unrecognized)
const countries = [
    // Africa
    "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi",
    "Cabo Verde", "Cameroon", "Central African Republic", "Chad", "Comoros",
    "Congo (Republic)", "Congo (Democratic Republic)", "Djibouti", "Egypt",
    "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Gambia",
    "Ghana", "Guinea", "Guinea-Bissau", "Ivory Coast", "Kenya", "Lesotho",
    "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania",
    "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria",
    "Rwanda", "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone",
    "Somalia", "Somaliland", "South Africa", "South Sudan", "Sudan", "Tanzania",
    "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe", "Western Sahara",
  
    // Asia
    "Afghanistan", "Armenia", "Azerbaijan", "Bahrain", "Bangladesh", "Bhutan",
    "Brunei", "Cambodia", "China", "East Timor", "Georgia", "India", "Indonesia",
    "Iran", "Iraq", "Israel", "Japan", "Jordan", "Kazakhstan", "Kuwait",
    "Kyrgyzstan", "Laos", "Lebanon", "Malaysia", "Maldives", "Mongolia",
    "Myanmar (Burma)", "Nepal", "North Korea", "Oman", "Pakistan", "Palestine",
    "Philippines", "Qatar", "Saudi Arabia", "Singapore", "South Korea", "Sri Lanka",
    "Syria", "Taiwan", "Tajikistan", "Thailand", "Turkey", "Turkmenistan",
    "United Arab Emirates", "Uzbekistan", "Vietnam", "Yemen",
  
    // Europe
    "Albania", "Andorra", "Austria", "Belarus", "Belgium", "Bosnia and Herzegovina",
    "Bulgaria", "Croatia", "Cyprus", "Czech Republic", "Denmark", "Estonia",
    "Finland", "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland",
    "Italy", "Kosovo", "Latvia", "Liechtenstein", "Lithuania", "Luxembourg",
    "Malta", "Moldova", "Monaco", "Montenegro", "Netherlands", "North Macedonia",
    "Norway", "Poland", "Portugal", "Romania", "Russia", "San Marino", "Serbia",
    "Slovakia", "Slovenia", "Spain", "Sweden", "Switzerland", "Ukraine",
    "United Kingdom", "Vatican City",
  
    // North America
    "Antigua and Barbuda", "Bahamas", "Barbados", "Belize", "Canada", "Costa Rica",
    "Cuba", "Dominica", "Dominican Republic", "El Salvador", "Grenada",
    "Guatemala", "Haiti", "Honduras", "Jamaica", "Mexico", "Nicaragua", "Panama",
    "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines",
    "Trinidad and Tobago", "United States", "Puerto Rico", "Greenland",
    "Bermuda",
  
    // South America
    "Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Ecuador", "Guyana",
    "Paraguay", "Peru", "Suriname", "Uruguay", "Venezuela", "French Guiana",
  
    // Oceania
    "Australia", "Fiji", "Kiribati", "Marshall Islands", "Micronesia",
    "Nauru", "New Zealand", "Palau", "Papua New Guinea", "Samoa",
    "Solomon Islands", "Tonga", "Tuvalu", "Vanuatu",
  
    // Territories and special regions
    "Hong Kong", "Macau", "Puerto Rico", "Greenland", "Faroe Islands",
    "Guam", "New Caledonia", "French Polynesia", "Cook Islands",
    "Niue", "Tokelau", "Montserrat", "Cayman Islands", "Aruba",
    "Curacao", "Sint Maarten", "Falkland Islands", "Gibraltar",
    "Isle of Man", "Jersey", "Guernsey"
  ];  

// Populate country dropdown
const cuisineSelect = document.getElementById("cuisine");

countries.forEach(country => {
  const option = document.createElement("option");
  option.value = country;
  option.textContent = country;
  cuisineSelect.appendChild(option);
});


const form = document.getElementById('food-form');
const resultDiv = document.getElementById('result');
const surpriseBtn = document.getElementById('surprise-btn');

function displayRecipe(data) {
    let linksHtml = "<ul>";
    if (data.recipe_links && data.recipe_links.length > 0) {
        data.recipe_links.forEach(l => {
            linksHtml += `<li><a href="${l.link}" target="_blank">${l.title}</a></li>`;
        });
    } else {
        linksHtml += "<li>No links available</li>";
    }
    linksHtml += "</ul>";

    resultDiv.innerHTML = `
        <div class="recipe-card">
            <h2>${data.food_name}</h2>
            <p><strong>Cuisine:</strong> ${data.cuisine}</p>
            <h3>Ingredients / Description:</h3>
            <p>${data.ingredients}</p>
            <h3>Recipe Links:</h3>
            ${linksHtml}
            <p><a href="${data.source_url}" target="_blank">View Main Source</a></p>
        </div>
    `;
}

function showLoader(message="Loading...") {
    resultDiv.innerHTML = `<div class="loader"></div><p>${message}</p>`;
}

// Form submit
form.addEventListener('submit', async (event) => {
    event.preventDefault();
    showLoader("Searching recipes...");

    const craving = document.getElementById('craving').value;
    const cuisine = document.getElementById('cuisine').value;
    const diet = document.getElementById('diet').value;
    const meal_type = document.getElementById('meal_type').value;

    const params = new URLSearchParams({ craving, cuisine, diet, meal_type });

    try {
        const response = await fetch(`/get_recipe?${params.toString()}`);
        const data = await response.json();

        if (response.ok) {
            displayRecipe(data);
        } else {
            resultDiv.innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
        }
    } catch (err) {
        resultDiv.innerHTML = `<p style="color:red;">Something went wrong: ${err.message}</p>`;
    }
});

// Surprise Me
surpriseBtn.addEventListener('click', async () => {
    showLoader("🌎 Fetching a random world dish...");

    const worldCuisines = ["Nigerian", "Kenyan", "Italian", "Japanese", "Thai"];
    const cravings = ["sweet", "salty", "spicy", "sweet-salty", "sweet-spicy"];
    const diets = ["vegetarian", "vegan", "eat-meat"];
    const meals = ["breakfast", "lunch", "dinner", "snack", "dessert"];

    const randomCuisine = worldCuisines[Math.floor(Math.random() * worldCuisines.length)];
    const randomCraving = cravings[Math.floor(Math.random() * cravings.length)];
    const randomDiet = diets[Math.floor(Math.random() * diets.length)];
    const randomMeal = meals[Math.floor(Math.random() * meals.length)];

    const params = new URLSearchParams({
        craving: randomCraving,
        cuisine: randomCuisine,
        diet: randomDiet,
        meal_type: randomMeal
    });

    try {
        const response = await fetch(`/get_recipe?${params.toString()}`);
        const data = await response.json();

        if (response.ok) {
            displayRecipe(data);
        } else {
            resultDiv.innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
        }
    } catch (err) {
        resultDiv.innerHTML = `<p style="color:red;">Something went wrong: ${err.message}</p>`;
    }
});
