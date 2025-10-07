from flask import Flask, request, jsonify, render_template
from serpapi import GoogleSearch

app = Flask(__name__)
SERPAPI_KEY = "d25d0feb948aa9475e14d0448f63f536d1779638a33c920174176ef6a7919714"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_recipe", methods=["GET"])
def get_recipe():
    craving = request.args.get("craving", "")
    cuisine = request.args.get("cuisine", "")
    diet = request.args.get("diet", "")
    meal_type = request.args.get("meal_type", "")

    query = f"{craving} {cuisine} {diet} {meal_type} recipe"

    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        # Google search results
        search_results = results.get("organic_results", [])
        if not search_results:
            return jsonify({"error": "No recipes found for that query."}), 404

        # Process first 5 results for links
        links = []
        for r in search_results[:5]:
            title = r.get("title")
            link = r.get("link")
            if title and link:
                links.append({"title": title, "link": link})

        # Example: take first result for main food display
        first_result = search_results[0]
        food_name = first_result.get("title", "Unknown Recipe")
        source_url = first_result.get("link", "#")

        # You can optionally extract snippet info for ingredients
        snippet = first_result.get("snippet", "Ingredients not available.")

        return jsonify({
            "food_name": food_name,
            "cuisine": cuisine or "Unknown",
            "ingredients": snippet,
            "recipe_links": links,
            "source_url": source_url
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)