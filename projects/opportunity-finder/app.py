# import logging

# import gradio as gr

# from database.connection import DatabaseConnection
# from services.candidate_service import CandidateService
# from services.resume_service import ResumeService


# # --------------------------------------------------
# # Logging and service initialization
# # --------------------------------------------------

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
# )
# logger = logging.getLogger(__name__)

# database = DatabaseConnection()
# database.create_tables()

# candidate_service = CandidateService(database)
# resume_service = ResumeService(candidate_service=candidate_service)


# # --------------------------------------------------
# # Candidate onboarding
# # --------------------------------------------------

# def onboard_candidate(
#     resume_file,
#     preferred_roles,
#     preferred_locations,
#     remote_preference,
#     visa_sponsorship_required,
# ):
#     if resume_file is None:
#         return """
#         <div class="status-message error">
#             <span class="status-icon">!</span>
#             <div>
#                 <strong>Resume required</strong>
#                 <p>Please upload your resume before continuing.</p>
#             </div>
#         </div>
#         """

#     if visa_sponsorship_required is None:
#         return """
#         <div class="status-message error">
#             <span class="status-icon">!</span>
#             <div>
#                 <strong>One more detail</strong>
#                 <p>Please tell us whether you require visa sponsorship.</p>
#             </div>
#         </div>
#         """

#     try:
#         logger.info("Starting candidate onboarding.")

#         # Gradio's multiselect dropdowns return lists. The fallback also
#         # supports comma-separated strings if the component value changes.
#         roles = (
#             [item.strip() for item in preferred_roles if item.strip()]
#             if isinstance(preferred_roles, list)
#             else [
#                 item.strip()
#                 for item in (preferred_roles or "").split(",")
#                 if item.strip()
#             ]
#         )
#         locations = (
#             [item.strip() for item in preferred_locations if item.strip()]
#             if isinstance(preferred_locations, list)
#             else [
#                 item.strip()
#                 for item in (preferred_locations or "").split(",")
#                 if item.strip()
#             ]
#         )

#         candidate_profile = resume_service.create_candidate_profile_from_resume(
#             file_path=resume_file,
#             preferred_roles=roles,
#             preferred_locations=locations,
#             remote_preference=remote_preference,
#             visa_sponsorship_required=(visa_sponsorship_required == "Yes"),
#         )

#         logger.info(
#             "Candidate onboarding completed: %s",
#             candidate_profile.candidate_id,
#         )

#         return f"""
#         <div class="status-message success">
#             <span class="status-icon">✓</span>
#             <div class="status-copy">
#                 <h3>Your profile is ready!</h3>
#                 <p>
#                     Your resume has been processed and your candidate profile
#                     has been saved successfully.
#                 </p>
#                 <div class="candidate-id">
#                     <span>YOUR CANDIDATE ID</span>
#                     <strong>{candidate_profile.candidate_id}</strong>
#                 </div>
#             </div>
#         </div>
#         """

#     except Exception:
#         logger.exception("Candidate onboarding failed.")
#         return """
#         <div class="status-message error">
#             <span class="status-icon">!</span>
#             <div>
#                 <strong>We couldn't finish your onboarding</strong>
#                 <p>
#                     Please try again. If the problem continues,
#                     check the application logs.
#                 </p>
#             </div>
#         </div>
#         """


# # --------------------------------------------------
# # Theme and custom styling
# # --------------------------------------------------

# theme = gr.themes.Soft(
#     primary_hue="violet",
#     secondary_hue="slate",
#     neutral_hue="slate",
#     font=["Inter", "Arial", "sans-serif"],
# )

# CUSTOM_CSS = r"""
# :root {
#     --ink: #17183b;
#     --muted: #68708f;
#     --violet: #7650f5;
#     --violet-dark: #5b35dc;
#     --lavender: #f1edff;
#     --line: #e5e2f3;
#     --surface: #ffffff;
# }

# /* --------------------------------------------------
#    Global page layout
#    -------------------------------------------------- */

# html,
# body,
# #root,
# gradio-app {
#     width: 100% !important;
#     min-height: 100% !important;
#     margin: 0 !important;
#     padding: 0 !important;
#     background: #f8f7ff !important;
# }

# .gradio-container {
#     width: 100% !important;
#     max-width: none !important;
#     min-height: 100vh !important;
#     margin: 0 !important;
#     padding: 0 0 40px !important;
#     color: var(--ink) !important;
#     font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
# }

