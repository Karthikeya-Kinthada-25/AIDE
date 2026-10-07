from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


# --------------------------------------------------
# Paths
# --------------------------------------------------

MANIFEST_FILE = Path(
    r"C:\Users\karthikeya\OneDrive\Desktop\AIDE\backend\dataset_tools\imd2020_manifest.csv"
)

OUTPUT_DIR = Path(
    r"C:\Users\karthikeya\OneDrive\Desktop\AIDE\backend\dataset_tools\splits"
)

RANDOM_STATE = 42


# --------------------------------------------------
# Split configuration
# --------------------------------------------------

TRAIN_SIZE = 0.70
VALIDATION_SIZE = 0.15
TEST_SIZE = 0.15


def main():

    if not MANIFEST_FILE.exists():
        print("ERROR: Manifest not found.")
        print(MANIFEST_FILE)
        return

    df = pd.read_csv(
        MANIFEST_FILE
    )

    print("=" * 60)
    print("IMD2020 CASE-LEVEL DATASET SPLIT")
    print("=" * 60)

    print(
        f"Total samples : {len(df)}"
    )

    print(
        f"Total cases   : {df['case_id'].nunique()}"
    )

    print()

    # --------------------------------------------------
    # First split:
    #
    # 70% train
    # 30% temporary
    # --------------------------------------------------

    splitter_1 = GroupShuffleSplit(
        n_splits=1,
        test_size=(1 - TRAIN_SIZE),
        random_state=RANDOM_STATE
    )

    train_indices, temp_indices = next(
        splitter_1.split(
            df,
            groups=df["case_id"]
        )
    )

    train_df = df.iloc[
        train_indices
    ].copy()

    temp_df = df.iloc[
        temp_indices
    ].copy()

    # --------------------------------------------------
    # Second split:
    #
    # Split remaining 30% into:
    # 15% validation
    # 15% test
    #
    # Therefore:
    # test_size = 0.5
    # --------------------------------------------------

    splitter_2 = GroupShuffleSplit(
        n_splits=1,
        test_size=0.5,
        random_state=RANDOM_STATE
    )

    validation_indices, test_indices = next(
        splitter_2.split(
            temp_df,
            groups=temp_df["case_id"]
        )
    )

    validation_df = temp_df.iloc[
        validation_indices
    ].copy()

    test_df = temp_df.iloc[
        test_indices
    ].copy()

    # --------------------------------------------------
    # Create output directory
    # --------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    train_file = OUTPUT_DIR / "train.csv"
    validation_file = OUTPUT_DIR / "validation.csv"
    test_file = OUTPUT_DIR / "test.csv"

    train_df.to_csv(
        train_file,
        index=False
    )

    validation_df.to_csv(
        validation_file,
        index=False
    )

    test_df.to_csv(
        test_file,
        index=False
    )

    # --------------------------------------------------
    # Print statistics
    # --------------------------------------------------

    print("-" * 60)
    print("TRAINING SET")
    print("-" * 60)

    print(
        f"Cases   : {train_df['case_id'].nunique()}"
    )

    print(
        f"Samples : {len(train_df)}"
    )

    print(
        f"Original: {(train_df['label'] == 0).sum()}"
    )

    print(
        f"Tampered: {(train_df['label'] == 1).sum()}"
    )

    print()

    print("-" * 60)
    print("VALIDATION SET")
    print("-" * 60)

    print(
        f"Cases   : {validation_df['case_id'].nunique()}"
    )

    print(
        f"Samples : {len(validation_df)}"
    )

    print(
        f"Original: {(validation_df['label'] == 0).sum()}"
    )

    print(
        f"Tampered: {(validation_df['label'] == 1).sum()}"
    )

    print()

    print("-" * 60)
    print("TEST SET")
    print("-" * 60)

    print(
        f"Cases   : {test_df['case_id'].nunique()}"
    )

    print(
        f"Samples : {len(test_df)}"
    )

    print(
        f"Original: {(test_df['label'] == 0).sum()}"
    )

    print(
        f"Tampered: {(test_df['label'] == 1).sum()}"
    )

    # --------------------------------------------------
    # Verify there is no case overlap
    # --------------------------------------------------

    train_cases = set(
        train_df["case_id"]
    )

    validation_cases = set(
        validation_df["case_id"]
    )

    test_cases = set(
        test_df["case_id"]
    )

    train_validation_overlap = (
        train_cases & validation_cases
    )

    train_test_overlap = (
        train_cases & test_cases
    )

    validation_test_overlap = (
        validation_cases & test_cases
    )

    print()

    print("-" * 60)
    print("LEAKAGE CHECK")
    print("-" * 60)

    print(
        "Train ↔ Validation overlap:",
        len(train_validation_overlap)
    )

    print(
        "Train ↔ Test overlap:",
        len(train_test_overlap)
    )

    print(
        "Validation ↔ Test overlap:",
        len(validation_test_overlap)
    )

    print()

    if (
        len(train_validation_overlap) == 0
        and len(train_test_overlap) == 0
        and len(validation_test_overlap) == 0
    ):
        print(
            "SUCCESS: No case-level data leakage detected."
        )
    else:
        print(
            "ERROR: Case overlap detected!"
        )

    print()

    print("-" * 60)
    print("OUTPUT FILES")
    print("-" * 60)

    print(train_file)
    print(validation_file)
    print(test_file)

    print("=" * 60)


if __name__ == "__main__":
    main()