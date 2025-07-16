
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from openai import OpenAI
from fpdf import FPDF
import tempfile
import os
import fitz  # PyMuPDF

app = Flask(__name__)
CORS(app)
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()

def generate_prompt(job_description: str, resume_text: str) -> str:
    return f"""
You are a professional cover letter writer. Write a concise, elite-sounding cover letter for a QA Engineer position using the job post below.

Job Description:
{job_description}

Resume Content:
{resume_text}

Make the tone polished, confident, and personalized to the role.
""".strip()

def create_pdf(content: str) -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in content.split("\n"):
        pdf.multi_cell(0, 10, line)
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
        client = openai.OpenAI()

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        letter = response.choices[0].message.content
        pdf_path = create_pdf(letter)

        return send_file(pdf_path, as_attachment=True, download_name="Hotambek_Yusupov_Cover_Letter.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
