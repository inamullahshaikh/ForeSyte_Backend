# 🔄 How to Resume Training

## ✅ **Current Status:**
- You've completed **10 epochs** (out of 50)
- Current mAP@50: **80.6%**
- Checkpoint saved at: `runs/yolo8m_high_accuracy/weights/last.pt`

---

## 📝 **To Resume Training from Epoch 11:**

### **Option 1: Quick Resume (Recommended)**
Add this code in a new cell **BEFORE Cell 5**:

```python
# RESUME TRAINING FROM CHECKPOINT
from ultralytics import YOLO

checkpoint = 'runs/yolo8m_high_accuracy/weights/last.pt'
model = YOLO(checkpoint)

print(f"Resuming training from: {checkpoint}")
results = model.train(resume=True)

print("\n✓ Training resumed and completed!")
```

That's it! This will:
- ✅ Load your checkpoint from epoch 10
- ✅ Resume from epoch 11
- ✅ Continue with all your previous hyperparameters
- ✅ Train until epoch 50

---

### **Option 2: Modify Cell 5**
The Cell 5 I just updated now **automatically** detects if a checkpoint exists.

Just run Cell 5 again - it will:
1. Check if `runs/yolo8m_high_accuracy/weights/last.pt` exists
2. If YES: Load it and resume from epoch 11
3. If NO: Start fresh from epoch 0

**The cell now shows:**
```
🔄 RESUMING TRAINING from checkpoint
📁 Loading: runs/yolo8m_high_accuracy/weights/last.pt
📊 Last completed epoch: 10
▶️  Will resume from epoch 11
```

---

## ⚠️ **Important Notes:**

### **If you want to start completely fresh:**
1. Delete or rename the `runs/yolo8m_high_accuracy` folder
2. Run Cell 5 - it will start from epoch 0

### **If training was interrupted:**
- ✅ Checkpoints are saved every epoch in `last.pt`
- ✅ Best model saved in `best.pt` (when validation improves)
- ✅ You can stop/resume anytime

### **Monitoring Progress:**
```python
# Check current epoch by reading results.csv
import pandas as pd
df = pd.read_csv('runs/yolo8m_high_accuracy/results.csv')
print(f"Last completed epoch: {df['epoch'].max()}")
print(f"Current mAP@50: {df['metrics/mAP50(B)'].iloc[-1]:.4f}")
```

---

## 📊 **Your Training Progress So Far:**

| Epoch | mAP@50 | mAP@50-95 | Box Loss | Cls Loss |
|-------|--------|-----------|----------|----------|
| 1 | 61.6% | 27.8% | 1.748 | 3.052 |
| 5 | 76.3% | 41.4% | 1.476 | 1.759 |
| 10 | **80.6%** | **45.2%** | 1.382 | 1.497 |

**Trend:** 📈 Excellent progress! Losses decreasing, accuracy increasing.

**Expected at epoch 50:** 
- mAP@50: ~88-92%
- mAP@50-95: ~72-78%

---

## 🚀 **Quick Command:**

Just run this in a new cell:

```python
from ultralytics import YOLO
YOLO('runs/yolo8m_high_accuracy/weights/last.pt').train(resume=True)
```

**Done!** It will continue from epoch 11 to 50. 🎯
