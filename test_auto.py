
from tool import validate_rule_config

# 测试一：合法配置
valid_rule = {
    "column": "price",
    "rule_type": "range",
    "rule_value": {"min": 0, "max": 1000}
}

print(validate_rule_config(valid_rule))
assert validate_rule_config(valid_rule)[0] is True

# 测试二：不是字典
assert validate_rule_config(None)[0] is False

# 测试三：缺少 rule_value
invalid_rule = {
    "column": "price",
    "rule_type": "range"
}

assert validate_rule_config(invalid_rule)[0] is False

print("PASS：规则配置结构测试通过！")



from tool import validate_rule_config


def check_rule(name, rule, expected):
    """检查规则配置，并输出测试结果。"""
    result = validate_rule_config(rule)

    print(f"{name}: {result}")

    assert result[0] is expected, (
        f"{name} 失败：预期 {expected}，实际得到 {result[0]}"
    )


# 1. 合法的范围规则
check_rule(
    "合法范围",
    {
        "column": "price",
        "rule_type": "range",
        "rule_value": {"min": 0, "max": 1000}
    },
    True
)

# 2. 规则不是字典
check_rule(
    "错误外部类型",
    None,
    False
)

# 3. 缺少 rule_value
check_rule(
    "缺少字段",
    {
        "column": "price",
        "rule_type": "range"
    },
    False
)

# 4. 不支持的规则类型
check_rule(
    "不支持的规则",
    {
        "column": "price",
        "rule_type": "unknown",
        "rule_value": None
    },
    False
)

# 5. 范围上下限颠倒
check_rule(
    "上下限颠倒",
    {
        "column": "price",
        "rule_type": "range",
        "rule_value": {"min": 1000, "max": 0}
    },
    False
)

# 6. 缺少 max
check_rule(
    "缺少 max",
    {
        "column": "price",
        "rule_type": "range",
        "rule_value": {"min": 0}
    },
    False
)

# 7. 布尔值不能当作范围边界
check_rule(
    "布尔值边界",
    {
        "column": "price",
        "rule_type": "range",
        "rule_value": {"min": True, "max": 1000}
    },
    False
)

# 8. NaN 不能当作范围边界
check_rule(
    "NaN 边界",
    {
        "column": "price",
        "rule_type": "range",
        "rule_value": {"min": float("nan"), "max": 1000}
    },
    False
)

# 9. 合法的类型规则
check_rule(
    "合法类型",
    {
        "column": "price",
        "rule_type": "type",
        "rule_value": "float"
    },
    True
)

# 10. 非法的类型规则
check_rule(
    "非法类型",
    {
        "column": "price",
        "rule_type": "type",
        "rule_value": "number"
    },
    False
)

# 11. 合法的正则表达式
check_rule(
    "合法格式",
    {
        "column": "phone",
        "rule_type": "format",
        "rule_value": r"\d{11}"
    },
    True
)

# 12. 非法的正则表达式
check_rule(
    "非法格式",
    {
        "column": "phone",
        "rule_type": "format",
        "rule_value": "["
    },
    False
)

# 13. 空值规则不需要额外参数
check_rule(
    "合法空值规则",
    {
        "column": "name",
        "rule_type": "not_null",
        "rule_value": None
    },
    True
)

rules = [
    {"column": "price", "rule_type": "range",
     "rule_value": {"min": 0, "max": 1000}},

    None,  # 故意放入一条错误规则

    {"column": "name", "rule_type": "not_null",
     "rule_value": None}
]


print("\nPASS：规则配置验证测试全部通过！")