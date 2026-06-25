# Running on Google Colab 🚀

You can run this entire application on Google Colab for free. Here is the step-by-step guide:

## 1. Upload Code to Colab
1. Zip your project folder (excluding `__pycache__` and `.git`).
2. Open [Google Colab](https://colab.research.google.com/).
3. Create a new notebook.
4. Upload your zip file to the "Files" section (left sidebar).
5. Unzip it using:
   ```bash
   !unzip Auction.zip -d .
   ```

## 2. Setup and Run
Run the following commands in a Colab cell to install dependencies and start the app:

```python
# Install requirements
!pip install -r requirements.txt
!pip install pyngrok  # Or use Localtunnel (see below)

# Run the app in the background
!streamlit run app.py & npx localtunnel --port 8501
```

## 3. Persistent Database (Google Drive)
To prevent losing your data when the Colab session ends:
1. Mount your Google Drive:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```
2. In `src/config.py`, point `DB_NAME` to a folder in your Google Drive (e.g., `/content/drive/MyDrive/Auction/auctions.db`).

## 4. Simplified Colab Script
I have included a `colab_setup.py` script that handles most of this for you. Just run:
```bash
!python colab_setup.py
```
This will give you a public URL to access your dashboard!
