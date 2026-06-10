from flask_cors import CORS
from flask import Flask, request, jsonify
import base64
import requests
import tempfile
from dotenv import load_dotenv
from pdf2image import convert_from_path
from pathlib import Path
import os

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

print("API:", os.environ.get("GOOGLE_API_KEY"))

API_KEY = os.getenv("GOOGLE_API_KEY")

#pdf
POPPLER_PATH = os.getenv("POPPLER_PATH")


app = Flask(__name__)
CORS(app)

@app.route("/ocr_google", methods=["POST"])
def ocr_google():
    if "file" not in request.files:
        print("ARQUIVO NÃO ENVIADO", flush=True)
        return jsonify({"error": "Arquivo não enviado"}), 400

    file = request.files["file"]
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()

    fd, filepath = tempfile.mkstemp(suffix=ext)
    os.close(fd)
    file.save(filepath)

    try:
        # Reabre o arquivo salvo para não usar o stream já exaurido pelo save()
        if ext == ".pdf":
            if POPPLER_PATH:
                paginas = convert_from_path(filepath, poppler_path=POPPLER_PATH)
            else:
                paginas = convert_from_path(filepath)

            textos = []
            for pagina in paginas:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as img_tmp:
                    img_path = img_tmp.name
                    pagina.save(img_path, "JPEG")

                try:
                    with open(img_path, "rb") as f:
                        texto_pagina = google_ocr(f)
                        if texto_pagina:
                            textos.append(texto_pagina)
                finally:
                    if os.path.exists(img_path):
                        os.remove(img_path)

            texto = "\n".join(textos)
        else:
            with open(filepath, "rb") as f:
                texto = google_ocr(f)

        print("Texto extraído:", texto, flush=True)

        if not texto:
            return jsonify({"error": "Nenhum texto extraído via Google OCR"}), 500

        audio = google_tts(texto)
        print("Áudio gerado (base64):", audio[:50] + "..." if audio else "None", flush=True)

        if not audio:
            return jsonify({"texto": texto, "audio": None})

        return jsonify({"texto": texto, "audio": audio})

    except Exception as e:
        print("Exceção:", str(e), flush=True)
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

#API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Verifica se a chave API foi configurada
if not API_KEY:
    raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi definida.")

OCR_URL = "https://vision.googleapis.com/v1/images:annotate?key=" + API_KEY
TTS_URL = "https://texttospeech.googleapis.com/v1/text:synthesize?key=" + API_KEY


def google_ocr(file):

    print("LENDO ARQUIVO...", flush=True)

    image_base64 = base64.b64encode(file.read()).decode("utf-8")

    print("ENVIANDO PARA GOOGLE OCR...", flush=True)

    body = {
        "requests": [
            {
                "image": {"content": image_base64},
                "features": [{"type": "TEXT_DETECTION"}]
            }
        ]
    }

    response = requests.post(OCR_URL, json=body)

    print("STATUS OCR:", response.status_code, flush=True)

    print("RESPOSTA BRUTA OCR:", response.text, flush=True)

    if response.status_code != 200:
        return None

    result = response.json()

    responses = result.get("responses", [])

    if not responses:
        print("SEM RESPONSES", flush=True)
        return None

    annotation = responses[0].get("fullTextAnnotation")

    if not annotation:
        print("SEM fullTextAnnotation", flush=True)
        return None

    texto = annotation.get("text", "")

    print("TEXTO OCR:", texto, flush=True)

    return texto


def google_tts(texto):
    body = {
        "input": {"text": texto},
        "voice": {
            "languageCode": "pt-BR",
            "name": "pt-BR-Wavenet-A"
        },
        "audioConfig": {
            "audioEncoding": "MP3"
        }
    }

    response = requests.post(TTS_URL, json=body)
    
    # Verifica status HTTP
    if response.status_code != 200:
        print(f"Erro HTTP TTS {response.status_code}: {response.text}", flush=True)
        return None
        
    result = response.json()
    
    # Verifica erro na resposta
    if "error" in result:
        print("Erro TTS:", result["error"], flush=True)
        return None

    return result.get("audioContent", "")


@app.route("/", methods=["GET"])
def index():
    return jsonify({"msg": "api em execução"})


if __name__ == "__main__":
    app.run(debug=True)