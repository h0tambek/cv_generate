from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from openai import OpenAI
from fpdf import FPDF
import tempfile
import os
import fitz  # PyMuPDF

app = Flask(__name__)
CORS(app)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    project=os.getenv("OPENAI_PROJECT_ID")
)

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()

def sanitize_text(text):
    return (
        text.replace("’", "'")
            .replace("‘", "'")
            .replace("“", '"')
            .replace("”", '"')
            .replace("—", "-")
            .replace("–", "-")
            .replace("…", "...")
    )

def generate_prompt(job_description: str, resume_text: str) -> str:
    return f"""
You are a professional cover letter writer. Write a concise, elite-sounding cover letter for a QA Engineer position.

ONLY use the provided resume info. NEVER add fake URLs, dates, names, or placeholders (e.g., "linkedin.com/in/yourname" or "github.com/yourprofile").

---
Job Description:
{job_description}

---
<resume>
{resume_text}
</resume>

Use only the content inside <resume>. Do not invent or assume missing contact info.
Tone should be polished, confident, and specific to the job post.
Limit the output to fit one standard A4 PDF page (~350-400 words max).
""".strip()

def create_pdf(content: str) -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)
    pdf.set_font("Helvetica", size=10)
    for line in content.split("\n"):
        pdf.multi_cell(0, 7, line)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name

@app.route("/", methods=["POST"])
def generate_cover_letter():
    try:
        data = request.get_json()
        jd = data.get("job_description", "").strip()
        if not jd:
            return jsonify({"error": "Missing job_description"}), 400

        resume_path = os.path.join(os.path.dirname(__file__), "Hotambek_Yusupov_Resume_Final.pdf")
        resume_text = extract_text_from_pdf(resume_path)

        prompt = generate_prompt(jd, resume_text)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        letter = sanitize_text(response.choices[0].message.content)

        # Trim output to keep PDF within one page
        letter_lines = letter.split("\n")
        if len(letter_lines) > 60:
            letter = "\n".join(letter_lines[:60])
        elif len(letter) > 2300:
            letter = letter[:2300]

        pdf_path = create_pdf(letter)
        return send_file(pdf_path, as_attachment=True, download_name="Hotambek_Yusupov_Cover_Letter.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
