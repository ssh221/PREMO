import os

# 스크립트 파일 위치 기준 상대 경로 설정
script_dir = os.path.dirname(os.path.abspath(__file__))
folder_path = os.path.join(script_dir, 'profile_pictures')

# 폴더 존재 여부 확인
if not os.path.exists(folder_path):
    print(f"오류: '{folder_path}' 폴더가 존재하지 않습니다.")
    exit(1)

# 폴더 내 모든 파일 목록 가져오기
files = os.listdir(folder_path)
count = 0

# 각 파일 이름 변경
for file_name in files:
    if file_name.endswith('.png'):
        parts = file_name.split('_')
        if len(parts) >= 2:
            # 마지막 부분(ID)만 추출
            id_part = parts[-1].replace('.png', '')
            new_name = f"{id_part}.png"
            
            old_path = os.path.join(folder_path, file_name)
            new_path = os.path.join(folder_path, new_name)
            
            # 이미 같은 이름의 파일이 있는지 확인
            if os.path.exists(new_path) and old_path != new_path:
                print(f"경고: '{new_name}'이 이미 존재합니다. '{file_name}'의 이름을 변경하지 않습니다.")
                continue
                
            try:
                os.rename(old_path, new_path)
                count += 1
                if count % 100 == 0:  # 진행 상황 표시
                    print(f"{count}개 파일 이름 변경 완료...")
            except Exception as e:
                print(f"오류: '{file_name}' 이름 변경 실패: {e}")

print(f"총 {count}개 파일의 이름이 변경되었습니다.")
