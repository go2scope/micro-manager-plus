import cv2
import numpy as np

image_path = "D:\\AcquisitionData\\upload-test\\Run_1\\Pos0\\img_000000000_Cy5_000.tif"

img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
print("Image dimensions: " + str(img.shape))

cv2.imshow('image', img)
cv2.waitKey(0)
cv2.destroyAllWindows()
