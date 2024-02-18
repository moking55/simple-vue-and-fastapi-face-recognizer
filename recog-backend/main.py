from typing_extensions import Annotated
from fastapi import FastAPI,Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn, os
import requests, sqlite3



load_dotenv(".env")
app = FastAPI()

api_key = os.getenv('IMAGGA_API_KEY')
api_secret = os.getenv('IMAGGA_SECRET')

origins = [
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

def upload_image(base64_image: str):
    response = requests.post(
        'https://api.imagga.com/v2/faces/detections?return_face_id=1',
        auth=(api_key, api_secret),
        files={'image_base64': base64_image})
    return response

def get_faces():
    conn = sqlite3.connect('faces.db')
    c = conn.cursor()
    c.execute("SELECT * FROM faces")
    rows = c.fetchall()
    conn.close()

    # grouping the faces by name
    faces = {}
    for row in rows:
        if row[0] in faces:
            faces[row[0]].append(row[1])
        else:
            faces[row[0]] = [row[1]]
    
    return faces

@app.post("/add")
async def recognizer(base64_image: Annotated[str, Form()], name: Annotated[str, Form()]):
    response = upload_image(base64_image).json()
    # create table faces if not exists
    conn = sqlite3.connect('faces.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS faces
                 (name text, face_id text)''')
    conn.commit()

    if response['status']['type'] == 'success':
        face_id = response['result']['faces'][0]['face_id']
        c.execute("INSERT INTO faces VALUES (?, ?)", (name, face_id))
        conn.commit()
        conn.close()
        return response
    else:
        return {"status": "error", "message": "No face detected"}
    
@app.get("/faces")
async def faces():
    faces = get_faces()
    return faces

@app.get("/train")
async def index():
    faces = get_faces()
    # grouping people by face_id
    response = requests.put("https://api.imagga.com/v2/faces/recognition/test?callback_url=1",
                            auth=(api_key, api_secret),
                            json={
                                "people": faces
                            }
                            )
                            
    # training the model
    response = requests.post("https://api.imagga.com/v2/faces/recognition/test?callback_url=1",
                            auth=(api_key, api_secret))
    return response.json()

@app.post("/recognize")
async def recognizer(base64_image: Annotated[str, Form()]):
    try:
        face = upload_image(base64_image).json()
        response = requests.get("https://api.imagga.com/v2/faces/recognition/test?face_id=" + face['result']['faces'][0]['face_id'],
                                auth=(api_key, api_secret))
        return response.json()
    except:
            return {"error": "No face detected in the image. Please try again."}
""" if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000) """