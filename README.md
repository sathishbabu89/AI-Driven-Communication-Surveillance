# 📧 AI-Driven Communication Surveillance (POC)

An intelligent compliance surveillance tool that leverages **Azure OpenAI** and **LangChain** to automatically monitor and analyze bank communications for regulatory risk.

## 🚀 Overview

This application automates the tedious process of manual email review. It ingests an Excel file containing email logs, performs sentence-level decomposition, and uses Large Language Models (LLMs) to identify potential compliance violations based on a predefined risk matrix.

### Key Features

* **Automated Risk Scoring:** Assigns priority scores (0-5) based on the severity of the violation category.
* **Line-Level Evidence:** Don't just get a "Yes/No" answer—the AI identifies specific sentence IDs that triggered the alert.
* **Real-time Analytics:** Watch the analysis progress live with a sorted priority table and category distribution charts.
* **Transparent Reasoning:** Expandable "Proof of Thought" sections for every email, showing the raw prompt, the JSON response, and the scoring logic.

---

## 🛠️ Technical Stack

* **Frontend:** [Streamlit](https://streamlit.io/) (Data Dashboard)
* **Orchestration:** [LangChain](https://www.langchain.com/)
* **LLM:** Azure OpenAI (GPT-4 / GPT-3.5)
* **Data Handling:** Pandas & OpenPyXL
* **Environment:** Python (dotenv)

---

## ⚖️ Compliance Risk Matrix

The system evaluates emails against the following categories and weights:

| Category | Risk Weight | Description |
| --- | --- | --- |
| **Market Manipulation** | 5 | Misconduct, price-fixing, or market abuse. |
| **Market Bribery** | 5 | Corruption or illegal incentives. |
| **Secrecy** | 4 | Unauthorized disclosure of sensitive data. |
| **Employee Ethics** | 3 | General violations of code of conduct. |
| **Change in Comm.** | 3 | Moving conversations to unmonitored channels. |
| **Complaints** | 2 | Customer dissatisfaction or formal grievances. |

---

## 📥 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ai-compliance-surveillance.git
cd ai-compliance-surveillance

```

### 2. Install Dependencies

```bash
pip install -r requirements.txt

```

### 3. Configure Environment Variables

Create a `.env` file in the root directory and add your Azure credentials:

```env
AZURE_OPENAI_API_KEY=your_key_here
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
OPENAI_API_VERSION=2023-05-15
AZURE_DEPLOYMENT_NAME=your_deployment_name

```

### 4. Run the Application

```bash
streamlit run app.py

```

---

## 📖 How It Works

1. **Preprocessing:** The app reads the `Subject` and `Message Body` from your Excel file. It splits the body into numbered sentences.
2. **Prompt Engineering:** A structured prompt is sent to Azure OpenAI requesting a **strict JSON response**.
3. **Parsing:** The app uses Regex and JSON libraries to extract the compliance status, the reason, and the specific line IDs of evidence.
4. **Priority Calculation:**

*(Where Non-Compliant = 1, Compliant = 0)*
5. **Visualization:** The UI sorts the "Red Flags" to the top of the list so compliance officers can investigate the highest risks first.

---

## 📊 Data Format

The application expects an `.xlsx` file with the following columns:

* `Email Address From`
* `Email Address To`
* `Subject`
* `Message Body`

## Screenshot
<img width="1348" height="630" alt="image" src="https://github.com/user-attachments/assets/f178f79d-3db5-44ef-b4cd-fa6d127cc23b" />
