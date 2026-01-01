from flask import Flask, request, jsonify, render_template
from serpapi import GoogleSearch
from bs4 import BeautifulSoup
import html
import json
import re
from urllib.parse import urljoin, urlparse
import requests

app = Flask(__name__)

# Your SerpApi key
SERPAPI_KEY = "d25d0feb948aa9475e14d0448f63f536d1779638a33c920174176ef6a7919714"

DEFAULT_LIMIT = 15
MIN_LIMIT = 5
MAX_LIMIT = 15
MAX_SOURCE_PAGES = 14
MAX_LIST_PAGES = 6
MAX_LINKS_PER_PAGE = 18
MAX_LIST_LINKS = 60
MAX_TOTAL_PAGES = 45
LIST_PAGE_MIN_RECIPES = 10

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

CRAVING_KEYWORDS = {
    "sweet": [
        "sweet",
        "sugar",
        "honey",
        "chocolate",
        "caramel",
        "vanilla",
        "dessert",
        "cake",
        "cookie",
        "brownie",
        "syrup",
        "frosting",
        "jam",
    ],
    "salty": [
        "salty",
        "salt",
        "soy sauce",
        "brine",
        "anchovy",
        "parmesan",
        "feta",
    ],
    "spicy": [
        "spicy",
        "chili",
        "chilli",
        "pepper",
        "cayenne",
        "jalapeno",
        "habanero",
        "sriracha",
        "hot sauce",
        "paprika",
        "harissa",
        "chipotle",
        "gochujang",
    ],
}

DIET_KEYWORDS = {
    "balanced": ["balanced"],
    "high protein": ["high protein", "protein", "lean"],
    "low fat": ["low fat", "light", "lean"],
    "low carb": ["low carb", "low-carb", "keto", "ketogenic"],
    "keto": ["keto", "ketogenic", "low carb", "low-carb"],
    "vegan": ["vegan", "plant-based", "plant based"],
    "vegetarian": ["vegetarian", "meatless", "veggie"],
    "pescatarian": ["pescatarian", "seafood", "fish", "salmon", "tuna", "shrimp"],
    "paleo": ["paleo", "palaeo"],
    "gluten free": ["gluten free", "gluten-free"],
    "dairy free": ["dairy free", "dairy-free", "lactose free"],
    "halal": ["halal"],
    "kosher": ["kosher"],
}

MEAL_KEYWORDS = {
    "breakfast": ["breakfast", "morning"],
    "brunch": ["brunch"],
    "lunch": ["lunch"],
    "snack": ["snack"],
    "dinner": ["dinner", "supper", "evening"],
    "dessert": ["dessert", "sweet", "cake", "cookie", "pudding", "ice cream"],
    "drink": ["drink", "beverage", "smoothie", "cocktail", "tea", "coffee", "juice"],
    "appetizer": ["appetizer", "starter"],
    "side dish": ["side dish", "side"],
    "soup": ["soup", "broth"],
    "salad": ["salad"],
    "main course": ["main course", "main dish", "entree"],
    "street food": ["street food"],
    "traditional dish": ["traditional", "classic", "heritage"],
    "fast food": ["fast food", "quick"],
}

COUNTRY_DISH_KEYWORDS = {
    "cameroon": ["ndole", "eru", "koki", "achu", "fufu", "okok", "njama njama", "plantain"],
    "ghana": ["jollof", "red red", "banku", "kelewele", "waakye", "kontomire", "light soup", "groundnut soup"],
    "nigeria": ["egusi", "suya", "pounded yam", "moi moi", "ofe", "pepper soup", "yam porridge"],
    "senegal": ["thieboudienne", "ceebu jen", "yassa", "maafe"],
    "ethiopia": ["injera", "doro wat", "kitfo", "shiro", "tibs"],
    "kenya": ["ugali", "nyama choma", "sukuma wiki", "githeri", "pilau"],
    "morocco": ["tagine", "couscous", "harira", "pastilla"],
    "south africa": ["bobotie", "biltong", "chakalaka", "pap", "boerewors"],
    "egypt": ["koshari", "ful medames", "molokhia", "taameya"],
    "tunisia": ["brik", "shakshuka", "harissa", "lablabi"],
}


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def clean_text(value):
    if not value:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    return str(value).strip()


