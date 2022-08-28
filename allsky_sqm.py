'''
allsky_sqm.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

Portions of this code are from inidi-allsky https://github.com/aaronwmorris/indi-allsky

'''
import allsky_shared as s
import cv2
import numpy as np
from math import sqrt

metaData = {
    "name": "Sky Quality",
    "description": "Calculates sky quality",
    "module": "allsky_sqm",     
    "events": [
        "day",
        "night"
    ],
    "experimental": "true",    
    "arguments":{
        "mask": "",
        "roi": "",
        "debug": "false",
        "fallback": 5        
    },
    "argumentdetails": {   
        "mask" : {
            "required": "false",
            "description": "Mask Path",
            "help": "The name of the image mask. This mask is applied prior to calculating the sky quality",
            "type": {
                "fieldtype": "image"
            }                
        },        
        "roi" : {
            "required": "true",
            "description": "Region of Interest",
            "help": "The area of the image to calculate the sky quality from",
            "type": {
                "fieldtype": "image"
            }                
        },
        "fallback" : {
            "required": "true",
            "description": "Fallback %",
            "help": "If no ROI is set then this % of the image, from the center will be used",
            "type": {
                "fieldtype": "spinner",
                "min": 1,
                "max": 100,
                "step": 1
            }
        },        
        "debug" : {
            "required": "false",
            "description": "Enable debug mode",
            "help": "If selected each stage of the detection will generate images in the allsky tmp debug folder",
            "type": {
                "fieldtype": "checkbox"
            }          
        }                            
    },
    "enabled": "false"            
}


def sqm(params):
    #ONLY AT NIGHT !

    mask = params["mask"]
    roi = params["roi"]
    debug = params["debug"]
    fallback = int(params["fallback"])

    binning = s.getEnvironmentVariable("AS_BIN")
    if binning is None:
        binning = 1

    image = cv2.imread("/home/pi/cleartest.jpg")
    #image = s.image

    imageMask = None
    if mask != "":
        maskPath = os.path.join(s.getEnvironmentVariable("ALLSKY_HOME"),"html","overlay","images",mask)
        imageMask = cv2.imread(maskPath,cv2.IMREAD_GRAYSCALE)
        if debug:
            s.writeDebugImage(metaData["module"], "image-mask.png", imageMask)  

    if len(image.shape) == 2:
        grayImage = image
    else:
        grayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if imageMask is not None:
        if grayImage.shape == imageMask.shape:
            grayImage = cv2.bitwise_and(src1=grayImage, src2=imageMask)
            if debug:
                s.writeDebugImage(metaData["module"], "masked-image.png", grayImage)                   
            else:
                s.log(0,"ERROR: Source image and mask dimensions do not match")

    imageHeight, imageWidth = grayImage.shape[:2]
    try:
        roiList = roi.split(",")
        x1 = int(int(roiList[0]) / binning)
        y1 = int(int(roiList[1]) / binning)
        x2 = int(int(roiList[2]) / binning)
        y2 = int(int(roiList[3]) / binning)
    except:
        if len(roi) > 0:
            s.log(0, "ERROR: SQM ROI is invalid, falling back to {0}% of image".format(fallback))
        else:
            s.log(1, "INFO: SQM ROI not set, falling back to {0}% of image".format(fallback))
        fallbackAdj = (100 / fallback)
        x1 = int((imageWidth / 2) - (imageWidth / fallbackAdj))
        y1 = int((imageHeight / 2) - (imageHeight / fallbackAdj))
        x2 = int((imageWidth / 2) + (imageWidth / fallbackAdj))
        y2 = int((imageHeight / 2) + (imageHeight / fallbackAdj))

    croppedImage = grayImage[y1:y2, x1:x2] 

    if debug:
        s.writeDebugImage(metaData["module"], "cropped-image.png", croppedImage) 

    sqmAvg = cv2.mean(src=croppedImage)[0]
    s.log(1,"INFO: SQM Mean calculated as {0}".format(sqmAvg))

    # offset the sqm based on the exposure and gain
    #weighted_sqm_avg = (((self.config['CCD_EXPOSURE_MAX'] - exposure) / 10) + 1) * (sqm_avg * (((self.config['CCD_CONFIG']['NIGHT']['GAIN'] - gain) / 10) + 1))

    return "Sky SQM is {0}".format(sqmAvg)