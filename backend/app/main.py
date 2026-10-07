from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path

from app.upload import router as upload_router
from app.analyzer import analyze_image
from app.forensic import perform_ela
from app.forensic_engine import extract_forensic_features
from app.scoring import generate_fusion_analysis
from app.ai_detector.inference import AIDetector
from app.evidence_fusion import generate_evidence_fusion
from app.localization import generate_suspicious_region_map
from app.report_generator import generate_forensic_report
from app.manipulation_classifier import classify_manipulation_type

from app.database import SessionLocal
from app.models import EvidenceImage, ForensicAnalysis


# =========================================================
# AIDE APPLICATION
# =========================================================

app = FastAPI(
    title="AIDE",
    description=(
        "AI-Powered Multi-Forensic Platform for "
        "Digital Image Evidence Integrity and Tampering Detection"
    ),
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DIRECTORIES
# =========================================================

UPLOAD_DIR = (
    Path(__file__).resolve().parent.parent / "uploads"
)

ELA_DIR = UPLOAD_DIR

REPORT_DIR = (
    Path(__file__).resolve().parent.parent / "reports"
)

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# =========================================================
# AI DETECTOR
# =========================================================

# Load the trained ResNet18 model once when
# the backend starts.
#
# This prevents the model from being loaded
# again for every image analysis request.

ai_detector = AIDetector()


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "project": "AIDE",
        "full_name": "Artificial Intelligence for Digital Evidence",
        "status": "Backend is running"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "AIDE Backend"
    }


# =========================================================
# IMAGE ANALYSIS
# =========================================================