def normalize_text_value(value):
    if not value:
        return ""
    if isinstance(value, list):
        parts = [clean_text(item) for item in value if clean_text(item)]
        return " ".join(parts)
    return clean_text(value)


def extract_url(value):
    if isinstance(value, dict):
        return value.get("url") or value.get("@id") or ""
    if isinstance(value, list):
        for item in value:
            url = extract_url(item)
            if url:
                return url
        return ""
    if isinstance(value, str):
        return value
    return ""


def normalize_cuisine(value):
    if isinstance(value, list):
        items = [clean_text(item) for item in value if clean_text(item)]
        return ", ".join(items)
    return clean_text(value)


def normalize_ingredients(value):
    if not value:
        return []
    if isinstance(value, list):
        items = value
    else:
        items = [value]
    return [clean_text(item) for item in items if clean_text(item)]


def normalize_instructions(value):
    steps = []

    def add_step(step):
        step = clean_text(step)
        if step:
            steps.append(step)

    def walk(item):
        if not item:
            return
        if isinstance(item, str):
            add_step(item)
        elif isinstance(item, dict):
            if "text" in item:
                add_step(item.get("text"))
            if "name" in item and len(item.keys()) <= 3:
                add_step(item.get("name"))
            if "itemListElement" in item:
                walk(item.get("itemListElement"))
            if "steps" in item:
                walk(item.get("steps"))
        elif isinstance(item, list):
            for sub in item:
                walk(sub)

    walk(value)
    return steps


def list_to_html(items, tag_name):
    safe_items = [html.escape(item) for item in items]
    return f"<{tag_name}>" + "".join(f"<li>{item}</li>" for item in safe_items) + f"</{tag_name}>"


def normalize_text(value):
    return clean_text(value).lower()


def normalize_filter_value(value):
    value = clean_text(value)
    if not value:
        return ""
    lowered = value.lower()
    if lowered in {"no preference", "select", "select..."}:
        return ""
    return value


def country_dish_keywords(country):
    key = normalize_text(country)
    if not key:
        return []
    key = re.sub(r"[^a-z0-9 ]+", "", key).strip()
    return COUNTRY_DISH_KEYWORDS.get(key, [])


def country_aliases(country):
    base = normalize_text(country)
    if not base:
        return []
    base_simple = re.sub(r"[^a-z0-9 ]+", "", base).strip()
    if not base_simple:
        return []

    aliases = set()
    aliases.add(base_simple)
    aliases.add(base_simple.replace(" ", ""))
    aliases.update(base_simple.split())

    if base_simple.endswith("y") and len(base_simple) > 1:
        aliases.add(base_simple[:-1] + "ian")
    if base_simple.endswith("o") and len(base_simple) > 1:
        aliases.add(base_simple[:-1] + "an")
        aliases.add(base_simple[:-1] + "ian")
    if base_simple.endswith("a") and len(base_simple) > 1:
        aliases.add(base_simple + "n")
        aliases.add(base_simple + "ian")
        aliases.add(base_simple[:-1] + "an")

    aliases.add(base_simple + "an")
    aliases.add(base_simple + "ian")
    aliases.add(base_simple + "ese")
    aliases.add(base_simple + "ish")

    irregular = {
        "united states": ["american", "usa", "u.s.", "u.s.a.", "us"],
        "united kingdom": ["british", "uk", "u.k.", "great britain", "england", "scotland", "wales"],
        "south korea": ["south korean", "korean", "korea"],
        "north korea": ["north korean", "korean", "korea"],
        "czech republic": ["czech"],
        "czechia": ["czech"],
        "ivory coast": ["ivorian", "cote divoire", "cote d ivoire", "cote d'ivoire"],
        "united arab emirates": ["emirati", "uae"],
        "germany": ["german"],
        "france": ["french"],
        "spain": ["spanish"],
        "portugal": ["portuguese"],
        "greece": ["greek"],
        "netherlands": ["dutch"],
        "sweden": ["swedish"],
        "norway": ["norwegian"],
        "finland": ["finnish"],
        "denmark": ["danish"],
        "poland": ["polish"],
        "ireland": ["irish"],
        "england": ["english"],
        "scotland": ["scottish"],
        "wales": ["welsh"],
        "turkey": ["turkish"],
        "switzerland": ["swiss"],
        "russia": ["russian"],
        "china": ["chinese"],
        "japan": ["japanese"],
        "israel": ["israeli"],
        "thailand": ["thai"],
        "mexico": ["mexican"],
        "brazil": ["brazilian"],
        "argentina": ["argentinian", "argentine"],
        "south africa": ["south african"],
    }

    if base_simple in irregular:
        aliases.update(irregular[base_simple])

    return [alias for alias in aliases if alias]


