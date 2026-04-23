import os
import time
from roboflow import Roboflow

# Initialize the Roboflow object with your API key
rf = Roboflow(api_key="2XbhRN5pMbb6bIk13z6C")

# Retrieve your current workspace and project name
print(rf.workspace())

# Specify the project for upload
workspaceId = 's-workspace-04sat'
projectId = 'wafflecar'
project = rf.workspace(workspaceId).project(projectId)

# Upload all images in savedImage/signOfStop
image_dir = "savedImage/signOfStop"
image_extensions = ('.jpg', '.jpeg', '.png', '.bmp')

START_INDEX = 0   # ← 아래 표에서 해당 배치의 값으로 교체 후 실행
                  #
                  #    배치  START_INDEX  업로드 범위       장수
                  #    ----  -----------  ---------------  ----
                  #    1번       0         0   ~ 58         59장
                  #    2번      59         59  ~ 117        59장
                  #    3번     118         118 ~ 176        59장
                  #    4번     177         177 ~ 235        59장
                  #    5번     236         236 ~ 294        59장
                  #    6번     295         295 ~ 353        59장
                  #    7번     354         354 ~ 399        46장  ← 마지막
BATCH_SIZE  = 399

images = sorted([f for f in os.listdir(image_dir) if f.lower().endswith(image_extensions)])
batch = images[START_INDEX:START_INDEX + BATCH_SIZE]

print(f"전체 {len(images)}개 중 [{START_INDEX}~{START_INDEX + len(batch) - 1}] {len(batch)}개 업로드 시작...")

DELAY_SEC = 10.0  # ← 업로드 간 딜레이 (초), 누락 발생 시 늘려보세요

for i, filename in enumerate(batch):
    image_path = os.path.join(image_dir, filename)
    print(f"[{START_INDEX + i + 1}/{len(images)}] {filename} 업로드 중...")
    project.upload(image_path)

print(f"업로드 완료 — 다음 배치: START_INDEX = {START_INDEX + len(batch)}")