# .gradio-container *,
# .gradio-container *::before,
# .gradio-container *::after {
#     box-sizing: border-box;
# }

# footer {
#     display: none !important;
# }

# /* --------------------------------------------------
#    Hero
#    -------------------------------------------------- */

# .hero-panel {
#     position: relative;
#     isolation: isolate;
#     overflow: hidden;
#     width: 100%;
#     min-height: 405px;
#     padding: 28px clamp(28px, 6.8vw, 110px) 30px;
#     color: #fff;
#     border-radius: 0 0 28px 28px;
#     background:
#         radial-gradient(ellipse at 88% 48%, rgba(151, 93, 255, .76) 0%, rgba(103, 62, 210, .38) 26%, transparent 52%),
#         radial-gradient(ellipse at 62% 100%, rgba(65, 77, 173, .55), transparent 42%),
#         linear-gradient(112deg, #10143c 0%, #15194d 52%, #352071 100%);
# }

# .hero-panel::before {
#     content: "";
#     position: absolute;
#     z-index: -1;
#     inset: auto -4% -2px 38%;
#     height: 36%;
#     opacity: .38;
#     background:
#         linear-gradient(145deg, transparent 0 24%, #111943 24.2% 45%, transparent 45.2%),
#         linear-gradient(35deg, transparent 0 32%, #25255f 32.2% 62%, transparent 62.2%);
#     clip-path: polygon(0 100%, 12% 55%, 24% 79%, 39% 23%, 54% 70%, 70% 35%, 84% 72%, 100% 20%, 100% 100%);
# }

# .hero-panel::after {
#     content: "";
#     position: absolute;
#     z-index: -1;
#     width: 420px;
#     height: 420px;
#     right: -135px;
#     top: -245px;
#     border: 1px solid rgba(255,255,255,.13);
#     border-radius: 50%;
#     box-shadow:
#         0 0 0 34px rgba(255,255,255,.025),
#         0 0 0 72px rgba(255,255,255,.02);
# }

# .brand-row {
#     display: flex;
#     align-items: center;
#     gap: 12px;
#     position: relative;
#     z-index: 2;
# }

# .brand-icon {
#     width: 40px;
#     height: 40px;
#     display: grid;
#     place-items: center;
#     border-radius: 12px;
#     background: linear-gradient(145deg,#a36aff,#6d48ed);
#     box-shadow: 0 8px 22px rgba(91,54,222,.35);
#     font-size: 23px;
# }

# .brand-name {
#     font-size: 20px;
#     font-weight: 750;
#     letter-spacing: -.6px;
# }

# .brand-label {
#     margin-left: auto;
#     padding: 9px 15px;
#     border-radius: 30px;
#     background: rgba(255,255,255,.10);
#     color: #e7e1ff;
#     font-size: 10px;
#     font-weight: 700;
#     letter-spacing: 1.3px;
# }

# .hero-grid {
#     display: grid;
#     grid-template-columns: minmax(0, 1.12fr) minmax(300px, .88fr);
#     align-items: center;
#     gap: 28px;
#     min-height: 285px;
#     position: relative;
#     z-index: 1;
# }

# .hero-copy {
#     max-width: 720px;
#     padding: 18px 0 4px;
# }

# .hero-eyebrow {
#     color: #c9b7ff;
#     font-size: 11px;
#     font-weight: 800;
#     letter-spacing: 2.4px;
#     text-transform: uppercase;
#     margin-bottom: 13px;
# }

# .hero-title {
#     margin: 0 0 17px;
#     color: #fff;
#     font-size: clamp(34px,4.2vw,58px);
#     line-height: 1.08;
#     font-weight: 800;
#     letter-spacing: -2.3px;
# }

# .hero-title em {
#     color: #a987ff;
#     font-style: normal;
# }

# .hero-description {
#     max-width: 620px;
#     margin: 0;
#     color: #e0def4;
#     font-size: 15px;
#     line-height: 1.75;
# }

# .hero-visual {
#     min-height: 230px;
#     position: relative;
#     display: flex;
#     align-items: center;
#     justify-content: center;
# }

# .match-card {
#     position: absolute;
#     width: min(330px, 88%);
#     padding: 17px 20px;
#     border: 1px solid rgba(255,255,255,.35);
#     border-radius: 20px;
#     background: linear-gradient(135deg,rgba(255,255,255,.23),rgba(255,255,255,.09));
#     box-shadow: 0 22px 55px rgba(5,8,40,.25);
#     backdrop-filter: blur(15px);
#     color: #fff;
#     transform: rotate(-5deg);
#     z-index: 3;
# }

