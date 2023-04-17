import numpy as np
import tensorflow as tf
from tensorflow import keras
from keras import layers
import sys

# get your data
dataset = np.load('/home/jo288/tool_lab_5/cifar100.npz')
x_train = dataset['x_train']
y_train = dataset['y_train']
x_val = dataset['x_val']
y_val = dataset['y_val']

# onehot encode your labels so your model knows its a category
y_train = tf.one_hot(y_train,
                     depth=y_train.max() + 1,
                     dtype=tf.float64)
y_val = tf.one_hot(y_val,
                   depth=y_val.max() + 1,
                   dtype=tf.float64)
  
y_train = tf.squeeze(y_train)
y_val = tf.squeeze(y_val)

checkpointCallbackFunction =  tf.keras.callbacks.ModelCheckpoint(
                                filepath='/checkpoints/model.{epoch:02d}-{val_loss:.2f}.h5',
                                save_freq="epoch")

# constant values
NUM_CLASSES = 100 #100 prediction classes
INPUT_SHAPE = (32,32,3) #shape of the input image 32x32 with 3 channels

# hyperparameters you will be tuning
BATCH_SIZE = int(sys.argv[1])
EPOCHS = int(sys.argv[2])
LEARNING_RATE = float(sys.argv[3])
L1NF = int(sys.argv[4])
L2NF = 512
L3NF = 512
FDROPOUT = float(sys.argv[5])

filename = str(BATCH_SIZE) + "_" + str(EPOCHS) + "_" + str(LEARNING_RATE) + "_" + str(L1NF) + "_" + str(FDROPOUT)

# here is a basic model that you will add to
model = tf.keras.models.Sequential([
                  
                  # CHANGE THESE: these are layers you should mix up and change
                  layers.Conv2D(L1NF, (3, 3), input_shape = INPUT_SHAPE,
                                activation='relu',
                                padding='same'),
                  layers.Conv2D(L1NF, (3, 3),
                                activation='relu',
                                padding='same'),
                  layers.Conv2D(L1NF, (3, 3),
                                activation='relu',
                                padding='same'),
                  layers.MaxPooling2D(2,2),

                  layers.Conv2D(L2NF, (3, 3),
                                activation='relu',
                                padding='same'),
                  layers.Conv2D(L2NF, (3, 3),
                                activation='relu',
                                padding='same'),
                  layers.Conv2D(L2NF, (3, 3),
                                activation='relu',
                                padding='same'),
                  layers.MaxPooling2D(2,2),

                  layers.Conv2D(L3NF, (3, 3),
                                activation='relu',
                                padding='same'),
                  layers.Conv2D(L3NF, (3, 3),
                                activation='relu',
                                padding='same'),
                  layers.Conv2D(L3NF, (3, 3),
                                activation='relu',
                                padding='same'),
                  layers.MaxPooling2D(2,2),
                  layers.Dropout(FDROPOUT),
                  
                  # DO NOT CHANGE THESE. They should be at the end of your model
                  layers.Flatten(),
                  layers.Dense(NUM_CLASSES, activation='softmax')])

# feel free to experiment with this
model.compile(loss='categorical_crossentropy',
             optimizer=keras.optimizers.RMSprop(learning_rate=LEARNING_RATE),
             # DO NOT CHANGE THE METRIC. This is what you will be judging your model on
             metrics=['accuracy'],)

# here you train the model using some of your hyperparameters and send the data
# to weights and biases after every batch            
history = model.fit(x_train, y_train,
                    epochs=EPOCHS,
                    batch_size=BATCH_SIZE,
                    verbose=1,
                    validation_data=(x_val, y_val))

# Save
model.save("./models/" + filename + ".h5")

#This will load my model
#model = keras.models.load_model("models/trainedMode.h5")