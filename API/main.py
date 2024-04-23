from fastapi import FastAPI , status , UploadFile , File
from mltu.configs import BaseModelConfigs
from mltu.utils.text_utils import ctc_decoder
from mltu.inferenceModel import OnnxInferenceModel

import os
import cv2
import typing
import numpy as np

from functools import lru_cache

app = FastAPI()


class ImageToWordModel(OnnxInferenceModel):
    
    def __init__(self, char_list: typing.Union[str, list], *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('Intialized')
        self.char_list = char_list

    def predict(self, image: np.ndarray):
        image = cv2.resize(image, self.input_shapes[0][1:3][::-1])
        image_pred = np.expand_dims(image, axis=0).astype(np.float32)
        preds = self.model.run(self.output_names, {self.input_names[0]: image_pred})[0]
        text = ctc_decoder(preds, self.char_list)[0]
        return text
    
@app.post('/captcha')
def root(file: UploadFile = File(...)):
    if file.size == 0:
        return {
            'mesg':"File is Missing",
            'status':status.HTTP_400_BAD_REQUEST
        }
    if  file is not None and "image" not in file.content_type:
        return {
            'mesg': "Invalid File Type ,Supported file JPEG , PNG",
            'status':status.HTTP_400_BAD_REQUEST,
        }
    
    #reading file 
    file = file.file.read()
    #loading ML Model & if not found , return internal error.
    mlModel = loadmodel()
    if not mlModel :
        return {'mesg':"Internal AI Model Error.",
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR}

    #converting string Img to nparray & predicting , return the output
    arrayImg = cv2.imdecode(np.frombuffer(file, np.uint8), cv2.IMREAD_COLOR)
    predictedText = mlModel.predict(arrayImg)
    return {'predicted':predictedText,
            'status':status.HTTP_200_OK}

@lru_cache(maxsize=30)
def loadmodel():
    modelPath = os.path.join(os.getcwd(),"Models","configs.yaml")
    try:
        configs = BaseModelConfigs.load(modelPath)
    except:
        return None
    model = ImageToWordModel(model_path=configs.model_path, char_list=configs.vocab)
    return model