# .match-card.secondary {
#     top: 30px;
#     left: 3%;
#     transform: rotate(5deg) scale(.94);
#     opacity: .48;
#     z-index: 1;
# }

# .match-card.tertiary {
#     bottom: 12px;
#     left: 12%;
#     transform: rotate(-2deg) scale(.96);
#     opacity: .62;
#     z-index: 2;
# }

# .match-top {
#     display: flex;
#     justify-content: flex-end;
#     margin-bottom: 12px;
# }

# .match-pill {
#     padding: 5px 11px;
#     border-radius: 20px;
#     color: #72f2d2;
#     background: rgba(13,43,72,.6);
#     font-size: 11px;
#     font-weight: 800;
# }

# .match-detail {
#     display: flex;
#     align-items: center;
#     gap: 13px;
# }

# .company-mark {
#     width: 42px;
#     height: 42px;
#     flex: 0 0 42px;
#     display: grid;
#     place-items: center;
#     border-radius: 50%;
#     background: #fff;
#     color: #151936;
#     font-size: 18px;
#     font-weight: 800;
# }

# .match-role {
#     font-size: 16px;
#     font-weight: 750;
# }

# .match-company {
#     color: #ded9f5;
#     font-size: 12px;
#     margin-top: 4px;
# }

# .hero-steps {
#     display: flex;
#     gap: 28px;
#     margin-top: 22px;
# }

# .hero-step {
#     min-width: 0;
#     color: #fff;
#     font-size: 12px;
#     font-weight: 700;
# }

# .hero-step-icon {
#     width: 38px;
#     height: 38px;
#     display: grid;
#     place-items: center;
#     margin-bottom: 8px;
#     border-radius: 50%;
#     background: rgba(255,255,255,.17);
#     border: 1px solid rgba(255,255,255,.18);
#     font-size: 17px;
# }

# .hero-step.active .hero-step-icon {
#     background: linear-gradient(135deg,#a66aff,#6745ed);
#     box-shadow: 0 0 0 5px rgba(153,116,255,.14);
# }

# .hero-step small {
#     display: block;
#     margin-top: 4px;
#     color: #c5c4e4;
#     font-size: 11px;
#     font-weight: 400;
# }

# /* --------------------------------------------------
#    Page content and cards
#    -------------------------------------------------- */

# .content-wrap {
#     width: 100% !important;
#     max-width: 1600px !important;
#     margin: 0 auto !important;
#     padding: 38px clamp(24px, 5vw, 90px) 0 !important;
# }

# .section-heading {
#     margin: 0 0 24px;
# }

# .section-heading h2 {
#     margin: 0 0 6px;
#     color: #17183b;
#     font-size: 27px;
#     font-weight: 800;
#     letter-spacing: -1px;
# }

# .section-heading h2 span {
#     color: #7951ed;
# }

# .section-heading p {
#     margin: 0;
#     color: #68708f;
#     font-size: 14px;
# }

# .form-row {
#     gap: 22px !important;
#     align-items: stretch !important;
# }

# .form-column {
#     min-width: 0 !important;
# }

# .panel-card {
#     height: 100%;
#     padding: 28px !important;
#     border: 1px solid #e7e3f4 !important;
#     border-radius: 23px !important;
#     background: rgba(255,255,255,.96) !important;
#     box-shadow: 0 12px 35px rgba(62,45,122,.075) !important;
# }

# .panel-heading {
#     display: flex;
#     align-items: center;
#     gap: 14px;
#     margin-bottom: 22px;
# }

# .panel-icon {
#     width: 52px;
#     height: 52px;
#     flex: 0 0 52px;
#     display: grid;
#     place-items: center;
#     border-radius: 16px;
#     color: #7c4bea;
#     font-size: 25px;
#     background: linear-gradient(145deg,#f7f0ff,#eee7ff);
#     box-shadow: 0 5px 13px rgba(112,75,224,.12);
# }

# .panel-heading h3 {
#     margin: 0 0 5px;
#     color: #17183b;
#     font-size: 19px;
#     font-weight: 800;
#     letter-spacing: -.5px;
# }

# .panel-heading p {
#     margin: 0;
#     color: #69718f;
#     font-size: 12px;
#     line-height: 1.5;
# }

