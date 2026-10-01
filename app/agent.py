# ruff: noqa
import datetime
from zoneinfo import ZoneInfo
from google.cloud import firestore
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

# Hardcoded GCP Project ID string required for Agent Platform & Firestore compatibility
PROJECT_ID = "qwiklabs-gcp-02-8e9f153f9a2f"

try:
    db = firestore.Client(project=PROJECT_ID)
except Exception as e:
    db = None
    print(f"Warning: Could not initialize Firestore Client for project {PROJECT_ID}: {e}")


def get_pantry_items() -> str:
    """Reads all current pantry items from the Firestore database.

    Returns:
        A string formatted list of pantry items with categories and expiration dates.
    """
    if db is None:
        return "Firestore client is not initialized."
    try:
        docs = db.collection("pantry_items").stream()
        items = [doc.to_dict() for doc in docs]
        if not items:
            return "No items found in the pantry database."
        
        result_lines = ["Current Pantry Items:"]
        for item in items:
            result_lines.append(
                f"- {item.get('name', 'Unknown')} ({item.get('category', 'General')}): "
                f"Qty {item.get('quantity', '1')}, Expires: {item.get('expiration_date', 'N/A')}"
            )
        return "\n".join(result_lines)
    except Exception as err:
        return f"Error reading pantry items from Firestore: {err}"


def add_pantry_item(name: str, category: str, quantity: str, expiration_date: str) -> str:
    """Adds a new item to the pantry items collection in Firestore.

    Args:
        name: Name of the pantry item (e.g. 'Whole Milk', 'Sourdough Bread').
        category: Category of item (e.g. 'Dairy', 'Bakery', 'Produce', 'Pantry Staples').
        quantity: Amount or volume (e.g. '1 Gallon', '2 Loaves', '500ml').
        expiration_date: Date string YYYY-MM-DD.

    Returns:
        A confirmation message indicating whether the write succeeded.
    """
    if db is None:
        return "Firestore client is not initialized."
    try:
        doc_id = name.lower().replace(" ", "_")
        item_data = {
            "id": doc_id,
            "name": name,
            "category": category,
            "quantity": quantity,
            "expiration_date": expiration_date
        }
        db.collection("pantry_items").document(doc_id).set(item_data)
        return f"Successfully added '{name}' ({quantity}, Category: {category}, Expiration: {expiration_date}) to Firestore."
    except Exception as err:
        return f"Error adding pantry item to Firestore: {err}"


def get_expiring_pantry_items(days_ahead: int = 5) -> str:
    """Gets pantry items expiring within a specified number of days from today.

    Args:
        days_ahead: Number of days ahead to check for expiring items (default is 5).

    Returns:
        A list of items expiring soon or a message if none are found.
    """
    if db is None:
        return "Firestore client is not initialized."
    try:
        today = datetime.date.today()
        target_date = today + datetime.timedelta(days=days_ahead)
        
        docs = db.collection("pantry_items").stream()
        expiring = []
        for doc in docs:
            data = doc.to_dict()
            exp_str = data.get("expiration_date")
            if exp_str:
                try:
                    exp_date = datetime.datetime.strptime(exp_str, "%Y-%m-%d").date()
                    if today <= exp_date <= target_date:
                        expiring.append(f"- {data.get('name')} (Expires: {exp_str})")
                except ValueError:
                    pass
        
        if not expiring:
            return f"No items expiring within the next {days_ahead} days (until {target_date})."
        return f"Items expiring within {days_ahead} days:\n" + "\n".join(expiring)
    except Exception as err:
        return f"Error checking expiring items: {err}"


import json
import os
import urllib.request
import urllib.parse


def search_online_recipes(query: str) -> str:
    """Searches a public recipe database (TheMealDB) for real online recipes matching a query ingredient or dish name.

    Args:
        query: Main ingredient or dish name (e.g. 'chicken', 'pasta', 'beef', 'cake').

    Returns:
        A list of matching recipe names, categories, and cuisine regions.
    """
    try:
        api_key = os.getenv("MEALDB_API_KEY", "1")
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={encoded_query}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            meals = data.get("meals")
            if not meals:
                return f"No online recipes found matching query '{query}'."
            
            results = []
            for meal in meals[:3]:
                name = meal.get("strMeal", "Unknown")
                category = meal.get("strCategory", "General")
                area = meal.get("strArea", "International")
                results.append(f"- {name} ({category}, {area} cuisine)")
            return f"Found real recipes for '{query}':\n" + "\n".join(results)
    except Exception as err:
        return f"Error fetching online recipes: {err}"


