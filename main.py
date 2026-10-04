from micronConverter import markdownToMicron
from datetime import datetime
from pathlib import Path
import requests
import json
import re

print('''
 _   _                                
( ) ( )                               
| | | |    __     ___ ___      _     ___ 
| , ` |  /'__`\ /' _ ` _ `\  /'_`\  /',__)
| |`\ | (  ___/ | ( ) ( ) | ( (_) ) \__, |
(_) (_) `\____) (_) (_) (_) `\___/' (____/
------------------------------------------
''')

# Variables
configPath = Path('config.json')

# Read the config file
if configPath.exists():
    print('Found a config file! reading...')

    with open('config.json', 'r') as f:
        settings = json.load(f)

        # Check the url parameter
        url = settings.get('url')
        if url:
            print('    Url parameter found!')
            url += '/api/v1/memos'
        else:   
            print('    Could not find url parameter, throwing error!')
            raise Exception('Invalid config! missing url parameter')

        # Check optional parameters
        tag = settings.get('tag')
        outputFolder = settings.get('output', 'output')
        styling = settings.get('styling')

        print('Finished reading config file!')
else:
    # Throw an error if the config file couldn't be found
    print('    Could not find a config json file, throwing error!')
    raise Exception('Missing config file! check name of file')

# Get memos
print('\nGetting memos...')
response = requests.request('GET', url)

if response.status_code == 200:
    print('    Got 200 response back!')

    # Take the little response and make it into a dict
    response = json.loads(response.text)
    
    memos = []
    # Go through the memos one at a time
    for memo in response.get('memos'):
        rawTags = memo.get('tags')

        # If the tag parameter is set then check if this memo has the correct tag
        if tag and tag not in rawTags:
            continue

        # Process tags
        tags = []
        for tag in rawTags:
            tags.append('#' + tag)

        print('    Found a post!')

        # Grab shit
        print('        Gathering info...')
        
        content = memo.get('content')
        name = content.split("\n")[0].lstrip("#").strip() # Take heading

        print('        Processing content...')
        content = re.sub(r"^# .*\n+", "", content, count=1) # Remove heading
        content = re.sub(r"#\w+", "", content) # Remove hashtags
        content = markdownToMicron(content, styling) # Make it micron

        # Get and convert update time
        print('        Converting time into datetime object')
        timeStamp = memo.get('updateTime')
        timeStamp = datetime.fromisoformat(timeStamp.replace("Z", "+00:00"))

        date = timeStamp.date()
        time = timeStamp.time()

        # Get creator and id
        user = memo.get('creator')
        user = user[6:]

        uid = memo.get('name')
        uid = uid[6:]

        print(f'''        Info grabbed!
            Id: {uid}
            Title: {name}
            Content: {content[:10]}...
            Date: {str(date)}
            Time: {str(time)}
            User: {user}''')

        # Make value dict for parsing function
        values = {
            'title': name,
            'content': content[:-1], # Have to remove final newline character
            'date': str(date),
            'time': str(time),
            'user': user,
            'hash': ', '.join(tags),
            'naviLink': outputFolder + '/navi.mu',
            'prev': content.strip('\n')[:30],
            'link': f'{outputFolder}/{uid}.mu'
        }

        # Read post templates
        print('        Reading post template...')
        with open('templates/post.mu', 'r') as f:
            postTemplate = f.read()

        # Go through changing the sections in double curly brackets
        print('        Going through template...')
        post = re.sub(
            r'\{\{\s*(.*?)\s*\}\}',
            lambda match: values.get(match.group(1), match.group(0)),
            postTemplate
        )

        # Write the output to a micron file in the output folder
        with open(f'{outputFolder}/{uid}.mu', 'w') as f:
            f.write(post)
            print('        Wrote output to file!')

        # Open entry template
        print('        Reading entry template...')
        with open('templates/entry.mu', 'r') as f:
            entryTemplate = f.read()

        # Go through changing the sections in double curly brackets
        entry = re.sub(
            r'\{\{\s*(.*?)\s*\}\}',
            lambda match: values.get(match.group(1), match.group(0)),
            entryTemplate
        )

        # Append this output to the memos list
        print('        Saved changed entry!')
        memos.append(entry)
    
    print('\nMaking navi page...')
    
    # Edit the values dict to have one entry so I can use the same function I used earlier
    values = {
        'posts': '\n\n'.join(memos)
    }

    # Open template    
    with open('templates/navi.mu', 'r') as f:
        naviTemplate = f.read()
        print('    Reading navi template...')

    navi = re.sub(
        r'\{\{\s*(.*?)\s*\}\}',
        lambda match: values.get(match.group(1), match.group(0)),
        naviTemplate
    )

    with open(f'{outputFolder}/navi.mu', 'w') as f:
        f.write(navi)
        print('    Wrote to output file!')

    print(f'\nFINISHED - {len(memos)} Memos Found, Wrote to "{outputFolder}"!')

else:
    print(f'    Got {response.status_code} response from request, throwing error!')
    raise Exception(f'{response.status_code} Response! Check server')