# /* --------------------------------------------------
#    Resume uploader
#    -------------------------------------------------- */

# .resume-uploader {
#     width: 100% !important;
#     margin: 0 !important;
#     background: transparent !important;
#     color: #35345d !important;
# }

# .resume-uploader > label {
#     display: none !important;
# }

# .resume-uploader > div,
# .resume-uploader .wrap,
# .resume-uploader .upload-container,
# .resume-uploader .file-preview,
# .resume-uploader [data-testid="file-upload"] {
#     box-shadow: none !important;
# }

# .resume-uploader .wrap {
#     width: 100% !important;
#     min-height: 300px !important;
#     display: flex !important;
#     align-items: center !important;
#     justify-content: center !important;
#     padding: 18px !important;
#     border: 2px dashed #9874ff !important;
#     border-radius: 20px !important;
#     background: linear-gradient(145deg,#fbf9ff,#f4efff) !important;
#     transition: all .2s ease !important;
# }

# .resume-uploader .wrap:hover {
#     border-color: #6940e8 !important;
#     background: #f0eaff !important;
# }

# .resume-uploader .upload-container {
#     width: 100% !important;
#     min-height: 240px !important;
#     display: flex !important;
#     align-items: center !important;
#     justify-content: center !important;
#     border: 0 !important;
#     background: transparent !important;
# }

# .resume-uploader .file-preview {
#     width: 100% !important;
#     border: 0 !important;
#     background: transparent !important;
# }

# .resume-uploader [data-testid="file-upload"] {
#     width: 100% !important;
#     min-height: 250px !important;
#     border: 0 !important;
#     border-radius: 16px !important;
#     background: transparent !important;
# }

# .resume-uploader button {
#     border-radius: 12px !important;
#     background: #7650f5 !important;
#     color: #fff !important;
# }

# .resume-uploader button:hover {
#     background: #5b35dc !important;
# }

# .resume-uploader,
# .resume-uploader * {
#     color: #35345d;
# }

# .resume-uploader svg {
#     color: #8251f4 !important;
# }

# .resume-uploader p,
# .resume-uploader span {
#     color: #686b88 !important;
# }

# .what-next {
#     position: relative;
#     overflow: hidden;
#     margin-top: 18px;
#     padding: 18px 19px;
#     border-radius: 17px;
#     background: linear-gradient(120deg,#f4efff,#eee8ff);
# }

# .what-next::after {
#     content: "";
#     position: absolute;
#     right: -20px;
#     bottom: -45px;
#     width: 145px;
#     height: 100px;
#     border-radius: 50%;
#     background: rgba(158,117,255,.18);
# }

# .what-next h4 {
#     margin: 0 0 11px;
#     color: #4933a6;
#     font-size: 14px;
#     font-weight: 800;
# }

# .what-next ul {
#     list-style: none;
#     padding: 0;
#     margin: 0;
#     position: relative;
#     z-index: 1;
# }

# .what-next li {
#     display: flex;
#     align-items: center;
#     gap: 9px;
#     margin: 7px 0;
#     color: #34365d;
#     font-size: 12px;
# }

# .check-dot {
#     width: 17px;
#     height: 17px;
#     display: grid;
#     place-items: center;
#     flex: 0 0 17px;
#     border-radius: 50%;
#     background: #d8f3e6;
#     color: #26885c;
#     font-size: 11px;
#     font-weight: 800;
# }

# /* --------------------------------------------------
#    Career preference fields
#    -------------------------------------------------- */

# .preference-label {
#     display: flex;
#     align-items: center;
#     gap: 10px;
#     margin: 20px 0 10px;
#     color: #242746;
#     font-size: 13px;
#     font-weight: 750;
# }

# .preference-label:first-of-type {
#     margin-top: 0;
# }

# .preference-label .field-icon {
#     width: 27px;
#     height: 27px;
#     display: grid;
#     place-items: center;
#     border-radius: 9px;
#     background: #f0eaff;
#     color: #7951ed;
#     font-size: 15px;
# }

# .preference-hint {
#     margin: 8px 0 16px;
#     color: #8589a3;
#     font-size: 11px;
# }

# /* Dropdown outer surfaces and wrappers */
# .preference-input,
# .preference-input > div,
# .preference-input .wrap,
# .preference-input [data-testid="dropdown"],
# .preference-input [role="listbox"] {
#     background: #fff !important;
#     color: #252748 !important;
#     border-radius: 14px !important;
#     box-shadow: none !important;
# }