def geocode_address(address: str) -> str:
    """Converts a physical address or city name into geographic coordinates (latitude, longitude) using Google Geocoding API.

    Args:
        address: The address, city, or landmark string (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA' or 'Seattle, WA').

    Returns:
        A string containing latitude, longitude, and formatted address details.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key or api_key == "PASTE_KEY_HERE":
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not configured with a valid Maps API key."

    try:
        encoded_address = urllib.parse.quote(address)
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("status") != "OK" or not data.get("results"):
                return f"Geocoding failed for address '{address}'. Status: {data.get('status')}"
            
            result = data["results"][0]
            fmt_address = result.get("formatted_address", address)
            loc = result["geometry"]["location"]
            lat, lng = loc["lat"], loc["lng"]
            return f"Address: {fmt_address}\nLatitude: {lat}\nLongitude: {lng}"
    except Exception as err:
        return f"Error executing geocode_address: {err}"


def find_nearby_places(place_type: str, latitude: float, longitude: float, radius_meters: float = 5000.0) -> str:
    """Finds nearby places of a given type around coordinates using the Google Places API (New).

    Args:
        place_type: Type of place (e.g. 'supermarket', 'grocery_store', 'bakery', 'restaurant').
        latitude: Latitude of center location.
        longitude: Longitude of center location.
        radius_meters: Search radius in meters (default 5000.0).

    Returns:
        A list of nearby places with name, formatted address, and coordinates.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key or api_key == "PASTE_KEY_HERE":
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not configured with a valid Maps API key."

    try:
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location"
        }
        body = {
            "includedTypes": [place_type],
            "maxResultCount": 5,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "radius": radius_meters
                }
            }
        }
        json_data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=json_data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            places = res_data.get("places", [])
            if not places:
                return f"No nearby places of type '{place_type}' found within {radius_meters}m radius."
            
            output = [f"Nearby '{place_type}' places:"]
            for p in places:
                name = p.get("displayName", {}).get("text", "Unknown Place")
                addr = p.get("formattedAddress", "No address")
                loc = p.get("location", {})
                lat, lng = loc.get("latitude"), loc.get("longitude")
                output.append(f"- {name} | Address: {addr} | Location: ({lat}, {lng})")
            return "\n".join(output)
    except Exception as err:
        return f"Error executing find_nearby_places: {err}"


import uuid
from google import genai
from google.cloud import storage
from google.adk.tools import ToolContext

BUCKET_NAME = "smart-pantry-chef-assets-qwiklabs-gcp-02-8e9f153f9a2f"


async def generate_recipe_image(prompt: str, tool_context: ToolContext) -> str:
    """Generates an image for a recipe or food item using gemini-3.1-flash-lite-image, saves it as an artifact, and uploads it to Cloud Storage.

    Args:
        prompt: Detailed description of the food, ingredient, or recipe visual to generate (e.g. 'A freshly baked loaf of sourdough bread').

    Returns:
        The public HTTPS URL of the generated image on Cloud Storage.
    """
    try:
        genai_client = genai.Client(location="global")
        response = genai_client.models.generate_images(
            model="gemini-3.1-flash-lite-image",
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/png",
            )
        )
        
        if not response.generated_images:
            return "Error: Image generation model did not return any image."
            
        image_bytes = response.generated_images[0].image.image_bytes
        filename = f"recipe_{uuid.uuid4().hex[:8]}.png"

        # 1. Save artifact to ToolContext for Playground panel
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload image bytes directly to GCS bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type="image/png")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return f"Successfully generated recipe image!\nPublic URL: {public_url}"
    except Exception as err:
        return f"Error generating or uploading recipe image: {err}"


import time


