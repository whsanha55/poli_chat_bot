import os
import shutil

def clean_pycache(start_path='.'):
    """
    모든 __pycache__ 디렉토리를 재귀적으로 찾아서 삭제합니다.
    
    Args:
        start_path (str): 검색을 시작할 디렉토리 경로
    """
    # 시작 경로를 절대 경로로 변환
    start_path = os.path.abspath(start_path)
    
    for root, dirs, files in os.walk(start_path):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f'삭제됨: {pycache_path}')
            except Exception as e:
                print(f'오류 발생: {pycache_path} - {str(e)}')
        
        # .pyc 파일도 삭제
        for file in files:
            if file.endswith('.pyc'):
                pyc_path = os.path.join(root, file)
                try:
                    os.remove(pyc_path)
                    print(f'삭제됨: {pyc_path}')
                except Exception as e:
                    print(f'오류 발생: {pyc_path} - {str(e)}')

if __name__ == '__main__':
    # 현재 디렉토리에서 시작
    clean_pycache()
    print('정리 완료!') 