# .preference-input {
#     width: 100% !important;
#     border: 1px solid #e1dcef !important;
#     border-radius: 14px !important;
#     overflow: visible !important;
# }

# .preference-input:hover {
#     border-color: #a58af5 !important;
# }

# .preference-input input {
#     min-height: 48px !important;
#     background: #fff !important;
#     color: #252748 !important;
#     border: 0 !important;
#     box-shadow: none !important;
# }

# .preference-input input::placeholder {
#     color: #a0a1b5 !important;
# }

# .preference-input:focus-within {
#     border-color: #8d6af2 !important;
#     box-shadow: 0 0 0 3px rgba(125,83,238,.11) !important;
# }

# /* Selected dropdown tags */
# .preference-input [data-testid="token"],
# .preference-input .token {
#     border: 1px solid #dfd3ff !important;
#     border-radius: 30px !important;
#     background: #eee7ff !important;
#     color: #4b32b4 !important;
# }

# /* Dropdown options */
# .preference-input [role="option"] {
#     background: #fff !important;
#     color: #252748 !important;
# }

# .preference-input [role="option"]:hover,
# .preference-input [role="option"][aria-selected="true"] {
#     background: #f1ebff !important;
#     color: #5636c4 !important;
# }

# /* --------------------------------------------------
#    Work arrangement and sponsorship selection cards
#    -------------------------------------------------- */

# .choice-radio {
#     margin: 0 0 20px !important;
# }

# .choice-radio > label {
#     display: none !important;
# }

# .choice-radio .wrap {
#     display: flex !important;
#     flex-direction: row !important;
#     flex-wrap: wrap !important;
#     gap: 10px !important;
#     padding: 0 !important;
#     background: transparent !important;
# }

# .choice-radio .wrap label {
#     min-height: 48px !important;
#     display: flex !important;
#     align-items: center !important;
#     justify-content: center !important;
#     gap: 9px !important;
#     padding: 10px 15px !important;
#     border: 1px solid #e3dff0 !important;
#     border-radius: 13px !important;
#     background: #fff !important;
#     color: #363958 !important;
#     font-size: 12px !important;
#     font-weight: 600 !important;
#     box-shadow: 0 3px 10px rgba(48,38,104,.035) !important;
#     transition: all .2s ease !important;
# }

# .choice-radio .wrap label:hover {
#     border-color: #ad96f7 !important;
#     background: #faf8ff !important;
# }

# .choice-radio .wrap label:has(input:checked) {
#     border: 1.5px solid #8254f4 !important;
#     background: #f1ebff !important;
#     color: #4b2dc4 !important;
#     box-shadow: 0 4px 12px rgba(112,70,222,.12) !important;
# }

# .choice-radio input {
#     accent-color: #7650f5 !important;
# }

# .work-choice .wrap label {
#     flex: 1 1 20%;
# }

# .sponsor-choice .wrap label {
#     flex: 1 1 45%;
#     min-height: 54px !important;
# }

# /* --------------------------------------------------
#    Submit button, status messages and trust strip
#    -------------------------------------------------- */

# .submit-area {
#     margin-top: 25px;
#     padding-top: 21px;
#     border-top: 1px solid #e5e1f0;
# }

# .submit-caption {
#     margin: 0 0 12px;
#     color: #737995;
#     font-size: 12px;
# }

# .primary-btn {
#     min-height: 58px !important;
#     width: 100% !important;
#     border: 0 !important;
#     border-radius: 15px !important;
#     color: #fff !important;
#     background: linear-gradient(100deg,#8051f4 0%,#6037df 55%,#8a5cf4 100%) !important;
#     font-size: 16px !important;
#     font-weight: 800 !important;
#     box-shadow: 0 9px 22px rgba(105,65,220,.24) !important;
#     transition: all .2s ease !important;
# }

# .primary-btn:hover {
#     transform: translateY(-2px);
#     box-shadow: 0 13px 26px rgba(105,65,220,.3) !important;
# }

# .status-message {
#     display: flex;
#     align-items: flex-start;
#     gap: 13px;
#     margin-top: 16px;
#     padding: 17px 19px;
#     border-radius: 15px;
#     line-height: 1.55;
# }

# .status-message.success {
#     color: #176b4b;
#     background: #effaf4;
#     border: 1px solid #c9ebd8;
# }