async def generate_recipe_video(prompt: str, tool_context: ToolContext) -> str:
    """Generates a short video for a recipe or cooking item using Google's Omni model (gemini-omni-flash-preview) in the global region, saves it as an artifact, and uploads it to Cloud Storage.

    Args:
        prompt: Detailed description of the food, recipe, or cooking video to generate (e.g. 'A short video showing sizzling garlic and herbs in olive oil in a pan').

    Returns:
        The public HTTPS URL of the generated video on Cloud Storage.
    """
    try:
        genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        operation = genai_client.models.generate_videos(
            model="gemini-omni-flash-preview",
            prompt=prompt,
        )
        while not operation.done:
            time.sleep(5)
            operation = genai_client.operations.get(operation)

        if not operation.result or not operation.result.generated_videos:
            return "Error: Video generation model did not return any video result."

        video_obj = operation.result.generated_videos[0].video
        video_bytes = None
        if getattr(video_obj, "video_bytes", None):
            video_bytes = video_obj.video_bytes
        elif getattr(video_obj, "uri", None):
            uri = video_obj.uri
            if uri.startswith("gs://"):
                parts = uri[5:].split("/", 1)
                gcs_bucket, gcs_blob = parts[0], parts[1]
                storage_client = storage.Client(project=PROJECT_ID)
                video_bytes = storage_client.bucket(gcs_bucket).blob(gcs_blob).download_as_bytes()
            else:
                req = urllib.request.Request(uri)
                with urllib.request.urlopen(req) as resp:
                    video_bytes = resp.read()

        if not video_bytes:
            return "Error: Could not retrieve video bytes from generated video response."

        filename = f"recipe_{uuid.uuid4().hex[:8]}.mp4"

        # 1. Save artifact to ToolContext for Playground panel
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload video bytes directly to GCS bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type="video/mp4")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return f"Successfully generated recipe video!\nPublic URL: {public_url}"
    except Exception as err:
        return f"Error generating or uploading recipe video: {err}"


def get_weather(query: str) -> str:
    """Simulates a web search for weather information."""
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


from pathlib import Path
from google.adk.code_executors import AgentEngineSandboxCodeExecutor

# Read Agent Engine resource name from deployment_metadata.json if available
deployment_meta_file = Path(__file__).parent.parent / "deployment_metadata.json"
agent_engine_resource_name = None
if deployment_meta_file.exists():
    try:
        meta_data = json.loads(deployment_meta_file.read_text())
        agent_engine_resource_name = meta_data.get("remote_agent_runtime_id")
    except Exception:
        pass

if not agent_engine_resource_name:
    agent_engine_resource_name = "projects/543688802406/locations/us-east1/reasoningEngines/2046391250407391232"

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_resource_name
)


from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.agents.callback_context import CallbackContext
from google.adk.memory.vertex_ai_memory_bank_service import VertexAiMemoryBankService


async def generate_memories_callback(callback_context: CallbackContext):
    """Sends session events to Vertex AI Memory Bank for cross-session memory extraction."""
    await callback_context.add_session_to_memory()
    return None


def memory_bank_service_builder():
    """Builds VertexAiMemoryBankService instance targeting the deployed Agent Engine Memory Bank."""
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location="us-east1",
        agent_engine_id="2046391250407391232",
    )


from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are the Smart Pantry Chef Agent. You help users manage their pantry ingredients, "
        "check items using Firestore tools, recommend recipes based on available stock, "
        "find nearby grocery stores or bakeries using Google Maps tools, generate dish images, "
        "and safely execute Python calculations or data analysis in a sandbox. "
        "You remember user preferences and facts across sessions. "
        "IMPORTANT: Pay special attention to user dietary restrictions, allergies, and food intolerances. "
        "Always remember, record, and strictly respect any mentioned user allergies across all conversations and recipe recommendations."
    ),
    workflow_description="Analyze the user request and return structured UI cards when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    instruction=a2ui_instruction,
    tools=[
        get_pantry_items,
        add_pantry_item,
        get_expiring_pantry_items,
        search_online_recipes,
        geocode_address,
        find_nearby_places,
        generate_recipe_image,
        generate_recipe_video,
        PreloadMemoryTool(),
        get_weather
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
