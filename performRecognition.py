#!/usr/bin/python

# Import the modules
import cv2
from sklearn.externals import joblib
from skimage.feature import hog
import numpy as np
import argparse as ap
from PIL import Image
import scipy.misc
Label = ['0','1','2','3','4','5','6','7','8','9','div','=','-','+','times']
def recognize(fn):
    clf, pp = joblib.load("digits_cls.pkl")
    # My image is a 200x374 jpeg that is 102kb large
    foo = Image.open(fn)
    print "original",foo.size
    Image.LOAD_TRUNCATED_IMAGES = True
    # I downsize the image with an ANTIALIAS filter (gives the highest quality)
    foo = foo.resize((480,640), Image.ANTIALIAS)
    foo.save(fn, quality=90)
    foo.save(fn, optimize=True, quality=95)
    print "compressed size",foo.size
    im = cv2.imread(fn)
    # Convert to grayscale and apply Gaussian filtering
    im_gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    #cv2.imshow("Gray_scale_Image", im_gray)
    #cv2.waitKey()
    # In this, instead of box filter, gaussian kernel is used. It is done with the function, cv2.GaussianBlur(). We should specify the width and height of kernel which should be positive and odd. We also should specify the standard deviation in X and Y direction, sigmaX and sigmaY respectively. If only sigmaX is specified, sigmaY is taken as same as sigmaX. If both are given as zeros, they are calculated from kernel size. Gaussian blurring is highly effective in removing gaussian noise from the image.
    im_gray = cv2.GaussianBlur(im_gray, (5, 5), 0)

    ret, im_th = cv2.threshold(im_gray, 90, 255, cv2.THRESH_BINARY_INV)
    cv2.imshow("Threshold_Image", im_th.copy())
    cv2.waitKey()
    # Find contours in the image
    ctrs, hier = cv2.findContours(im_th.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    imcopy = im.copy()
    cv2.drawContours(imcopy, ctrs, -1, (0, 255, 0))
    cv2.imshow('draw contours', imcopy)
    cv2.waitKey()
    areas = [cv2.contourArea(c) for c in ctrs]
    max_index = np.argmax(areas)
    #del ctrs[max_index]
    #hierarchy = hier[0]
    #rects = [cv2.boundingRect(ctr) for ctr in ctrs]
    for ctr in ctrs:
        area = cv2.contourArea(ctr)
        if area>10:
            # Draw the rectangles
            rect = cv2.boundingRect(ctr)
            cv2.rectangle(im, (rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), (0, 255, 0), 3)
            # Make the rectangular region around the digit
            leng = int(rect[3] * 1.6)
            pt1 = int(rect[1] + rect[3] // 2 - leng // 2)
            pt2 = int(rect[0] + rect[2] // 2 - leng // 2)
            roi = im_th[pt1:pt1 + leng, pt2:pt2 + leng]
            try:
                roi = cv2.resize(roi, (28, 28), interpolation=cv2.INTER_AREA)
            except:
                try:
                    roi = cv2.resize(np.rot90(roi, axes=(-1, -2)), (28, 28), interpolation=cv2.INTER_AREA)

                except:
                    roi = cv2.resize(np.rot90(roi, axes=(-2, -1)), (28, 28), interpolation=cv2.INTER_AREA)

                finally:
                    cv2.putText(im, "Fail", (rect[0], rect[1]), cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 255), 3)
                    break

            roi = cv2.dilate(roi, (3, 3))
            # Calculate the HOG features
            roi_hog_fd = hog(roi, orientations=9, pixels_per_cell=(14, 14), cells_per_block=(1, 1), visualise=False)

            roi_hog_fd = pp.transform(np.array([roi_hog_fd], 'float64'))
            nbr = clf.predict(roi_hog_fd)
            #f.write(str(int(nbr[0])))
            print nbr
            cv2.putText(im, str(int(nbr[0])), (rect[0], rect[1]), cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 255), 3)


    # For each rectangular region, calculate HOG features and predict
    # the digit using Linear SVM.
    #f = open('helloworld.txt', 'wb')
    #for rect in rects:
        # # Draw the rectangles
        # cv2.rectangle(im, (rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), (0, 255, 0), 3)
        # # Make the rectangular region around the digit
        # leng = int(rect[3] * 1.6)
        # pt1 = int(rect[1] + rect[3] // 2 - leng // 2)
        # pt2 = int(rect[0] + rect[2] // 2 - leng // 2)
        # roi = im_th[pt1:pt1 + leng, pt2:pt2 + leng]
        # try:
        #     roi = cv2.resize(roi, (28, 28), interpolation=cv2.INTER_AREA)
        # except:
        #     try:
        #         roi = cv2.resize(np.rot90(roi, axes=(-1, -2)), (28, 28), interpolation=cv2.INTER_AREA)
        #     except:
        #         roi = cv2.resize(np.rot90(roi, axes=(-2, -1)), (28, 28), interpolation=cv2.INTER_AREA)
        #     finally:
        #         cv2.putText(im, "Fail", (rect[0], rect[1]), cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 255), 3)
        #         break
        #
        #
        # roi = cv2.dilate(roi, (3, 3))
        # # Calculate the HOG features
        # roi_hog_fd = hog(roi, orientations=9, pixels_per_cell=(14, 14), cells_per_block=(1, 1), visualise=False)
        # # clf=pp.fit([roi_hog_fd], 'float64')	scaler.scale_ = scaler.std_.copy()
        # # pp.scale_= pp.std_.copy()
        # roi_hog_fd = pp.transform(np.array([roi_hog_fd], 'float64'))
        # nbr = clf.predict(roi_hog_fd)
        # #f.write(str(int(nbr[0])))
        # cv2.putText(im, str(int(nbr[0])), (rect[0], rect[1]), cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 255), 3)

    #f.close()
    cv2.namedWindow("Resulting Image with Rectangular ROIs", cv2.WINDOW_NORMAL)
    cv2.imshow("Resulting Image with Rectangular ROIs", im)
    #scipy.misc.imsave(fn, im)
    cv2.waitKey()

# if __name__ == '__main__':
#     sys.exit(recognize(sys.argv[1]))
recognize("1.jpg")
