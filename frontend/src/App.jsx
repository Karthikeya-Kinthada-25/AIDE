import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);

  const [analysis, setAnalysis] = useState(null);
  const [manipulation, setManipulation] = useState(null);
  const [localization, setLocalization] = useState(null);

  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [localizing, setLocalizing] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportError, setReportError] = useState("");
  const [storedFilename, setStoredFilename] = useState("");

  const [error, setError] = useState("");

  // =========================================================
  // FILE SELECTION
  // =========================================================

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setSelectedFile(file);
    setAnalysis(null);
    setManipulation(null);
    setLocalization(null);
    setStoredFilename("");
    setGeneratingReport(false);
    setReportError("");
    setError("");

    const previewUrl = URL.createObjectURL(file);

    setPreview(previewUrl);
  };

  // =========================================================
  // ANALYZE EVIDENCE
  // =========================================================

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError("Please select an image first.");
      return;
    }

    setUploading(true);
    setAnalyzing(false);
    setLocalizing(false);

    setError("");
    setAnalysis(null);
    setManipulation(null);
    setLocalization(null);

    try {
      // =====================================================
      // STEP 1 — UPLOAD
      // =====================================================

      const formData = new FormData();

      formData.append(
        "file",
        selectedFile
      );

      const uploadResponse = await fetch(
        `${API_URL}/api/upload/`,
        {
          method: "POST",
          body: formData,
        }
      );

      const uploadData =
        await uploadResponse.json();

      if (
        !uploadResponse.ok ||
        uploadData.status !== "success"
      ) {
        throw new Error(
          uploadData.detail ||
            uploadData.message ||
            "Image upload failed."
        );
      }

      setUploading(false);
      setAnalyzing(true);

      // =====================================================
      // STEP 2 — MAIN FORENSIC ANALYSIS
      // =====================================================

      const storedFilename =
        uploadData.stored_filename;

      setStoredFilename(storedFilename);

      const analysisResponse =
        await fetch(
          `${API_URL}/api/analyze/${encodeURIComponent(
            storedFilename
          )}`
        );

      const data =
        await analysisResponse.json();

      if (
        !analysisResponse.ok ||
        data.status !== "success"
      ) {
        throw new Error(
          data.detail ||
            data.message ||
            data.error ||
            "Image analysis failed."
        );
      }

      // -----------------------------------------------------
      // Store complete main analysis
      // -----------------------------------------------------

      setAnalysis(data);

      // =====================================================
      // MAIN ANALYSIS COMPLETE
      // Release the main Analyze button state immediately.
      // Manipulation analysis must NEVER block the workflow.
      // =====================================================

      setAnalyzing(false);
      setLocalizing(true);

      // =====================================================
      // MANIPULATION-TYPE INDICATION
      // Run independently so a slow/hanging backend endpoint
      // cannot keep the UI stuck on "Analyzing Evidence..."
      // =====================================================

      const runManipulationAnalysis = async () => {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
          controller.abort();
        }, 30000);

        try {
          const manipulationResponse = await fetch(
            `${API_URL}/api/forensics/manipulation/${encodeURIComponent(
              storedFilename
            )}`,
            {
              method: "GET",
              signal: controller.signal,
            }
          );

          const manipulationData =
            await manipulationResponse.json();

          if (
            manipulationResponse.ok &&
            manipulationData.status === "success"
          ) {
            setManipulation(
              manipulationData.manipulation_type
            );
          } else {
            setManipulation({
              status: "error",
              message:
                manipulationData.message ||
                manipulationData.error ||
                "Manipulation-type analysis failed.",
            });
          }
        } catch (manipulationError) {
          console.error(
            "Manipulation-type analysis error:",
            manipulationError
          );

          setManipulation({
            status: "error",
            message:
              manipulationError.name === "AbortError"
                ? "Manipulation-type analysis timed out. Other forensic results are still available."
                : "Manipulation-type analysis could not be completed.",
          });
        } finally {
          clearTimeout(timeoutId);
        }
      };

      // Do NOT await this call.
      // It must not block localization or the UI.
      runManipulationAnalysis();

      // =====================================================
      // STEP 3 — SUSPICIOUS-REGION LOCALIZATION
      // =====================================================

      try {
        const localizationResponse =
          await fetch(
            `${API_URL}/api/forensics/localization/${encodeURIComponent(
              storedFilename
            )}`
          );

        const localizationData =
          await localizationResponse.json();

        if (
          localizationResponse.ok &&
          localizationData.status === "success"
        ) {
          setLocalization(
            localizationData
          );
        } else {
          setLocalization({
            status: "error",
            message:
              localizationData.message ||
              "Suspicious-region localization failed.",
          });
        }
      } catch (localizationError) {
        console.error(
          "Localization error:",
          localizationError
        );

        setLocalization({
          status: "error",
          message:
            "Suspicious-region localization could not be completed."
        });
      }

      setLocalizing(false);

    } catch (err) {
      setError(
        err.message ||
          "Something went wrong during analysis."
      );
    } finally {
      setUploading(false);
      setAnalyzing(false);
      setLocalizing(false);
    }
  };

  // =========================================================
  // GENERATE AND DOWNLOAD PDF REPORT
  // =========================================================

  const handleGenerateReport = async () => {
    if (!storedFilename) {
      setReportError(
        "Please complete an image analysis before generating the report."
      );
      return;
    }

    setGeneratingReport(true);
    setReportError("");

    try {
      const generateResponse = await fetch(
        `${API_URL}/api/reports/generate/${encodeURIComponent(
          storedFilename
        )}`,
        {
          method: "POST",
        }
      );

      const reportData = await generateResponse.json();

      if (
        !generateResponse.ok ||
        reportData.status !== "success" ||
        !reportData.report_url
      ) {
        throw new Error(
          reportData.detail ||
            reportData.message ||
            reportData.error ||
            "PDF report generation failed."
        );
      }

      const reportResponse = await fetch(
        `${API_URL}${reportData.report_url}`
      );

      if (!reportResponse.ok) {
        throw new Error(
          "The PDF was generated, but it could not be downloaded."
        );
      }

      const pdfBlob = await reportResponse.blob();
      const downloadUrl = window.URL.createObjectURL(pdfBlob);

      const downloadLink = document.createElement("a");
      downloadLink.href = downloadUrl;
      downloadLink.download =
        reportData.filename || "AIDE_Forensic_Report.pdf";

      document.body.appendChild(downloadLink);
      downloadLink.click();
      downloadLink.remove();

      window.URL.revokeObjectURL(downloadUrl);
    } catch (reportGenerationError) {
      console.error(
        "PDF report generation error:",
        reportGenerationError
      );

      setReportError(
        reportGenerationError.message ||
          "Unable to generate the forensic PDF report."
      );
    } finally {
      setGeneratingReport(false);
    }
  };

  // =========================================================
  // DATA FROM MAIN BACKEND RESPONSE
  // =========================================================

  const imageInfo =
    analysis?.analysis?.image || {};

  const metadata =
    analysis?.analysis?.metadata || {};

  const metadataStatus =
    analysis?.analysis?.metadata_status ||
    "Not Available";

  const ela =
    analysis?.forensic_analysis?.ela || {};

  const features =
    analysis?.forensic_analysis?.features || {};

  const noise =
    features?.noise || {};

  const fusion =
    analysis?.forensic_analysis?.fusion || {};

  const indicators =
    fusion?.indicators || {};

  const assessment =
    fusion?.assessment || {};

  const aiDetection =
    analysis?.forensic_analysis?.ai_detection ||
    {};

  const evidenceFusion =
    analysis?.forensic_analysis
      ?.evidence_fusion || {};

  const database =
    analysis?.database || {};

  // =========================================================
  // ELA IMAGE URL
  // =========================================================

  const elaUrl = ela.ela_image
    ? `${API_URL}/api/forensics/ela/${encodeURIComponent(
        ela.ela_image
      )}`
    : "";

  // =========================================================
  // LOCALIZATION IMAGE URL
  // =========================================================

  const localizationUrl =
    localization?.localization_url
      ? `${API_URL}${localization.localization_url}`
      : "";

  // =========================================================
  // AI DISPLAY VALUES
  // =========================================================

  const originalProbability =
    aiDetection.original_probability != null
      ? (
          aiDetection.original_probability *
          100
        ).toFixed(2)
      : "—";

  const tamperedProbability =
    aiDetection.tampered_probability != null
      ? (
          aiDetection.tampered_probability *
          100
        ).toFixed(2)
      : "—";

  // =========================================================
  // EVIDENCE FUSION DISPLAY VALUES
  // =========================================================

  const evidenceAI =
    evidenceFusion?.ai_evidence || {};

  const evidenceForensic =
    evidenceFusion?.forensic_evidence ||
    {};

  const combinedAssessment =
    evidenceFusion?.combined_assessment ||
    "";

  const evidenceRelationship =
    evidenceFusion?.evidence_relationship ||
    "";

  const reviewStatus =
    evidenceFusion?.review_status ||
    "";

  // =========================================================
  // RENDER
  // =========================================================

  return (
    <div className="app">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="header">

        <div className="brand">

          <div className="brand-mark">
            A
          </div>

          <div>
            <h1>AIDE</h1>
            <p>Digital Forensics</p>
          </div>

        </div>

        <div className="status">

          <span className="status-dot"></span>

          System Online

        </div>

      </header>


      {/* =====================================================
          MAIN
      ===================================================== */}

      <main className="main">

        {/* ===================================================
            HERO
        =================================================== */}

        <section className="hero">

          <span className="eyebrow">
            AI-POWERED DIGITAL EVIDENCE ANALYSIS
          </span>

          <h2>
            Analyze digital images
            <br />
            with forensic intelligence.
          </h2>

          <p>
            Upload digital evidence and examine image
            properties, metadata, compression behaviour,
            forensic indicators, AI predictions and
            evidence consistency.
          </p>

        </section>


        {/* ===================================================
            UPLOAD
        =================================================== */}

        <section className="upload-card">

          <div className="upload-header">

            <h3>
              Evidence Input
            </h3>

            <p>
              Upload a JPG, JPEG or PNG image for
              forensic analysis.
            </p>

          </div>


          {/* FILE DROP / SELECT */}

          <label className="drop-zone">

            {preview ? (

              <img
                src={preview}
                alt="Selected evidence"
                className="preview"
              />

            ) : (

              <div className="upload-placeholder">

                <div className="upload-icon">
                  ↑
                </div>

                <strong>
                  Select evidence image
                </strong>

                <span>
                  JPG, JPEG or PNG
                </span>

              </div>

            )}

            <input
              type="file"
              accept=".jpg,.jpeg,.png,image/jpeg,image/png"
              onChange={handleFileChange}
              hidden
            />

          </label>


          {/* FILE INFORMATION */}

          {selectedFile && (

            <div className="file-info">

              <div>

                <strong>
                  {selectedFile.name}
                </strong>

                <span>
                  {(
                    selectedFile.size /
                    (1024 * 1024)
                  ).toFixed(2)}{" "}
                  MB
                </span>

              </div>

            </div>

          )}


          {/* ANALYZE BUTTON */}

          <button
            className="analyze-button"
            onClick={handleAnalyze}
            disabled={
              !selectedFile ||
              uploading ||
              analyzing ||
              localizing
            }
          >

            {uploading
              ? "Uploading Evidence..."
              : analyzing
              ? "Analyzing Evidence..."
              : localizing
              ? "Generating Localization..."
              : "Analyze Evidence"}

          </button>


          {/* ERROR */}

          {error && (

            <div className="error">
              {error}
            </div>

          )}

        </section>


        {/* ===================================================
            RESULTS
        =================================================== */}

        {analysis && (

          <section className="results">

            {/* =================================================
                RESULT HEADER
            ================================================= */}

            <div className="section-title">

              <div>

                <span className="eyebrow">
                  FORENSIC ANALYSIS
                </span>

                <h2>
                  Evidence Results
                </h2>

              </div>


              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  flexWrap: "wrap",
                  justifyContent: "flex-end",
                }}
              >
                {database.status === "saved" && (

                  <div className="database-badge">
                    Database Saved
                  </div>

                )}

                <button
                  type="button"
                  onClick={handleGenerateReport}
                  disabled={generatingReport || !storedFilename}
                  style={{
                    padding: "12px 18px",
                    borderRadius: "10px",
                    border: "1px solid rgba(110, 140, 190, 0.35)",
                    background: generatingReport
                      ? "rgba(110, 140, 190, 0.12)"
                      : "rgba(110, 140, 190, 0.20)",
                    color: "inherit",
                    cursor: generatingReport
                      ? "wait"
                      : "pointer",
                    fontWeight: 600,
                    opacity: generatingReport ? 0.75 : 1,
                  }}
                >
                  {generatingReport
                    ? "Generating PDF..."
                    : "Generate PDF Report"}
                </button>
              </div>

            </div>

            {reportError && (
              <div
                className="error"
                style={{ marginTop: "16px" }}
              >
                {reportError}
              </div>
            )}


            {/* =================================================
                SCORE + IMAGE INFORMATION
            ================================================= */}

            <div className="result-grid">

              {/* FORENSIC SCORE */}

              <div className="score-card">

                <span className="card-label">
                  FORENSIC CONSISTENCY
                </span>

                <div className="score">
                  {fusion.score ?? "—"}
                </div>

                <div className="score-description">
                  Prototype Forensic Consistency Index
                </div>

                {assessment.level && (

                  <div className="assessment">
                    {assessment.level}
                  </div>

                )}

              </div>


              {/* IMAGE INFORMATION */}

              <div className="info-card">

                <span className="card-label">
                  IMAGE INFORMATION
                </span>


                <div className="info-row">

                  <span>
                    Format
                  </span>

                  <strong>
                    {imageInfo.format || "—"}
                  </strong>

                </div>


                <div className="info-row">

                  <span>
                    Resolution
                  </span>

                  <strong>

                    {imageInfo.width &&
                    imageInfo.height
                      ? `${imageInfo.width} × ${imageInfo.height}`
                      : "—"}

                  </strong>

                </div>


                <div className="info-row">

                  <span>
                    Megapixels
                  </span>

                  <strong>
                    {imageInfo.megapixels ?? "—"}
                  </strong>

                </div>


                <div className="info-row">

                  <span>
                    File Size
                  </span>

                  <strong>

                    {imageInfo.file_size_bytes
                      ? `${(
                          imageInfo.file_size_bytes /
                          1024
                        ).toFixed(1)} KB`
                      : "—"}

                  </strong>

                </div>


                <div className="info-row">

                  <span>
                    Metadata
                  </span>

                  <strong>
                    {metadataStatus}
                  </strong>

                </div>

              </div>

            </div>


            {/* =================================================
                ASSESSMENT
            ================================================= */}

            {assessment.description && (

              <div className="database-info">

                <span>
                  Assessment
                </span>

                <strong>
                  {assessment.description}
                </strong>

              </div>

            )}


            {/* =================================================
                MANIPULATION-TYPE INDICATION
            ================================================= */}

            {manipulation?.status !== "error" &&
              manipulation && (
                <section
                  className="forensic-card"
                  style={{ marginTop: "24px" }}
                >
                  <span className="card-label">
                    MANIPULATION-TYPE INDICATION
                  </span>

                  <h2 style={{ marginTop: "12px" }}>
                    {manipulation.primary_indication ||
                      "Requires Forensic Review"}
                  </h2>

                  <p>
                    Preliminary indication based on
                    self-similarity, ELA behaviour and
                    suspicious-region characteristics.
                  </p>

                  <div className="indicator-grid">
                    <div>
                      <span>Primary Score</span>
                      <strong>
                        {manipulation.primary_score ?? "—"}
                      </strong>
                    </div>

                    <div>
                      <span>Copy-Move</span>
                      <strong>
                        {manipulation.scores?.[
                          "Copy-Move Indication"
                        ] ?? "—"}
                      </strong>
                    </div>

                    <div>
                      <span>Splicing</span>
                      <strong>
                        {manipulation.scores?.[
                          "Splicing Indication"
                        ] ?? "—"}
                      </strong>
                    </div>

                    <div>
                      <span>Object Removal</span>
                      <strong>
                        {manipulation.scores?.[
                          "Object-Removal Indication"
                        ] ?? "—"}
                      </strong>
                    </div>

                    <div>
                      <span>Compression</span>
                      <strong>
                        {manipulation.scores?.[
                          "Compression Inconsistency"
                        ] ?? "—"}
                      </strong>
                    </div>
                  </div>

                  {manipulation.copy_move_analysis && (
                    <div className="ela-note">
                      <strong>Copy-Move Analysis:</strong>{" "}
                      {manipulation.copy_move_analysis.keypoints ??
                        "—"}{" "}
                      keypoints examined,{" "}
                      {manipulation.copy_move_analysis.matched_pairs ??
                        "—"}{" "}
                      matched pairs.
                    </div>
                  )}

                  <div className="ela-note">
                    <strong>Interpretation:</strong>{" "}
                    {manipulation.warning ||
                      "This is a preliminary heuristic indication and requires further forensic review."}
                  </div>
                </section>
              )}

            {manipulation?.status === "error" && (
              <div className="error" style={{ marginTop: "24px" }}>
                {manipulation.message ||
                  "Manipulation-type analysis failed."}
              </div>
            )}

            {/* =================================================
                FORENSIC INDICATORS
            ================================================= */}

            <div className="forensic-card">

              <span className="card-label">
                FORENSIC INDICATORS
              </span>


              <div className="indicator-grid">

                <div>

                  <span>
                    ELA Consistency
                  </span>

                  <strong>
                    {indicators.ela ?? "—"}
                  </strong>

                </div>


                <div>

                  <span>
                    Noise Consistency
                  </span>

                  <strong>
                    {indicators.noise ?? "—"}
                  </strong>

                </div>


                <div>

                  <span>
                    Image Statistics
                  </span>

                  <strong>
                    {indicators.image_statistics ?? "—"}
                  </strong>

                </div>

              </div>


              {/* SUPPORTING FEATURES */}

              <div className="indicator-grid">

                <div>

                  <span>
                    Entropy
                  </span>

                  <strong>
                    {features.entropy ?? "—"}
                  </strong>

                </div>


                <div>

                  <span>
                    Noise Std. Dev.
                  </span>

                  <strong>
                    {noise.noise_standard_deviation ??
                      "—"}
                  </strong>

                </div>


                <div>

                  <span>
                    Edge Density
                  </span>

                  <strong>

                    {features.edge_density_percent !=
                    null
                      ? `${features.edge_density_percent}%`
                      : "—"}

                  </strong>

                </div>

              </div>


              {/* LAPLACIAN */}

              <div className="indicator-grid">

                <div>

                  <span>
                    Laplacian Variance
                  </span>

                  <strong>
                    {features.laplacian_variance ??
                      "—"}
                  </strong>

                </div>

              </div>

            </div>


            {/* =================================================
                ELA
            ================================================= */}

            <div className="ela-card">

              <div>

                <span className="card-label">
                  ERROR LEVEL ANALYSIS
                </span>

                <h3>
                  ELA Heatmap
                </h3>

                <p>
                  Error Level Analysis visualizes
                  differences produced by JPEG
                  recompression. Brighter regions indicate
                  stronger reconstruction differences and
                  should be interpreted together with other
                  forensic indicators.
                </p>

              </div>


              <div className="ela-result">

                {/* ORIGINAL */}

                <div className="ela-panel">

                  <span className="ela-panel-title">
                    ORIGINAL IMAGE
                  </span>

                  <img
                    src={preview}
                    alt="Original evidence"
                    className="ela-image"
                  />

                </div>


                {/* ELA */}

                <div className="ela-panel">

                  <span className="ela-panel-title">
                    ELA HEATMAP
                  </span>

                  {ela.status === "success" ? (

                    <img
                      src={elaUrl}
                      alt="ELA forensic heatmap"
                      className="ela-image"
                    />

                  ) : (

                    <div className="error">
                      ELA visualization is not
                      available for this image.
                    </div>

                  )}

                </div>

              </div>


              <div className="ela-note">

                <strong>
                  Interpretation:
                </strong>{" "}

                ELA is a supporting forensic technique.
                Highlighted regions do not by themselves
                prove image manipulation.

              </div>

            </div>


            {/* =================================================
                ELA NUMERICAL RESULTS
            ================================================= */}

            <div className="forensic-card">

              <span className="card-label">
                ELA MEASUREMENTS
              </span>


              <div className="indicator-grid">

                <div>

                  <span>
                    Mean Error
                  </span>

                  <strong>
                    {ela.mean_error ?? "—"}
                  </strong>

                </div>


                <div>

                  <span>
                    Maximum Error
                  </span>

                  <strong>
                    {ela.maximum_error ?? "—"}
                  </strong>

                </div>


                <div>

                  <span>
                    Standard Deviation
                  </span>

                  <strong>
                    {ela.standard_deviation ?? "—"}
                  </strong>

                </div>

              </div>

            </div>


            {/* =================================================
                AI TAMPERING DETECTION
            ================================================= */}

            {aiDetection.prediction_available && (

              <section
                className="ai-detection-card"
                style={{
                  marginTop: "24px",
                  padding: "30px",
                  border:
                    "1px solid rgba(110, 140, 190, 0.25)",
                  borderRadius: "18px",
                  background:
                    "rgba(12, 17, 27, 0.8)",
                }}
              >

                <div
                  style={{
                    textAlign: "center",
                    marginBottom: "24px",
                  }}
                >

                  <span
                    className="card-label"
                  >
                    ARTIFICIAL INTELLIGENCE
                  </span>

                  <h2
                    style={{
                      marginTop: "10px",
                    }}
                  >
                    AI Tampering Detection
                  </h2>

                  <p>
                    ResNet18 transfer-learning baseline
                    trained on IMD2020.
                  </p>

                </div>


                {/* AI PREDICTION */}

                <div
                  style={{
                    textAlign: "center",
                    padding: "18px",
                    marginBottom: "24px",
                    borderRadius: "999px",
                    border:
                      aiDetection.prediction ===
                      "Tampered"
                        ? "1px solid #b52b2b"
                        : "1px solid #2b8a57",
                    background:
                      aiDetection.prediction ===
                      "Tampered"
                        ? "rgba(120, 20, 25, 0.25)"
                        : "rgba(20, 120, 70, 0.20)",
                  }}
                >

                  <strong
                    style={{
                      fontSize: "22px",
                    }}
                  >
                    {aiDetection.prediction ||
                      "Unavailable"}
                  </strong>

                </div>


                {/* AI INFORMATION */}

                <div className="indicator-grid">

                  <div>

                    <span>
                      Model
                    </span>

                    <strong>
                      {aiDetection.model ||
                        "—"}
                    </strong>

                  </div>


                  <div>

                    <span>
                      Device
                    </span>

                    <strong>
                      {aiDetection.device ||
                        "—"}
                    </strong>

                  </div>


                  <div>

                    <span>
                      Original
                    </span>

                    <strong>
                      {originalProbability}%
                    </strong>

                  </div>


                  <div>

                    <span>
                      Tampered
                    </span>

                    <strong>
                      {tamperedProbability}%
                    </strong>

                  </div>


                  <div>

                    <span>
                      Checkpoint
                    </span>

                    <strong>

                      {aiDetection.checkpoint_epoch !=
                      null
                        ? `Epoch ${aiDetection.checkpoint_epoch}`
                        : "—"}

                    </strong>

                  </div>


                  <div>

                    <span>
                      Validation F1
                    </span>

                    <strong>

                      {aiDetection.validation_f1 ??
                        "—"}

                    </strong>

                  </div>

                </div>


                <div
                  style={{
                    marginTop: "20px",
                    padding: "16px",
                    borderLeft:
                      "3px solid #7186a6",
                    background:
                      "rgba(255,255,255,0.025)",
                    borderRadius: "8px",
                    lineHeight: "1.7",
                  }}
                >

                  <strong>
                    Interpretation:
                  </strong>{" "}

                  {aiDetection.warning ||
                    "AI prediction is a model-based forensic indication and is not a definitive forensic verdict."}

                </div>

              </section>

            )}


            {/* =================================================
                EVIDENCE FUSION
            ================================================= */}

            {evidenceFusion.status ===
              "success" && (

              <section
                className="evidence-fusion-card"
                style={{
                  marginTop: "24px",
                  padding: "30px",
                  border:
                    "1px solid rgba(110, 140, 190, 0.25)",
                  borderRadius: "18px",
                  background:
                    "rgba(12, 17, 27, 0.8)",
                }}
              >

                <div
                  style={{
                    textAlign: "center",
                    marginBottom: "26px",
                  }}
                >

                  <span className="card-label">
                    MULTI-FORENSIC EVIDENCE FUSION
                  </span>

                  <h2
                    style={{
                      marginTop: "10px",
                    }}
                  >
                    AIDE Evidence Fusion
                  </h2>

                  <p>
                    Combined interpretation of AI-based
                    and traditional forensic evidence.
                  </p>

                </div>


                {/* AI + FORENSIC */}

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns:
                      "repeat(auto-fit, minmax(260px, 1fr))",
                    gap: "18px",
                  }}
                >

                  {/* AI EVIDENCE */}

                  <div
                    style={{
                      padding: "28px",
                      border:
                        "1px solid rgba(110, 140, 190, 0.20)",
                      borderRadius: "16px",
                      textAlign: "center",
                    }}
                  >

                    <span className="card-label">
                      AI INDICATION
                    </span>

                    <h2
                      style={{
                        marginTop: "20px",
                      }}
                    >
                      {evidenceAI.prediction ||
                        aiDetection.prediction ||
                        "—"}
                    </h2>

                    <p>
                      Tampered probability:{" "}

                      <strong>
                        {evidenceAI.tampered_probability !=
                        null
                          ? `${(
                              evidenceAI.tampered_probability *
                              100
                            ).toFixed(2)}%`
                          : "—"}
                      </strong>

                    </p>

                  </div>


                  {/* FORENSIC EVIDENCE */}

                  <div
                    style={{
                      padding: "28px",
                      border:
                        "1px solid rgba(110, 140, 190, 0.20)",
                      borderRadius: "16px",
                      textAlign: "center",
                    }}
                  >

                    <span className="card-label">
                      FORENSIC EVIDENCE
                    </span>

                    <h2
                      style={{
                        marginTop: "20px",
                      }}
                    >
                      {evidenceForensic.assessment_level ||
                        "—"}
                    </h2>

                    <p>
                      Consistency index:{" "}

                      <strong>
                        {evidenceForensic.consistency_score ??
                          "—"}
                      </strong>

                    </p>

                  </div>

                </div>


                {/* RELATIONSHIP */}

                <div
                  style={{
                    marginTop: "18px",
                    padding: "20px",
                    border:
                      "1px solid rgba(110, 140, 190, 0.20)",
                    borderRadius: "14px",
                    display: "flex",
                    justifyContent: "space-between",
                    gap: "20px",
                    flexWrap: "wrap",
                  }}
                >

                  <span className="card-label">
                    EVIDENCE RELATIONSHIP
                  </span>

                  <strong>
                    {evidenceRelationship ||
                      "—"}
                  </strong>

                </div>


                {/* COMBINED ASSESSMENT */}

                <div
                  style={{
                    marginTop: "18px",
                    padding: "26px",
                    background:
                      "rgba(255,255,255,0.025)",
                    borderRadius: "14px",
                    lineHeight: "1.8",
                    textAlign: "center",
                  }}
                >

                  <span className="card-label">
                    COMBINED ASSESSMENT
                  </span>

                  <p
                    style={{
                      marginTop: "18px",
                    }}
                  >
                    {combinedAssessment ||
                      "Combined assessment unavailable."}
                  </p>

                </div>


                {/* REVIEW STATUS */}

                {reviewStatus && (

                  <div
                    style={{
                      marginTop: "18px",
                      padding: "20px",
                      border:
                        "1px solid rgba(190, 50, 50, 0.7)",
                      background:
                        "rgba(100, 15, 20, 0.25)",
                      borderRadius: "14px",
                      display: "flex",
                      justifyContent:
                        "space-between",
                      alignItems: "center",
                      gap: "20px",
                      flexWrap: "wrap",
                    }}
                  >

                    <span className="card-label">
                      REVIEW STATUS
                    </span>

                    <strong
                      style={{
                        color: "#ff6b6b",
                      }}
                    >
                      {reviewStatus}
                    </strong>

                  </div>

                )}


                {/* WARNING */}

                <div
                  style={{
                    marginTop: "18px",
                    padding: "18px",
                    borderLeft:
                      "3px solid #7186a6",
                    background:
                      "rgba(255,255,255,0.025)",
                    borderRadius: "8px",
                    lineHeight: "1.7",
                  }}
                >

                  <strong>
                    Interpretation:
                  </strong>{" "}

                  {evidenceFusion.warning ||
                    "This combined assessment is a prototype interpretive layer and is not a definitive forensic verdict."}

                </div>

              </section>

            )}


            {/* =================================================
                SUSPICIOUS-REGION LOCALIZATION
            ================================================= */}

            <section
              style={{
                marginTop: "24px",
                padding: "30px",
                border:
                  "1px solid rgba(110, 140, 190, 0.25)",
                borderRadius: "18px",
                background:
                  "rgba(12, 17, 27, 0.8)",
              }}
            >

              {/* HEADER */}

              <div
                style={{
                  textAlign: "center",
                  marginBottom: "26px",
                }}
              >

                <span className="card-label">
                  EXPLAINABLE FORENSIC LOCALIZATION
                </span>

                <h2
                  style={{
                    marginTop: "10px",
                  }}
                >
                  Suspicious-Region Localization
                </h2>

                <p>
                  Preliminary candidate-region analysis
                  derived from ELA differences.
                </p>

              </div>


              {/* LOADING */}

              {localizing && (

                <div
                  style={{
                    padding: "30px",
                    textAlign: "center",
                  }}
                >
                  Generating suspicious-region
                  localization...
                </div>

              )}


              {/* LOCALIZATION RESULT */}

              {!localizing &&
                localization?.status ===
                  "success" && (

                <>

                  {/* IMAGE COMPARISON */}

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns:
                        "repeat(auto-fit, minmax(320px, 1fr))",
                      gap: "20px",
                    }}
                  >

                    {/* ORIGINAL IMAGE */}

                    <div
                      style={{
                        padding: "16px",
                        border:
                          "1px solid rgba(110, 140, 190, 0.20)",
                        borderRadius: "14px",
                      }}
                    >

                      <span
                        className="ela-panel-title"
                      >
                        ORIGINAL IMAGE
                      </span>

                      <img
                        src={preview}
                        alt="Original evidence"
                        style={{
                          width: "100%",
                          display: "block",
                          marginTop: "14px",
                          borderRadius: "10px",
                        }}
                      />

                    </div>


                    {/* LOCALIZATION IMAGE */}

                    <div
                      style={{
                        padding: "16px",
                        border:
                          "1px solid rgba(110, 140, 190, 0.20)",
                        borderRadius: "14px",
                      }}
                    >

                      <span
                        className="ela-panel-title"
                      >
                        CANDIDATE REGIONS
                      </span>

                      {localizationUrl ? (

                        <img
                          src={localizationUrl}
                          alt="Suspicious-region localization"
                          style={{
                            width: "100%",
                            display: "block",
                            marginTop: "14px",
                            borderRadius: "10px",
                          }}
                        />

                      ) : (

                        <div className="error">
                          Localization visualization
                          is unavailable.
                        </div>

                      )}

                    </div>

                  </div>


                  {/* LOCALIZATION STATISTICS */}

                  <div
                    className="indicator-grid"
                    style={{
                      marginTop: "20px",
                    }}
                  >

                    <div>

                      <span>
                        Candidate Regions
                      </span>

                      <strong>
                        {localization.candidate_region_count ??
                          0}
                      </strong>

                    </div>


                    <div>

                      <span>
                        Rejected Large Regions
                      </span>

                      <strong>
                        {localization.rejected_large_regions ??
                          0}
                      </strong>

                    </div>


                    <div>

                      <span>
                        Threshold
                      </span>

                      <strong>
                        {localization.threshold_value ??
                          "—"}
                      </strong>

                    </div>


                    <div>

                      <span>
                        Threshold Percentile
                      </span>

                      <strong>

                        {localization.threshold_percentile !=
                        null
                          ? `${localization.threshold_percentile}th percentile`
                          : "—"}

                      </strong>

                    </div>

                  </div>


                  {/* REGION DETAILS */}

                  {Array.isArray(
                    localization.regions
                  ) &&
                    localization.regions.length >
                      0 && (

                    <div
                      style={{
                        marginTop: "20px",
                      }}
                    >

                      <span className="card-label">
                        DETECTED CANDIDATE REGIONS
                      </span>


                      <div
                        className="indicator-grid"
                        style={{
                          marginTop: "14px",
                        }}
                      >

                        {localization.regions.map(
                          (region, index) => (

                            <div
                              key={`${region.x}-${region.y}-${index}`}
                            >

                              <span>
                                Candidate {index + 1}
                              </span>

                              <strong>
                                {region.width} ×{" "}
                                {region.height}
                              </strong>

                              <small
                                style={{
                                  display: "block",
                                  marginTop: "6px",
                                  opacity: 0.65,
                                }}
                              >
                                Position:{" "}
                                {region.x},{" "}
                                {region.y}
                              </small>

                            </div>

                          )
                        )}

                      </div>

                    </div>

                  )}


                  {/* LOCALIZATION WARNING */}

                  <div
                    style={{
                      marginTop: "22px",
                      padding: "18px",
                      borderLeft:
                        "3px solid #7186a6",
                      background:
                        "rgba(255,255,255,0.025)",
                      borderRadius: "8px",
                      lineHeight: "1.7",
                    }}
                  >

                    <strong>
                      Interpretation:
                    </strong>{" "}

                    {localization.warning ||
                      "Highlighted regions are candidate areas for further forensic examination and do not by themselves prove image manipulation."}

                  </div>

                </>

              )}


              {/* LOCALIZATION ERROR */}

              {!localizing &&
                localization?.status ===
                  "error" && (

                <div className="error">

                  {localization.message ||
                    "Suspicious-region localization failed."}

                </div>

              )}

            </section>


            {/* =================================================
                METADATA
            ================================================= */}

            <div
              className="info-card"
              style={{
                marginTop: "18px",
              }}
            >

              <span className="card-label">
                METADATA
              </span>


              {Object.keys(metadata).length >
              0 ? (

                Object.entries(metadata).map(
                  ([key, value]) => (

                    <div
                      className="info-row"
                      key={key}
                    >

                      <span>

                        {key
                          .replaceAll(
                            "_",
                            " "
                          )
                          .replace(
                            /\b\w/g,
                            (char) =>
                              char.toUpperCase()
                          )}

                      </span>

                      <strong>
                        {value}
                      </strong>

                    </div>

                  )
                )

              ) : (

                <div className="info-row">

                  <span>
                    Status
                  </span>

                  <strong>
                    No EXIF metadata detected
                  </strong>

                </div>

              )}

            </div>


            {/* =================================================
                DATABASE
            ================================================= */}

            {database.status && (

              <div className="database-info">

                <span>
                  Database
                </span>

                <strong>

                  {database.status === "saved"
                    ? "Saved successfully"
                    : database.status}

                </strong>


                <span>
                  Evidence ID
                </span>

                <strong>
                  #{database.evidence_id}
                </strong>


                <span>
                  Operation
                </span>

                <strong>
                  {database.operation}
                </strong>

              </div>

            )}

          </section>

        )}

      </main>


      {/* =====================================================
          FOOTER
      ===================================================== */}

      <footer>

        AIDE · AI-Powered Digital Image Evidence
        Integrity & Tampering Detection Platform

      </footer>

    </div>
  );
}

export default App;