from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, List
import random
import string
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://localhost:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SignalMessage(BaseModel):
    kind: str
    data: str

class Room:
    def __init__(self):
        self.participants: List[WebSocket] = []

    async def add(self, websocket: WebSocket):
        await websocket.accept()
        self.participants.append(websocket)

    async def remove(self, websocket: WebSocket):
        self.participants.remove(websocket)

    async def broadcast(self, message: SignalMessage, sender: WebSocket):
        for participant in self.participants:
            if participant != sender:
                await participant.send_json(message.dict())

class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}

    def create_room(self) -> str:
        room_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        self.rooms[room_id] = Room()
        return room_id

    def get_room(self, room_id: str) -> Room:
        return self.rooms.get(room_id)

    async def connect_to_room(self, room_id: str, websocket: WebSocket):
        room = self.get_room(room_id)
        if room and len(room.participants) < 2:
            await room.add(websocket)
            return room
        return None

    async def disconnect_from_room(self, room_id: str, websocket: WebSocket):
        room = self.get_room(room_id)
        if room:
            await room.remove(websocket)
            if not room.participants:
                del self.rooms[room_id]

manager = ConnectionManager()

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    room = await manager.connect_to_room(room_id, websocket)
    if not room:
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_json()
            message = SignalMessage(**data)
            await room.broadcast(message, websocket)
    except WebSocketDisconnect:
        await manager.disconnect_from_room(room_id, websocket)

@app.get("/create_room")
async def create_room():
    room_id = manager.create_room()
    return {"room_id": room_id}

@app.get("/join_random_room")
async def join_random_room():
    available_rooms = [room_id for room_id, room in manager.rooms.items() if len(room.participants) < 2]
    if not available_rooms:
        room_id = manager.create_room()
    else:
        room_id = random.choice(available_rooms)
    return {"room_id": room_id}

@app.get("/rooms")
async def get_rooms():
    rooms = [room_id for room_id in manager.rooms]
    rooms_len = len(rooms)

    return {
        "rooms": rooms,
        "length": rooms_len
    }
