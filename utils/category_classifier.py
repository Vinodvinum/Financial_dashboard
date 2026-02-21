# utils/category_classifier.py

def classify_transaction(description):
    desc = str(description).lower()

    # -----------------------------
    # Specific Merchant FIRST
    # -----------------------------
    if any(word in desc for word in ["visonverse", "visionverse"]):
        return "VISONVERSE"

    # -----------------------------
    # Generic Types AFTER
    # -----------------------------
    elif "imps" in desc:
        return "IMPS Transfer"

    elif "upi" in desc:
        return "UPI Transfer"

    elif "bna" in desc or "cwdr" in desc:
        return "Cash Withdrawal"

    elif any(word in desc for word in ["recharge", "airtel", "vodafone"]):
        return "Recharge"

    elif "salary" in desc:
        return "Salary"

    elif any(word in desc for word in ["paytm", "bharatpe"]):
        return "Merchant Payment"

    else:
        return "Others"


def add_category(df):
    df["category"] = df["description"].apply(classify_transaction)
    return df