@app.get("/api/analyze/{filename}")
def analyze_uploaded_image(filename: str):

    file_path = UPLOAD_DIR / filename


    # -----------------------------------------------------
    # Check whether image exists
    # -----------------------------------------------------

    if not file_path.exists():

        return {
            "status": "error",
            "message": "Image not found"
        }


    # -----------------------------------------------------
    # 1. Basic image analysis
    # -----------------------------------------------------

    basic_analysis = analyze_image(
        file_path
    )


    # -----------------------------------------------------
    # 2. ELA analysis
    # -----------------------------------------------------

    ela_analysis = perform_ela(
        file_path
    )


    # -----------------------------------------------------
    # 3. Forensic feature extraction
    # -----------------------------------------------------

    forensic_features = extract_forensic_features(
        file_path
    )


    # -----------------------------------------------------
    # 4. Multi-forensic fusion
    # -----------------------------------------------------

    fusion_analysis = generate_fusion_analysis(
        ela_analysis,
        forensic_features
    )


    # -----------------------------------------------------
    # 4A. AI tampering detection
    # -----------------------------------------------------

    ai_analysis = ai_detector.predict(
        file_path
    )
    # -----------------------------------------------------
    # 4B. AI + traditional forensic evidence fusion
    # -----------------------------------------------------
    
    evidence_fusion = generate_evidence_fusion(
        ai_analysis,
        fusion_analysis
    )


    # -----------------------------------------------------
    # 5. Database session
    # -----------------------------------------------------

    db = SessionLocal()


    try:

        image_info = basic_analysis["image"]


        # -------------------------------------------------
        # 6. Check whether evidence already exists
        # -------------------------------------------------

        existing_evidence = (
            db.query(EvidenceImage)
            .filter(
                EvidenceImage.stored_filename == filename
            )
            .first()
        )


        # -------------------------------------------------
        # 7. Create new evidence OR reuse existing evidence
        # -------------------------------------------------

        if existing_evidence:

            evidence = existing_evidence

        else:

            evidence = EvidenceImage(

                original_filename=filename,

                stored_filename=filename,

                file_type=image_info["format"],

                file_size=image_info[
                    "file_size_bytes"
                ],

                width=image_info["width"],

                height=image_info["height"],

                format=image_info["format"],

                megapixels=image_info["megapixels"],

                metadata_status=(
                    basic_analysis[
                        "metadata_status"
                    ]
                )
            )

            db.add(evidence)


            # Flush sends INSERT to PostgreSQL
            # and gives us the generated ID
            # without committing yet.

            db.flush()


        # -------------------------------------------------
        # 8. Check whether forensic analysis already exists
        # -------------------------------------------------

        existing_analysis = (
            db.query(ForensicAnalysis)
            .filter(
                ForensicAnalysis.evidence_id == evidence.id
            )
            .first()
        )


        noise = forensic_features["noise"]


        # -------------------------------------------------
        # 9. Update existing forensic analysis
        # -------------------------------------------------

        if existing_analysis:

            forensic_record = existing_analysis


            forensic_record.ela_mean_error = (
                ela_analysis.get(
                    "mean_error"
                )
            )


            forensic_record.ela_maximum_error = (
                ela_analysis.get(
                    "maximum_error"
                )
            )


            forensic_record.ela_standard_deviation = (
                ela_analysis.get(
                    "standard_deviation"
                )
            )


            forensic_record.entropy = (
                forensic_features.get(
                    "entropy"
                )
            )


            forensic_record.noise_mean = (
                noise.get(
                    "noise_mean"
                )
            )


            forensic_record.noise_standard_deviation = (
                noise.get(
                    "noise_standard_deviation"
                )
            )


            forensic_record.edge_density = (
                forensic_features.get(
                    "edge_density_percent"
                )
            )


            forensic_record.laplacian_variance = (
                forensic_features.get(
                    "laplacian_variance"
                )
            )


            forensic_record.forensic_score = (
                fusion_analysis.get(
                    "score"
                )
            )


            forensic_record.assessment_level = (
                fusion_analysis[
                    "assessment"
                ].get(
                    "level"
                )
            )


            forensic_record.warning = (
                fusion_analysis.get(
                    "warning"
                )
            )


        # -------------------------------------------------
        # 10. Create new forensic analysis
        # -------------------------------------------------

        else:

            forensic_record = ForensicAnalysis(

                evidence_id=evidence.id,


                ela_mean_error=(
                    ela_analysis.get(
                        "mean_error"
                    )
                ),


                ela_maximum_error=(
                    ela_analysis.get(
                        "maximum_error"
                    )
                ),


                ela_standard_deviation=(
                    ela_analysis.get(
                        "standard_deviation"
                    )
                ),


                entropy=(
                    forensic_features.get(
                        "entropy"
                    )
                ),


                noise_mean=(
                    noise.get(
                        "noise_mean"
                    )
                ),


                noise_standard_deviation=(
                    noise.get(
                        "noise_standard_deviation"
                    )
                ),


                edge_density=(
                    forensic_features.get(
                        "edge_density_percent"
                    )
                ),


                laplacian_variance=(
                    forensic_features.get(
                        "laplacian_variance"
                    )
                ),


                forensic_score=(
                    fusion_analysis.get(
                        "score"
                    )
                ),


                assessment_level=(
                    fusion_analysis[
                        "assessment"
                    ].get(
                        "level"
                    )
                ),


                warning=(
                    fusion_analysis.get(
                        "warning"
                    )
                )
            )

            db.add(
                forensic_record
            )


        # -------------------------------------------------
        # 11. Commit database transaction
        # -------------------------------------------------

        db.commit()


        # -------------------------------------------------
        # 12. Return successful response
        # -------------------------------------------------

        return {

            "status": "success",

            "filename": filename,


            # ---------------------------------------------
            # Basic image + metadata analysis
            # ---------------------------------------------

            "analysis": basic_analysis,


            # ---------------------------------------------
            # Complete forensic analysis
            # ---------------------------------------------

            "forensic_analysis": {

                "ela": ela_analysis,

                "features": forensic_features,

                "fusion": fusion_analysis,

                # -----------------------------------------
                # AI DETECTION
                # -----------------------------------------

                "ai_detection": ai_analysis,

                "evidence_fusion": evidence_fusion
            },


            # ---------------------------------------------
            # Database information
            # ---------------------------------------------

            "database": {

                "status": "saved",

                "evidence_id": evidence.id,

                "operation": (
                    "updated"
                    if existing_evidence
                    else "created"
                )
            }
        }


    # -----------------------------------------------------
    # Database / analysis error
    # -----------------------------------------------------

    except Exception as error:

        db.rollback()


        print(
            "========================================"
        )

        print(
            "DATABASE ERROR:"
        )

        print(
            repr(error)
        )

        print(
            "========================================"
        )


        return {

            "status": "error",

            "message": (
                "Failed to save analysis to database"
            ),

            "error": str(error)
        }


    finally:

        db.close()


# =========================================================
# ELA IMAGE
# =========================================================

@app.get("/api/forensics/ela/{filename}")
def get_ela_image(filename: str):

    ela_path = ELA_DIR / filename


    if not ela_path.exists():

        return {

            "status": "error",

            "message": "ELA image not found."
        }


    return FileResponse(

        path=ela_path,

        media_type="image/png",

        headers={
            "Content-Disposition": "inline"
        }
    )
# ---------------------------------------------------------
# Suspicious-Region Localization
# ---------------------------------------------------------

