import os
from datetime import date, datetime

import cv2
import joblib
import numpy as np
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sklearn.neighbors import KNeighborsClassifier
from sqlalchemy.orm import Session

import models
from admin_site import admin
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

# Initializing VideoCapture object to access WebCam
face_detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

# If these directories don't exist, create them
if not os.path.isdir("static"):
    os.makedirs("static")
if not os.path.isdir("static/faces"):
    os.makedirs("static/faces")


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
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
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

    return templates.TemplateResponse(
        "listusers.html",
        {
            "request": request,
        },
    )


# Our main Face Recognition functionality.
# This function will run when we click on Take Attendance Button.
@app.post("/start", response_class=HTMLResponse)
async def start(request: Request,
                unit_code: str = Form(...),
        db: Session = Depends(get_db),
                ):
    unit = db.query(models.Unit).filter_by(code=unit_code).first()
    if unit is None:
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                
                "mess": "No unit with the provided code!",
            },
        )
    current_time = datetime.now().time()
    if not (unit.starts_at < current_time <= unit.ends_at):
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                
                "mess": "You can't take attendance out of classtime!!",
            },
        )
    
    if "face_recognition_model.pkl" not in os.listdir("static"):
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "mess": "There is no trained model in the static folder. Please add a new face to continue.",
            },
        )

    ret = True
    cap = cv2.VideoCapture(0)
    identified_person: str|None = None
    try:
        while ret:
            ret, frame = cap.read()
            if len(extract_faces(frame)) > 0:
                (x, y, w, h) = extract_faces(frame)[0]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (86, 32, 251), 1)
                cv2.rectangle(frame, (x, y), (x + w, y - 40), (86, 32, 251), -1)
                face = cv2.resize(frame[y : y + h, x : x + w], (50, 50))
                identified_person = identify_face(face.reshape(1, -1))[0]

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
        identified_p_list = identified_person.split("_")[-3:]
        reg_no = f"{identified_p_list[0]}/{identified_p_list[1]}/{identified_p_list[2]}"
        student = db.query(models.Student).filter_by(reg_no=reg_no).first()
        if student:
            attendance = models.Attendance()
            attendance.student_id = student.id
            attendance.unit_id = unit.id
            db.add(attendance)
            db.commit()
        return templates.TemplateResponse(
            "identification_info.html",
            {
                "request": request,
                "identified_person": identified_person,
            },
        )
    else:
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
            },
        )


# Handles registration of a new user into the db
# Captures 10 instances of a persons  face and uses it to train the model to recognize that
# person during attendance taking stage.
@app.post("/add", response_class=HTMLResponse)
async def add(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(),
    reg_no: str = Form(...),
    db: Session = Depends(get_db),
):
    student = models.Student()
    student.first_name = first_name
    student.last_name = last_name
    student.reg_no = reg_no
    db.add(student)
    db.commit()

    # format reg_no with underscores to esnure correct folder names
    # replacing "/" with "_"
    formatted_reg_no = reg_no.replace("/", "_")

    userimagefolder = f"static/faces/{first_name}_{last_name}_{formatted_reg_no}"
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
                name = f"{first_name}_{last_name}_{i}.jpg"
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

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
        },
    )


admin.mount_to(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
