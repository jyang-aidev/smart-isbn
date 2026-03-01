# 📚 Smart ISBN: AI-Powered Book Scanner & Metadata Search

**Smart ISBN** is an intelligent book scanning and metadata retrieval engine. Designed to bridge the gap between physical inventory and digital intelligence, it utilizes hardware barcode integration and Large Language Models (LLMs) to provide instant, high-fidelity book verification and data enrichment.



## 🚀 Key Features

* **Smart Barcode Scanning:** Optimized for high-speed hardware scanners with a custom JavaScript "Focus Keeper" to ensure zero-latency, continuous input.
* **Deep Metadata Search:** Aggregates data from multiple high-trust sources, including the **Google Books API** and headless scraping of **Douban**.
* **Agentic Verification:** Uses OpenAI's GPT-4o to cross-reference search results, ensuring metadata accuracy and flagging potential data discrepancies.
* **Cloud-Native Architecture:** Fully optimized for Streamlit Cloud with automated headless browser management and resource cleanup.

---

## 🛠️ Tech Stack

* **Frontend:** [Streamlit](https://streamlit.io/)
* **AI Engine:** [OpenAI API](https://openai.com/) (GPT-4o)
* **Search & Scraping:** BeautifulSoup4, Requests
* **Data Validation:** Pydantic, ISBNlib
* **Environment:** Poetry & Docker (Streamlit Cloud)

---

## 📦 Installation & Local Setup

To run the scanner and search engine locally:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/smart-isbn.git](https://github.com/your-username/smart-isbn.git)
    cd smart-isbn
    ```

2.  **Install dependencies:**
    ```bash
    poetry install
    ```

3.  **Environment Variables:**
    Create a `.env` file in the root directory:
    ```env
    OPENAI_API_KEY=your_api_key_here
    ```

4.  **Launch the App:**
    ```bash
    streamlit run app_barcode_cloud.py
    ```

---

## ☁️ Cloud Deployment Logic

This repository is "Cloud-Ready" with specific configurations to handle environments:

* **`pyproject.toml`**: Uses `package-mode = false` to handle local module imports (`book_details.py`, `auditor.py`) on remote servers.
* **Persistent Focus:** Injected JavaScript ensures that the search field remains active even during rapid-fire physical scanning.

---

## 📂 Project Structure

```text
├── app_barcode_cloud.py    # Main UI & Scanner Interface
├── book_details.py         # Metadata Search Logic (Scraping & APIs)
├── pyproject.toml          # Dependency Management
```
---

## 🛡️ License
### Distributed under the MIT License
