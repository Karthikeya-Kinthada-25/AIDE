from typing import Dict


def generate_evidence_fusion(
    ai_analysis: Dict,
    forensic_fusion: Dict
) -> Dict:
    """
    Combine AI model evidence with traditional forensic
    consistency evidence.

    IMPORTANT:
    This module does NOT produce a validated probability
    of tampering.

    AI probabilities and the forensic consistency index
    represent different measurements and are therefore
    reported separately.

    The result is an interpretive evidence assessment.
    """

    # -----------------------------------------------------
    # AI information
    # -----------------------------------------------------

    ai_prediction = ai_analysis.get(
        "prediction",
        "Unknown"
    )

    tampered_probability = float(
        ai_analysis.get(
            "tampered_probability",
            0.0
        )
    )

    original_probability = float(
        ai_analysis.get(
            "original_probability",
            0.0
        )
    )


    # -----------------------------------------------------
    # Traditional forensic information
    # -----------------------------------------------------

    forensic_score = float(
        forensic_fusion.get(
            "score",
            0.0
        )
    )

    forensic_assessment = (
        forensic_fusion.get(
            "assessment",
            {}
        )
    )

    forensic_level = forensic_assessment.get(
        "level",
        "UNKNOWN"
    )


    # -----------------------------------------------------
    # Determine evidence relationship
    # -----------------------------------------------------

    if ai_prediction == "Tampered":

        if forensic_level == "LOW CONSISTENCY":

            agreement = "CONVERGING INDICATIONS"

            assessment = (
                "The AI model indicates the Tampered class, "
                "while the traditional forensic consistency "
                "assessment is lower. The two evidence sources "
                "provide converging indications that warrant "
                "further forensic examination."
            )

            review_status = "REQUIRES FORENSIC REVIEW"

        elif forensic_level == "MODERATE CONSISTENCY":

            agreement = "MIXED / SUPPORTING EVIDENCE"

            assessment = (
                "The AI model indicates the Tampered class. "
                "Traditional forensic indicators show moderate "
                "consistency under the current analysis "
                "conditions. Further forensic examination "
                "is recommended."
            )

            review_status = "REQUIRES FORENSIC REVIEW"

        else:

            agreement = "AI INDICATION + FORENSIC CONSISTENCY"

            assessment = (
                "The AI model indicates the Tampered class, "
                "while the traditional forensic indicators "
                "show relatively high consistency with the "
                "current analysis conditions. These measurements "
                "should be reviewed together and do not by "
                "themselves establish a definitive tampering verdict."
            )

            review_status = "REQUIRES FORENSIC REVIEW"


    elif ai_prediction == "Original":

        if forensic_level == "LOW CONSISTENCY":

            agreement = "CONFLICTING INDICATIONS"

            assessment = (
                "The AI model indicates the Original class, "
                "while traditional forensic indicators show "
                "lower consistency. Additional examination "
                "is recommended."
            )

            review_status = "REQUIRES FORENSIC REVIEW"

        else:

            agreement = "NO STRONG TAMPERING INDICATION"

            assessment = (
                "The AI model indicates the Original class "
                "and the traditional forensic indicators do "
                "not currently show a low-consistency condition. "
                "The result should still be treated as a "
                "computational forensic indication."
            )

            review_status = "ADDITIONAL REVIEW RECOMMENDED"


    else:

        agreement = "INSUFFICIENT AI RESULT"

        assessment = (
            "A definitive combined assessment cannot be "
            "generated because the AI prediction is unavailable "
            "or unknown."
        )

        review_status = "REQUIRES FORENSIC REVIEW"


    # -----------------------------------------------------
    # Return combined evidence
    # -----------------------------------------------------

    return {

        "status": "success",

        "assessment_type": (
            "AIDE Combined Evidence Assessment"
        ),

        "ai_evidence": {

            "prediction": ai_prediction,

            "original_probability": round(
                original_probability,
                4
            ),

            "tampered_probability": round(
                tampered_probability,
                4
            )
        },

        "forensic_evidence": {

            "consistency_score": round(
                forensic_score,
                2
            ),

            "assessment_level": forensic_level
        },

        "evidence_relationship": agreement,

        "combined_assessment": assessment,

        "review_status": review_status,

        "warning": (
            "This combined assessment is a prototype "
            "interpretive layer. It is not a validated "
            "forensic probability, legal conclusion, or "
            "definitive determination of image authenticity "
            "or tampering."
        )
    }