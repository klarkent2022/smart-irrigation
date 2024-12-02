from google.cloud import firestore

# Initialize Firestore client
db = firestore.Client.from_service_account_json("smart-irrigation.json")

# Test function to verify Firestore connection
def test_firestore_connection():
    # Attempt to access a dummy collection
    test_ref = db.collection("test").document("test_doc")
    try:
        test_ref.get()  # Trigger a read operation
        return True  # If no exception, connection is fine
    except Exception as e:
        print(f"Firestore connection error: {e}")
        return False

# Add a new user to Firestore
def create_user(user_id: str, user_data: dict):
    db.collection("users").document(user_id).set(user_data)

# Get a user by username
def get_user_by_id(username: str):
    user_ref = db.collection("users").document(username)
    user = user_ref.get()
    return user.to_dict() if user.exists else None

# Get a user by email
def get_user_by_email(email: str):
    user_query = db.collection("users").where("email", "==", email).stream()
    user_docs = [doc for doc in user_query]
    if not user_docs:
        return None
    return user_docs[0].to_dict()  # Return the first matching document

def create_plant(plant_data: dict):
    plant_ref = db.collection("plants").document()
    plant_ref.set(plant_data)
    return plant_ref.id


def get_user_plants(username: str):
    plants_ref = db.collection("plants").where("owner", "==", username).stream()
    plants = []
    for plant in plants_ref:
        plant_data = plant.to_dict()
        plant_data["plant_id"] = plant.id  # Include the document ID as the plant_id
        plants.append(plant_data)
    return plants

def get_plant_by_id(plant_id: str, username: str):
    plant_ref = db.collection("plants").document(plant_id)
    plant = plant_ref.get()
    
    if not plant.exists:
        return None
    
    plant_data = plant.to_dict()
    # Ensure the plant belongs to the authenticated user
    if plant_data.get("owner") != username:
        return None
    
    # Include the document ID as plant_id in the response
    plant_data["plant_id"] = plant_id
    return plant_data

def update_plant(plant_id: str, updates: dict, username: str):
    plant_ref = db.collection("plants").document(plant_id)
    plant = plant_ref.get()
    
    # Ensure the plant exists and belongs to the user
    if not plant.exists:
        return None
    plant_data = plant.to_dict()
    if plant_data["owner"] != username:
        return None

    # Merge existing watering data if "watering" is partially updated
    if "watering" in updates and isinstance(updates["watering"], dict):
        updates["watering"] = {**plant_data.get("watering", {}), **updates["watering"]}

    # Update the plant with the merged data
    plant_ref.update(updates)
    return {**plant_data, **updates, "plant_id": plant_id}
