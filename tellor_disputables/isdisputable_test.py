import data

test_query_id = "0x0000000000000000000000000000000000000000000000000000000000000001"
test_val = 2100.0
test_threshold = 0.05

print((2767 - test_val) / test_val)
print("is disputable: ", data.is_disputable(test_val, test_query_id, test_threshold))
