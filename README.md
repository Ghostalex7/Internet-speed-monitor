# Internet Speed Monitor – Python Application

[![Language: Python](https://img.shields.io/badge/language-python-blue.svg)](https://www.python.org/)  
A Python GUI app for real-time internet speed monitoring using speedtest and matplotlib.

---

## 📘 Description
This application tracks your internet connection in real time, visualizing download and upload speeds through a modern, interactive GUI built with CustomTkinter and matplotlib. Designed for practical use and clear performance insight.

---

## 🔧 Features
- Real-time download/upload monitoring
- Modern CustomTkinter interface with dark mode
- Dynamic matplotlib-based speed chart
- Background speed testing (non-blocking)
- Export data to text file for later analysis
- Responsive UI with graph auto-scaling

---

## 🛠 Requirements
- Python 3.7+
- `customtkinter`, `matplotlib`, `speedtest-cli`

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/Ghostalex7/Internet-speed-monitor.git
cd Internet-speed-monitor
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the App
```bash
python3 monitor.py
```
The app will open and begin checking your connection every 10 seconds.

---

## 📂 Project Structure
- `monitor.py` – Main application with GUI, logic, and plotting
- `requirements.txt` – List of required packages

---

## 💾 Exported Output
When you click **EXPORT DATA**, the app saves speed records to:
```
medicion_1.txt
medicion_2.txt
...
```
Example format:
```
Date,Time,Download (Mbps),Upload (Mbps)
2025-04-19,13:00:00,134.75,42.98
```

---

## 🤝 Contributing
Contributions are welcome! Please fork this repo and submit a pull request with enhancements or fixes.

---

## 🛡 License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 👤 Author
Ghostalex7 – [github.com/Ghostalex7](https://github.com/Ghostalex7)

