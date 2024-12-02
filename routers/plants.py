from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from services.firestore import create_plant, get_user_plants, get_plant_by_id, update_plant
from pydantic import BaseModel, FieldValidationInfo, field_validator
from typing import Optional, Union

router = APIRouter()

class WateringAutoMode(BaseModel):
    interval_type: str  # "days" | "weeks" | "months"
    interval_value: int
    time_of_day: str

class WateringManualMode(BaseModel):
    duration: int

class PlantCreate(BaseModel):
    name: str
    image_url: Optional[str] = None
    auto_mode: bool
    watering: Union[WateringAutoMode, WateringManualMode]

    # Validate the watering field based on the value of auto_mode
    @field_validator("watering", mode="before")
    def validate_watering(cls, watering, info: FieldValidationInfo):
        auto_mode = info.data.get("auto_mode")  # Access the auto_mode field
        if auto_mode:  # auto_mode = True
            if not isinstance(watering, dict) or "interval_type" not in watering or "interval_value" not in watering or "time_of_day" not in watering:
                raise ValueError(
                    "When auto_mode is true, watering must include 'interval_type', 'interval_value', and 'time_of_day'."
                )
        else:  # auto_mode = False
            if not isinstance(watering, dict) or "duration" not in watering:
                raise ValueError(
                    "When auto_mode is false, watering must include 'duration'."
                )
        return watering


@router.post("/api/plants/")
async def create_plant_route(plant: PlantCreate, user: dict = Depends(get_current_user)):
    username = user["sub"]  # Extract the authenticated user's username

    # Prepare plant data
    plant_data = plant.dict()
    plant_data["owner"] = username
    plant_data["status"] = "stopped"  # Default status
    plant_data["soil_moisture"] = "0%"  # Default soil moisture

    # Save the plant in Firestore
    plant_id = create_plant(plant_data)

    return {
        "plant_id": plant_id,
        **plant_data
    }

@router.get("/api/plants")
async def get_plants(user: dict = Depends(get_current_user)):
    # Fetch plants for the authenticated user
    username = user["sub"]  # Extract the username from the JWT token
    plants = get_user_plants(username)
    
    if not plants:
        raise HTTPException(status_code=404, detail="No plants found for this user")
    
    return {"plants": plants}

@router.get("/api/plants/{plant_id}")
async def get_plant(plant_id: str, user: dict = Depends(get_current_user)):
    username = user["sub"]  # Extract the username from the JWT token
    
    # Fetch the plant by ID
    plant = get_plant_by_id(plant_id, username)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found or you do not have access to this plant")
    
    return plant

class WateringUpdateAutoMode(BaseModel):
    interval_type: str  # "days" | "weeks" | "months"
    interval_value: int
    time_of_day: str
    command: str  # "start" | "stop"

class WateringUpdateManualMode(BaseModel):
    duration: Optional[int] = None
    command: str  # "start" | "stop"

class PlantUpdate(BaseModel):
    name: Optional[str] = None
    image_url: Optional[str] = None
    auto_mode: Optional[bool] = None
    watering: Optional[Union[WateringUpdateAutoMode, WateringUpdateManualMode]] = None

    @field_validator("watering", mode="before")
    def validate_watering(cls, watering, info: FieldValidationInfo):
        if watering:
            if "command" not in watering:
                raise ValueError("The watering field must include a 'command' field.")
            if watering["command"] not in ["start", "stop"]:
                raise ValueError("The 'command' field must be either 'start' or 'stop'.")
        return watering

@router.put("/api/plants/{plant_id}")
async def update_plant_route(
    plant_id: str,
    updates: PlantUpdate,
    user: dict = Depends(get_current_user)
):
    username = user["sub"]  # Extract the authenticated user's username

    # Prepare the update data
    update_data = updates.dict(exclude_unset=True)

    # Handle watering commands
    if "watering" in update_data:
        watering_data = update_data["watering"]

        # Update the plant's status based on the command
        if "command" in watering_data:
            update_data["status"] = "running" if watering_data["command"] == "start" else "stopped"
        
        # Remove the command field before saving to Firestore
        watering_data.pop("command", None)

        # If the watering object is empty after popping, remove it from updates
        if not watering_data:
            del update_data["watering"]

    # Update the plant in Firestore
    updated_plant = update_plant(plant_id, update_data, username)
    if not updated_plant:
        raise HTTPException(status_code=404, detail="Plant not found or you do not have access to this plant")

    return updated_plant
