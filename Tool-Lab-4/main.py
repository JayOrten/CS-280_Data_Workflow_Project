from fastapi import FastAPI
from fastapi import File, UploadFile
import tensorflow as tf
from tensorflow import keras
from PIL import Image
from io import BytesIO
import numpy as np
import cv2

app = FastAPI()
# Home route
@app.get("/")
async def root():
	return {"api_info": "Jay - Orten's CS280 Image Classifier"}

# Classify image:
@app.post("/classify/")
async def classify(file: UploadFile = File(...)):
    # Recieve image
    fileString = file.filename
    fileContent = file.read() # Reads file information from request as a stream of byte
    image = Image.open(BytesIO(fileContent)) # Converts file to a python image from a stream of bytes.
    imageArray = np.asarray(image) #converts image to numpy array
    smallImage = cv2.resize(imageArray, dsize=(32, 32,3), interpolation=cv2.INTER_CUBIC) # Resizes the image
    batchedImage = np.expand_dims(smallImage, axis=0)
    
    # Classify image

    # Load model
    model = keras.models.load_model("trainedMode.h5")

    imageClassification = model.predict(batchedImage)
    
    return {"classification":imageClassification}



