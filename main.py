import os
from datetime import date, datetime

import cv2
import joblib
import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sklearn.neighbors import KNeighborsClassifier
from sqlalchemy.orm import Session

import models
from database import SessionLocal, engine

# Defining FastAPI App
app = FastAPI()

# Database Connections
models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


templates = Jinja2Templates(directory="templates")

nimgs = 10

# Saving Date today in 2 different formats
datetoday = date.today().strftime("%m_%d_%y")
datetoday2 = date.today().strftime("%d-%B-%Y")

# Initializing VideoCapture object to access WebCam
face_detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

# If these directories don't exist, create them
if not os.path.isdir("Attendance"):
    os.makedirs("Attendance")
if not os.path.isdir("static"):
    os.makedirs("static")
if not os.path.isdir("static/faces"):
    os.makedirs("static/faces")
if f"Attendance-{datetoday}.csv" not in os.listdir("Attendance"):
    with open(f"Attendance/Attendance-{datetoday}.csv", "w") as f:
        f.write("Name,Roll,Time")


# get a number of total registered users
def totalreg():
    return len(os.listdir("static/faces"))


# extract the face from an image
def extract_faces(img):
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_points = face_detector.detectMultiScale(gray, 1.2, 5, minSize=(20, 20))
        return face_points
    except:
        return []


# Identify face using ML model
def identify_face(facearray):
    model = joblib.load("static/face_recognition_model.pkl")
    return model.predict(facearray)


# A function which trains the model on all the faces available in faces folder
def train_model():
    faces = []
    labels = []
    userlist = os.listdir("static/faces")
    for user in userlist:
        for imgname in os.listdir(f"static/faces/{user}"):
            img = cv2.imread(f"static/faces/{user}/{imgname}")
            resized_face = cv2.resize(img, (50, 50))
            faces.append(resized_face.ravel())
            labels.append(user)
    faces = np.array(faces)
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(faces, labels)
    joblib.dump(knn, "static/face_recognition_model.pkl")


# Extract info from today's attendance file in attendance folder
def extract_attendance():
    df = pd.read_csv(f"Attendance/Attendance-{datetoday}.csv")
    names = df["Name"]
    rolls = df["Roll"]
    times = df["Time"]
    l = len(df)
    return names, rolls, times, l


# Add Attendance of a specific user
def add_attendance(name):
    username = name.split("_")[0]
    userid = name.split("_")[1]
    current_time = datetime.now().strftime("%H:%M:%S")

    df = pd.read_csv(f"Attendance/Attendance-{datetoday}.csv")
    if int(userid) not in list(df["Roll"]):
        with open(f"Attendance/Attendance-{datetoday}.csv", "a") as f:
            f.write(f"\n{username},{userid},{current_time}")


# A function to get names and rol numbers of all users
def getallusers():
    userlist = os.listdir("static/faces")
    names = []
    rolls = []
    l = len(userlist)

    for i in userlist:
        name, roll = i.split("_")
        names.append(name)
        rolls.append(roll)

    return userlist, names, rolls, l


# A function to delete a user folder
def deletefolder(duser):
    pics = os.listdir(duser)
    for i in pics:
        os.remove(duser + "/" + i)
    os.rmdir(duser)


################## ROUTING FUNCTIONS #########################


# Our main page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    names, rolls, times, l = extract_attendance()
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "names": names,
            "rolls": rolls,
            "times": times,
            "l": l,
            "totalreg": totalreg(),
            "datetoday2": datetoday2,
        },
    )


# List users page
@app.get("/listusers", response_class=HTMLResponse)
async def listusers(request: Request, db: Session = Depends(get_db)):
    users = db.query(models.Student).all()
    return templates.TemplateResponse(
        "listusers.html",
        {
            "request": request,
            "users": users,
        },
    )


