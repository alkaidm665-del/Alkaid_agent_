from pathlib import Path
import pandas as pd
import re
from numbers import Integral, Real


# ==============================
# 1. 检查并读取文件
# ==============================

def inspect_file(file_path):
    path = Path(file_path)

    if not path.exists():
        return {
            '成功': False,
            '原因': '文件不存在'
        }

    if not path.is_file():
        return {
            '成功': False,
            '原因': '指定路径不是文件'
        }

    if path.suffix.lower() != '.csv':
        return {
            '成功': False,
            '原因': '暂不支持该文件格式'
        }

    try:
        df = pd.read_csv(path)

    except Exception as e:
        return {
            '成功': False,
            '原因': str(e)
        }

    return {
        '成功': True,
        '文件名': path.name,
        '行数': len(df),
        '列数': len(df.columns),
        '字段': list(df.columns),
        '数据类型': {
            str(column): str(dtype)
            for column, dtype in df.dtypes.items()
        },
        'data': df
    }


# ==============================
# 2. 统一生成校验结果
# ==============================

def make_result(column, bad_rows, reason):
    bad_rows = list(bad_rows)

    return {
        '问题': bool(bad_rows),
        '异常列': column,
        '异常行号': bad_rows,
        '原因': reason
    }


# ==============================
# 3. 通用单列校验
# ==============================

def validate_data(df, column, rule_type, rule_value=None):

    # 检查参数
    if not isinstance(df, pd.DataFrame):
        return make_result(
            column, [], '输入数据不是 DataFrame'
        ) | {'问题': True}

    if column not in df.columns:
        return make_result(
            column, [], '数据中不存在该列'
        ) | {'问题': True}

    if rule_type not in {
        'not_null', 'unique', 'type',
        'range', 'format', 'logic'
    }:
        return make_result(
            column, [], f'不支持的规则类型：{rule_type}'
        ) | {'问题': True}

    data = df[column]

    # --------------------------
    # 规则一：非空检查
    # --------------------------

    if rule_type == 'not_null':

        bad_mask = data.isna()

        # 同时识别空字符串和只有空格的字符串
        text_mask = data.map(
            lambda x: isinstance(x, str)
            and x.strip() == ''
        )

        bad_mask = bad_mask | text_mask

        return make_result(
            column,
            data[bad_mask].index,
            f"'{column}'列存在空值"
        ) if bad_mask.any() else make_result(
            column, [], f"'{column}'符合要求"
        )

    # --------------------------
    # 规则二：唯一性检查
    # --------------------------

    elif rule_type == 'unique':

        bad_mask = data.duplicated(keep=False)

        return make_result(
            column,
            data[bad_mask].index,
            f"'{column}'列存在重复值"
        ) if bad_mask.any() else make_result(
            column, [], f"'{column}'符合要求"
        )

    # --------------------------
    # 规则三：类型检查
    # --------------------------

    elif rule_type == 'type':

        if rule_value not in {'int', 'float', 'str'}:
            return {
                '问题': True,
                '异常列': column,
                '异常行号': [],
                '原因': f'不支持的类型参数：{rule_value}'
            }

        def matches_type(value):
            # 缺失值交给 not_null 规则检查
            if pd.isna(value):
                return True

            if rule_value == 'int':
                return (
                    isinstance(value, Integral)
                    and not isinstance(value, bool)
                )

            elif rule_value == 'float':
                return (
                    isinstance(value, Real)
                    and not isinstance(value, Integral)
                    and not isinstance(value, bool)
                )

            elif rule_value == 'str':
                return isinstance(value, str)

        bad_mask = ~data.map(matches_type)

        return make_result(
            column,
            data[bad_mask].index,
            f"'{column}'类型异常，要求 {rule_value}"
        ) if bad_mask.any() else make_result(
            column, [], f"'{column}'符合类型要求"
        )

    # --------------------------
    # 规则四：数值范围检查
    # --------------------------

    elif rule_type == 'range':

        if (
            not isinstance(rule_value, dict)
            or 'min' not in rule_value
            or 'max' not in rule_value
        ):
            return {
                '问题': True,
                '异常列': column,
                '异常行号': [],
                '原因': 'range 参数必须包含 min 和 max'
            }

        min_value = rule_value['min']
        max_value = rule_value['max']

        if min_value > max_value:
            return {
                '问题': True,
                '异常列': column,
                '异常行号': [],
                '原因': '范围参数错误：min 不能大于 max'
            }

        numeric_data = pd.to_numeric(
            data, errors='coerce'
        )

        # 非空但无法转换为数字的值，也视为异常
        invalid_mask = data.notna() & numeric_data.isna()

        bad_mask = (
            (numeric_data < min_value)
            | (numeric_data > max_value)
            | invalid_mask
        )

        return make_result(
            column,
            data[bad_mask].index,
            f"'{column}'不符合数值范围要求"
        ) if bad_mask.any() else make_result(
            column, [], f"'{column}'符合范围要求"
        )

    # --------------------------
    # 规则五：格式检查
    # --------------------------

    elif rule_type == 'format':

        if not isinstance(rule_value, str):
            return {
                '问题': True,
                '异常列': column,
                '异常行号': [],
                '原因': 'format 参数必须是正则表达式字符串'
            }

        try:
            re.compile(rule_value)
        except re.error as e:
            return {
                '问题': True,
                '异常列': column,
                '异常行号': [],
                '原因': f'正则表达式无效：{e}'
            }

        def matches_format(value):
            if pd.isna(value):
                return True

            return bool(
                re.fullmatch(rule_value, str(value))
            )

        bad_mask = ~data.map(matches_format)

        return make_result(
            column,
            data[bad_mask].index,
            f"'{column}'存在不符合格式的值"
        ) if bad_mask.any() else make_result(
            column, [], f"'{column}'符合格式要求"
        )

    # --------------------------
    # 规则六：自定义逻辑检查
    # --------------------------

    elif rule_type == 'logic':

        if not callable(rule_value):
            return {
                '问题': True,
                '异常列': column,
                '异常行号': [],
                '原因': 'logic 参数必须是可调用函数'
            }

        bad_indexes = []

        for index, value in data.items():
            try:
                # 自定义规则返回 True 代表合法
                if not bool(rule_value(value)):
                    bad_indexes.append(index)

            except Exception:
                bad_indexes.append(index)

        return make_result(
            column,
            bad_indexes,
            f"'{column}'不符合自定义校验规则"
        ) if bad_indexes else make_result(
            column, [], f"'{column}'符合自定义规则"
        )






