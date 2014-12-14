import json
from functools import partial
import IPython.nbformat as nbf
import mistune

# nb to markdown
# -----------------------------------------------------------------------------
def process_cell_markdown(cell):
    return ''.join(cell.get('source', [])) + '\n'

def process_cell_input(cell, lang=None):
    # input_lines = cell.get('input', [])  # nbformat 3
    input_lines = cell.get('source', [])  # nbformat 4
    code = ''.join(input_lines)
    code = '```{0:s}\n'.format(lang or '') + code + '\n```\n'
    return code

def process_cell(cell, lang=None):
    cell_type = cell.get('cell_type', None)
    if cell_type == 'markdown':
        return process_cell_markdown(cell)
    elif cell_type == 'code':
        return process_cell_input(cell, lang=lang)

def _merge_successive_inputs(cells):
    """Return a new list of cells where successive input cells are merged
    together."""
    cells_merged = []
    is_last_input = False
    for cell in cells:
        cell_type = cell.get('cell_type', None)
        is_input = cell_type == 'code'
        # If the last cell and the current cell are input cells.
        if is_last_input and is_input:
            # Extend the last cell input with the new cell.
            cells_merged[-1]['source'].extend(['\n'] + cell['source'])
        else:
            cells_merged.append(cell)
        # Save the last input cell.
        is_last_input = is_input
    return cells_merged

def nb_to_markdown(filepath, saveto=None):
    with open(filepath, "r") as f:
        nb = json.load(f)
    # Only work for nbformat 4 for now.
    assert nb['nbformat'] >= 4
    # cells = n-b['worksheets'][0]['cells']  # nbformat 3
    cells = nb['cells']
    # # Merge successive code inputs together.
    # cells = _merge_successive_inputs(cells)
    # Find the notebook language.
    lang = nb['metadata'].get('language_info', {}).get('name', 'python')
    md = '\n'.join([process_cell(_, lang=lang) for _ in cells])
    if saveto is None:
        return md
    else:
        with open(saveto, "w") as f:
            f.write(md)


# markdown to nb
# -----------------------------------------------------------------------------
class NotebookWriter(object):
    def __init__(self):
        self._nb = nbf.v4.new_notebook()

    def append_markdown(self, source):
        self._nb['cells'].append(nbf.v4.new_markdown_cell(source))

    def append_code(self, source):
        self._nb['cells'].append(nbf.v4.new_code_cell(source))

    def save(self, filepath):
        with open(filepath, 'w') as f:
            nbf.write(self._nb, f)


class MyRenderer(object):
    def __init__(self, **kwargs):
        self.options = kwargs
        self._nbwriter = NotebookWriter()

    def placeholder(self):
        return ''

    def block_code(self, code, lang):
        # Only explicit Python code becomes a code cell.
        if lang == 'python':
            self._nbwriter.append_code(code)
        else:
            self._nbwriter.append_markdown('```%s\n%s\n```' % (lang or '',
                                                               code.strip()))
        return code

    def block_quote(self, text):
        text = '\n'.join(('> ' + l)
                         for l in text.split('\n'))
        self._nbwriter.append_markdown(text)
        return text

    def block_html(self, html):
        self._nbwriter.append_markdown(html)
        return html

    def header(self, text, level, raw=None):
        text = ('#' * level) + ' ' + text
        self._nbwriter.append_markdown(text)
        return text

    def hrule(self):
        return ''

    def list(self, body, ordered=True):
        items = body.strip().split('\n')
        if ordered:
            text = '\n'.join('%d. %s' % (i+1,s) for i,s in enumerate(items))
        else:
            text = '\n'.join('* %s' % _ for _ in items)
        self._nbwriter.append_markdown(text)
        return text

    def list_item(self, text):
        return text + '\n'

    def paragraph(self, text):
        self._nbwriter.append_markdown(text)
        return text

    def table(self, header, body):
        pass

    def table_row(self, content):
        pass

    def table_cell(self, content, **flags):
        pass

    def autolink(self, link, is_email=False):
        pass

    def codespan(self, text):
        return '`%s`' % text

    def double_emphasis(self, text):
        return '**%s**' % text

    def emphasis(self, text):
        return '*%s*' % text

    def image(self, src, title, alt_text):
        return '![%s](%s)' % (title or alt_text, src)

    def linebreak(self, ):
        return '\n'

    def newline(self, ):
        return '\n'

    def link(self, link, title, content):
        return '[%s](%s)' % (content or title, link)

    def tag(self, html):
        return html

    def strikethrough(self, text):
        return '~~%s~~' % text

    def text(self, text):
        return text


def markdown_to_nb(filepath, saveto=None):
    with open(filepath, 'r') as f:
        contents = f.read()
    renderer = MyRenderer()
    md = mistune.Markdown(renderer=renderer)
    md.render(contents)
    renderer._nbwriter.save(saveto)