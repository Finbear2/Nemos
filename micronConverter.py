from markdown_it import MarkdownIt

# Make markdown it variable because of it's great token splitter
markdown = MarkdownIt()

# Outline basic markdown elements and their micron counterpart
micron = {
    'boldStart': '`!',
    'boldEnd': '`!',
    'italicStart': '`*',
    'italicEnd': '`*',
    'underlineStart': '`_',
    'underlineEnd': '`_',
    'inlineCodeStart': '`*',
    'inlineCodeEnd': '`*',
    'linkStart': '`_(',
    'linkCloseStart': ')[',
    'linkCloseEnd': ']`_',
    'imageStart': '`!',
    'imageEnd': '`!',
    'heading': '>',
    'bullet': '•',
    'hr': '---',
    'codeStart': '`B000`F0f0',
    'codeEnd': '``\n',
    # Not a markdown token but I felt it needed
    'codeLanguagePlaceholder': 'text'
}

# Make a function to convert inline markdown tokens
def convertInline(token):
    # Make basic variables
    output = ''
    link_url = None

    if not token.children:
        return token.content

    for child in token.children:

        # Handle normal text
        if child.type == 'text':
            output += child.content

        # Handle inline elements
        elif child.type == 'code_inline':
            output += micron['inlineCodeStart'] + child.content+ micron['inlineCodeEnd']

        elif child.type == 'strong_open':
            output += micron['boldStart']

        elif child.type == 'strong_close':
            output += micron['boldEnd']

        elif child.type == 'em_open':
            output += micron['italicStart']

        elif child.type == 'em_close':
            output += micron['italicEnd']

        elif child.type == 'link_open':
            link_url = child.attrGet('href')
            output += micron['linkStart']

        elif child.type == 'link_close':
            start = micron['linkCloseStart']
            end = micron['linkCloseEnd']
            output += start + link_url + end
            link_url = None

        elif child.type == 'softbreak':
            output += '\n'

        elif child.type == 'hardbreak':
            output += '\n'

        elif child.type == 'image':
            alt = child.content
            output += micron['imageStart'] + alt + micron['imageEnd']

    return output

# Basic markdown to micron heading converter
def convertHeading(level):
    return micron['heading'] * level + ' '

# Main markdown to micron function called by main.py
def markdownToMicron(text, styling):

    # Go through and check config.json for any differences from preset
    for parameter in micron.keys():
        micron[parameter] = styling.get(parameter, micron[parameter])

    # Get the tokens
    tokens = markdown.parse(text)

    # Make variables
    output = []
    headingLevel = None
    listDepth = 0
    listType = None
    listNumber = 0
    insideListItem = False

    # Go through tokens
    for token in tokens:

        # Headings
        if token.type == 'heading_open':
            headingLevel = int(token.tag[1])

        elif token.type == 'inline':

            if headingLevel is not None:
                # Keep the heading marker and heading text together.
                output.append(
                    convertHeading(headingLevel) + convertInline(token)
                )

                headingLevel = None

            # Lists
            elif insideListItem:
                indent = '    ' * (listDepth - 1)
                bullet = micron['bullet']

                if listType == 'ordered':
                    output.append(
                        f'{indent}{listNumber}. {convertInline(token)}'
                    )
                else:
                    output.append(
                        f'{indent}{bullet} {convertInline(token)}'
                    )

                insideListItem = False

            else:
                # Convert inline components
                output.append(convertInline(token))

        # Stops blank lines in lists
        elif token.type == 'paragraph_close':
            if listDepth == 0:
                output.append('')

        # Horizontal rule
        elif token.type == 'hr':
            output.append(micron['hr'])

        # Code block
        elif token.type == 'fence':
            language = token.info.strip()

            if not language:
                language = micron['codeLanguagePlaceholder']

            output.append(f"{micron['codeStart']}{language}")
            output.append(token.content.rstrip('\n'))
            output.append(micron['codeEnd'])

        # Bullet list
        elif token.type == 'bullet_list_open':
            listDepth += 1
            listType = 'bullet'

        elif token.type == 'bullet_list_close':
            listDepth -= 1

            if listDepth == 0:
                listType = None
                output.append('')

        # Ordered list
        elif token.type == 'ordered_list_open':
            listDepth += 1
            listType = 'ordered'
            listNumber = 0

        elif token.type == 'ordered_list_close':
            listDepth -= 1

            if listDepth == 0:
                listType = None
                output.append('')

        # List item
        elif token.type == 'list_item_open':
            insideListItem = True

            if listType == 'ordered':
                listNumber += 1

        elif token.type == 'list_item_close':
            insideListItem = False

    # Return the output
    return '\n'.join(output)

# Test run for easy testing
if __name__ == '__main__':
    import json

    with open('config.json', 'r') as f:
        config = json.load(f)

    styling = config.get('styling')
    with open('test.mu', 'w') as f:
        f.write(markdownToMicron('''
# Hello

This is a **paragraph**.

---

## This is **another heading**

And this is _some text_.

- Hi
- Hello
- **Bold item**
- *Italic item*

1. First
2. Second
3. Third

```
print('hello')

if True:
    meow()
````

[title](https://www.example.com)
''', styling))