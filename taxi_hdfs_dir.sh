#!/bin/bash

# HDFS directory path
HDFS_DIR="/user/talentum/Final_Project"

# Check if directory exists
hdfs dfs -test -d $HDFS_DIR

if [ $? -eq 0 ]; then
    echo "Directory exists. Deleting it..."
    hdfs dfs -rm -r $HDFS_DIR
else
    echo "Directory does not exist. Creating new directory..."
fi

# Create the directory
hdfs dfs -mkdir -p $HDFS_DIR
echo "Directory created: $HDFS_DIR"
