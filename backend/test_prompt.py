import sys
sys.path.insert(0, r'D:\Project\AI Tutor\backend')

try:
    from agent.prompt import INSTRUCTOR_PROMPT
    result = INSTRUCTOR_PROMPT.format(input='测试问题')
    print('Success!')
    print(result[:300])
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