# .status-message.error {
#     color: #9e3939;
#     background: #fff4f3;
#     border: 1px solid #f1d1ce;
# }

# .status-icon {
#     width: 30px;
#     height: 30px;
#     flex: 0 0 30px;
#     display: grid;
#     place-items: center;
#     border-radius: 50%;
#     background: #d8f3e4;
#     color: #168454;
#     font-weight: 900;
# }

# .status-message.error .status-icon {
#     background: #ffe2df;
#     color: #b33d38;
# }

# .status-copy h3 {
#     margin: 0 0 4px;
#     font-size: 16px;
# }

# .status-copy p,
# .status-message p {
#     margin: 0;
#     font-size: 12px;
# }

# .candidate-id {
#     margin-top: 12px;
#     padding: 10px 12px;
#     border: 1px solid #d5e9dc;
#     border-radius: 10px;
#     background: rgba(255,255,255,.75);
#     overflow-wrap: anywhere;
# }

# .candidate-id span {
#     display: block;
#     margin-bottom: 3px;
#     font-size: 9px;
#     letter-spacing: 1.1px;
#     opacity: .7;
# }

# .candidate-id strong {
#     font-size: 12px;
# }

# .trust-strip {
#     display: grid;
#     grid-template-columns: repeat(3,1fr);
#     gap: 16px;
#     padding: 22px 4px 0;
# }

# .trust-item {
#     display: flex;
#     align-items: center;
#     gap: 12px;
#     padding: 0 16px;
#     border-right: 1px solid #ddd8ed;
# }

# .trust-item:last-child {
#     border: 0;
# }

# .trust-icon {
#     color: #8751ed;
#     font-size: 24px;
# }

# .trust-item strong {
#     display: block;
#     color: #202344;
#     font-size: 12px;
# }

# .trust-item small {
#     display: block;
#     margin-top: 3px;
#     color: #777b96;
#     font-size: 10px;
# }

# /* --------------------------------------------------
#    Responsive layout
#    -------------------------------------------------- */

# @media (min-width: 1600px) {
#     .content-wrap {
#         padding-left: 100px !important;
#         padding-right: 100px !important;
#     }

#     .form-row {
#         gap: 28px !important;
#     }

#     .panel-card {
#         padding: 32px !important;
#     }
# }

# @media (max-width: 850px) {
#     .hero-grid {
#         grid-template-columns: 1fr;
#         gap: 0;
#     }

#     .hero-visual {
#         display: none;
#     }

#     .hero-panel {
#         min-height: auto;
#     }

#     .hero-steps {
#         gap: 15px;
#     }

#     .hero-step {
#         flex: 1;
#     }

#     .form-row {
#         flex-direction: column !important;
#     }
# }

# @media (max-width: 650px) {
#     .hero-panel {
#         padding: 22px 20px 26px;
#         border-radius: 0 0 22px 22px;
#     }

#     .brand-label {
#         display: none;
#     }

#     .hero-title {
#         font-size: 36px;
#         letter-spacing: -1.5px;
#     }

#     .hero-description {
#         font-size: 13px;
#     }

#     .hero-steps {
#         gap: 9px;
#     }

#     .hero-step {
#         font-size: 10px;
#     }

#     .hero-step small {
#         font-size: 9px;
#     }

#     .hero-step-icon {
#         width: 32px;
#         height: 32px;
#     }

#     .content-wrap {
#         padding: 22px 14px 0 !important;
#     }

#     .section-heading h2 {
#         font-size: 23px;
#     }

#     .panel-card {
#         padding: 18px !important;
#     }

#     .panel-heading h3 {
#         font-size: 16px;
#     }

#     .resume-uploader .wrap {
#         min-height: 235px !important;
#     }

#     .trust-strip {
#         grid-template-columns: 1fr;
#         gap: 12px;
#     }

#     .trust-item {
#         border: 0;
#         padding: 0 8px;
#     }

#     .work-choice .wrap label {
#         flex: 1 1 40%;
#     }
# }
# """


# # --------------------------------------------------
# # Gradio application
# # --------------------------------------------------

# with gr.Blocks(
#     title="Opportunity Finder",
#     theme=theme,
#     css=CUSTOM_CSS,
# ) as app:
#     gr.HTML(
#         """
#         <section class="hero-panel">
#             <div class="brand-row">
#                 <div class="brand-icon">✦</div>
#                 <div class="brand-name">Opportunity Finder</div>
#                 <div class="brand-label">✦ &nbsp; YOUR CAREER COMPANION</div>
#             </div>

