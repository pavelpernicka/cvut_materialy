ZIP=zip
TEST_SCRIPT = "./test.sh"
TRAIN_FOLDER = "train_1000_28"
TEST_FOLDER = "train_700_28"
all: zip

zip:
	$(ZIP) 06-brute.zip knn.py naive_bayes.py classifier.py
	
run_knn:
	python3 knn.py -k 3 -o classification.dsv -t -tp $(TEST_FOLDER)/truth.dsv $(TRAIN_FOLDER) $(TEST_FOLDER)

run_bayes:
	python3 naive_bayes.py -o classification.dsv -t -tp $(TEST_FOLDER)/truth.dsv $(TRAIN_FOLDER) $(TEST_FOLDER)
test:
	$(TEST_SCRIPT)
