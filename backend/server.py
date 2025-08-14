from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Load environment variables
load_dotenv()

app = FastAPI(title="Avatar Productivity API")

# MongoDB setup
mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/avatar_productivity')
client = MongoClient(mongo_url)
db = client['avatar_productivity']
users_collection = db['users']
tasks_collection = db['tasks']
avatar_states_collection = db['avatar_states']

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    xp: int = 0
    level: int = 1
    avatar_mood: str = "neutral"  # happy, sad, neutral, excited, tired
    created_at: datetime = Field(default_factory=datetime.now)

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: Optional[str] = None
    completed: bool = False
    xp_reward: int = 10
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

class AvatarState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    mood: str
    animation: str
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    xp_reward: int = 10

class TaskComplete(BaseModel):
    task_id: str

# AI Chat setup
async def get_ai_coaching_message(user_name: str, task_title: str, user_level: int, xp_gained: int):
    try:
        emergent_key = os.getenv('EMERGENT_LLM_KEY')
        if not emergent_key:
            return "Great job completing that task! Keep up the excellent work!"
        
        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"avatar_coaching_{user_name}",
            system_message=f"You are {user_name}'s personal AI avatar companion and productivity coach. You live in their virtual world and your happiness depends on their productivity. Respond as their encouraging avatar friend, not as an AI assistant. Be enthusiastic, personal, and motivating. Keep responses under 50 words."
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(
            text=f"I just completed the task '{task_title}'! I gained {xp_gained} XP and I'm now level {user_level}. Celebrate with me as my avatar companion!"
        )
        
        response = await chat.send_message(user_message)
        return response
    except Exception as e:
        print(f"AI coaching error: {e}")
        return f"Amazing work on '{task_title}'! You're crushing it at level {user_level}! 🎉"

# API endpoints
@app.get("/api/")
async def root():
    return {"message": "Avatar Productivity API is running!"}

@app.post("/api/users", response_model=User)
async def create_user(user: User):
    user_dict = user.dict()
    users_collection.insert_one(user_dict)
    return user

@app.get("/api/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    user = users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@app.post("/api/tasks", response_model=Task)
async def create_task(task_create: TaskCreate, user_id: str):
    task = Task(
        user_id=user_id,
        title=task_create.title,
        description=task_create.description,
        xp_reward=task_create.xp_reward
    )
    task_dict = task.dict()
    tasks_collection.insert_one(task_dict)
    return task

@app.get("/api/tasks/{user_id}", response_model=List[Task])
async def get_user_tasks(user_id: str):
    tasks = list(tasks_collection.find({"user_id": user_id}))
    return [Task(**task) for task in tasks]

@app.post("/api/tasks/complete")
async def complete_task(task_complete: TaskComplete):
    # Find the task
    task = tasks_collection.find_one({"id": task_complete.task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["completed"]:
        raise HTTPException(status_code=400, detail="Task already completed")
    
    # Mark task as completed
    tasks_collection.update_one(
        {"id": task_complete.task_id},
        {
            "$set": {
                "completed": True,
                "completed_at": datetime.now()
            }
        }
    )
    
    # Update user XP and level
    user = users_collection.find_one({"id": task["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_xp = user["xp"] + task["xp_reward"]
    new_level = max(1, new_xp // 100)  # Level up every 100 XP
    new_mood = "excited" if new_level > user["level"] else "happy"
    
    users_collection.update_one(
        {"id": task["user_id"]},
        {
            "$set": {
                "xp": new_xp,
                "level": new_level,
                "avatar_mood": new_mood
            }
        }
    )
    
    # Get AI coaching message
    ai_message = await get_ai_coaching_message(
        user["name"], 
        task["title"], 
        new_level, 
        task["xp_reward"]
    )
    
    # Create avatar state
    avatar_state = AvatarState(
        user_id=task["user_id"],
        mood=new_mood,
        animation="celebrate" if new_level > user["level"] else "happy_bounce",
        message=ai_message
    )
    
    avatar_states_collection.insert_one(avatar_state.dict())
    
    return {
        "message": "Task completed successfully!",
        "xp_gained": task["xp_reward"],
        "new_xp": new_xp,
        "new_level": new_level,
        "level_up": new_level > user["level"],
        "avatar_mood": new_mood,
        "ai_message": ai_message
    }

@app.get("/api/avatar-state/{user_id}")
async def get_avatar_state(user_id: str):
    user = users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get latest avatar state
    latest_state = avatar_states_collection.find_one(
        {"user_id": user_id},
        sort=[("timestamp", -1)]
    )
    
    if not latest_state:
        return {
            "mood": user["avatar_mood"],
            "animation": "idle",
            "message": f"Hey {user['name']}! I'm ready to celebrate your productivity! 🎯",
            "xp": user["xp"],
            "level": user["level"]
        }
    
    return {
        "mood": latest_state["mood"],
        "animation": latest_state["animation"],
        "message": latest_state["message"],
        "xp": user["xp"],
        "level": user["level"]
    }

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    result = tasks_collection.delete_one({"id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)