# Lane detect with Yolov8 segmenation

## 1. environments

- python 3.10
- cuda 12.2
- torch : 2.0.1
- torchaudio : 2.2.1
- torchvision : 0.15.2

```
python -m venv yolov8_seg
source ~/venv/yolov8_seg/bin/activate
pip install -r requirements.txt
```

## 2. description

- train
    - yolov8_train.py : Train a yolov8-segmenation model with a dataset
    - roboflow_dataset.yaml : Dataset path and class name

- inference
    - yolov8_inference_fps.py : Inference with trained model, check fps