from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
import openai

app = Flask(__name__)

# Set your OpenAI API key here
openai.api_key = <add_your_openai_api_key>

def get_url_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '').lower()

        if 'text/html' in content_type:
            return extract_html_content(response.text)
        elif 'application/pdf' in content_type:
            return extract_pdf_content(response.content)
        else:
            return response.text

    except requests.RequestException as e:
        return f"Error fetching URL: {str(e)}"

def extract_html_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    for script in soup(["script", "style"]):
        script.decompose()
    
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return text

def extract_pdf_content(pdf_content):
    pdf_file = io.BytesIO(pdf_content)
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def get_chatgpt_summary(content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text."},
                {"role": "user", "content": f"Please summarize the following text:\n\n{content}. Focus on the key innovations or important aspects. Make sure each sentence is complete."}
            ],
            max_tokens=200
        )
        return response.choices[0].message['content'].strip()
    except openai.error.InvalidRequestError as e:
        if "maximum context length" in str(e):
            return "The input text is too long to process in a single request. Please limit the number of pages to 15."
        else:
            return f"An error occurred: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        content = get_url_content(url)
        summary = get_chatgpt_summary(content)
        return jsonify({'content': content, 'summary': summary})
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)



