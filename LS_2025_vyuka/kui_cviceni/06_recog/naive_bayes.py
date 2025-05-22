#!/usr/bin/env python3
import argparse
import numpy as np
import os
from PIL import Image
from classifier import ClassifierCorpus, EmptyDatasetError, DatasetLoadingError

class ClassifierBayes(ClassifierCorpus):
    """Extended class of naive bayes image classifier"""
    
    def __init__(self, train_path, test_path, dataset_description_path=None, out_file=None):
        super().__init__(train_path, test_path, dataset_description_path, out_file)
        self.trained = False
        self.num_shades = 16  # pixel value quantization
        self.laplace_k = 1  # laplace correction coefficient
        self.class_pixel_prob = {}  # P(x[i] = v | s)
        self.class_priors = {}      # P(s)

    def _quantize(self, img_array):
        """Quantize colors in image to self.num_shades levels"""
        
        return (img_array // (256 // self.num_shades)).astype(int)

    def train(self):
        """Train classifier by filling class_pixel_prob dictionary of conditional probabilities for each label at each pixel and value"""
        
        # count clases and pixel values
        class_counts = {}
        pixel_value_counts = {}

        for label, images in self.train_dataset.items():
            class_counts[label] = len(images)
            pixel_value_counts[label] = {}

            for img in images:
                img_array = self._quantize(self.load_image(img)).flatten()

                for i, val in enumerate(img_array):
                    if i not in pixel_value_counts[label]:
                        pixel_value_counts[label][i] = [0] * self.num_shades
                    pixel_value_counts[label][i][val] += 1

        # compute class priors and conditional probabilities
        total_images = sum(class_counts.values())

        for label in class_counts:
            self.class_priors[label] = class_counts[label] / total_images
            self.class_pixel_prob[label] = {}

            for i in pixel_value_counts[label]: # use laplace smoothing
                total = sum(pixel_value_counts[label][i]) + self.laplace_k * self.num_shades
                self.class_pixel_prob[label][i] = [
                    (count + self.laplace_k) / total for count in pixel_value_counts[label][i]
                ]

        self.trained = True

    def classify(self, data_array):
        """Classify image by probabilities found in training process"""
        
        if not self.trained:
            return None

        data = self._quantize(data_array.flatten())

        best_label = None
        best_log_prob = float('-inf')

        for label in self.class_priors:
        	# helping myself by using logarithms to overcome near-zero values misinterpretation
            log_prob = np.log(self.class_priors[label])

            for i, val in enumerate(data):
                if i in self.class_pixel_prob[label]:
                    prob = self.class_pixel_prob[label][i][val]
                    log_prob += np.log(prob)
                else:
                    log_prob += np.log(1 / (self.laplace_k * self.num_shades))

            if log_prob > best_log_prob:
                best_log_prob = log_prob
                best_label = label

        return best_label

    def test(self):
        """Classify all images in test dataset"""
        
        if not self.trained:
        	return None
        result_dict = {}
        for counter, filename in enumerate(self.test_dataset, 1):
            print(f"processing nr. {counter}")
            path = os.path.join(self.test_path, filename)
            result_dict[filename] = self.classify(self.load_image(path))
        return result_dict
        

def parse_args():
    parser = argparse.ArgumentParser(
        description="Learn and classify image data with a k-NN classifier."
    )
    parser.add_argument("train_path", help="path to the training data directory")
    parser.add_argument("test_path", help="path to the testing data directory")
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
    classifier = ClassifierBayes(args.train_path, args.test_path, args.i, args.o)
    print("Initialized:")
    print(f"Train dataset path: {classifier.train_path}")
    print(f"Train dataset total: {len(classifier.train_dataset)}")
    print("Train dataset images per key:")
    print(" | ".join(f"{k}: {len(v)}" for k, v in classifier.train_dataset.items()))
    print("----")
    print(f"Test dataset path: {classifier.test_path}")
    print(f"Test dataset size: {len(classifier.test_dataset)}")
    print("----")
    
    # training phase
    print("Training classifier")
    classifier.train()
    
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

