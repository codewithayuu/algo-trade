# 🚀 Team Cool as Code - Trading Agent Setup Guide

## 📋 Quick Overview
This guide will help you run our algorithmic trading agent. Just follow these steps exactly!

---

## 🔧 Step 1: Install Python (if not already installed)

### Check if you have Python:
1. Open Command Prompt (Windows) or Terminal (Mac/Linux)
2. Type: `python --version`
3. If you see version 3.8 or higher → **Good! Skip to Step 2**
4. If you see "command not found" → **Install Python first**

### Install Python (if needed):
1. Go to: https://www.python.org/downloads/
2. Download Python 3.8 or higher
3. During installation: **IMPORTANT** - Check "Add Python to PATH"
4. Restart your computer after installation

---

## 📥 Step 2: Get the Code from GitHub

### Option A: Using GitHub Desktop (Easiest)
1. Install GitHub Desktop from: https://desktop.github.com/
2. Login to your GitHub account
3. Click "Clone a Repository"
4. Enter the GitHub URL your teammate gives you
5. Choose where to save the folder
6. Click "Clone"

### Option B: Using Git Commands
1. Open Command Prompt/Terminal
2. Navigate to where you want to save the project:
   ```
   cd Desktop
   ```
3. Clone the repository:
   ```
   git clone [GITHUB_URL_YOUR_TEAMMATE_GIVES_YOU]
   ```
4. Navigate into the project folder:
   ```
   cd AlgoTrade
   ```

---

## 🔑 Step 3: Set Up API Configuration

### Create the Environment File:
1. In the AlgoTrade folder, create a new file named `.env` (yes, with the dot at the start)
2. Open this file with Notepad or any text editor
3. Add these two lines (your teammate will give you the actual values):

```
API_URL=https://algotrading.sanyamchhabra.in/api
TEAM_API_KEY=(will be given by team leader)
```

4. Save the file
5. **IMPORTANT**: Make sure the file is named exactly `.env` (not `.env.txt`)

---

## 📦 Step 4: Install Required Packages

### Method A: Using requirements.txt (Recommended)
1. Open Command Prompt/Terminal
2. Navigate to the AlgoTrade folder:
   ```
   cd Desktop/AlgoTrade
   ```
3. Install all required packages:
   ```
   pip install -r requirements.txt
   ```

### Method B: Manual Installation (if above doesn't work)
1. Install each package separately:
   ```
   pip install requests
   pip install numpy
   ```

---

## 🏃 Step 5: Run the Trading Agent

### Start the Agent:
1. Make sure you're in the AlgoTrade folder in Command Prompt/Terminal
2. Run the agent:
   ```
   python agent.py
   ```

### What You Should See:
```
==============================================================
  TEAM :- Cool as Code 🦇🦇 | Disciplined Capital Deployment
  Strategy: Hold 59% + Regime Awareness + Crash Protection
==============================================================
  API: https://algotrading.sanyamchhabra.in/api
  Key: configured

*T   1 [N] BUY 150                        | p=  450.23 | pos=59% | nw=$10,000 | dd=0.0% | pnl=+0.00% | m=+0.0012
 T   2 [N] HOLD                            | p=  450.45 | pos=59% | nw=$10,015 | dd=0.0% | pnl=+0.15% | m=+0.0015
```

---

## 🛠️ Troubleshooting Common Issues

### Issue: "python: command not found"
**Solution**: Make sure Python is installed and added to PATH (see Step 1)

### Issue: "No module named 'requests'" or "No module named 'numpy'"
**Solution**: Run `pip install requests numpy` again

### Issue: "API error, skipping tick"
**Possible causes**:
1. Internet connection problem
2. Wrong API URL in .env file
3. Wrong API key in .env file
4. Competition hasn't started yet

**Solution**: Check your .env file and internet connection

### Issue: "Key: MISSING!"
**Solution**: Your .env file is not being read properly
1. Make sure the file is named exactly `.env` (not `.env.txt`)
2. Make sure it's in the same folder as agent.py
3. Check that the lines have no extra spaces

---

## 📊 Understanding the Output

### What the Agent Does:
- **Buys** assets at 59% allocation immediately
- **Holds** through normal market movements
- **Protects** against major crashes (reduces to 20-35% if needed)
- **Minimizes** trades to avoid fees

### Reading the Display:
```
*T   1 [N] BUY 150                        | p=  450.23 | pos=59% | nw=$10,000 | dd=0.0% | pnl=+0.00% | m=+0.0012
```

- `*` = Trade executed this tick
- `T   1` = Tick number 1
- `[N]` = State: N=Normal, C=Cautious, X=Crashed
- `BUY 150` = Action taken
- `p=450.23` = Current price
- `pos=59%` = Position percentage
- `nw=$10,000` = Net worth
- `dd=0.0%` = Drawdown (loss from peak)
- `pnl=+0.00%` = Profit/Loss percentage
- `m=+0.0012` = 30-bar momentum

---

## 🎯 Important Notes

### During Competition:
1. **Don't close the window** - the agent needs to keep running
2. **Keep internet stable** - interruptions cause missed trades
3. **Monitor occasionally** - but don't interfere unless needed
4. **Competition ends automatically** when market closes

### If Something Goes Wrong:
1. **Don't panic** - the agent has built-in error handling
2. **Take a screenshot** of any error messages
3. **Contact your teammate** with the screenshot
4. **You can restart** the agent by closing and running `python agent.py` again

---

## 🏆 Success Indicators

### Everything is Working When:
✅ Agent starts without errors  
✅ Shows "Key: configured"  
✅ Shows "BUY" action on first tick  
✅ Updates price and position every 10 seconds  
✅ No "API error" messages  

### Competition Status:
- **Running**: Agent updates every 10 seconds
- **Market Closed**: Agent will show "MARKET CLOSED" and stop
- **Error**: Agent will show error messages but won't crash

---

## 🎉 You're Ready!

Once you complete these steps, the trading agent will run automatically and handle everything for you. Just let it do its job and good luck in the competition!

**Remember**: Trust the system and let it run! 🚀