@app.get("/api/forensics/localization/{filename}")
def get_localization(filename: str):

    file_path = UPLOAD_DIR / filename

    # -----------------------------------------------------
    # Check whether original image exists
    # -----------------------------------------------------

    if not file_path.exists():

        return {
            "status": "error",
            "message": "Image not found."
        }

    try:

        # -------------------------------------------------
        # Generate localization analysis
        # -------------------------------------------------

        localization_analysis = (
            generate_suspicious_region_map(
                file_path
            )
        )

        # -------------------------------------------------
        # If localization is not applicable
        # -------------------------------------------------

        if (
            localization_analysis.get("status")
            != "success"
        ):

            return localization_analysis

        # -------------------------------------------------
        # Add image URL for frontend
        # -------------------------------------------------

        localization_filename = (
            localization_analysis.get(
                "localization_image"
            )
        )

        localization_analysis[
            "localization_url"
        ] = (
            f"/api/forensics/localization/image/"
            f"{localization_filename}"
        )

        return localization_analysis

    except Exception as error:

        print(
            "========================================"
        )

        print(
            "LOCALIZATION ERROR:"
        )

        print(
            repr(error)
        )

        print(
            "========================================"
        )

        return {
            "status": "error",
            "message": (
                "Suspicious-region localization failed."
            ),
            "error": str(error)
        }


# ---------------------------------------------------------
# Suspicious-Region Localization Image
# ---------------------------------------------------------

# ---------------------------------------------------------
# Suspicious-Region Localization Image
# ---------------------------------------------------------

@app.get(
    "/api/forensics/localization/image/{filename}"
)
def get_localization_image(filename: str):

    # -----------------------------------------------------
    # Convert localization filename back to original
    # image filename
    # -----------------------------------------------------

    localization_suffix = (
        "_suspicious_regions.jpg"
    )

    if not filename.endswith(
        localization_suffix
    ):

        return {
            "status": "error",
            "message": (
                "Invalid localization image filename."
            )
        }


    original_stem = filename[
        :-len(localization_suffix)
    ]


    # -----------------------------------------------------
    # Locate the original uploaded JPEG
    # -----------------------------------------------------

    original_jpg = (
        UPLOAD_DIR /
        f"{original_stem}.jpg"
    )

    original_jpeg = (
        UPLOAD_DIR /
        f"{original_stem}.jpeg"
    )


    if original_jpg.exists():

        original_path = original_jpg

    elif original_jpeg.exists():

        original_path = original_jpeg

    else:

        return {
            "status": "error",
            "message": (
                "Original image for localization "
                "was not found."
            )
        }


    try:

        # -------------------------------------------------
        # ALWAYS regenerate localization visualization
        # -------------------------------------------------

        localization_result = (
            generate_suspicious_region_map(
                original_path
            )
        )


        if (
            localization_result.get("status")
            != "success"
        ):

            return localization_result


        # -------------------------------------------------
        # Get freshly generated visualization path
        # -------------------------------------------------

        generated_filename = (
            localization_result.get(
                "localization_image"
            )
        )


        generated_path = (
            UPLOAD_DIR /
            generated_filename
        )


        # -------------------------------------------------
        # Verify generated image
        # -------------------------------------------------

        if not generated_path.exists():

            return {
                "status": "error",
                "message": (
                    "Localization visualization "
                    "could not be generated."
                )
            }


        # -------------------------------------------------
        # Return the ACTUAL localization image
        # -------------------------------------------------

        return FileResponse(

            path=generated_path,

            media_type="image/jpeg",

            headers={
                "Content-Disposition": "inline"
            }

        )


    except Exception as error:

        print(
            "========================================"
        )

        print(
            "LOCALIZATION IMAGE ERROR:"
        )

        print(
            repr(error)
        )

        print(
            "========================================"
        )


        return {
            "status": "error",
            "message": (
                "Unable to generate localization image."
            ),
            "error": str(error)
        }
# =========================================================
# PDF FORENSIC REPORT
# =========================================================

