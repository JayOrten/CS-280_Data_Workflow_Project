# this will download the cifar100 dataset and save it to the current directory to be used on the compute node
# this script is run on the login node

from tensorflow import keras
import numpy as np
import itertools

# import the dataset
(x_train, y_train), (x_val, y_val) = keras.datasets.cifar100.load_data()

# save the dataset to the current directory
np.savez('/home/jo288/tool_lab_5/cifar100.npz', x_train=x_train, y_train=y_train, x_val=x_val, y_val=y_val)


# define the range of hyperparameters to test
BATCH_SIZE = [25,50,75,100]
EPOCHS = [10, 50, 100]
LEARNING_RATE = [1e-1, 3e-1, 1e-2, 3e-2, 1e-3, 3e-3]
L1NF = [2,4,8,16]
FDROPOUT = [.25, 0.5, .75]