def text_matches_aliases(text, aliases):
    if not aliases:
        return True
    haystack = normalize_text(text)
    if not haystack:
        return False
    for alias in aliases:
        if len(alias) <= 2:
            if re.search(rf"\b{re.escape(alias)}\b", haystack):
                return True
        elif alias in haystack:
            return True
    return False


def recipe_matches_country(recipe, country):
    aliases = country_aliases(country)
    if not aliases:
        return True
    combined = " ".join(
        [
            recipe.get("title", ""),
            recipe.get("cuisine", ""),
            recipe.get("matchText", ""),
        ]
    )
    return text_matches_aliases(combined, aliases)


def keyword_matches(text, keywords):
    if not keywords:
        return True
    for keyword in keywords:
        if not keyword:
            continue
        needle = keyword.lower()
        if " " in needle:
            if needle in text:
                return True
        else:
            if re.search(rf"\b{re.escape(needle)}\b", text):
                return True
    return False


def craving_matches(text, craving):
    if not craving:
        return True
    craving_key = normalize_text(craving).replace("_", "-")
    if craving_key in {"sweet-salty", "sweet salty"}:
        return keyword_matches(text, CRAVING_KEYWORDS["sweet"]) and keyword_matches(text, CRAVING_KEYWORDS["salty"])
    if craving_key in {"sweet-spicy", "sweet spicy"}:
        return keyword_matches(text, CRAVING_KEYWORDS["sweet"]) and keyword_matches(text, CRAVING_KEYWORDS["spicy"])
    keywords = CRAVING_KEYWORDS.get(craving_key)
    if not keywords:
        return True
    return keyword_matches(text, keywords)


def diet_matches(text, diet):
    if not diet:
        return True
    diet_key = normalize_text(diet)
    keywords = DIET_KEYWORDS.get(diet_key)
    if not keywords:
        return True
    return keyword_matches(text, keywords)


def meal_matches(text, meal_type):
    if not meal_type:
        return True
    meal_key = normalize_text(meal_type)
    keywords = MEAL_KEYWORDS.get(meal_key)
    if not keywords:
        return True
    return keyword_matches(text, keywords)


def score_recipe(recipe, country, craving, diet, meal_type):
    text = normalize_text(recipe.get("matchText", ""))
    checks = []
    if craving:
        checks.append(craving_matches(text, craving))
    if diet:
        checks.append(diet_matches(text, diet))
    if meal_type:
        checks.append(meal_matches(text, meal_type))
    if not checks:
        dish_score = 1 if keyword_matches(text, country_dish_keywords(country)) else 0
        return True, 0, dish_score
    all_match = all(checks)
    score = sum(1 for match in checks if match)
    dish_score = 1 if keyword_matches(text, country_dish_keywords(country)) else 0
    return all_match, score, dish_score


def same_domain(url, base_url):
    try:
        base_domain = urlparse(base_url).netloc
        target_domain = urlparse(url).netloc
    except ValueError:
        return False
    if not base_domain or not target_domain:
        return False
    return target_domain == base_domain or target_domain.endswith(f".{base_domain}")


def extract_recipes_from_ld_json(data):
    recipes = []

    def walk(node):
        if isinstance(node, dict):
            node_type = node.get("@type")
            if node_type:
                types = node_type if isinstance(node_type, list) else [node_type]
                if any("recipe" in str(item).lower() for item in types):
                    recipes.append(node)
            for key in ("@graph", "graph", "itemListElement", "mainEntity", "mainEntityOfPage", "item", "items"):
                if key in node:
                    walk(node[key])
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return recipes


