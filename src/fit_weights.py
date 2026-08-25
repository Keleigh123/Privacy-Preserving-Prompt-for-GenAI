import sys
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, classification_report

LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
LEVEL_TO_ORD = {l: i for i, l in enumerate(LEVELS)}

REGEX_COLS = ["email", "phone", "credit_card", "iban", "ip", "api_key"]
NER_COLS = ["person", "org", "gpe", "loc", "product"]
ENT_COLS = ["ent_high", "ent_medium"]
FEATURE_COLS = REGEX_COLS + NER_COLS + ENT_COLS


def load_data(path):
    df = pd.read_csv(path)
    X = df[FEATURE_COLS].values.astype(float)
    sim = df["semantic"].values.astype(float)
    y = df["expected"].map(LEVEL_TO_ORD).values
    return df, X, sim, y


def score_and_predict(X, sim, w, bonus, t1, t2, t3, s1, s2, s3):
    base = X @ w
    regex_active = X[:, :len(REGEX_COLS)].sum(axis=1) > 0
    ner_active = X[:, len(REGEX_COLS):len(REGEX_COLS) + len(NER_COLS)].sum(axis=1) > 0
    ent_active = X[:, -len(ENT_COLS):].sum(axis=1) > 0
    n_groups = regex_active.astype(int) + ner_active.astype(int) + ent_active.astype(int)
    score = np.where(n_groups >= 2, base * bonus, base)
    score = np.clip(score, 0, 100)

    pred = np.zeros(len(X), dtype=int)
    has_signal = score > 0

    #thresholds on 0-100 score
    thresholds = sorted([t1, t2, t3])
    pred_signal = np.digitize(score, thresholds)  # 0..3
    pred = np.where(has_signal, pred_signal, pred)

    #semantic similarity only, when nothing else fired
    sthresh = sorted([s1, s2, s3])
    pred_sem = np.digitize(sim, sthresh)
    pred = np.where(~has_signal, pred_sem, pred)

    return pred, score


def random_search(X, sim, y, n_iter=60000, seed=0):
    rng = np.random.default_rng(seed)
    n_feat = X.shape[1]
    best = None
    best_key = None

    for _ in range(n_iter):
        w = np.zeros(n_feat)
        w[:len(REGEX_COLS)] = rng.uniform(0, 90, len(REGEX_COLS))
        w[len(REGEX_COLS):len(REGEX_COLS) + len(NER_COLS)] = rng.uniform(0, 35, len(NER_COLS))
        w[-len(ENT_COLS):] = rng.uniform(0, 100, len(ENT_COLS))
        bonus = rng.uniform(1.0, 2.2)
        t1, t2, t3 = np.sort(rng.uniform(0, 100, 3))
        s1, s2, s3 = np.sort(rng.uniform(0, 1, 3))

        pred, _ = score_and_predict(X, sim, w, bonus, t1, t2, t3, s1, s2, s3)
        acc = np.mean(pred == y)
        mae = np.mean(np.abs(pred - y))
        key = (acc, -mae)

        if best_key is None or key > best_key:
            best_key = key
            best = dict(w=w, bonus=bonus, t1=t1, t2=t2, t3=t3, s1=s1, s2=s2, s3=s3,
                        acc=acc, mae=mae)

    return best


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "calibration_dataset.csv"
    df, X, sim, y = load_data(path)

    n = len(y)
    n_train = int(n * 0.7)
    rng = np.random.default_rng(42)
    idx = rng.permutation(n)
    train_idx, test_idx = idx[:n_train], idx[n_train:]

    best = random_search(X[train_idx], sim[train_idx], y[train_idx])

    pred_all, score_all = score_and_predict(X, sim, best["w"], best["bonus"],
                                             best["t1"], best["t2"], best["t3"],
                                             best["s1"], best["s2"], best["s3"])

    print(f"Train accuracy: {best['acc']:.3f}   Train MAE(ordinal): {best['mae']:.3f}\n")
    print("REGEX_WEIGHTS =", {c: round(v, 1) for c, v in zip(REGEX_COLS, best["w"][:6])})
    print("NER_WEIGHTS   =", {c: round(v, 1) for c, v in zip(NER_COLS, best["w"][6:11])})
    print("ENTERPRISE    =", {c: round(v, 1) for c, v in zip(ENT_COLS, best["w"][11:13])})
    print(f"co-occurrence bonus (>=2 categories fire) = x{best['bonus']:.2f}")
    print(f"score thresholds (LOW|MEDIUM|HIGH|CRITICAL cuts) = "
          f"{best['t1']:.1f}, {best['t2']:.1f}, {best['t3']:.1f}")
    print(f"semantic-fallback thresholds = "
          f"{best['s1']:.2f}, {best['s2']:.2f}, {best['s3']:.2f}\n")

    print("Test split performance")
    y_test, pred_test = y[test_idx], pred_all[test_idx]
    print(f"Test accuracy: {np.mean(y_test == pred_test):.3f}")
    print(f"Test MAE(ordinal): {np.mean(np.abs(y_test - pred_test)):.3f}\n")
    print(classification_report(y_test, pred_test, target_names=LEVELS, zero_division=0))

    print("=== Full-dataset confusion matrix (rows=expected, cols=predicted) ===")
    cm = confusion_matrix(y, pred_all, labels=[0, 1, 2, 3])
    cm_df = pd.DataFrame(cm, index=LEVELS, columns=LEVELS)
    print(cm_df, "\n")

    mism = df.copy()
    mism["predicted"] = [LEVELS[p] for p in pred_all]
    mism["score"] = score_all.round(1)
    mism = mism[mism["expected"] != mism["predicted"]]
    print(f"=== {len(mism)} mismatches out of {n} ===")
    print(mism[["id", "prompt", "expected", "predicted", "score"]].to_string(index=False))


if __name__ == "__main__":
    main()