from fastapi import FastAPI
from fastapi import File, UploadFile
from PIL import Image
from io import BytesIO
import numpy as np
import cv2

app = FastAPI()

# This is a post request that allows you to receive a file:
@app.post("/receiveFile/")
async def classify(file: UploadFile = File(...)):
    fileString = file.filename
    fileContent = file.read() # Reads file information from request as a stream of byte
    image = Image.open(BytesIO(fileContent)) # Converts file to a python image from a stream of bytes.
    imageArray = np.asarray(image) #converts image to numpy array
    smallImage = cv2.resize(imageArray, dsize=(32, 32,3), interpolation=cv2.INTER_CUBIC) # Resizes the image
    batchedImage = np.expand_dims(smallImage, axis=0)


@app.get("/")
async def root():
	return {"message":"Hello World"}