def parse_item_list_entry(item):
    if isinstance(item, dict):
        if "item" in item:
            nested = parse_item_list_entry(item.get("item"))
            if nested:
                return nested
        url = extract_url(item.get("url") or item.get("@id") or item.get("item"))
        title = clean_text(item.get("name") or item.get("headline") or item.get("title"))
        image = extract_url(item.get("image"))
        if url:
            return {"url": url, "title": title, "image": image}
    if isinstance(item, str):
        return {"url": item, "title": "", "image": ""}
    return None


def extract_item_list_entries(data):
    entries = []

    def walk(node):
        if isinstance(node, dict):
            node_type = node.get("@type")
            if node_type:
                types = node_type if isinstance(node_type, list) else [node_type]
                if any("itemlist" in str(item).lower() for item in types):
                    items = node.get("itemListElement") or node.get("itemList") or []
                    for item in items:
                        entry = parse_item_list_entry(item)
                        if entry and entry.get("url"):
                            entries.append(entry)
            if "itemListElement" in node and not node_type:
                for item in node.get("itemListElement") or []:
                    entry = parse_item_list_entry(item)
                    if entry and entry.get("url"):
                        entries.append(entry)
            for key in ("@graph", "graph", "itemListElement", "mainEntity", "mainEntityOfPage", "item", "items"):
                if key in node:
                    walk(node[key])
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return entries


def extract_candidate_links_from_html(soup, base_url, limit):
    links = []
    seen = set()

    for anchor in soup.select("a[href]"):
        if anchor.find_parent(["nav", "header", "footer"]):
            continue
        href = anchor.get("href", "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        full_url = urljoin(base_url, href)
        if full_url in seen:
            continue

        text = clean_text(anchor.get_text(" ", strip=True) or anchor.get("title") or anchor.get("aria-label"))
        class_blob = " ".join(anchor.get("class", []))
        parent = anchor.parent
        if parent:
            class_blob += " " + " ".join(parent.get("class", []))
        class_blob = class_blob.lower()

        img = anchor.find("img")
        img_url = ""
        if img:
            img_url = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""
            img_url = urljoin(base_url, img_url) if img_url else ""
            if not text:
                text = clean_text(img.get("alt"))

        is_recipeish = (
            "recipe" in href.lower()
            or "recipe" in text.lower()
            or "recipe" in class_blob
            or any(token in class_blob for token in ["card", "tile", "grid", "list"])
        )
        has_visual = img is not None

        if not is_recipeish and not has_visual:
            continue

        links.append({"url": full_url, "title": text, "image": img_url})
        seen.add(full_url)

        if len(links) >= limit:
            break

    return links


def fetch_page(url):
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=8,
        )
        response.raise_for_status()
        if "text/html" not in response.headers.get("content-type", ""):
            return ""
        return response.text
    except requests.RequestException:
        return ""


def extract_page_context(soup):
    parts = []
    if soup.title and soup.title.text:
        parts.append(clean_text(soup.title.text))
    meta_description_tag = soup.find("meta", attrs={"name": "description"})
    if meta_description_tag and meta_description_tag.get("content"):
        parts.append(clean_text(meta_description_tag.get("content")))
    og_description = soup.find("meta", property="og:description")
    if og_description and og_description.get("content"):
        parts.append(clean_text(og_description.get("content")))
    h1_tag = soup.find("h1")
    if h1_tag:
        parts.append(clean_text(h1_tag.get_text(" ", strip=True)))
    return " ".join(part for part in parts if part)