@app.post("/api/reports/generate/{filename}")
def generate_report(filename: str):

    # -----------------------------------------------------
    # Locate uploaded evidence
    # -----------------------------------------------------

    file_path = UPLOAD_DIR / filename

    if not file_path.exists():

        return {
            "status": "error",
            "message": "Evidence image not found."
        }


    try:

        # -------------------------------------------------
        # Run the same complete AIDE analysis
        # -------------------------------------------------

        analysis_result = analyze_image(
            file_path
        )


        # -------------------------------------------------
        # ELA
        # -------------------------------------------------

        ela_result = perform_ela(
            file_path
        )


        # -------------------------------------------------
        # Traditional forensic features
        # -------------------------------------------------

        forensic_features = (
            extract_forensic_features(
                file_path
            )
        )


        # -------------------------------------------------
        # Prototype forensic fusion
        # -------------------------------------------------

        fusion_result = (
            generate_fusion_analysis(
                ela_result,
                forensic_features
            )
        )


        # -------------------------------------------------
        # AI detection
        # -------------------------------------------------

        ai_result = None

        try:

            from app.ai_detector.inference import (
                AIDetector
            )

            model_path = (
                Path(__file__).resolve()
                .parent.parent
                / "models"
                / "aide_tampering_resnet18_balanced.pth"
            )


            detector = AIDetector(
                model_path=model_path
            )


            ai_result = detector.predict(
                file_path
            )

        except Exception as ai_error:

            ai_result = {
                "status": "error",
                "prediction_available": False,
                "message": (
                    "AI analysis could not be included."
                ),
                "error": str(ai_error)
            }


        # -------------------------------------------------
        # Evidence fusion
        # -------------------------------------------------

        evidence_fusion = None

        try:

            # Use the same fusion function already present
            # in your main analysis pipeline if available.

            from app.evidence_fusion import (
                generate_evidence_fusion
            )

            evidence_fusion = (
                generate_evidence_fusion(
                    ai_result,
                    fusion_result
                )
            )

        except Exception:

            # Keep report generation functional even if
            # the optional evidence-fusion import is not
            # available in this endpoint.

            evidence_fusion = {
                "status": "not_available",
                "message": (
                    "Evidence fusion result was not "
                    "available during report generation."
                )
            }


        # -------------------------------------------------
        # Suspicious-region localization
        # -------------------------------------------------

        localization_result = (
            generate_suspicious_region_map(
                file_path
            )
        )


        # -------------------------------------------------
        # Manipulation-type indication
        # -------------------------------------------------

        manipulation_result = (
            classify_manipulation_type(
                image_path=file_path,
                ela_analysis=ela_result,
                localization=localization_result,
                image_width=int(
                    analysis_result.get("image", {}).get(
                        "width",
                        0
                    )
                ),
                image_height=int(
                    analysis_result.get("image", {}).get(
                        "height",
                        0
                    )
                )
            )
        )


        # -------------------------------------------------
        # Build complete analysis structure
        # -------------------------------------------------

        complete_analysis = {

            "status": "success",

            "filename": filename,

            "analysis": analysis_result,

            "forensic_analysis": {

                "ela": ela_result,

                "features": forensic_features,

                "fusion": fusion_result,

                "ai_detection": ai_result,

                "evidence_fusion": evidence_fusion,

            },

            "localization": localization_result,

            "manipulation_type": manipulation_result,

        }


        # -------------------------------------------------
        # Determine generated image paths
        # -------------------------------------------------

        ela_image_path = None

        if (
            ela_result.get(
                "ela_image"
            )
        ):

            ela_image_path = (
                UPLOAD_DIR
                / ela_result["ela_image"]
            )


        localization_image_path = None

        if (
            localization_result.get(
                "localization_image"
            )
        ):

            localization_image_path = (
                UPLOAD_DIR
                / localization_result[
                    "localization_image"
                ]
            )


        # -------------------------------------------------
        # Report filename
        # -------------------------------------------------

        report_filename = (
            f"{Path(filename).stem}_"
            f"AIDE_Forensic_Report.pdf"
        )


        report_path = (
            REPORT_DIR /
            report_filename
        )


        # -------------------------------------------------
        # Generate PDF
        # -------------------------------------------------

        generate_forensic_report(

            report_path=report_path,

            evidence_filename=filename,

            analysis_data=complete_analysis,

            original_image_path=file_path,

            ela_image_path=ela_image_path,

            localization_image_path=(
                localization_image_path
            ),

            manipulation_analysis=manipulation_result

        )


        # -------------------------------------------------
        # Verify PDF
        # -------------------------------------------------

        if not report_path.exists():

            return {
                "status": "error",
                "message": (
                    "PDF report was not generated."
                )
            }


        # -------------------------------------------------
        # Return result
        # -------------------------------------------------

        return {

            "status": "success",

            "message": (
                "AIDE forensic report generated "
                "successfully."
            ),

            "filename": report_filename,

            "report_url": (
                f"/api/reports/file/"
                f"{report_filename}"
            ),

            "file_size_bytes": (
                report_path.stat().st_size
            )

        }


    except Exception as error:

        print(
            "========================================"
        )

        print(
            "PDF REPORT ERROR:"
        )

        print(
            repr(error)
        )

        print(
            "========================================"
        )


        return {

            "status": "error",

            "message": (
                "Unable to generate forensic report."
            ),

            "error": str(error)

        }


