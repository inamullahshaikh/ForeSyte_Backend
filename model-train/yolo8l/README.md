# YOLOv8l (LARGE) Training Setup

## 🚀 **About YOLOv8l**

YOLOv8l is the **LARGE version** of YOLOv8 with:
- ✅ **43.7M parameters** (vs YOLOv8m's 25.9M)
- ✅ **+2-4% higher accuracy** than YOLOv8m
- ✅ **Better feature extraction** (deeper network)
- ✅ **Improved small object detection**
- ⚠️ **Slower training** (70% more parameters)
- ⚠️ **Needs more VRAM/RAM**

---

## 📊 **Model Comparison**

| Feature | YOLOv8m | YOLOv8l | Difference |
|---------|---------|---------|------------|
| Parameters | 25.9M | **43.7M** | +69% |
| Model Size | 52 MB | **87 MB** | +67% |
| Expected mAP@50 | 92-96% | **94-97%** | +2-4% |
| Training Speed | 1x | **0.7x** | 30% slower |
| Inference Speed | ~35 FPS | **~28 FPS** | Slightly slower |

---

## 📁 **Folder Structure**

```
yolo8l/
  ├── yolo8l.ipynb          # Training notebook
  ├── runs/                 # Training outputs
  │   └── yolo8l_high_accuracy/
  │       ├── weights/
  │       │   ├── best.pt (87 MB)
  │       │   ├── last.pt
  │       │   └── epoch*.pt
  │       └── results.csv
  ├── models/               # Exported models
  └── results/              # Evaluation results
```

**Dataset:** Shared from `../yolo8m/dataset/` (no duplication)

---

## ⚙️ **Optimized Hyperparameters for YOLOv8l**

### **Key Differences from YOLOv8m:**

| Parameter | YOLOv8m | YOLOv8l | Reason |
|-----------|---------|---------|---------|
| **Learning Rate (lr0)** | 0.001 | **0.0008** | Lower for stability (larger model) |
| **Weight Decay** | 0.0005 | **0.0006** | Higher to prevent overfitting |
| **Warmup Epochs** | 5 | **6** | Longer warmup for large model |
| **Classification Loss** | 0.75 | **0.8** | Higher for better class discrimination |
| **DFL Loss** | 1.5 | **1.6** | Better localization |
| **Patience** | 30 | **35** | More patience for convergence |
| **Batch Size (GPU)** | 8 | **6** | Reduced (VRAM constraints) |
| **Batch Size (CPU)** | 2 | **1** | Single batch for CPU |
| **Image Size (CPU)** | 832 | **640** | Lower resolution (heavy model) |

---

## 🎯 **Training Configuration**

### **GPU (Recommended):**
```python
EPOCHS = 100
IMGSZ = 1280
BATCH = 6          # Reduced from 8 (large model needs more VRAM)
WORKERS = 8
CACHE = True
AMP = True
PATIENCE = 35
```

**Expected:**
- Training time: **4-6 hours**
- Final mAP@50: **94-97%**
- Inference: **~28 FPS**

### **CPU:**
```python
EPOCHS = 100
IMGSZ = 640        # Lower resolution (large model is heavy)
BATCH = 1          # Single batch only
WORKERS = 2
CACHE = False
AMP = False
PATIENCE = 30
```

**Expected:**
- Training time: **25-35 hours** (much slower!)
- Final mAP@50: **91-94%**
- Inference: **~5-8 FPS**

---

## 🚀 **Quick Start**

### **1. Open Notebook:**
```bash
model-train/yolo8l/yolo8l.ipynb
```

### **2. Run Cells in Order:**
```
Cell 0: Fix PyTorch (if needed)
Cell 1: Setup directories
Cell 2: Install packages
Cell 3: Verify dataset
Cell 4: Check system (CPU/GPU)
Cell 5: TRAIN YOLOv8l (main cell)
Cell 6: EVALUATE
Cell 7: EXPORT
```

### **3. Training will:**
- Load `yolov8l.pt` base model
- Use shared dataset from `../yolo8m/dataset/`
- Save to `runs/yolo8l_high_accuracy/`
- Auto-resume if interrupted

---

## ⏱️ **Training Time Estimates**

| Hardware | Configuration | Time (100 epochs) |
|----------|---------------|-------------------|
| RTX 3090 | imgsz=1280, batch=6 | **~4 hours** |
| RTX 3080 | imgsz=1280, batch=4 | **~5 hours** |
| RTX 3060 | imgsz=1280, batch=2 | **~7 hours** |
| CPU (i7/Ryzen 7) | imgsz=640, batch=1 | **25-35 hours** |

---

## 🔄 **Parallel Training**

You can train **YOLOv8m and YOLOv8l simultaneously**:

1. ✅ YOLOv8m running in `yolo8m/` folder
2. ✅ Start YOLOv8l in `yolo8l/` folder
3. ✅ Both use **same dataset** (no duplication)
4. ✅ Outputs saved to **separate folders**:
   - YOLOv8m: `yolo8m/runs/yolo8m_high_accuracy/`
   - YOLOv8l: `yolo8l/runs/yolo8l_high_accuracy/`
5. ✅ No interference between trainings

---

## 📈 **Expected Performance Gains**

### **Over YOLOv8m:**

```
mAP@50:      +2-4%  (e.g., 93% → 96%)
mAP@50-95:   +2-3%  (e.g., 76% → 79%)
Precision:   +1-3%
Recall:      +1-2%
```

### **Best for:**
- ✅ **Maximum accuracy** required
- ✅ **Small object detection** (phones, hands)
- ✅ **Complex behaviors** (subtle movements)
- ✅ **Production deployment** (offline processing okay)

### **Not ideal for:**
- ❌ **Real-time constraints** (<30 FPS required)
- ❌ **Limited hardware** (CPU only, low VRAM)
- ❌ **Fast iteration** (training takes longer)

---

## 🔄 **Resume Training**

If training is interrupted, just run Cell 5 again:
- Automatically detects checkpoint at `runs/yolo8l_high_accuracy/weights/last.pt`
- Resumes from last completed epoch
- Uses original hyperparameters

Or manually:
```python
from ultralytics import YOLO
model = YOLO('runs/yolo8l_high_accuracy/weights/last.pt')
model.train(resume=True)
```

---

## 💡 **When to Use YOLOv8l vs YOLOv8m**

### **Use YOLOv8l when:**
- ✅ Accuracy is **top priority**
- ✅ You have **good hardware** (GPU with 8GB+ VRAM)
- ✅ Training time is **not critical**
- ✅ You need **best small object detection**
- ✅ **Offline processing** is acceptable

### **Use YOLOv8m when:**
- ✅ Need **balance** of speed and accuracy
- ✅ **Limited hardware** (CPU or low VRAM)
- ✅ **Faster training** preferred
- ✅ **Real-time inference** required (30+ FPS)
- ✅ Model size matters (deployment constraints)

---

## 📊 **Monitoring Training**

### **Check Progress:**
```python
import pandas as pd
df = pd.read_csv('runs/yolo8l_high_accuracy/results.csv')

# View recent epochs
print(df.tail())

# Plot learning curve
import matplotlib.pyplot as plt
plt.plot(df['epoch'], df['metrics/mAP50(B)'])
plt.xlabel('Epoch')
plt.ylabel('mAP@50')
plt.title('YOLOv8l Training Progress')
plt.show()
```

### **Compare with YOLOv8m:**
```python
df_m = pd.read_csv('../yolo8m/runs/yolo8m_high_accuracy/results.csv')
df_l = pd.read_csv('runs/yolo8l_high_accuracy/results.csv')

print(f"YOLOv8m final mAP@50: {df_m['metrics/mAP50(B)'].iloc[-1]:.4f}")
print(f"YOLOv8l final mAP@50: {df_l['metrics/mAP50(B)'].iloc[-1]:.4f}")
print(f"Improvement: +{(df_l['metrics/mAP50(B)'].iloc[-1] - df_m['metrics/mAP50(B)'].iloc[-1])*100:.2f}%")
```

---

## 🎯 **Final Recommendations**

### **Strategy:**
1. **Train both YOLOv8m and YOLOv8l** (they run in parallel)
2. **Compare results** after training completes
3. **Use YOLOv8l** if accuracy gain justifies slower inference
4. **Use YOLOv8m** if speed/size is more important

### **Expected Outcome:**
- YOLOv8l should achieve **94-97% mAP@50**
- Improvement over YOLOv8m: **+2-4%**
- Worth it if: **Every percentage point matters**

---

## 📦 **Model Export**

Run Cell 7 to export:
- **PyTorch (.pt)** - 87 MB
- **ONNX (.onnx)** - For deployment
- **TorchScript (.torchscript)** - For C++/mobile

---

## ⚠️ **Important Notes**

1. **VRAM Requirements:**
   - GPU: Minimum 8GB VRAM (RTX 3060 or better)
   - Reduce batch size if OOM errors occur

2. **Training Time:**
   - 30% slower than YOLOv8m
   - Budget accordingly (4-6 hours GPU, 25-35 hours CPU)

3. **Accuracy Gains:**
   - Expect +2-4% mAP improvement
   - Diminishing returns vs YOLOv8m
   - Best for production/final deployment

4. **Dataset:**
   - Uses same dataset as YOLOv8m (shared, no duplication)
   - No need to copy images

---

**Ready to train? Run Cell 5!** 🚀

*Expected final accuracy: 94-97% mAP@50*