import math
import re


def validate_rule_config(rule):
    """
    检查规则配置是否合法。

    返回：
        (True, "规则配置合法")
        (False, "具体错误原因")
    """

    # 第一层：检查规则的外部结构
    if not isinstance(rule, dict):
        return False, "规则配置必须是字典"

    required_fields = {
        "column",
        "rule_type",
        "rule_value"
    }

    if not required_fields.issubset(rule):
        return False, "规则缺少必要字段"

    # 第二层：检查字段名
    column = rule["column"]

    if not isinstance(column, str):
        return False, "column 必须是字符串"

    if not column.strip():
        return False, "column 不能为空"

    # 第三层：检查规则类型
    rule_type = rule["rule_type"]

    if not isinstance(rule_type, str):
        return False, "rule_type 必须是字符串"

    supported_rule_types = {
        "not_null",
        "unique",
        "type",
        "range",
        "format",
        "logic"
    }

    if rule_type not in supported_rule_types:
        return False, f"不支持的规则类型：{rule_type}"

    # 第四层：获取规则参数
    rule_value = rule["rule_value"]

    # 第五层：根据不同规则检查参数
    if rule_type in {"not_null", "unique"}:
        if rule_value is not None:
            return False, (
                f"{rule_type} 规则的 rule_value 必须是 None"
            )

    elif rule_type == "type":
        supported_types = {"int", "float", "str"}

        if rule_value not in supported_types:
            return False, (
                "type 的 rule_value 必须是 int、float 或 str"
            )

    elif rule_type == "range":
        if not isinstance(rule_value, dict):
            return False, "range 的 rule_value 必须是字典"

        if "min" not in rule_value or "max" not in rule_value:
            return False, "range 必须包含 min 和 max"

        min_value = rule_value["min"]
        max_value = rule_value["max"]

        # 布尔值不能当成数值边界
        if (
            isinstance(min_value, bool)
            or isinstance(max_value, bool)
            or not isinstance(min_value, (int, float))
            or not isinstance(max_value, (int, float))
        ):
            return False, "min 和 max 必须是数字"

        # 排除 NaN 和正负无穷大
        if (
            not math.isfinite(min_value)
            or not math.isfinite(max_value)
        ):
            return False, "min 和 max 必须是有限数字"

        if min_value > max_value:
            return False, "range 的 min 不能大于 max"

    elif rule_type == "format":
        if not isinstance(rule_value, str):
            return False, "format 的 rule_value 必须是字符串"

        try:
            re.compile(rule_value)
        except re.error as e:
            return False, f"正则表达式不合法：{e}"

    elif rule_type == "logic":
        if not callable(rule_value):
            return False, "logic 的 rule_value 必须是可调用对象"

    # 所有检查通过
    return True, "规则配置合法"