# =========================================================
# SERVE GENERATED PDF
# =========================================================

@app.get(
    "/api/reports/file/{filename}"
)
def get_report_file(filename: str):

    report_path = (
        REPORT_DIR /
        filename
    )


    if not report_path.exists():

        return {

            "status": "error",

            "message": (
                "Forensic report not found."
            )

        }


    return FileResponse(

        path=report_path,

        media_type="application/pdf",

        headers={
            "Content-Disposition":
                f'inline; filename="{filename}"'
        }

    )

# =========================================================
# IMAGE UPLOAD ROUTER
# =========================================================

# ---------------------------------------------------------
# Manipulation-Type Indication
# ---------------------------------------------------------

@app.get("/api/forensics/manipulation/{filename}")
def get_manipulation_type(filename: str):

    file_path = UPLOAD_DIR / filename

    # -----------------------------------------------------
    # Check image
    # -----------------------------------------------------

    if not file_path.exists():

        return {
            "status": "error",
            "message": "Image not found"
        }

    try:

        # -------------------------------------------------
        # Basic image information
        # -------------------------------------------------

        basic_analysis = analyze_image(
            file_path
        )

        image_info = basic_analysis.get(
            "image",
            {}
        )

        image_width = int(
            image_info.get(
                "width",
                0
            )
        )

        image_height = int(
            image_info.get(
                "height",
                0
            )
        )

        # -------------------------------------------------
        # ELA analysis
        # -------------------------------------------------

        ela_analysis = perform_ela(
            file_path
        )

        # -------------------------------------------------
        # Preliminary localization summary
        #
        # We intentionally keep this separate from the
        # existing localization visualization module.
        # The manipulation classifier only needs candidate
        # region information.
        # -------------------------------------------------

        localization_summary = {
            "candidate_regions": 0,
            "regions": []
        }

        # -------------------------------------------------
        # Estimate ELA candidate regions
        # -------------------------------------------------

        if ela_analysis.get("status") == "success":

            try:

                import cv2
                import numpy as np

                ela_path = (
                    UPLOAD_DIR /
                    ela_analysis.get(
                        "ela_image",
                        ""
                    )
                )

                if ela_path.exists():

                    ela_image = cv2.imread(
                        str(ela_path),
                        cv2.IMREAD_COLOR
                    )

                    if ela_image is not None:

                        gray = cv2.cvtColor(
                            ela_image,
                            cv2.COLOR_BGR2GRAY
                        )

                        # Strong brightness regions in
                        # the generated ELA visualization.
                        threshold_value = 180

                        _, binary = cv2.threshold(
                            gray,
                            threshold_value,
                            255,
                            cv2.THRESH_BINARY
                        )

                        contours, _ = cv2.findContours(
                            binary,
                            cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE
                        )

                        regions = []

                        image_area = (
                            image_width *
                            image_height
                        )

                        for contour in contours:

                            x, y, w, h = (
                                cv2.boundingRect(
                                    contour
                                )
                            )

                            area = float(
                                cv2.contourArea(
                                    contour
                                )
                            )

                            if area < 100:
                                continue

                            # Ignore extremely large
                            # image-wide regions.
                            if (
                                image_area > 0
                                and area >
                                image_area * 0.01
                            ):
                                continue

                            regions.append(
                                {
                                    "x": int(x),
                                    "y": int(y),
                                    "width": int(w),
                                    "height": int(h),
                                    "area": round(
                                        area,
                                        2
                                    )
                                }
                            )

                        localization_summary = {
                            "candidate_regions": len(
                                regions
                            ),
                            "regions": regions[:20]
                        }

            except Exception as localization_error:

                print(
                    "Manipulation localization "
                    "summary warning:",
                    repr(localization_error)
                )

        # -------------------------------------------------
        # Manipulation-type indication
        # -------------------------------------------------

        manipulation_result = (
            classify_manipulation_type(
                image_path=file_path,
                ela_analysis=ela_analysis,
                localization=localization_summary,
                image_width=image_width,
                image_height=image_height
            )
        )

        # -------------------------------------------------
        # Response
        # -------------------------------------------------

        return {
            "status": "success",
            "filename": filename,
            "manipulation_type": manipulation_result
        }

    except Exception as error:

        print(
            "========================================"
        )

        print(
            "MANIPULATION ANALYSIS ERROR:"
        )

        print(
            repr(error)
        )

        print(
            "========================================"
        )

        return {
            "status": "error",
            "message": (
                "Manipulation-type analysis failed"
            ),
            "error": str(error)
        }

app.include_router(
    upload_router
)