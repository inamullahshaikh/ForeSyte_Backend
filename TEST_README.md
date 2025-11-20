# 🧪 Quick Test Guide

## Run Video Stream Tests in 3 Steps

### Step 1: Update Video Path ✏️

Edit line 15 in `test_complete_video_streams.py`:

```python
VIDEO_FILE_PATH = "Cheat-1.mp4"  # ← Change this to your video path
```

### Step 2: Start Backend 🚀

```bash
cd ForeSyte_Backend-main/src
uvicorn main:app --reload
```

### Step 3: Run Tests 🧪

```bash
cd ForeSyte_Backend-main
python test_complete_video_streams.py
```

---

## 📋 What Gets Tested

✅ Video file upload  
✅ Processing status monitoring  
✅ Frame extraction  
✅ Results retrieval  
✅ File storage verification  
✅ API endpoints  
✅ Documentation access  

**Total:** 9 comprehensive tests

---

## ✅ Expected Output

```
================================================================================
  ForeSyte - Complete Video Streams Test Suite
================================================================================

Configuration:
  API URL: http://localhost:8000
  Video File: Cheat-1.mp4

... [9 tests run] ...

================================================================================
  TEST SUMMARY
================================================================================

Results:
   Total Tests: 9
   Passed: 9 ✅
   Failed: 0
   Success Rate: 100.0%

Next Steps:
✅ All tests passed! ✨
   1. Check extracted frames in: src/uploads/frames/
   2. View API docs: http://localhost:8000/docs
   3. Ready for frontend integration!

================================================================================
```

---

## 🐛 Common Issues

### "Video file not found"
**Fix:** Update `VIDEO_FILE_PATH` in test script (line 15)

### "Cannot connect to API"
**Fix:** Make sure backend is running (`uvicorn main:app --reload`)

### "Processing timeout"
**Fix:** Increase `MAX_WAIT_TIME` in test script (line 20) or use smaller video

---

## 📚 More Details

See **TESTING_GUIDE.md** for:
- Detailed test descriptions
- Troubleshooting guide
- Customization options
- API verification commands

---

## 🎯 Quick Commands

```bash
# Start backend
cd ForeSyte_Backend-main/src && uvicorn main:app --reload

# Run tests (in new terminal)
cd ForeSyte_Backend-main && python test_complete_video_streams.py

# Check extracted frames
ls src/uploads/frames/

# View API docs
# Open: http://localhost:8000/docs
```

---

## ✨ That's It!

Your video stream processing backend is fully tested and ready! 🚀

**Questions?** Check TESTING_GUIDE.md for complete documentation.

