from flask import Flask, request, jsonify, render_template
import requests
import os

app = Flask(__name__)

API_KEY = '1a1544ab52194d4dbca2b74d7a7ad577'  # Replace with a valid key if expired
BASE_URL = 'https://api.spoonacular.com/recipes/complexSearch'

@app.route('/', methods=['GET', 'POST'])
def home_and_recommend():
    print("Rendering index.html from:", os.path.abspath("templates/index.html"))
    cuisine = request.args.get('cuisine') if request.method == 'GET' else request.form.get('cuisine')
    meal_type = request.args.get('meal_type') if request.method == 'GET' else request.form.get('meal_type')
    diet = request.args.get('diet') if request.method == 'GET' else request.form.get('diet')

    if not any([cuisine, meal_type, diet]):
        return render_template('index.html')

    params = {
        'apiKey': API_KEY,
        'cuisine': cuisine,
        'type': meal_type,
        'diet': diet,
        'number': 5,
        'addRecipeInformation': True
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        if data['results']:
            recipe = data['results'][0]
            recommendation = {
                'title': recipe['title'],
                'image': recipe['image'],
                'sourceUrl': recipe['sourceUrl'],
                'instructions': recipe.get('instructions', 'Instructions not available.')
            }
            return jsonify(recommendation)
        else:
            return jsonify({"error": "No recipes found for your input."}), 404
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)