def extract_microdata_recipe(soup, base_url, fallback_title, fallback_image, meta_title, meta_image, match_text):
    root = soup.find(attrs={"itemtype": lambda value: value and "recipe" in value.lower()})
    scope = root if root else soup

    def prop_values(prop):
        values = []
        for tag in scope.select(f'[itemprop="{prop}"]'):
            if tag.name == "meta":
                value = clean_text(tag.get("content"))
            elif tag.name == "img":
                value = tag.get("src") or tag.get("data-src")
                value = clean_text(value)
            else:
                value = clean_text(tag.get_text(" ", strip=True))
            if value:
                values.append(value)
        return values

    title_candidates = prop_values("name") or prop_values("headline")
    title = title_candidates[0] if title_candidates else clean_text(meta_title or fallback_title)

    image_candidates = prop_values("image")
    image = ""
    for candidate in image_candidates:
        if candidate:
            image = candidate
            break
    if image:
        image = urljoin(base_url, image)
    else:
        fallback = meta_image or fallback_image or ""
        image = urljoin(base_url, fallback) if fallback else ""

    cuisine_values = prop_values("recipeCuisine")
    cuisine = ", ".join(cuisine_values) if cuisine_values else "Unknown"

    ingredients = prop_values("recipeIngredient") or prop_values("ingredients")
    instructions = []
    for tag in scope.select('[itemprop="recipeInstructions"]'):
        list_items = [clean_text(li.get_text(" ", strip=True)) for li in tag.select("li")]
        list_items = [item for item in list_items if item]
        if list_items:
            instructions.extend(list_items)
            continue
        text = clean_text(tag.get_text(" ", strip=True))
        if text:
            instructions.append(text)

    if not ingredients and not instructions:
        return None

    ingredients_text = " ".join(ingredients)
    instructions_text = " ".join(instructions)
    combined_match = " ".join([match_text, title, cuisine, ingredients_text, instructions_text]).strip()

    return {
        "title": title or "Unknown Dish",
        "image": image,
        "cuisine": cuisine,
        "ingredients": ingredients,
        "instructions": instructions,
        "sourceUrl": base_url,
        "matchText": combined_match,
    }


def parse_recipe_page(html_text, base_url, fallback_title, fallback_image):
    soup = BeautifulSoup(html_text, "html.parser")

    meta_title = ""
    meta_title_tag = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "title"})
    if meta_title_tag and meta_title_tag.get("content"):
        meta_title = clean_text(meta_title_tag.get("content"))
    elif soup.title and soup.title.text:
        meta_title = clean_text(soup.title.text)

    meta_description = ""
    meta_description_tag = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
    if meta_description_tag and meta_description_tag.get("content"):
        meta_description = clean_text(meta_description_tag.get("content"))

    meta_keywords = ""
    meta_keywords_tag = soup.find("meta", attrs={"name": "keywords"})
    if meta_keywords_tag and meta_keywords_tag.get("content"):
        meta_keywords = clean_text(meta_keywords_tag.get("content"))

    meta_image = ""
    meta_image_tag = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
    if meta_image_tag and meta_image_tag.get("content"):
        meta_image = meta_image_tag.get("content")

    h1_text = ""
    h1_tag = soup.find("h1")
    if h1_tag:
        h1_text = clean_text(h1_tag.get_text(" ", strip=True))

    match_text = " ".join([meta_title, meta_description, meta_keywords, h1_text]).strip()

    recipes = []
    item_list_entries = []

    for script in soup.select('script[type="application/ld+json"]'):
        content = script.string or script.get_text()
        if not content:
            continue
        content = content.strip()
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            continue
        recipes.extend(extract_recipes_from_ld_json(data))
        item_list_entries.extend(extract_item_list_entries(data))

    parsed = []
    seen = set()
    for recipe in recipes:
        title = clean_text(recipe.get("name") or meta_title or fallback_title)
        if not title:
            continue

        cuisine = normalize_cuisine(recipe.get("recipeCuisine") or recipe.get("cuisine")) or "Unknown"
        image = extract_url(recipe.get("image")) or meta_image or fallback_image or ""
        if image:
            image = urljoin(base_url, image)

        source_url = extract_url(recipe.get("url") or recipe.get("mainEntityOfPage")) or base_url
        source_url = urljoin(base_url, source_url)

        ingredients = normalize_ingredients(recipe.get("recipeIngredient") or recipe.get("ingredients"))
        instructions = normalize_instructions(recipe.get("recipeInstructions"))

        if not ingredients and not instructions:
            continue

        recipe_description = normalize_text_value(recipe.get("description"))
        recipe_keywords = normalize_text_value(recipe.get("keywords"))
        recipe_category = normalize_text_value(recipe.get("recipeCategory"))
        ingredients_text = " ".join(ingredients)
        instructions_text = " ".join(instructions)
        recipe_match_text = " ".join(
            [
                match_text,
                title,
                cuisine,
                recipe_description,
                recipe_keywords,
                recipe_category,
                ingredients_text,
                instructions_text,
            ]
        ).strip()

        key = (title.lower(), source_url)
        if key in seen:
            continue
        seen.add(key)

        parsed.append({
            "title": title,
            "image": image,
            "cuisine": cuisine,
            "ingredients": ingredients,
            "instructions": instructions,
            "sourceUrl": source_url,
            "matchText": recipe_match_text,
        })

    if not parsed:
        micro_recipe = extract_microdata_recipe(
            soup,
            base_url,
            fallback_title,
            fallback_image,
            meta_title,
            meta_image,
            match_text,
        )
        if micro_recipe:
            parsed.append(micro_recipe)

    link_candidates = []
    seen_links = set()

    for entry in item_list_entries:
        url = entry.get("url")
        if not url:
            continue
        url = urljoin(base_url, url)
        if url in seen_links:
            continue
        image = entry.get("image") or ""
        if image:
            image = urljoin(base_url, image)
        link_candidates.append({
            "url": url,
            "title": entry.get("title") or "",
            "image": image,
        })
        seen_links.add(url)

    for entry in extract_candidate_links_from_html(soup, base_url, MAX_LINKS_PER_PAGE):
        url = entry.get("url")
        if not url or url in seen_links:
            continue
        link_candidates.append(entry)
        seen_links.add(url)

    return parsed, link_candidates


