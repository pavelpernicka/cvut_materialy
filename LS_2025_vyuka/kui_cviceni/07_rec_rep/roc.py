import os
import numpy as np
import matplotlib.pyplot as plt

def getROCseries(ground_truth, predictions):
    """Calculate TPR and FPR for each alpha"""
    
    num_alpha = predictions.shape[1]
    tpr_list = []
    fpr_list = []
    
    for k in range(num_alpha):
        pred = predictions[:, k] # k-th line
        tp = np.sum((pred == 1) & (ground_truth == 1))
        fp = np.sum((pred == 1) & (ground_truth == 0))
        fn = np.sum((pred == 0) & (ground_truth == 1))
        tn = np.sum((pred == 0) & (ground_truth == 0))

        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0  # sensitivity / recall
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0  # 1 - specificity

        tpr_list.append(tpr)
        fpr_list.append(fpr)
        
    return tpr_list, fpr_list

def best_alpha_maxdiff(tpr_list, fpr_list):
    """Find best alpha parameter from ROC by maximal difference between TPR nad FPR"""
    
    difference = np.array(tpr_list) - np.array(fpr_list)
    best_index = np.argmax(difference)
    return best_index

def best_alpha_mindist(tpr_list, fpr_list):
    """Find best alpha parameter from ROC by distance from (0, 1)"""  
    distances = np.sqrt((np.array(fpr_list))**2 + (1 - np.array(tpr_list))**2)
    best_index = np.argmin(distances)
    return best_index
    
