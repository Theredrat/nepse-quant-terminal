import os
workflow_dir = '.github/workflows'
if os.path.exists(workflow_dir):
    for f in os.listdir(workflow_dir):
        print(f'=== {f} ===')
        print(open(f'{workflow_dir}/{f}', encoding='utf-8').read())
else:
    print('No workflows folder found')