def extract_list_page_links(html_text, base_url):
    soup = BeautifulSoup(html_text, "html.parser")
    links = []
    seen = set()

    for script in soup.select('script[type="application/ld+json"]'):
        content = script.string or script.get_text()
        if not content:
            continue
        content = content.strip()
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            continue
        for entry in extract_item_list_entries(data):
            url = entry.get("url")
            if not url:
                continue
            url = urljoin(base_url, url)
            if not same_domain(url, base_url) or url in seen:
                continue
            image = entry.get("image") or ""
            if image:
                image = urljoin(base_url, image)
            links.append({
                "url": url,
                "title": entry.get("title") or "",
                "image": image,
            })
            seen.add(url)

    for entry in extract_candidate_links_from_html(soup, base_url, MAX_LIST_LINKS):
        url = entry.get("url")
        if not url or url in seen:
            continue
        if not same_domain(url, base_url):
            continue
        links.append(entry)
        seen.add(url)

    return links, extract_page_context(soup)


def extract_recipes_from_url(url, fallback_title, fallback_image):
    html_text = fetch_page(url)
    if not html_text:
        return [], []
    return parse_recipe_page(html_text, url, fallback_title, fallback_image)


def build_candidates(results):
    candidates = []
    seen = set()

    def add_candidate(item):
        link = item.get("link") or item.get("source") or item.get("url")
        if not link or link in seen:
            return
        candidates.append({
            "link": link,
            "title": clean_text(item.get("title") or item.get("name")),
            "image": item.get("thumbnail") or item.get("thumbnail_url") or item.get("image") or "",
        })
        seen.add(link)

    for item in results.get("recipes_results") or []:
        add_candidate(item)

    for item in results.get("organic_results") or []:
        add_candidate(item)

    return candidates


def run_search(query, result_count=20):
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "gl": "us",
        "hl": "en",
        "num": result_count,
    }
    search = GoogleSearch(params)
    return search.get_dict()


def build_search_query(country, craving, diet, meal_type, fallback):
    parts = []
    if country:
        parts.append(country)
    if craving:
        parts.append(craving.replace("-", " "))
    if diet:
        parts.append(diet)
    if meal_type:
        parts.append(meal_type)
    parts.append("recipes")
    query = " ".join(part for part in parts if part).strip()
    return query or fallback


