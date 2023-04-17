#!/bin/bash

BATCH_SIZE="25 50 75 100"

EPOCHS="10 50 100"

LEARNING_RATE="1e-1 3e-1 1e-2 3e-2 1e-3 3e-3"

L1NF="2 4 8 16"

FDROPOUT=".25 0.5 .75"

sbatch ./second_script.sh 25 10 1e-1 2 .25

#or BS in $BATCH_SIZE ; do

#    for EP in $EPOCHS ; do
    
#        for LR in $LEARNING_RATE ; do

#            for L1 in $L1NF ; do

#                for DO in $FDROPOUT ; do

#                    sbatch ./second_script.sh $BS $EP $LR $L1 $DO

#                done
                
#            done

#        done
    
#    done

#done