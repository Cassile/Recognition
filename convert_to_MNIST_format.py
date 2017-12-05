import os
from PIL import Image
from array import *
from sklearn.externals import joblib
from skimage.feature import hog
from sklearn.svm import LinearSVC
from sklearn import preprocessing
import numpy as np
from collections import Counter


def chunks(l, n):
    return [l[i:i + n] for i in range(0, len(l), n)]



# Load from and save to
Names = [['training-images', 'train']]

# dataset = datasets.fetch_mldata("MNIST Original")
#
# # Extract the features and labels
# features_digit = np.array(dataset.data, 'int16')
# labels_digit = np.array(dataset.target, 'int')

for name in Names:

    data_image = array('B')
    data_label = array('B')

    FileList = []
    for dirname in os.listdir(name[0]):
        label = dirname# [1:] Excludes .DS_Store from Mac OS
        path = os.path.join(name[0], dirname)
        print path
        for filename in os.listdir(path):
            #print filename
            if filename.endswith(".png"):
                FileList.append(os.path.join(name[0], dirname, filename))
                Im = Image.open(os.path.join(name[0], dirname, filename))

                pixel = Im.load()

                width, height = Im.size

                for x in range(0, width):
                    for y in range(0, height):
                        data_image.append(pixel[y, x])

                data_label.append(int(label))

features_symbol = chunks(data_image,784)

features = np.array(features_symbol, 'int16')

labels = np.array(data_label, 'int')

# features = np.concatenate((features_symbol,features_digit),axis=0)
# labels = np.concatenate((labels_digit,labels_symbol),axis=0)
#print labels[1:100]
# Extract the hog features
list_hog_fd = []
for feature in features:
    fd = hog(feature.reshape((28, 28)), orientations=9, pixels_per_cell=(14, 14), cells_per_block=(1, 1), visualise=False)
    list_hog_fd.append(fd)
hog_features = np.array(list_hog_fd, 'float64')

# Normalize the features
pp = preprocessing.StandardScaler().fit(hog_features)
hog_features = pp.transform(hog_features)

print "Count of digits in dataset", Counter(labels)

# Create an linear SVM object
clf = LinearSVC()

# Perform the training
clf.fit(hog_features, labels)

# Save the classifier
joblib.dump((clf, pp), "digits_cls.pkl", compress=3)