#             <div class="hero-grid">
#                 <div class="hero-copy">
#                     <div class="hero-eyebrow">Discover what's possible</div>
#                     <h1 class="hero-title">
#                         Find opportunities<br>
#                         that move <em>you forward.</em>
#                     </h1>
#                     <p class="hero-description">
#                         Your experience. Your ambitions. Better opportunities.
#                         Build your profile and let us help you discover roles
#                         that align with your career goals.
#                     </p>

#                     <div class="hero-steps">
#                         <div class="hero-step active">
#                             <div class="hero-step-icon">♙</div>
#                             Build profile
#                             <small>Tell us about you</small>
#                         </div>
#                         <div class="hero-step">
#                             <div class="hero-step-icon">⌕</div>
#                             Discover opportunities
#                             <small>We find relevant roles</small>
#                         </div>
#                         <div class="hero-step">
#                             <div class="hero-step-icon">ϟ</div>
#                             Find your match
#                             <small>Get the best fits</small>
#                         </div>
#                     </div>
#                 </div>

#                 <div class="hero-visual" aria-hidden="true">
#                     <div class="match-card secondary">
#                         <div class="match-detail">
#                             <div class="company-mark">⌘</div>
#                             <div>
#                                 <div class="match-role">Backend Engineer</div>
#                                 <div class="match-company">Global technology team</div>
#                             </div>
#                         </div>
#                     </div>

#                     <div class="match-card tertiary">
#                         <div class="match-detail">
#                             <div class="company-mark">▦</div>
#                             <div>
#                                 <div class="match-role">Data Scientist</div>
#                                 <div class="match-company">Analytics &amp; AI</div>
#                             </div>
#                         </div>
#                     </div>

#                     <div class="match-card">
#                         <div class="match-top">
#                             <span class="match-pill">◉ &nbsp; 98% Match</span>
#                         </div>
#                         <div class="match-detail">
#                             <div class="company-mark">✦</div>
#                             <div>
#                                 <div class="match-role">AI Engineer</div>
#                                 <div class="match-company">A role aligned with your goals</div>
#                             </div>
#                         </div>
#                     </div>
#                 </div>
#             </div>
#         </section>
#         """
#     )

#     with gr.Column(elem_classes=["content-wrap"]):
#         gr.HTML(
#             """
#             <div class="section-heading">
#                 <h2>Let's get to know <span>you.</span></h2>
#                 <p>
#                     Start by sharing your professional background and the
#                     opportunities you're interested in.
#                 </p>
#             </div>
#             """
#         )

#         with gr.Row(equal_height=True, elem_classes=["form-row"]):
#             with gr.Column(scale=5, elem_classes=["form-column"]):
#                 with gr.Column(elem_classes=["panel-card"]):
#                     gr.HTML(
#                         """
#                         <div class="panel-heading">
#                             <div class="panel-icon">▤</div>
#                             <div>
#                                 <h3>Your professional background</h3>
#                                 <p>
#                                     Upload your latest resume. We'll extract
#                                     your experience, education, and skills
#                                     automatically.
#                                 </p>
#                             </div>
#                         </div>
#                         """
#                     )

#                     resume_file = gr.File(
#                         label="Upload your resume",
#                         file_types=[".pdf", ".docx"],
#                         file_count="single",
#                         type="filepath",
#                         elem_classes=["resume-uploader"],
#                     )

#                     gr.HTML(
#                         """
#                         <div class="what-next">
#                             <h4>✦ &nbsp; What happens next?</h4>
#                             <ul>
#                                 <li>
#                                     <span class="check-dot">✓</span>
#                                     We extract your experience, education, and skills
#                                 </li>
#                                 <li>
#                                     <span class="check-dot">✓</span>
#                                     Create your candidate profile
#                                 </li>
#                                 <li>
#                                     <span class="check-dot">✓</span>
#                                     Match you with relevant opportunities
#                                 </li>
#                             </ul>
#                         </div>
#                         """
#                     )

#             with gr.Column(scale=7, elem_classes=["form-column"]):
#                 with gr.Column(elem_classes=["panel-card"]):
#                     gr.HTML(
#                         """
#                         <div class="panel-heading">
#                             <div class="panel-icon">◎</div>
#                             <div>
#                                 <h3>Your career preferences</h3>
#                                 <p>Tell us what your next opportunity looks like.</p>
#                             </div>
#                         </div>

