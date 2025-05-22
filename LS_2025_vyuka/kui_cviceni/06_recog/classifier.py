#!/usr/bin/env python3
import os
import numpy as np
from PIL import Image

# definitions of custom exceptions for better error propagation when the project gets bigger
# (planning to use this as base for my own project)

class EmptyDatasetError(Exception):
    pass

class DatasetLoadingError(Exception):
    pass

class ClassifierCorpus():
    """Base class for classifiers, contains basic dataset handling methods"""
    
    def __init__(self, train_path, test_path, dataset_description_path = None, out_file = None):
        self.train_path = train_path
        self.test_path = test_path
        self.out_file = out_file
        
        self.default_img_extension = ".png"
        self.default_description_filename = "truth.dsv"
        
        if not dataset_description_path:
            dataset_description_path = os.path.join(self.train_path, self.default_description_filename)
        
        # train dataset in format {letter1:[path1, path2, ...], letter2:[]}
        self.train_dataset = self._sort_dataset(self.train_path, dataset_description_path) 
        
        # test dataset is just list of filenames
        self.test_dataset = self._get_files_by_extension(test_path)
        
    def _get_files_by_extension(self, path):
        """Gets files from directory "path" with self.default_img_extension""" 
        
        file_list = []
        for file in os.listdir(path):
            if file.endswith(self.default_img_extension):
                file_list.append(file)
        if(len(file_list) == 0):
            raise EmptyDatasetError(f"No dataset candidates in folder: {path} (searching extension {extension})")
        return file_list
    
    def parse_dataset_description(self, description_path):
        """Parses .dsv file "key:value" as dictionary"""
        
        if not os.path.isfile(description_path):
            raise DatasetLoadingError(f"Dataset description file not found: {description_path}")

        description = {}
        with open(description_path, 'r') as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                if ':' not in line:
                    raise DatasetParsingError(f"Missing ':' on line {lineno}: {line}")
                parts = line.split(':', 1)
                if len(parts) != 2 or not parts[0] or not parts[1]:
                    raise DatasetParsingError(f"Invalid format on line {lineno}: {line}")
                filename, value = parts
                description[filename] = value
        return description

    def _sort_dataset(self, dataset_path, description_path):
        """Merge dataset and dataset_description into dictionary with list of all values for each key"""
        
        file_list = self._get_files_by_extension(dataset_path)
        description = self.parse_dataset_description(description_path)

        dataset = {}
        for filename, label in description.items():
            if filename in file_list:
                dataset.setdefault(label, []).append(os.path.join(dataset_path, filename))
        if not dataset:
            raise EmptyDatasetError(f"No dataset candidates in folder: {dataset_path}, described by: {description_path}")
        return dataset
        
    def export_test_result(self, data):
        """Creates .dsv file from "data" dictionary"""
        
        if not self.out_file:
            for key, value in data.items():
                #print(f"{key} --- {value}")
                pass
        else:
            with open(self.out_file, 'w') as f:
                for key, value in data.items():
                    f.write(f"{key}:{value}\n")
            
    def load_image(self, path):
        """Load image from path as numpy vector"""
        
        image_vector = np.array(Image.open(path)).astype(int).flatten()
        return image_vector

