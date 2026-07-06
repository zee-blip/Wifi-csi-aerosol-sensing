import os
import numpy as np

from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    x_path = os.path.join(base_dir, "data_sample", "X_sample_features.csv")
    y_path = os.path.join(base_dir, "data_sample", "Y_sample_labels.csv")

    model_dir = os.path.join(base_dir, "models")
    os.makedirs(model_dir, exist_ok=True)

    out_path = os.path.join(model_dir, "lsvm_edge_params.npz")

    print("Loading data...")
    print("X path:", x_path)
    print("Y path:", y_path)

    X = np.loadtxt(x_path, delimiter=",", dtype=np.float32)
    y = np.loadtxt(y_path, delimiter=",", dtype=np.int32).ravel()

    print("X shape:", X.shape)
    print("y shape:", y.shape)
    print("classes:", np.unique(y))

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=1,
        stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = LinearSVC(
        C=1.0,
        max_iter=10000,
        dual=False
    )

    print("Training LSVM...")
    model.fit(X_train_s, y_train)

    pred = model.predict(X_test_s)
    acc = accuracy_score(y_test, pred)

    print("Training finished.")
    print("Test accuracy:", acc)
    print("Confusion matrix:")
    print(confusion_matrix(y_test, pred))

    np.savez(
        out_path,
        mean=scaler.mean_.astype(np.float32),
        scale=scaler.scale_.astype(np.float32),
        coef=model.coef_.astype(np.float32),
        intercept=model.intercept_.astype(np.float32),
        classes=model.classes_.astype(np.int32)
    )

    print("Saved LSVM parameter file:", out_path)
    print("coef shape:", model.coef_.shape)
    print("intercept shape:", model.intercept_.shape)


if __name__ == "__main__":
    main()