# ==============================
# 4. 执行多条规则
# ==============================
# 1.检查规则配置
# 2.配置合法才执行
# 3.出错也不中断其他规则




def run_rules(df, rules):
    results = []

    for rule_index, rule in enumerate(rules):
        column = "未知字段"

        try:
            if not isinstance(rule, dict):
                raise TypeError("规则配置必须是字典")

            column = rule.get("column", "未知字段")
            rule_type = rule.get("rule_type")
            rule_value = rule.get("rule_value")

            result = validate_data(
                df,
                column,
                rule_type,
                rule_value
            )

        except Exception as e:
            results.append({
                "问题": True,
                "异常列": column,
                "异常行号": [],
                "原因": (
                    f"第 {rule_index + 1} 条规则执行失败："
                    f"{type(e).__name__}: {e}"
                )
            })
            continue

        results.append(result)

    return results




# ==============================
# 5. 生成异常报告
# ==============================

def build_validation_report(df, rules, results):

    report = []

    for result in results:

        if not result['问题']:
            continue

        column = result['异常列']
        row_indexes = result['异常行号']
        reason = result['原因']

        # 没有具体行号：通常是列名或规则参数错误
        if not row_indexes:
            report.append({
                'column': column,
                'row_index': None,
                'reason': reason
            })
            continue

        for row_index in row_indexes:
            report.append({
                'column': column,
                'row_index': row_index,
                'reason': reason
            })

    return report


# ==============================
# 6. 数据清洗：暂不自动修改
# ==============================

def clean_file(df,strategy,column,value=None):
    # df:要處理的數據，column：需要指定处理的列，某些时候不需要！
    # ,strateg：用户选择的清洗的策略,value=None：清洗参数例如填充值或目标数据类型
    # 比如clean_file(df,'dropna,'column='某一列',value='int')
    cleaned_df=df.copy()
    if strategy=='fillna':
        # 填补空值
        cleaned_df[column]=cleaned_df[column].fillna(value)
        # 为了保护原始数据，复制一个再修改为副本
        
        
    elif strategy=='dropna':
        cleaned_df=cleaned_df.dropna(subset=[column])
        # cleaned_df=cleaned_df.reset_index(drop=True)
        # subset():指定哪些列用于判断是否删除行
        # 删除空值所在的行
        
    elif strategy=='astype':
        # 转换数据类型
        cleaned_df[column]=cleaned_df[column].astype(value)
    else:
        # 不支持
        print('不支持策略')
    return cleaned_df



# ==============================
# 7. 数据分析：后续实现
# ==============================

def analyze_file():
    pass