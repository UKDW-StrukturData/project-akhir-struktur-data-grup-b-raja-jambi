from src import ai_helper

result = ai_helper.ai_search_recipes('ayam', 'testuser', max_results=5)
print(f'Found {len(result)} recipes')
for r in result[:3]:
    print(f"  - {r.get('title')}")
