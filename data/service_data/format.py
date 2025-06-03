import pandas as pd
from dateutil import parser
import pytz
from tqdm import tqdm  # 진행률 표시용

def convert_timezone(csv_path):
    # CSV 파일 로드
    df = pd.read_csv(csv_path)
    
    # 타임존 매핑 정보 (GMT+01:00 -> Europe/London)
    tz_mapping = {
        'GMT': 'Europe/London',
        'BST': 'Europe/London',
        'GMT+01:00': 'Europe/London'
    }

    # 오류 카운터
    error_log = []

    # 각 행별 처리 (진행률 표시)
    tqdm.pandas(desc="시간 변환 진행 중")
    for idx in tqdm(df.index):
        try:
            # 1. 원본 날짜 파싱
            dt_str = df.at[idx, 'date']
            
            # 2. 시간대 정보 추출
            if 'GMT' in dt_str:
                main_part, tz_info = dt_str.rsplit('GMT', 1)
                tz_offset = f"GMT{tz_info.strip()}"
                tz = tz_mapping.get(tz_offset, 'UTC')
            else:
                main_part = dt_str
                tz = 'Europe/London'

            # 3. 날짜 파싱 (초 단위 제거)
            dt_naive = parser.parse(main_part.strip(), dayfirst=True).replace(second=0, microsecond=0)
            
            # 4. 시간대 적용
            local_tz = pytz.timezone(tz)
            dt_local = local_tz.localize(dt_naive)
            
            # 5. 한국 시간 변환
            dt_kst = dt_local.astimezone(pytz.timezone('Asia/Seoul'))
            
            # 6. 컬럼 업데이트
            df.at[idx, 'date'] = dt_local.strftime('%Y-%m-%d')
            df.at[idx, 'kr_start_time'] = dt_kst.strftime('%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            error_log.append(f"Row {idx}: {str(e)}")
            df.at[idx, 'date'] = None
            df.at[idx, 'kr_start_time'] = None

    # 오류 리포트 출력
    if error_log:
        print("\n⚠️ 처리 실패 레코드:")
        for log in error_log[:5]:  # 최대 5개 오류만 표시
            print(f"  - {log}")
        print(f"총 {len(error_log)}개 오류 발생. 자세한 내용은 콘솔 출력 확인")

    # CSV 파일 덮어쓰기
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    return df

# 사용 예시
convert_timezone('matches.csv')
