#!/usr/bin/python

# Import the modules
import cv2
from sklearn.externals import joblib
from skimage.feature import hog
import numpy as np
from PIL import Image
import string
Label = ['0','1','2','3','4','5','6','7','8','9',')','=','-','+','*','/','(']
def recognize(fn):
    result = []
    i = 0
    clf, pp = joblib.load("digits_cls.pkl")
    foo = Image.open(fn)
    #print "original",foo.size
    w,l = foo.size
    if(w>l):
        rotation = 0
        foo = foo.resize((840,480),Image.ANTIALIAS)
    else:
        rotation = 1
        foo = foo.resize((480, 640), Image.ANTIALIAS)
    Image.LOAD_TRUNCATED_IMAGES = True
    # I downsize the image with an ANTIALIAS filter (gives the highest quality)

    foo.save(fn, quality=90)
    foo.save(fn, optimize=True, quality=95)
    #print "compressed size",foo.size
    im = cv2.imread(fn)


    # Convert to grayscale and apply Gaussian filtering
    im_gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    #cv2.imshow("Gray_scale_Image", im_gray)
    #cv2.waitKey()


    # In this, instead of box filter, gaussian kernel is used. It is done with the function, cv2.GaussianBlur().
    # We should specify the width and height of kernel which should be positive and odd.
    # We also should specify the standard deviation in X and Y direction, sigmaX and sigmaY respectively.
    # If only sigmaX is specified, sigmaY is taken as same as sigmaX.
    # If both are given as zeros, they are calculated from kernel size.
    # Gaussian blurring is highly effective in removing gaussian noise from the image.
    im_gray = cv2.GaussianBlur(im_gray, (5, 5), 0)
    #cv2.imshow("GaussianBlur", im_gray)
    #cv2.waitKey()


    ret, im_th = cv2.threshold(im_gray, 90, 255, cv2.THRESH_BINARY_INV)
    #cv2.imshow("Threshold_Image", im_th.copy())
    #cv2.waitKey()


    # Find contours in the image
    ctrs, hier = cv2.findContours(im_th.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    imcopy = im.copy()
    cv2.drawContours(imcopy, ctrs, -1, (0, 255, 0))
    #cv2.imshow('draw contours', imcopy)
    #cv2.waitKey()

    boundingBoxes = [cv2.boundingRect(c) for c in ctrs]
    (ctrs, boundingBoxes) = zip(*sorted(zip(ctrs, boundingBoxes),key=lambda b: b[1][i], reverse=False))


    areas = [cv2.contourArea(c) for c in ctrs]
    max_index = np.argmax(areas)
    for ctr in ctrs:
        area = cv2.contourArea(ctr)
        if area>100:
            # Draw the rectangles

            rect = cv2.boundingRect(ctr)
            #print 'bounding',rect
            cv2.rectangle(im, (rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), (0, 255, 0), 3)
            # Make the rectangular region around the digit


            #roi = cv2.resize(roi, (28, 28), interpolation=cv2.INTER_AREA)
            if rotation == 1:
                try:
                    leng = int(rect[3] * 1.2)
                    pt1 = int(rect[1] + rect[3] // 2 - leng // 2)
                    pt2 = int(rect[0] + rect[2] // 2 - leng // 2)
                    roi = im_th[pt1:pt1 + leng, pt2:pt2 + leng]
                    cv2.imshow('A', roi)
                    cv2.waitKey()
                    roi = cv2.resize(roi, (28, 28), interpolation=cv2.INTER_AREA)
                except:
                    leng = int(rect[3] * 0.8)
                    pt1 = int(rect[1] + rect[3] // 2 - leng // 2)
                    pt2 = int(rect[0] + rect[2] // 2 - leng // 2)
                    roi = im_th[pt1:pt1 + leng, pt2:pt2 + leng]
                    cv2.imshow('C', roi)
                    cv2.waitKey()
                    roi = cv2.resize(roi, (28, 28), interpolation=cv2.INTER_AREA)

            else:
                leng = int(rect[3] * 0.8)
                pt1 = int(rect[1] + rect[3] // 2 - leng // 2)
                pt2 = int(rect[0] + rect[2] // 2 - leng // 2)
                roi = im_th[pt1:pt1 + leng, pt2:pt2 + leng]
                cv2.imshow('B', roi)
                cv2.waitKey()
                roi = cv2.resize(roi, (28, 28), interpolation=cv2.INTER_AREA)


            roi = cv2.dilate(roi, (3, 3))
            # Calculate the HOG features
            roi_hog_fd = hog(roi, orientations=9, pixels_per_cell=(14, 14), cells_per_block=(1, 1), visualise=False)

            roi_hog_fd = pp.transform(np.array([roi_hog_fd], 'float64'))
            nbr = clf.predict(roi_hog_fd)
            #f.write(str(int(nbr[0])))
            result.append(int(nbr[0]))
            #i=i+1
            cv2.putText(im, str(int(nbr[0])), (rect[0], rect[1]), cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 255), 3)


    cv2.namedWindow("Resulting Image with Rectangular ROIs", cv2.WINDOW_NORMAL)
    cv2.imshow("Resulting Image with Rectangular ROIs", im)
    cv2.waitKey()
    print result
    return  result
def getNumber(l):
    t = [i for i, x in enumerate(l) if x > 10]
    a = 0
    number_list=[]
    for index in t:
        num = l[a:index+1]
        for digit in num:
            num = digit
        number_list.append(int(num))
        a = index+2
    print number_list

def calculate(l):
    t = l[0:3]
    print t
    del l[0:3]
    if t[1]>10:
        if t[1] == 12:
            c = t[0]-t[2]
            l.insert(0, c)

        elif t[1] == 13:
            c = t[0]+t[2]
            l.insert(0,c)

        elif t[1] == 14:
            c= t[0]*t[2]
            l.insert(0,c)
        elif t[1] == 15:
            c= t[0]/t[2]
            l.insert(0,c)

    if len(l)>2:
        return calculate(l)
    else:
        print c
        return c

if __name__ == '__main__':
    sys.exit(recognize(sys.argv[1]))
#recognize('test60.jpg')
#getNumber([8,5,13,4,9])