def gather_list_pages(candidates, country):
    list_pages = []
    fallback_pages = []
    pages_left = MAX_TOTAL_PAGES

    for candidate in candidates[:MAX_SOURCE_PAGES]:
        if len(list_pages) >= MAX_LIST_PAGES or pages_left <= 0:
            break
        url = candidate.get("link")
        if not url:
            continue

        html_text = fetch_page(url)
        pages_left -= 1
        if not html_text:
            continue

        links, context_text = extract_list_page_links(html_text, url)
        if not links:
            continue

        entry = {
            "url": url,
            "links": links,
            "contextText": context_text,
        }

        if len(links) >= LIST_PAGE_MIN_RECIPES:
            list_pages.append(entry)
        else:
            fallback_pages.append(entry)

    if list_pages:
        return list_pages
    if country:
        return fallback_pages
    return fallback_pages


def collect_recipes_from_lists(list_pages, country, craving, diet, meal_type, limit):
    recipes_pool = []
    seen_urls = set()
    pages_left = MAX_TOTAL_PAGES

    for page in list_pages:
        if pages_left <= 0:
            break
        for link in page.get("links", []):
            if pages_left <= 0 or len(recipes_pool) >= limit * 4:
                break
            link_url = link.get("url")
            if not link_url or link_url in seen_urls:
                continue
            recipes, _ = extract_recipes_from_url(
                link_url,
                link.get("title") or "",
                link.get("image") or "",
            )
            pages_left -= 1
            for recipe in recipes:
                source_url = recipe.get("sourceUrl") or link_url
                if source_url in seen_urls:
                    continue
                recipe["sourceUrl"] = source_url
                recipes_pool.append(recipe)
                seen_urls.add(source_url)

    if not recipes_pool:
        return []

    matched = []
    partial = []
    used = set()

    for recipe in recipes_pool:
        source_url = recipe.get("sourceUrl")
        if not source_url or source_url in used:
            continue
        if country and not recipe_matches_country(recipe, country):
            continue
        all_match, score, dish_score = score_recipe(recipe, country, craving, diet, meal_type)
        if all_match:
            matched.append((dish_score, score, recipe))
        elif score > 0:
            partial.append((dish_score, score, recipe))
        used.add(source_url)

    matched.sort(key=lambda item: (item[0], item[1]), reverse=True)
    partial.sort(key=lambda item: (item[0], item[1]), reverse=True)

    selected = [recipe for _, _, recipe in matched]
    if len(selected) < limit:
        selected.extend(recipe for _, _, recipe in partial)

    return selected[:limit]


# Homepage route
@app.route("/")
def home():
    return render_template("index.html")


# Recipe recommendation route
@app.route("/recommend")
def recommend():
    query = clean_text(request.args.get("query", ""))
    country = normalize_filter_value(request.args.get("country", ""))
    craving = normalize_filter_value(request.args.get("craving", ""))
    diet = normalize_filter_value(request.args.get("diet", ""))
    meal_type = normalize_filter_value(request.args.get("meal_type", ""))

    if not query and not (country or craving or diet or meal_type):
        return jsonify({"error": "No query provided."}), 400

    try:
        limit = int(request.args.get("limit", DEFAULT_LIMIT))
    except ValueError:
        limit = DEFAULT_LIMIT
    limit = clamp(limit, MIN_LIMIT, MAX_LIMIT)

    search_query = build_search_query(country, craving, diet, meal_type, query)
    result_count = max(limit * 6, 50)

    try:
        results = run_search(search_query, result_count=result_count)
        if results.get("error"):
            return jsonify({"error": results["error"]}), 500

        candidates = build_candidates(results)
        list_pages = gather_list_pages(candidates, country)
        recipes = collect_recipes_from_lists(list_pages, country, craving, diet, meal_type, limit)

        if not recipes:
            return jsonify({"error": "No recipes were found. Try a different query."}), 404

        response_data = []
        for recipe in recipes:
            ingredients_list = recipe.get("ingredients") or []
            instructions_list = recipe.get("instructions") or []
            response_data.append({
                "title": recipe.get("title") or "Unknown Dish",
                "image": recipe.get("image") or "",
                "country": country or recipe.get("cuisine") or "Unknown",
                "ingredients": list_to_html(ingredients_list, "ul") if ingredients_list else "N/A",
                "instructions": list_to_html(instructions_list, "ol") if instructions_list else "N/A",
                "sourceUrl": recipe.get("sourceUrl") or "",
            })

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Run Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
