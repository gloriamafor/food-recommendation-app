const form = document.getElementById('food-form');
const resultDiv = document.getElementById('result');

form.addEventListener('submit', async (event) => {
    event.preventDefault();  // Ensure form doesn't submit traditionally
    resultDiv.innerHTML = 'Loading...';

    const cuisine = document.getElementById('cuisine').value;
    const meal_type = document.getElementById('meal_type').value;
    const diet = document.getElementById('diet').value;

    const params = new URLSearchParams();
    if (cuisine) params.append('cuisine', cuisine);
    if (meal_type) params.append('meal_type', meal_type);
    if (diet) params.append('diet', diet);

    try {
        const response = await fetch(`/?${params.toString()}`, {
            method: 'GET'  // Explicitly set GET to match the route
        });
        const data = await response.json();

        if (response.ok) {
            resultDiv.innerHTML = `
                <div class="recipe-card">
                    <h2>${data.title}</h2>
                    <img src="${data.image}" alt="${data.title}" style="max-width: 300px;" />
                    <p><strong>Instructions:</strong></p>
                    <p>${data.instructions}</p>
                    <p><a href="${data.sourceUrl}" target="_blank">View Full Recipe</a></p>
                </div>
            `;
        } else {
            resultDiv.innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
        }
    } catch (err) {
        resultDiv.innerHTML = `<p style="color:red;">Something went wrong: ${err.message}</p>`;
    }
});