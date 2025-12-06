from flask import Flask, request, jsonify, render_template
from serpapi import GoogleSearch

app = Flask(__name__)

# Your SerpApi key
SERPAPI_KEY = "d25d0feb948aa9475e14d0448f63f536d1779638a33c920174176ef6a7919714"

# Homepage route
@app.route("/")
def home():
    return render_template("index.html")

# Recipe recommendation route
@app.route("/recommend")
def recommend():
    query = request.args.get("query", "")
    if not query:
        return jsonify({"error": "No query provided."}), 400

    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_KEY,
            "gl": "us",
            "hl": "en"
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        recipes = results.get("recipes_results") or []

        if not recipes:
            # fallback to first 3 organic results
            organic = results.get("organic_results") or []
            response_data = []
            for item in organic[:3]:
                link = item.get("link")
                title = item.get("title")
                if link and title:
                    response_data.append({
                        "title": title,
                        "image": item.get("thumbnail", ""),
                        "country": "Unknown",
                        "ingredients": "N/A",
                        "instructions": "N/A",
                        "sourceUrl": link
                    })
            if response_data:
                return jsonify(response_data)
            return jsonify({"error": "No recipes found."}), 404

        response_data = []
        for recipe in recipes[:3]:  # top 3 recipes
            title = recipe.get("title", "Unknown Dish")
            image = recipe.get("thumbnail", "")
            source_url = recipe.get("link", "")
            cuisine = recipe.get("cuisine", "Unknown")
            ingredients_list = recipe.get("ingredients") or []
            instructions_list = recipe.get("instructions") or []
            ingredients_html = "<ul>" + "".join(f"<li>{i}</li>" for i in ingredients_list) + "</ul>" if ingredients_list else "N/A"
            instructions_html = "<ol>" + "".join(f"<li>{s}</li>" for s in instructions_list) + "</ol>" if instructions_list else "N/A"

            response_data.append({
                "title": title,
                "image": image,
                "country": cuisine,
                "ingredients": ingredients_html,
                "instructions": instructions_html,
                "sourceUrl": source_url
            })

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

