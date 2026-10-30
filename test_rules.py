from tool import (

    inspect_file,
    run_rules,
    build_validation_report,
    clean_file
)
import pandas as pd

# ==============================
# 1. 读取用户指定的 CSV 文件
# ==============================




df=pd.DataFrame({
    '订单号':['A001','A002',None],
    '数量':[2,None,5],
    '重量':[1.5,20,60]
})
cleaned_df=clean_file(
    df,'dropna',column='数量'
)
print('原始数据')
print(df)
print('======测试filla=======')
result=clean_file(df,'fillna',column='数量',value=0)
print(result)

print('======测试dropna=====')
result=clean_file(df,'dropna',column='数量')
print(result)

print('======测试astype=====')
result=clean_file(df,'astype',column='数量',value='float')
print(result)
print('数量列类型:',result['数量'].dtype)
print('原始数据:')
print(df)