from pathlib import Path

print('进入成功ovO!')
BASE_DIR=Path(__file__).parent
#__file__ 当前这个python文件本身的位置
#E:\Alkaid_agent\config.py
#agent 工作目錄
workspace_dir=BASE_DIR /'workspace'
#base 根目錄
#輸入文件
inputput_dir=workspace_dir/'input'
#輸出文件
output_dir=workspace_dir/'output'
#報告文件
reports_dir=workspace_dir/'reports'

if __name__=='__main__':
    print('工作目錄:',BASE_DIR)
    print('輸入文件:',workspace_dir)
    print('輸出文件:',output_dir)