# 🚀 Quick Start - NormCode Orchestrator App

Get up and running with the Streamlit orchestrator in 60 seconds!

## ⚡ 1-Minute Setup

```bash
# Navigate to the app directory
cd streamlit_app

# Install Streamlit (if not already installed)
pip install streamlit

# Launch the app
streamlit run app.py
```

The app opens at `http://localhost:8501` 🎉

## 📁 What You Need

Three JSON files (see `infra/examples/add_examples/repo/` for examples):

1. **concepts.json** - Your data structures
2. **inferences.json** - Your logic steps  
3. **inputs.json** - Initial values (optional)

## 🎯 First Run - Addition Example

### Step 1: Create `my_inputs.json`

```json
{
  "{number pair}": {
    "data": [["%(123)", "%(456)"]],
    "axes": ["number pair", "number"]
  }
}
```

### Step 2: Upload in App

- **Concepts**: `infra/examples/add_examples/repo/addition_concepts.json`
- **Inferences**: `infra/examples/add_examples/repo/addition_inferences.json`  
- **Inputs**: `my_inputs.json`

### Step 3: Configure

- **LLM**: `qwen-plus`
- **Max Cycles**: `50`
- **Mode**: `Fresh Run`

### Step 4: Execute

Click **▶️ Start Execution**

### Step 5: View Results

Check the **Results** tab!

## 🔄 Second Run - Using Checkpoint

After completing the first run:

1. Upload `combination_concepts.json` and `combination_inferences.json`
2. Select **Resume (PATCH)** mode
3. Click **▶️ Start Execution**

The app will load `{new number pair}` from the first run's checkpoint! 

## 📚 Learn More

- **Full Guide**: [STREAMLIT_APP_GUIDE.md](STREAMLIT_APP_GUIDE.md)
- **App README**: [APP_README.md](APP_README.md)
- **Orchestration Docs**: [infra/_orchest/README.md](infra/_orchest/README.md)

## 🆘 Common Issues

### "streamlit: command not found"
```bash
pip install streamlit
```

### "No module named 'infra'"
```bash
# Make sure you're in the streamlit_app directory
cd /path/to/normCode/streamlit_app
streamlit run app.py
```

### "File won't upload"
Check JSON syntax:
```bash
python -m json.tool your_file.json
```

## 💡 Pro Tips

✅ **Use PATCH mode** - Safest for most scenarios  
✅ **Start simple** - Test with small examples first  
✅ **Check History tab** - See all your past runs  
✅ **Export results** - Download as JSON for backup  

---

**Need help?** Check the **Help** tab in the app or read [STREAMLIT_APP_GUIDE.md](STREAMLIT_APP_GUIDE.md)

