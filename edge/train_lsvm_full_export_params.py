import os
import numpy as np

from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    x_path = os.path.join(base_dir, "data_sample", "X_all_features.csv")
    y_path = os.path.join(base_dir, "data_sample", "Y_all_labels.csv")

    model_dir = os.path.join(base_dir, "models")
    os.makedirs(model_dir, exist_ok=True)

    out_path = os.path.join(model_dir, "lsvm_edge_params_v2.npz")

    print("Loading FULL dataset...")
    print("X path:", x_path)
    print("Y path:", y_path)

    X = np.loadtxt(x_path, delimiter=",", dtype=np.float32)
    y = np.loadtxt(y_path, delimiter=",", dtype=np.int32).ravel()

    print("X shape:", X.shape)
    print("y shape:", y.shape)
    print("classes:", np.unique(y, return_counts=True))

    print("\nSplitting train/test for validation...")
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = LinearSVC(
        C=1.0,
        max_iter=20000,
        dual=False,
        class_weight="balanced"
    )

    print("\nTraining validation LSVM...")
    model.fit(X_train_s, y_train)

    pred = model.predict(X_test_s)
    acc = accuracy_score(y_test, pred)

    print("\nValidation finished.")
    print("Validation accuracy:", acc)
    print("Confusion matrix:")
    print(confusion_matrix(y_test, pred))
    print("Classification report:")
    print(classification_report(y_test, pred))

    print("\nRetraining final LSVM on ALL data for deployment...")
    final_scaler = StandardScaler()
    X_all_s = final_scaler.fit_transform(X)

    final_model = LinearSVC(
        C=1.0,
        max_iter=20000,
        dual=False,
        class_weight="balanced"
    )

    final_model.fit(X_all_s, y)

    np.savez(
        out_path,
        mean=final_scaler.mean_.astype(np.float32),
        scale=final_scaler.scale_.astype(np.float32),
        coef=final_model.coef_.astype(np.float32),
        intercept=final_model.intercept_.astype(np.float32),
        classes=final_model.classes_.astype(np.int32)
    )

    print("\nSaved FULL-data LSVM parameter file:")
    print(out_path)
    print("mean shape:", final_scaler.mean_.shape)
    print("scale shape:", final_scaler.scale_.shape)
    print("coef shape:", final_model.coef_.shape)
    print("intercept shape:", final_model.intercept_.shape)
    print("classes:", final_model.classes_)


if __name__ == "__main__":
    main()