#                         <div class="preference-label">
#                             <span class="field-icon">▣</span>
#                             Preferred roles
#                             <span style="color:#e45c76">*</span>
#                         </div>
#                         """
#                     )

#                     preferred_roles = gr.Dropdown(
#                         choices=[
#                             "Backend Engineer",
#                             "Software Engineer",
#                             "AI Engineer",
#                             "Machine Learning Engineer",
#                             "Data Scientist",
#                             "Data Engineer",
#                             "DevOps Engineer",
#                             "Product Manager",
#                         ],
#                         multiselect=True,
#                         allow_custom_value=True,
#                         show_label=False,
#                         interactive=True,
#                         elem_classes=["preference-input", "tag-input"],
#                     )

#                     gr.HTML(
#                         """
#                         <div class="preference-hint">
#                             Choose suggestions or type a role and press Enter to add it.
#                         </div>
#                         <div class="preference-label">
#                             <span class="field-icon">⌖</span>
#                             Preferred locations
#                             <span style="color:#e45c76">*</span>
#                         </div>
#                         """
#                     )

#                     preferred_locations = gr.Dropdown(
#                         choices=[
#                             "United States",
#                             "Canada",
#                             "United Kingdom",
#                             "Germany",
#                             "Netherlands",
#                             "France",
#                             "Ireland",
#                             "Rwanda",
#                             "Ghana",
#                             "Europe",
#                             "Africa",
#                             "Remote",
#                         ],
#                         multiselect=True,
#                         allow_custom_value=True,
#                         show_label=False,
#                         interactive=True,
#                         elem_classes=["preference-input", "tag-input"],
#                     )

#                     gr.HTML(
#                         """
#                         <div class="preference-hint">
#                             Choose suggestions or type a country, region, or Remote.
#                         </div>
#                         <div class="preference-label">
#                             <span class="field-icon">▱</span>
#                             Preferred work arrangement
#                         </div>
#                         """
#                     )

#                     remote_preference = gr.Radio(
#                         choices=["Remote", "Hybrid", "Onsite", "Flexible"],
#                         value="Flexible",
#                         show_label=False,
#                         elem_classes=["choice-radio", "work-choice"],
#                     )

#                     gr.HTML(
#                         """
#                         <div class="preference-label">
#                             <span class="field-icon">◎</span>
#                             Do you require visa sponsorship?
#                             <span style="color:#e45c76">*</span>
#                         </div>
#                         """
#                     )

#                     visa_sponsorship_required = gr.Radio(
#                         choices=["Yes", "No"],
#                         value=None,
#                         show_label=False,
#                         elem_classes=["choice-radio", "sponsor-choice"],
#                     )

#         gr.HTML(
#             """
#             <div class="submit-area">
#                 <p class="submit-caption">
#                     You're one step closer to discovering your next opportunity.
#                 </p>
#             </div>
#             """
#         )

#         submit_button = gr.Button(
#             "Create my profile   →",
#             variant="primary",
#             elem_classes=["primary-btn"],
#         )

#         onboarding_status = gr.HTML()

#         gr.HTML(
#             """
#             <div class="trust-strip">
#                 <div class="trust-item">
#                     <span class="trust-icon">♧</span>
#                     <div>
#                         <strong>Your data is secure</strong>
#                         <small>Your professional information stays private.</small>
#                     </div>
#                 </div>
#                 <div class="trust-item">
#                     <span class="trust-icon">ϟ</span>
#                     <div>
#                         <strong>AI-powered matching</strong>
#                         <small>Discover roles aligned with your goals.</small>
#                     </div>
#                 </div>
#                 <div class="trust-item">
#                     <span class="trust-icon">▥</span>
#                     <div>
#                         <strong>Save time</strong>
#                         <small>Get relevant opportunities, not endless searches.</small>
#                     </div>
#                 </div>
#             </div>
#             """
#         )

#     submit_button.click(
#         fn=onboard_candidate,
#         inputs=[
#             resume_file,
#             preferred_roles,
#             preferred_locations,
#             remote_preference,
#             visa_sponsorship_required,
#         ],
#         outputs=onboarding_status,
#         show_progress="full",
#     )


# if __name__ == "__main__":
#     app.launch(inbrowser=True)
