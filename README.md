# ✍️ Convert PDF to Handwritten Notes

A full-stack web application built with **Python** and **Flask** that transforms digital PDF text into aesthetic, handwritten-style notes. This tool is designed for students and creators who prefer the look of handwritten documents but want the efficiency of digital typing.

## 🚀 Live Demo
[Check out the live app on Vercel here!](https://pdf-to-handwritten.vercel.app)

## ✨ Features
* **Customization:** Adjust font size, text color, and heading color.
* **Handwriting Styles:** Choose from multiple unique handwriting fonts.
* **Paper Templates:** Support for different paper styles (Ruled, Blank, etc.).
* **Instant Conversion:** Fast processing from digital PDF to a downloadable "handwritten" version.
* **Glassmorphism UI:** A modern, aesthetic interface with backdrop-blur effects.

## 🛠️ Tech Stack
* **Backend:** Python (Flask)
* **PDF Processing:** PyPDF2 & ReportLab
* **Frontend:** HTML5, CSS3 (Modern Glassmorphism)
* **Deployment:** Vercel (Serverless Functions)

## 📂 Project Structure
```text
.
├── api/
│   └── index.py       # Main Flask application logic
├── static/            # CSS, Images (Background), and Fonts
├── templates/         # HTML structure (index.html)
├── fonts/             # Custom handwriting .ttf files
├── vercel.json        # Vercel deployment configuration
└── requirements.txt   # Python dependencies