def plotROC(tpr_list, fpr_list, point_index, name=""):
    plt.figure(figsize=(6, 6))
    plt.plot(fpr_list, tpr_list, marker='o', label='ROC curve')
    plt.plot([0, 1], [0, 1], 'k--', alpha=0.5)
    plt.plot(fpr_list[point_index], tpr_list[point_index], 'ro', markersize=9, label='Best alpha parameter')
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(f"ROC Curve of classifier {name}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("roc.pdf")
    plt.show()
    
def best_alpha(classifier_name):
    """Task 1"""
    
    path = "classif_result_tables"
    gt_path = os.path.join(path, "GT.dsv")
    ground_truth = np.loadtxt(gt_path, delimiter=',', dtype=int)
    positive_count = np.sum(ground_truth)
    negative_count = len(ground_truth) - positive_count
    print("Ground truth contains these situations:")
    print(f"Positive: {positive_count}")
    print(f"Negative: {negative_count}")
    print("--------")
    
    classifier_path = os.path.join(path, f"{classifier_name}.dsv")
    predictions = np.loadtxt(classifier_path, delimiter=',', dtype=int)
    
    tpr_list, fpr_list = getROCseries(ground_truth, predictions)
    
    best_index_maxdiff = best_alpha_maxdiff(tpr_list, fpr_list)
    print(f"Best alpha parameter (maxdiff): {best_index_maxdiff}")
    print(f"TPR: {tpr_list[best_index_maxdiff]:.3f}, FPR: {fpr_list[best_index_maxdiff]:.3f}")

    best_index_mindist = best_alpha_mindist(tpr_list, fpr_list)
    print(f"Best alpha parameter (nearest [0,1]): {best_index_mindist}")
    print(f"TPR: {tpr_list[best_index_mindist]:.3f}, FPR: {fpr_list[best_index_mindist]:.3f}")

    best_index = best_index_mindist
    plotROC(tpr_list, fpr_list, best_index, classifier_name)

def most_secure_classifier(plot=False, fpr_threshold=0.01):
    """
    Find name and best alpha of the best classifier, 
    metric is based on finding highest TPR-FPR in right sided neighbourheed of zero FPR
    """
    path = "classif_result_tables"
    gt_path = os.path.join(path, "GT.dsv")
    ground_truth = np.loadtxt(gt_path, delimiter=',', dtype=int)

    best_classifier = None
    best_alpha_index = None
    best_score = -float('inf')

    best_tpr_list = None
    best_fpr_list = None

    for i in range(1, 6):
        classifier_name = f"C{i}"
        classifier_path = os.path.join(path, f"{classifier_name}.dsv")
        predictions = np.loadtxt(classifier_path, delimiter=',', dtype=int)

        tpr_list, fpr_list = getROCseries(ground_truth, predictions)

        for k, (fpr, tpr) in enumerate(zip(fpr_list, tpr_list)):
            if 0.0 <= fpr <= fpr_threshold:
                score = tpr - fpr
                if score > best_score:
                    best_score = score
                    best_classifier = classifier_name
                    best_alpha_index = k
                    best_tpr_list = tpr_list
                    best_fpr_list = fpr_list

    if best_classifier is None:
        raise ValueError(f"No classifier has FPR within [0, {fpr_threshold}]")

    print(f"Most secure classifier (TPR - FPR maximized in FPR ≤ {fpr_threshold}): {best_classifier} at alpha index {best_alpha_index}")
    print(f"TPR: {best_tpr_list[best_alpha_index]:.3f}, FPR: {best_fpr_list[best_alpha_index]:.3f}, Score: {best_score:.3f}")

    if plot:
        plotROC(best_tpr_list, best_fpr_list, best_alpha_index, best_classifier)

    return best_classifier, best_alpha_index

def is_better(new_classifier, fpr_threshold=0.01):
    """
    Returns True if new_classifier is better than best classifier, otherwise False.
    Metric is based on finding highest TPR-FPR in right sided neighbourheed of zero FPR [0, fpr_threshold]
    """
    path = "classif_result_tables"
    gt_path = os.path.join(path, "GT.dsv")
    ground_truth = np.loadtxt(gt_path, delimiter=',', dtype=int)

    best_classifier, _ = most_secure_classifier(plot=False, fpr_threshold=fpr_threshold)
    ref_predictions = np.loadtxt(os.path.join(path, f"{best_classifier}.dsv"), delimiter=',', dtype=int)
    ref_tpr_list, ref_fpr_list = getROCseries(ground_truth, ref_predictions)

    ref_score = -float('inf')
    for fpr, tpr in zip(ref_fpr_list, ref_tpr_list):
        if 0.0 <= fpr <= fpr_threshold:
            score = tpr - fpr
            if score > ref_score:
                ref_score = score
                
    new_predictions = np.loadtxt(os.path.join(path, f"{new_classifier}.dsv"), delimiter=',', dtype=int)
    new_tpr_list, new_fpr_list = getROCseries(ground_truth, new_predictions)

    best_new_score = -float('inf')
    for fpr, tpr in zip(new_fpr_list, new_tpr_list):
        if 0.0 <= fpr <= fpr_threshold:
            score = tpr - fpr
            if score > best_new_score:
                best_new_score = score

    return best_new_score > ref_score

def plotROC_comparison_dual_thresholds():
    thresholds = [0.01, 0.02]
    path = "classif_result_tables"
    gt_path = os.path.join(path, "GT.dsv")
    ground_truth = np.loadtxt(gt_path, delimiter=',', dtype=int)

    plt.figure(figsize=(6, 6))

    colors = ['blue', 'green']
    labels = []

    for i, fpr_threshold in enumerate(thresholds):
        best_classifier, best_index = most_secure_classifier(plot=False, fpr_threshold=fpr_threshold)
        classifier_path = os.path.join(path, f"{best_classifier}.dsv")
        predictions = np.loadtxt(classifier_path, delimiter=',', dtype=int)
        tpr_list, fpr_list = getROCseries(ground_truth, predictions)

        plt.plot(fpr_list, tpr_list, marker='o', linestyle='-', color=colors[i], label=f"{best_classifier}, threshold={fpr_threshold}")
        plt.plot(fpr_list[best_index], tpr_list[best_index], 'ro', markersize=9)

    plt.plot([0, 1], [0, 1], 'k--', alpha=0.4)
    plt.axvspan(0.0, 0.02, color='gray', alpha=0.2, label='FPR ≤ 0.02')

    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Comparason of 2 most secure classifier candidates")
    plt.xlim(0, 0.15)
    plt.ylim(0, 1.0)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("roc_comparison.pdf")
    plt.show()
    
if __name__ == "__main__":
    fpr_threshold = 0.01
    
    best_alpha("C1")
    print("--------")
    most_secure_classifier(fpr_threshold=fpr_threshold)
    print("--------")
    for i in range(1,6):
        res = is_better(f"C{i}", fpr_threshold)
        print(f"{i} {res}")
    plotROC_comparison_dual_thresholds()

