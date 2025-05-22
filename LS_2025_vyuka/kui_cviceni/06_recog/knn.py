#!/usr/bin/env python3
import argparse
import numpy as np
import os
from PIL import Image
from classifier import ClassifierCorpus, EmptyDatasetError, DatasetLoadingError

class ClassifierKNN(ClassifierCorpus):
    """Extended class of k-nearest neighbours image classifier"""
    
    def __init__(self, train_path, test_path, k, dataset_description_path=None, out_file=None):
        super().__init__(train_path, test_path, dataset_description_path, out_file)
        self.k = 10 if k == 0 else k # default k value if not specified
        self.train_vectors = []
        self.train_labels = []
        self.test_vectors = {}
        self._preload_images() # with vectorization speeds-up classification process almost 20x

    def _preload_images(self):
        """Preloads all images from train_dataset and test_dataset as vectors into numpy arrays"""
        
        for label, paths in self.train_dataset.items():
            for path in paths:
                img_array = self.load_image(path)
                self.train_vectors.append(img_array)
                self.train_labels.append(label)
        self.train_vectors = np.array(self.train_vectors)

        for filename in self.test_dataset:
            path = os.path.join(self.test_path, filename)
            img_array = self.load_image(path)
            self.test_vectors[filename] = img_array

    def distance(self, a, b):
        """Find distance between image vectors"""
        
        return np.sum((a - b) ** 2, axis=1) # euclidan
        #return 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        #return np.sum(np.abs(a - b), axis=1)
        
    def weighted_vote(self, labels, distances):
        """Find the matching label by occurance and distance from classified image"""
        weight_sum = {}
        for label, dist in zip(labels, distances):
            weight = 1 / (dist + 1e-5)  # avoid zero division
            weight_sum[label] = weight_sum.get(label, 0) + weight
        return max(weight_sum, key=weight_sum.get)
    
    def find_nearest(self, filename):
        """Find label of the nearest image, vectorize the process as much as possible"""
        
        input_vec = self.test_vectors[filename]
        dists = self.distance(self.train_vectors, input_vec)
        k_indices = np.argpartition(dists, self.k)[:self.k]
        k_labels = [self.train_labels[i] for i in k_indices]
        k_dists = [dists[i] for i in k_indices]
        return self.weighted_vote(k_labels, k_dists)

    def test(self):
        """Classify all images in test dataset"""
        
        result_dict = {}
        for counter, filename in enumerate(self.test_dataset, 1):
            print(f"processing nr. {counter}")
            result_dict[filename] = self.find_nearest(filename)
        return result_dict


def parse_args():
    parser = argparse.ArgumentParser(
        description="Learn and classify image data with a k-NN classifier."
    )
    parser.add_argument("train_path", help="path to the training data directory")
    parser.add_argument("test_path", help="path to the testing data directory")
    parser.add_argument("-k", type=int, required=True,
                        help="number of neighbours")
    parser.add_argument("-o", metavar="filepath",
                        help="path of the output .dsv file with the results")
    parser.add_argument("-i", metavar="filepath",
                        help="path of the input .dsv file with dataset description")
    parser.add_argument("-t", "--test", action="store_true",
                        help="Run evaluation of test dataset classification resluts; requires --truth_path")
    parser.add_argument("-tp", "--truth_path", metavar="filepath",
                        help="path of the test dataset truth description file (.dsv)")
    args =  parser.parse_args()
    
    if args.test and args.truth_path is None:
        parser.error("--truth_path (-tp) is required when --test (-t) is specified.")
        
    return args

def main():
    args = parse_args()
    
    print("Initializing classifier...")
    classifier = ClassifierKNN(args.train_path, args.test_path, args.k, args.i, args.o)
    print("Initialized:")
    print(f"Train dataset path: {classifier.train_path}")
    print(f"Train dataset total: {len(classifier.train_dataset)}")
    print("Train dataset images per key:")
    print(" | ".join(f"{k}: {len(v)}" for k, v in classifier.train_dataset.items()))
    print("----")
    print(f"Test dataset path: {classifier.test_path}")
    print(f"Test dataset size: {len(classifier.test_dataset)}")
    print("----")
    
    # testing phase
    print("Testing classifier")
    result_dict = classifier.test()
    classifier.export_test_result(result_dict)
    
    # evaluation phase
    if(args.test):
        reality = classifier.parse_dataset_description(args.truth_path)
        num_images = len(classifier.test_dataset)
        correct = 0
        for key, value in result_dict.items():
            if key in reality:
                if value == reality[key]:
                    print(f"{key} classified correctly as {value}")
                    correct += 1
                else:
                    print(f"{key} classified incorrectly as {value} instead of {reality[key]}")
            else:
                print(f"{key} not present in truth description.")
                num_images -= 1
        print("----")
        print("Evaluation result:")
        print(f"Total images: {num_images}")
        print(f"Correctly classified: {correct}")
        print(f"Incorrectly classified: {num_images-correct}")
        print(f"Success rate: {correct/num_images*100}%")

if __name__ == "__main__":
    main()

