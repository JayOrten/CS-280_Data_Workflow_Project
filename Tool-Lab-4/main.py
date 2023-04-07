from fastapi import FastAPI
from fastapi import File, UploadFile
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import Response
import tensorflow as tf
from tensorflow import keras
from PIL import Image
from io import BytesIO
import numpy as np
import cv2

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter # Define's the api's limiter object
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # Adds the exception to the api 


# Home route
@app.get("/")
@limiter.limit("15/minute")
async def root():
	return {"api_info": "Jay - Orten's CS280 Image Classifier"}

# Classify image:
@app.post("/classify/")
@limiter.limit("5/minute")
async def classify(file: UploadFile = File(...)):
    # Recieve image
    fileString = file.filename
    fileContent = await file.read() # Reads file information from request as a stream of byte
    image = Image.open(BytesIO(fileContent)) # Converts file to a python image from a stream of bytes.
    imageArray = np.asarray(image) #converts image to numpy array
    smallImage = cv2.resize(imageArray, dsize=(32,32), interpolation=cv2.INTER_CUBIC) # Resizes the image
    batchedImage = np.expand_dims(smallImage, axis=0)
    
    # Classify image

    # Load model
    model = keras.models.load_model("trainedModel.h5")

    prediction = model.predict(batchedImage)
    imageClassification = np.argmax(prediction, axis=1)
    #print('REACHED')

    return {"classification":f"{imageClassification}"}