# Delete functionality
@app.get("/deleteuser")
async def deleteuser(request: Request, user: str = None):
    duser = user
    deletefolder("static/faces/" + duser)

    # if all the face are deleted, delete the trained file...
    if os.listdir("static/faces/") == []:
        os.remove("static/face_recognition_model.pkl")

    try:
        train_model()
    except:
        pass

    userlist, names, rolls, l = getallusers()
    return templates.TemplateResponse(
        "listusers.html",
        {
            "request": request,
            "userlist": userlist,
            "names": names,
            "rolls": rolls,
            "l": l,
            "totalreg": totalreg(),
            "datetoday2": datetoday2,
        },
    )


# Our main Face Recognition functionality.
# This function will run when we click on Take Attendance Button.
@app.get("/start", response_class=HTMLResponse)
async def start(request: Request):
    names, rolls, times, l = extract_attendance()

    if "face_recognition_model.pkl" not in os.listdir("static"):
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "names": names,
                "rolls": rolls,
                "times": times,
                "l": l,
                "totalreg": totalreg(),
                "datetoday2": datetoday2,
                "mess": "There is no trained model in the static folder. Please add a new face to continue.",
            },
        )

    ret = True
    cap = cv2.VideoCapture(0)
    identified_person = None
    try:
        while ret:
            ret, frame = cap.read()
            if len(extract_faces(frame)) > 0:
                (x, y, w, h) = extract_faces(frame)[0]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (86, 32, 251), 1)
                cv2.rectangle(frame, (x, y), (x + w, y - 40), (86, 32, 251), -1)
                face = cv2.resize(frame[y : y + h, x : x + w], (50, 50))
                identified_person = identify_face(face.reshape(1, -1))[0]
                add_attendance(identified_person)
                cv2.putText(
                    frame,
                    f"{identified_person}",
                    (x + 5, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    2,
                )
                # Break out of the loop after the first user is identified
                break

            cv2.imshow("Attendance", frame)
            if cv2.waitKey(1) == 27:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

    if identified_person:
        return templates.TemplateResponse(
            "identification_info.html",
            {
                "request": request,
                "identified_person": identified_person,
            },
        )
    else:
        names, rolls, times, l = extract_attendance()
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "names": names,
                "rolls": rolls,
                "times": times,
                "l": l,
                "totalreg": totalreg(),
                "datetoday2": datetoday2,
            },
        )


# Handles registration of a new user into the db
# Captures 10 instances of a persons  face and uses it to train the model to recognize that
# person during attendance taking stage.
@app.post("/add", response_class=HTMLResponse)
async def add(
    request: Request,
    first_name: str = Form(...),
    other_names: str = Form(),
    reg_no: str = Form(...),
    db: Session = Depends(get_db),
):
    student = models.Student()
    student.first_name = first_name
    student.other_names = other_names
    student.reg_no = reg_no
    db.add(student)
    db.commit()

    # format reg_no with underscores to esnure correct folder names
    # replacing "/" with "_"
    formatted_reg_no = reg_no.replace("/", "_")

    userimagefolder = f"static/faces/{first_name}_{other_names}_{formatted_reg_no}"
    if not os.path.isdir(userimagefolder):
        os.makedirs(userimagefolder)
    i, j = 0, 0
    cap = cv2.VideoCapture(0)
    while 1:
        _, frame = cap.read()
        faces = extract_faces(frame)
        for x, y, w, h in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 20), 2)
            cv2.putText(
                frame,
                f"Images Captured: {i}/{nimgs}",
                (30, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 0, 20),
                2,
                cv2.LINE_AA,
            )
            if j % 5 == 0:
                name = f"{first_name}_{other_names}_{i}.jpg"
                cv2.imwrite(f"{userimagefolder}/{name}", frame[y : y + h, x : x + w])
                i += 1
            j += 1
        if j == nimgs * 5:
            break
        cv2.imshow("Adding new User", frame)
        if cv2.waitKey(1) == 27:
            break
    cap.release()
    cv2.destroyAllWindows()
    # training the model with the collected images
    train_model()
    names, rolls, times, l = extract_attendance()
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "names": names,
            "rolls": rolls,
            "times": times,
            "l": l,
            "totalreg": totalreg(),
            "datetoday2": datetoday2,
        },
    )
